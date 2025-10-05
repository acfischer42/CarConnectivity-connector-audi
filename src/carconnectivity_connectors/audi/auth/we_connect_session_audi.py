"""
Module implements the WeConnect Session handling.
"""
from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING

import requests
from carconnectivity.errors import AuthenticationError, RetrievalError, TemporaryAuthenticationError
from oauthlib.common import to_unicode
from oauthlib.oauth2 import InsecureTransportError, is_secure_transport
from requests.models import CaseInsensitiveDict

from carconnectivity_connectors.audi.auth.audi_web_session import AudiWebSession
from carconnectivity_connectors.audi.auth.openid_session import AccessType

if TYPE_CHECKING:
    pass


LOG: logging.Logger = logging.getLogger("carconnectivity.connectors.audi.auth")


class WeConnectSession(AudiWebSession):
    """
    WeConnectSession class handles the authentication and session management for Audi's WeConnect service.
    """

    def __init__(self, session_user, **kwargs) -> None:
        # Let the parent AudiWebSession handle the client_id and redirect_uri
        # Pass only the necessary parameters that don't conflict
        kwargs["session_user"] = session_user
        kwargs["cache"] = kwargs.get("cache", {})
        super(WeConnectSession, self).__init__(**kwargs)

        # Force the correct client_id after initialization
        self.client_id = "09b6cbec-cd19-4589-82fd-363dfa8c24da@apps_vw-dilab_com"
        self.redirect_uri = "myaudi:///"

        LOG.debug(f"WeConnectSession initialized with client_id: {self.client_id}")
        LOG.debug(f"WeConnectSession initialized with redirect_uri: {self.redirect_uri}")

        self.headers = CaseInsensitiveDict(
            {
                "accept": "*/*",
                "content-type": "application/json",
                "content-version": "1",
                "x-newrelic-id": "VgAEWV9QDRAEXFlRAAYPUA==",
                "user-agent": "WeConnect/3 CFNetwork/1331.0.7 Darwin/21.4.0",
                "accept-language": "de-de",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
        )

    def request(
        self,
        method,
        url,
        data=None,
        headers=None,
        withhold_token=False,
        access_type=AccessType.ACCESS,
        token=None,
        timeout=None,
        **kwargs,
    ):
        """Intercept all requests and add weconnect-trace-id header."""

        import secrets

        traceId = secrets.token_hex(16)
        we_connect_trace_id = (
            traceId[:8] + "-" + traceId[8:12] + "-" + traceId[12:16] + "-" + traceId[16:20] + "-" + traceId[20:]
        ).upper()
        headers = headers or {}
        headers["weconnect-trace-id"] = we_connect_trace_id

        return super(WeConnectSession, self).request(
            method,
            url,
            headers=headers,
            data=data,
            withhold_token=withhold_token,
            access_type=access_type,
            token=token,
            timeout=timeout,
            **kwargs,
        )

    def login(self):
        # Use the simple working flow that bypasses MBB registration
        LOG.info("Starting simple Audi authentication flow")

        # Don't call the complex dual-token super().login()
        # Instead, use the direct OAuth2 approach

        # Generate authorization URL
        authorization_url_str: str = self.authorization_url(url="https://identity.vwgroup.io/oidc/v1/authorize")
        LOG.debug(f"Generated authorization URL: {authorization_url_str[:100]}...")

        # Perform web authentication (this should work with the original AudiWebSession.do_web_auth)
        response = self.do_web_auth(authorization_url_str)
        LOG.debug(f"Web auth completed, got response: {response[:100]}...")

        # Parse tokens directly from the OAuth response
        try:
            self.parse_from_fragment(response)
            LOG.info("Login successful - tokens obtained from OAuth flow!")
        except Exception as parse_error:
            LOG.error(f"Failed to parse authentication response: {parse_error}")
            LOG.debug(f"Response that failed to parse: {response}")
            raise

        # Set the last_login time
        self.last_login = time.time()

    def refresh(self) -> None:
        # Try refresh tokens from refresh endpoint first
        try:
            LOG.info("Attempting token refresh from refresh endpoint")
            self.refresh_tokens(
                "https://emea.bff.cariad.digital/user-login/refresh/v1",
            )
            LOG.info("Token refresh from endpoint successful")
        except Exception as e:
            LOG.warning(f"Token refresh from endpoint failed: {e}")
            LOG.info("Falling back to full re-authentication using working login flow")
            # Fall back to the same login process that worked initially
            try:
                self.login()
                LOG.info("Fallback re-authentication successful")
            except Exception as login_error:
                LOG.error(f"Fallback re-authentication also failed: {login_error}")
                raise

    def authorization_url(self, url, state=None, **kwargs) -> str:
        # Use the same approach as the working VW version
        # Call the parent class authorization_url method directly
        return super(WeConnectSession, self).authorization_url(url=url, state=state, **kwargs)

    def fetch_tokens(self, token_url, authorization_response=None, **_):
        """
        Fetches tokens using the given token URL using the tokens from authorization response.

        Args:
            token_url (str): The URL to request the tokens from.
            authorization_response (str, optional): The authorization response containing the tokens. Defaults to None.
            **_ : Additional keyword arguments.

        Returns:
            dict: A dictionary containing the fetched tokens if successful.
            None: If the tokens could not be fetched.

        Raises:
            TemporaryAuthenticationError: If the token request fails due to a temporary WeConnect failure.
        """
        # take token from authorization response (those are stored in self.token now!)
        self.parse_from_fragment(authorization_response)

        if self.token is not None and all(key in self.token for key in ("state", "id_token", "access_token", "code")):
            # Generate json body for token request
            body: str = json.dumps(
                {
                    "state": self.token["state"],
                    "id_token": self.token["id_token"],
                    "redirect_uri": self.redirect_uri,
                    "region": "emea",
                    "access_token": self.token["access_token"],
                    "authorizationCode": self.token["code"],
                }
            )

            request_headers: CaseInsensitiveDict = self.headers  # pyright: ignore reportAssignmentType
            request_headers["accept"] = "application/json"

            # request tokens from token_url
            token_response = self.post(
                token_url, headers=request_headers, data=body, allow_redirects=False, access_type=AccessType.ID
            )  # pyright: ignore reportCallIssue
            if token_response.status_code != requests.codes["ok"]:
                raise TemporaryAuthenticationError(
                    f"Token could not be fetched due to temporary WeConnect failure: {token_response.status_code}"
                )
            # parse token from response body
            token = self.parse_from_body(token_response.text)

            return token
        return None

    def parse_from_body(self, token_response, state=None):
        """
        Fix strange token naming before parsing it with OAuthlib.
        """
        try:
            # Tokens are in body of response in json format
            token = json.loads(token_response)
        except json.decoder.JSONDecodeError as err:
            raise TemporaryAuthenticationError(
                "Token could not be refreshed due to temporary WeConnect failure: json could not be decoded"
            ) from err
        # Fix token keys, we want access_token instead of accessToken
        if "accessToken" in token:
            token["access_token"] = token.pop("accessToken")
        # Fix token keys, we want id_token instead of idToken
        if "idToken" in token:
            token["id_token"] = token.pop("idToken")
        # Fix token keys, we want refresh_token instead of refreshToken
        if "refreshToken" in token:
            token["refresh_token"] = token.pop("refreshToken")
        # generate json from fixed dict
        fixed_token_response = to_unicode(json.dumps(token)).encode("utf-8")
        # Let OAuthlib parse the token
        return super(WeConnectSession, self).parse_from_body(token_response=fixed_token_response, state=state)

    def refresh_tokens(
        self, token_url, refresh_token=None, auth=None, timeout=None, headers=None, verify=True, proxies=None, **_
    ):
        """
        Refreshes the authentication tokens using the provided refresh token.
        Args:
            token_url (str): The URL to request new tokens from.
            refresh_token (str, optional): The refresh token to use. Defaults to None.
            auth (tuple, optional): Authentication credentials. Defaults to None.
            timeout (float or tuple, optional): How long to wait for the server to send data before giving up.
                Defaults to None.
            headers (dict, optional): Headers to include in the request. Defaults to None.
            verify (bool, optional): Whether to verify the server's TLS certificate. Defaults to True.
            proxies (dict, optional): Proxies to use for the request. Defaults to None.
            **_ (dict): Additional arguments.
        Raises:
            ValueError: If no token endpoint is set for auto_refresh.
            InsecureTransportError: If the token URL is not secure.
            AuthenticationError: If the server requests new authorization.
            TemporaryAuthenticationError: If the token could not be refreshed due to a temporary server failure.
            RetrievalError: If the status code from the server is not recognized.
        Returns:
            dict: The new tokens.
        """
        LOG.info("Refreshing tokens")
        if not token_url:
            raise ValueError("No token endpoint set for auto_refresh.")

        if not is_secure_transport(token_url):
            raise InsecureTransportError()

        # Store old refresh token in case no new one is given
        refresh_token = refresh_token or self.refresh_token

        if headers is None:
            headers = self.headers

        # Request new tokens using the refresh token
        token_response = self.get(
            token_url,
            auth=auth,
            timeout=timeout,
            headers=headers,
            verify=verify,
            withhold_token=False,  # pyright: ignore reportCallIssue
            proxies=proxies,
            access_type=AccessType.REFRESH,  # pyright: ignore reportCallIssue
        )
        if token_response.status_code == requests.codes["unauthorized"]:
            raise AuthenticationError("Refreshing tokens failed: Server requests new authorization")
        elif token_response.status_code in (
            requests.codes["internal_server_error"],
            requests.codes["service_unavailable"],
            requests.codes["gateway_timeout"],
        ):
            raise TemporaryAuthenticationError(
                "Token could not be refreshed due to temporary WeConnect failure: {tokenResponse.status_code}"
            )
        elif token_response.status_code == requests.codes["ok"]:
            # parse new tokens from response
            self.parse_from_body(token_response.text)
            if self.token is not None and "refresh_token" not in self.token:
                LOG.debug("No new refresh token given. Re-using old.")
                self.token["refresh_token"] = refresh_token
            return self.token
        else:
            raise RetrievalError(f"Status Code from WeConnect while refreshing tokens was: {token_response.status_code}")
