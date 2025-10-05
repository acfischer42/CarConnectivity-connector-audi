# CarConnectivity Connector for Audi

A Python connector for Audi vehicles that integrates with the [CarConnectivity framework](https://github.com/tillsteinbach/CarConnectivity) by Till Steinbach, allowing you to interact with your Audi vehicle's data and controls through a standardized API.

## About CarConnectivity

This connector is built for the [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) framework, which provides a unified interface for connecting to various car manufacturers' APIs. CarConnectivity is developed and maintained by [Till Steinbach](https://github.com/tillsteinbach).

## Features

- 🚗 **Vehicle Status**: Access battery/fuel levels, range, odometer readings
- 🔐 **Remote Control**: Lock/unlock doors, start/stop charging and climatization
- 📍 **Location Services**: Get vehicle position and parking information
- 🔧 **Maintenance**: Check inspection and service due dates
- 🌡️ **Climate Control**: Remote climate control and window heating
- 💡 **Vehicle Lights**: Monitor and control vehicle lighting
- ⚡ **Charging**: Monitor and control electric vehicle charging

## Installation

Install the connector using pip:

```bash
pip install carconnectivity-connector-audi
```

You'll also need the CarConnectivity CLI:

```bash
pip install carconnectivity-cli
```

For more information about the CarConnectivity framework, visit:
- **Main Repository**: [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)
- **CLI Repository**: [CarConnectivity-CLI](https://github.com/tillsteinbach/CarConnectivity-cli)
- **Documentation**: See the [CarConnectivity Wiki](https://github.com/tillsteinbach/CarConnectivity/wiki)

## Configuration

Create a configuration file (e.g., `audi_config.json`) with your Audi credentials:

```json
{
    "carConnectivity": {
        "connectors": [
            {
                "type": "audi",
                "config": {
                    "username": "your.email@example.com",
                    "password": "your_password"
                }
            }
        ]
    }
}
```

## Usage

### List all available resources
```bash
carconnectivity-cli audi_config.json list
```

### Get vehicle state
```bash
carconnectivity-cli audi_config.json get /garage/YOUR_VIN/state
```

### Get battery/fuel level
```bash
carconnectivity-cli audi_config.json get /garage/YOUR_VIN/drives/primary/level
```

### Get vehicle position
```bash
carconnectivity-cli audi_config.json get /garage/YOUR_VIN/position/latitude
carconnectivity-cli audi_config.json get /garage/YOUR_VIN/position/longitude
```

### Control charging (for electric vehicles)
```bash
carconnectivity-cli audi_config.json set /garage/YOUR_VIN/charging/commands/start-stop start
```

### Control climatization
```bash
carconnectivity-cli audi_config.json set /garage/YOUR_VIN/climatization/commands/start-stop start
```

### Lock/unlock doors
```bash
carconnectivity-cli audi_config.json set /garage/YOUR_VIN/doors/commands/lock-unlock lock
```

## Running with Docker

You can run the Audi connector using Docker with the [CarConnectivity-MQTT](https://github.com/tillsteinbach/CarConnectivity-plugin-mqtt) image made by Till. This allows you to publish vehicle data to an MQTT broker for integration with home automation systems.

### Docker Compose Setup

Create a `docker-compose.yml` file:

```yaml
services:
  carconnectivity-mqtt:
    image: "tillsteinbach/carconnectivity-mqtt:latest"
    environment:
      - ADDITIONAL_INSTALLS=carconnectivity-connector-audi
      - TZ=Europe/Berlin  # Set your timezone
    volumes:
      - ./carconnectivity.json:/carconnectivity.json
    restart: unless-stopped
```

### Configuration for Docker

Create a `carconnectivity.json` configuration file:

```json
{
    "carConnectivity": {
        "log_level": "info",
        "connectors": [
            {
                "type": "audi",
                "config": {
                    "interval": 600,
                    "username": "your.email@example.com",
                    "password": "your_password"
                }
            }
        ],
        "plugins": [
            {
                "type": "mqtt",
                "config": {
                    "broker": "192.168.1.100",
                    "port": 1883,
                    "username": "mqtt_user",
                    "password": "mqtt_password"
                }
            }
        ]
    }
}
```

### Running the Container

```bash
docker-compose up -d
```


For detailed Docker configuration options, refer to the [CarConnectivity-MQTT Docker documentation](https://github.com/tillsteinbach/CarConnectivity-plugin-mqtt/blob/main/docker/README.md).

## Development

### Building from source

1. Clone the repository:
```bash
git clone https://github.com/acfischer42/CarConnectivity-connector-audi.git
cd CarConnectivity-connector-audi
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install build
```

4. Build the package:
```bash
python -m build
```

5. Install locally:
```bash
pip install dist/carconnectivity_connector_audi-*.whl
```

## Requirements

- Python 3.9 or higher
- [CarConnectivity framework](https://github.com/tillsteinbach/CarConnectivity) >= 0.8
- Valid myAudi account with connected vehicle

## Related Projects

This connector is part of the CarConnectivity ecosystem:

- **[CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)** - The main framework by Till Steinbach
- **[CarConnectivity-CLI](https://github.com/tillsteinbach/CarConnectivity-cli)** - Command-line interface
- **[WeConnect-python](https://github.com/tillsteinbach/WeConnect-python)** - Volkswagen connector
- **[VWConnect](https://github.com/tillsteinbach/VWConnect)** - Alternative VW solution

## Supported Vehicles

This connector works with Audi vehicles that support myAudi connected services, including:
- Electric vehicles (e-tron models)
- Hybrid vehicles
- Modern ICE vehicles with connectivity features

## Security

- Credentials are securely handled through OAuth2 authentication
- Tokens are cached locally and refreshed automatically
- No credentials are stored in plain text after initial setup

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

- **Till Steinbach** for creating the [CarConnectivity framework](https://github.com/tillsteinbach/CarConnectivity)
- Based on authentication patterns from the broader CarConnectivity ecosystem

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial connector not affiliated with Audi AG or Till Steinbach's original CarConnectivity project. Use at your own risk and ensure you comply with your vehicle's terms of service.
