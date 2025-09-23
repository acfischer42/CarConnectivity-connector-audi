"""
Module implements an Audi Web session with dual-token authentication.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

import json
import logging
import time
from urllib.parse import parse_qsl, urlparse, urlsplit, urljoin

from urllib3.util.retry import Retry

import requests
from requests.adapters import HTTPAdapter
from requests.models import CaseInsensitiveDict

from carconnectivity.errors import APICompatibilityError, AuthenticationError, RetrievalError

from carconnectivity_connectors.audi.auth.auth_util import CredentialsFormParser, HTMLFormParser, TermsAndConditionsFormParser
from carconnectivity_connectors.audi.auth.openid_session import OpenIDSession

if TYPE_CHECKING:
    from typing import Any, Dict

LOG = logging.getLogger("carconnectivity.connectors.audi.auth")


class AudiWebSession(OpenIDSession):
    """
    AudiWebSession handles the web authentication process for Audi's web services.
    Implements dual-token authentication system:
    - VW Token (vwToken): For legacy VW Group APIs
    - Bearer Token (_bearer_token_json): For modern Cariad BFF APIs
    """
    def __init__(self, session_user, cache, accept_terms_on_login=False, country='DE', language='de', **kwargs):
        # Audi-specific client_id and redirect_uri (from audi_connect_ha)
        audi_client_id = '09b6cbec-cd19-4589-82fd-363dfa8c24da@apps_vw-dilab_com'
        audi_redirect_uri = 'myaudi:///'
        audi_scope = 'address profile badge birthdate birthplace nationalIdentifier nationality profession email vin phone nickname name picture mbb gallery openid'
        kwargs['client_id'] = audi_client_id
        kwargs['redirect_uri'] = audi_redirect_uri
        kwargs['scope'] = audi_scope
        super(AudiWebSession, self).__init__(**kwargs)
        self.session_user = session_user
        self.cache = cache
        self.accept_terms_on_login: bool = accept_terms_on_login
        self.country = country
        self.language = language

        # Dual token system
        self.vwToken = None  # Legacy VW Group API token
        self._bearer_token_json = None  # Modern Cariad BFF API token
        
        # Configuration URLs
        self.region = 'emea'  # Can be 'emea', 'na', etc.
        self.market_config = None
        self.openid_config = None
        
        # Dynamic client registration for MBB OAuth
        self.client_secret = None
        self.registration_data = {
            "client_name": "CarConnectivity-Python",
            "platform": "android",
            "client_brand": "Audi",
            "appName": "myAudi",
            "appVersion": "4.31.0",
            "appId": "de.myaudi.mobile.assistant",
        }

        # Set up the web session
        retries = Retry(
            total=self.retries,
            backoff_factor=0.1,
            status_forcelist=[500],
            raise_on_status=False
        )

        self.websession: requests.Session = requests.Session()
        self.websession.proxies.update(self.proxies)
        self.websession.mount('https://', HTTPAdapter(max_retries=retries))
        # Audi-specific user-agent and headers (from audi_connect_ha mobile app pattern)
        self.websession.headers = CaseInsensitiveDict({
            'user-agent': 'myAudi-Android/4.31.0 (Android 11; SDK 30)',
            'accept': 'application/json, text/plain, */*',
            'accept-language': f'{self.language}-{self.country},{self.language};q=0.9',
            'accept-encoding': 'gzip, deflate',
            'x-requested-with': 'de.audi.myaudi',
            'x-app-version': '4.31.0',
            'x-app-name': 'myAudi',
            'upgrade-insecure-requests': '1',
        })

    def do_web_auth(self, url: str) -> str:
        """
        Perform web authentication using the provided URL.

        This method handles the web authentication process by:
        1. Retrieving the login form.
        2. Setting the email to the provided username.
        3. Retrieving the password form.
        4. Setting the credentials (email and password).
        5. Logging in and getting the redirect URL.
        6. Checking the URL for terms and conditions and handling consent if required.
        7. Following redirects until the final URL is reached.

        Args:
            url (str): The URL to start the authentication process.

        Returns:
            str: The final URL after successful authentication.

        Raises:
            AuthenticationError: If terms and conditions need to be accepted.
            RetrievalError: If there is a temporary server error during login.
            APICompatibilityError: If forwarding occurs without 'Location' in headers.
        """
        # Get the login form
        email_form: HTMLFormParser = self._get_login_form(url)

        # Set email to the provided username
        email_form.data['email'] = self.session_user.username

        # Get password form
        password_form = self._get_password_form(
            urljoin('https://identity.vwgroup.io', email_form.target),
            email_form.data
        )

        # Set credentials
        password_form.data['email'] = self.session_user.username
        password_form.data['password'] = self.session_user.password

        # Log in and get the redirect URL
        url = self._handle_login(
            f'https://identity.vwgroup.io/signin-service/v1/{self.client_id}/{password_form.target}',
            password_form.data
        )

        if self.redirect_uri is None:
            raise ValueError('Redirect URI is not set')
        # Check URL for terms and conditions
        while True:
            if url.startswith(self.redirect_uri):
                break

            url = urljoin('https://identity.vwgroup.io', url)

            if 'terms-and-conditions' in url:
                if self.accept_terms_on_login:
                    url = self._handle_consent_form(url)
                else:
                    raise AuthenticationError(f'It seems like you need to accept the terms and conditions. '
                                              f'Try to visit the URL "{url}" or log into smartphone app.')

            response = self.websession.get(url, allow_redirects=False)
            if response.status_code == requests.codes['internal_server_error']:
                raise RetrievalError('Temporary server error during login')

            if 'Location' not in response.headers:
                if 'consent' in url:
                    raise AuthenticationError('Could not find Location in headers, probably due to missing consent. Try visiting: ' + url)
                raise APICompatibilityError('Forwarding without Location in headers')

            url = response.headers['Location']

        return url.replace(self.redirect_uri + '#', 'https://egal?')

    def login(self):
        """
        Enhanced login method with dual-token authentication flow.
        """
        LOG.info("Starting Audi dual-token authentication flow")
        
        # Step 1: Get market configuration
        self._get_market_config()
        
        # Step 2: Get OpenID configuration
        self._get_openid_config()
        
        # Step 3: Perform standard OAuth2 authentication
        super().login()
        
        # Step 4: Register dynamic client and get VW token
        self._get_vw_token()
        
        # Step 5: Exchange for Bearer token via IDK
        self._get_bearer_token()
        
        # Step 6: Exchange for AZS token (Audi-specific)
        self._get_azs_token()
        
        LOG.info("Audi dual-token authentication completed successfully")

    def _get_market_config(self):
        """Get market-specific configuration for Audi services."""
        LOG.debug("Fetching market configuration")
        marketcfg_url = f"https://content.app.my.audi.com/service/mobileapp/configurations/market/{self.country}/{self.language}?v=4.23.1"
        
        response = self.websession.get(marketcfg_url)
        response.raise_for_status()
        
        self.market_config = response.json()
        LOG.debug(f"Market config retrieved for {self.country}/{self.language}")

    def _get_openid_config(self):
        """Get OpenID Connect configuration from Cariad BFF."""
        LOG.debug("Fetching OpenID configuration")
        openidcfg_url = f"https://{self.region}.bff.cariad.digital/login/v1/idk/openid-configuration"
        
        response = self.websession.get(openidcfg_url)
        response.raise_for_status()
        
        self.openid_config = response.json()
        LOG.debug("OpenID configuration retrieved")

    def _get_vw_token(self):
        """Get VW token via dynamic client registration and OAuth2."""
        LOG.debug("Starting VW token acquisition")
        
        # Dynamic client registration
        reg_url = "https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth/mobile/oauth2/v1/clients"
        
        response = self.websession.post(reg_url, json=self.registration_data)
        response.raise_for_status()
        
        client_data = response.json()
        self.client_secret = client_data.get('client_secret')
        
        # Get VW token using authorization code
        if self.token and 'code' in self.token:
            token_url = "https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth/mobile/oauth2/v1/token"
            
            token_data = {
                'grant_type': 'authorization_code',
                'code': self.token['code'],
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
            
            response = self.websession.post(token_url, data=token_data)
            response.raise_for_status()
            
            self.vwToken = response.json()
            LOG.debug("VW token acquired successfully")

    def _get_bearer_token(self):
        """Exchange VW token for Bearer token via IDK."""
        if not self.vwToken:
            raise AuthenticationError("VW token required for Bearer token exchange")
            
        LOG.debug("Starting Bearer token exchange")
        
        idk_token_url = f"https://{self.region}.bff.cariad.digital/login/v1/idk/token"
        
        token_data = {
            'grant_type': 'token_exchange',
            'subject_token': self.vwToken['access_token'],
            'subject_token_type': 'urn:ietf:params:oauth:token-type:access_token',
            'audience': 'https://api.apps.emea.vwapps.io',
            'client_id': self.client_id,
        }
        
        response = self.websession.post(idk_token_url, data=token_data)
        response.raise_for_status()
        
        self._bearer_token_json = response.json()
        LOG.debug("Bearer token acquired successfully")

    def _get_azs_token(self):
        """Exchange Bearer token for AZS token (Audi-specific services)."""
        if not self._bearer_token_json:
            raise AuthenticationError("Bearer token required for AZS token exchange")
            
        LOG.debug("Starting AZS token exchange")
        
        azs_token_url = f"https://{self.region}.bff.cariad.digital/login/v1/audi/token"
        
        headers = {
            'Authorization': f"Bearer {self._bearer_token_json['access_token']}",
            'Content-Type': 'application/json',
        }
        
        token_data = {
            'grant_type': 'token_exchange',
            'audience': 'https://api.apps.emea.vwapps.io',
        }
        
        response = self.websession.post(azs_token_url, json=token_data, headers=headers)
        response.raise_for_status()
        
        # Update Bearer token with AZS token
        azs_response = response.json()
        self._bearer_token_json.update(azs_response)
        LOG.debug("AZS token acquired successfully")

    def refresh(self):
        """Refresh both VW and Bearer tokens."""
        LOG.debug("Refreshing Audi tokens")
        
        # Refresh VW token if available
        if self.vwToken and 'refresh_token' in self.vwToken:
            self._refresh_vw_token()
        
        # Refresh Bearer token if available  
        if self._bearer_token_json and 'refresh_token' in self._bearer_token_json:
            self._refresh_bearer_token()

    def _refresh_vw_token(self):
        """Refresh VW token using refresh token."""
        LOG.debug("Refreshing VW token")
        
        token_url = "https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth/mobile/oauth2/v1/token"
        
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.vwToken['refresh_token'],
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        response = self.websession.post(token_url, data=token_data)
        response.raise_for_status()
        
        refreshed_token = response.json()
        self.vwToken.update(refreshed_token)
        LOG.debug("VW token refreshed successfully")

    def _refresh_bearer_token(self):
        """Refresh Bearer token using refresh token."""
        LOG.debug("Refreshing Bearer token")
        
        idk_token_url = f"https://{self.region}.bff.cariad.digital/login/v1/idk/token"
        
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self._bearer_token_json['refresh_token'],
            'client_id': self.client_id,
        }
        
        response = self.websession.post(idk_token_url, data=token_data)
        response.raise_for_status()
        
        refreshed_token = response.json()
        self._bearer_token_json.update(refreshed_token)
        LOG.debug("Bearer token refreshed successfully")

    def get_token_for_endpoint(self, url: str) -> str:
        """
        Route API calls to appropriate token based on endpoint URL.
        
        Args:
            url (str): The API endpoint URL
            
        Returns:
            str: The appropriate token for the endpoint
        """
        # Modern BFF API endpoints use Bearer token
        bff_patterns = [
            'bff.cariad.digital',
            '/vehicle/v1/',
            '/charging/v1/',
            '/climatisation/v1/',
            '/vehicle-health/v1/',
        ]
        
        # Legacy VW Group API endpoints use VW token
        legacy_patterns = [
            '/fs-car/',
            '/api/rolesrights/',
            '/api/bs/',
            'mal-1a.prd.ece.vwg-connect.com',
            'mal-3a.prd.eu.dp.vwg-connect.com',
        ]
        
        # Check for BFF patterns first (Bearer token)
        for pattern in bff_patterns:
            if pattern in url:
                if self._bearer_token_json and 'access_token' in self._bearer_token_json:
                    return self._bearer_token_json['access_token']
                break
        
        # Check for legacy patterns (VW token)
        for pattern in legacy_patterns:
            if pattern in url:
                if self.vwToken and 'access_token' in self.vwToken:
                    return self.vwToken['access_token']
                break
        
        # Default to Bearer token for new endpoints
        if self._bearer_token_json and 'access_token' in self._bearer_token_json:
            return self._bearer_token_json['access_token']
        elif self.vwToken and 'access_token' in self.vwToken:
            return self.vwToken['access_token']
        
        raise AuthenticationError("No valid token available for endpoint")

    def request(self, method, url, **kwargs):
        """
        Override request method to use appropriate token for each endpoint.
        """
        # Add appropriate Authorization header based on endpoint
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        try:
            token = self.get_token_for_endpoint(url)
            kwargs['headers']['Authorization'] = f'Bearer {token}'
        except AuthenticationError:
            # If no token available, let parent class handle login
            pass
        
        return super().request(method, url, **kwargs)

    def _get_login_form(self, url: str) -> HTMLFormParser:
        while True:
            # Check if we've reached the redirect URL with oauth tokens
            if url.startswith(self.redirect_uri):
                raise APICompatibilityError(f'Reached redirect URI, tokens should be extracted from URL: {url}')
            
            response = self.websession.get(url, allow_redirects=False)
            if response.status_code == requests.codes['ok']:
                break

            if response.status_code in (requests.codes['found'], requests.codes['see_other']):
                if 'Location' not in response.headers:
                    raise APICompatibilityError('Forwarding without Location in headers')

                url = response.headers['Location']
                continue

            raise APICompatibilityError(f'Retrieving login page was not successful, '
                                        f'status code: {response.status_code}')

        # Find login form on page to obtain inputs
        email_form = HTMLFormParser(form_id='emailPasswordForm')
        email_form.feed(response.text)

        if not email_form.target or not all(x in email_form.data for x in ['_csrf', 'relayState', 'hmac', 'email']):
            raise APICompatibilityError('Could not find all required input fields on login page')

        return email_form

    def _get_password_form(self, url: str, data: Dict[str, Any]) -> CredentialsFormParser:
        response = self.websession.post(url, data=data, allow_redirects=True)
        if response.status_code != requests.codes['ok']:
            raise APICompatibilityError(f'Retrieving credentials page was not successful, '
                                        f'status code: {response.status_code}')

        # Find login form on page to obtain inputs
        credentials_form = CredentialsFormParser()
        credentials_form.feed(response.text)

        if not credentials_form.target or not all(x in credentials_form.data for x in ['relayState', 'hmac', '_csrf']):
            raise APICompatibilityError('Could not find all required input fields on credentials page')

        if credentials_form.data.get('error', None) is not None:
            if credentials_form.data['error'] == 'validator.email.invalid':
                raise AuthenticationError('Error during login, email invalid')
            raise AuthenticationError(f'Error during login: {credentials_form.data["error"]}')

        if 'errorCode' in credentials_form.data:
            raise AuthenticationError('Error during login, is the username correct?')

        if credentials_form.data.get('registerCredentialsPath', None) == 'register':
            raise AuthenticationError(f'Error during login, account {self.session_user.username} does not exist')

        return credentials_form

    def _handle_login(self, url: str, data: Dict[str, Any]) -> str:
        response: requests.Response = self.websession.post(url, data=data, allow_redirects=False)

        if response.status_code == requests.codes['internal_server_error']:
            raise RetrievalError('Temporary server error during login')

        if response.status_code not in (requests.codes['found'], requests.codes['see_other']):
            raise APICompatibilityError(f'Forwarding expected (status code 302), '
                                        f'but got status code {response.status_code}')

        if 'Location' not in response.headers:
            raise APICompatibilityError('Forwarding without Location in headers')

        # Parse parameters from forwarding url
        params: Dict[str, str] = dict(parse_qsl(urlsplit(response.headers['Location']).query))

        # Check for login error
        if 'error' in params and params['error']:
            error_messages: Dict[str, str] = {
                'login.errors.password_invalid': 'Password is invalid',
                'login.error.throttled': 'Login throttled, probably too many wrong logins. You have to wait '
                                         'a few minutes until a new login attempt is possible'
            }

            raise AuthenticationError(error_messages.get(params['error'], params['error']))

        # Check for user ID
        if 'userId' not in params or not params['userId']:
            if 'updated' in params and params['updated'] == 'dataprivacy':
                raise AuthenticationError('You have to login at myAudi.de and accept the terms and conditions')
            raise APICompatibilityError('No user ID provided')

        self.user_id = params['userId']  # pylint: disable=unused-private-member
        return response.headers['Location']

    def _handle_consent_form(self, url: str) -> str:
        response = self.websession.get(url, allow_redirects=False)
        if response.status_code == requests.codes['internal_server_error']:
            raise RetrievalError('Temporary server error during login')

        # Find form on page to obtain inputs
        tc_form = TermsAndConditionsFormParser()
        tc_form.feed(response.text)

        # Remove query from URL
        url = urlparse(response.url)._replace(query='').geturl()

        response = self.websession.post(url, data=tc_form.data, allow_redirects=False)
        if response.status_code == requests.codes['internal_server_error']:
            raise RetrievalError('Temporary server error during login')

        if response.status_code not in (requests.codes['found'], requests.codes['see_other']):
            raise APICompatibilityError('Forwarding expected (status code 302), '
                                        f'but got status code {response.status_code}')

        if 'Location' not in response.headers:
            raise APICompatibilityError('Forwarding without Location in headers')

        return response.headers['Location']
