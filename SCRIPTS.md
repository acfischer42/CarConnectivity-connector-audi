# Build and Run Scripts

This directory contains automation scripts to help you build, test, and run the CarConnectivity Audi connector.

## Scripts Overview

### 1. `build-and-test.sh` - Complete Build and Test
**Purpose**: Full automation of the build, test, and setup process

**What it does**:
- Cleans up any existing test environments
- Sets up the main virtual environment with build tools
- Builds the connector package (wheel and source distribution)
- Creates a fresh test virtual environment
- Installs the built package and all dependencies
- Tests basic functionality and imports
- Validates configuration files
- Provides usage instructions

**When to use**:
- First time setup
- After making code changes
- When you want a clean rebuild
- For CI/CD pipelines

**Usage**:
```bash
./build-and-test.sh
```

### 2. `run.sh` - Quick Start Service
**Purpose**: Quickly start the CarConnectivity service

**What it does**:
- Checks if the test environment exists
- Validates configuration file
- Checks for port conflicts
- Activates the test environment
- Starts the CarConnectivity service

**When to use**:
- Daily usage after initial setup
- Quick service restarts
- Testing configuration changes

**Usage**:
```bash
./run.sh
```

## Prerequisites

1. **Python 3.9+** installed on your system
2. **Valid Audi credentials** in `audi_config.json`
3. **Internet connection** for downloading dependencies

## Quick Start

1. **First time setup**:
   ```bash
   ./build-and-test.sh
   ```

2. **Create your configuration** (if not exists):
   ```bash
   cp audi_config.json.example audi_config.json
   # Edit with your credentials
   ```

3. **Run the service**:
   ```bash
   ./run.sh
   ```

## Configuration

Your `audi_config.json` should look like this:

```json
{
    "carConnectivity": {
        "log_level": "info",
        "connectors": [
            {
                "type": "audi",
                "config": {
                    "interval": 300,
                    "username": "your.email@example.com",
                    "password": "your_password"
                }
            }
        ],
        "plugins": [
            {
                "type": "webui",
                "config": {
                    "port": 4000,
                    "username": "admin",
                    "password": "secret"
                }
            },
            {
                "type": "mqtt",
                "config": {
                    "broker": "your.mqtt.broker.com"
                }
            }
        ]
    }
}
```

## Troubleshooting

### Port Already in Use
If port 4000 is occupied:
1. Edit `audi_config.json` and change the webui port:
   ```json
   "plugins": [{"type": "webui", "config": {"port": 8080}}]
   ```
2. Or kill the process using port 4000:
   ```bash
   sudo lsof -i :4000
   sudo kill -9 <PID>
   ```

### Build Failures
- Ensure Python 3.9+ is installed
- Check internet connection for dependency downloads
- Try cleaning and rebuilding:
  ```bash
  rm -rf test-venv build dist
  ./build-and-test.sh
  ```

### Authentication Issues
- Verify your Audi credentials in `audi_config.json`
- Check if your account has connected vehicle services enabled
- Ensure 2FA is properly configured if enabled

### Package Import Errors
- Run the full build script: `./build-and-test.sh`
- Check that all dependencies installed correctly
- Verify the test environment was created successfully

## File Structure After Setup

```
CarConnectivity-connector-audi/
├── build-and-test.sh          # Build automation script
├── run.sh                     # Quick run script
├── audi_config.json           # Your configuration
├── test-venv/                 # Test virtual environment
├── venv/                      # Main virtual environment
├── dist/                      # Built packages
│   ├── *.whl                  # Wheel package
│   └── *.tar.gz               # Source distribution
├── build/                     # Build artifacts
└── src/                       # Source code
```

## Advanced Usage

### Manual Testing
After running `build-and-test.sh`, you can manually test:

```bash
source test-venv/bin/activate
carconnectivity-cli audi_config.json list
carconnectivity-cli audi_config.json get /garage/YOUR_VIN/state
```

### Development Workflow
1. Make code changes
2. Run `./build-and-test.sh` to rebuild and test
3. Run `./run.sh` to start service with changes
4. Test functionality
5. Repeat as needed

### Custom Configuration
You can create multiple config files for different environments:
```bash
./run.sh  # Uses audi_config.json
# Or manually:
source test-venv/bin/activate
carconnectivity-cli my-custom-config.json
```
