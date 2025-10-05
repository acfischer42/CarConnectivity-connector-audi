

# CarConnectivity Connector for Audi Config Options

The configuration for CarConnectivity is a .json file.

## Quick Start

### Full Configuration (Recommended)
Use the complete template with WebUI authentication and MQTT:
```bash
cp audi_config_template.json audi_config.json
# Edit audi_config.json with your actual Audi credentials
```

### Minimal Configuration (Testing)
Use the minimal template for quick testing without authentication:
```bash
cp audi_config_minimal.json audi_config.json
# Edit audi_config.json with your actual Audi credentials
```

## Audi Connector Options

These are the valid options for the Audi Connector:

```json
{
    "carConnectivity": {
        "log_level": "info", // Global log level (debug, info, warning, error)
        "connectors": [
            {
                "type": "audi", // Definition for the Audi Connector
                "config": {
                    "interval": 300, // Interval in which the server is checked in seconds
                    "username": "your.email@example.com", // Username of your MyAudi Account
                    "password": "your_myaudi_password", // Password of your MyAudi Account
                    "country": "DE", // Country code (DE, GB, US, etc.)
                    "spin": "1234", // S-Pin used for some special commands like locking/unlocking
                    "netrc": "~/.netrc", // Optional: netrc file if to be used for passwords
                    "max_age": 300, // Cache requests to the server for MAX_AGE seconds
                    "hide_vins": ["WUA12345678901234"] // Optional: Don't fetch these VINs
                }
            }
        ],
        "plugins": [
            {
                "type": "webui", // Web interface plugin
                "config": {
                    "port": 4000, // Port for the web interface
                    "username": "admin", // WebUI username
                    "password": "change_this_password", // WebUI password
                    "locale": "en_AU.UTF-8", // Optional: locale setting
                    "time_format": "%d.%m.%Y %H:%M:%S" // Optional: time format
                    // For testing without login, add:
                    // "app_config": { "LOGIN_DISABLED": true }
                }
            },
            {
                "type": "mqtt", // MQTT plugin for home automation integration
                "config": {
                    "broker": "localhost", // MQTT broker hostname/IP
                    "port": 1883, // MQTT broker port
                    "username": "", // MQTT username (optional)
                    "password": "", // MQTT password (optional)
                    "client_id": "carconnectivity_audi", // MQTT client ID
                    "topic_prefix": "carconnectivity" // Prefix for MQTT topics
                }
            }
        ]
    }
}
```

## Configuration Parameters

### Required Parameters
- **username**: Your MyAudi account email address
- **password**: Your MyAudi account password

### Optional Parameters
- **country**: Country code (default: "DE"). Supported: DE, GB, US, AT, CH, etc.
- **spin**: S-PIN for secure operations (required for lock/unlock commands)
- **interval**: Data refresh interval in seconds (default: 300)
- **netrc**: Path to .netrc file for credential storage
- **max_age**: Cache duration for API responses in seconds
- **hide_vins**: Array of VINs to exclude from data collection

## WebUI Plugin Configuration

### With Password Protection (Production)
```json
{
    "type": "webui",
    "config": {
        "port": 4000,
        "username": "admin",
        "password": "secure_password_here"
    }
}
```

### Without Password Protection (Testing/Development)
```json
{
    "type": "webui",
    "config": {
        "port": 4000,
        "username": "admin",
        "password": "secret",
        "app_config": {
            "LOGIN_DISABLED": true
        }
    }
}
```

**⚠️ Security Warning**: Only use password-free configuration for local testing. Always use username/password protection when the WebUI is accessible from other machines or networks.

### Password Protection Control

The WebUI password protection can be controlled using the `LOGIN_DISABLED` setting:

#### How LOGIN_DISABLED Works
- **`LOGIN_DISABLED: false`** (default): Normal login required with username/password
- **`LOGIN_DISABLED: true`**: Bypasses login screen, direct access to WebUI
- When `LOGIN_DISABLED: true`, the username/password are still required in config but ignored at runtime
- This setting is part of Flask's application configuration passed to the WebUI plugin

#### Use Cases
- **Development/Testing**: Set `LOGIN_DISABLED: true` for quick local testing
- **Production**: Remove `app_config` section or set `LOGIN_DISABLED: false`
- **Debugging**: Temporarily disable login when troubleshooting authentication issues

#### Security Considerations
- **Local Only**: Only use `LOGIN_DISABLED: true` when WebUI is bound to localhost (127.0.0.1)
- **Network Access**: Never disable login when WebUI is accessible from other machines
- **Container Deployments**: Be extra careful in Docker/K8s environments where port exposure might change

### WebUI Options
- **port**: Port number for the web interface (default: 4000)
- **username**: Login username
- **password**: Login password
- **host**: Bind address (default: "127.0.0.1" for localhost only)
- **locale**: Locale setting (e.g., "en_AU.UTF-8")
- **time_format**: Time display format (e.g., "%d.%m.%Y %H:%M:%S")
- **app_config**: Flask application configuration
  - **LOGIN_DISABLED**: Set to `true` to disable login requirement (testing only)

## Common Configuration Scenarios

### Quick Local Testing
```json
{
    "type": "webui",
    "config": {
        "port": 4000,
        "username": "admin",
        "password": "temp",
        "app_config": {
            "LOGIN_DISABLED": true
        }
    }
}
```

### Production with Custom Port
```json
{
    "type": "webui",
    "config": {
        "port": 8080,
        "host": "0.0.0.0",
        "username": "admin",
        "password": "secure_random_password_here"
    }
}
```

### Development with Locale Settings
```json
{
    "type": "webui",
    "config": {
        "port": 4000,
        "username": "admin",
        "password": "dev",
        "locale": "en_AU.UTF-8",
        "time_format": "%d.%m.%Y %H:%M:%S",
        "app_config": {
            "LOGIN_DISABLED": true
        }
    }
}
```
```
