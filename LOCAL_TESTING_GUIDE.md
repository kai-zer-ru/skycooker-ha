# Local Testing Guide for SkyCooker Integration

## Overview

This guide explains how to test the SkyCooker integration locally without affecting your production Home Assistant instance.

## Prerequisites

1. **Second Bluetooth Adapter** - You already have one connected
2. **Python 3.9+** - Required for Home Assistant
3. **Virtual Environment** - To isolate dependencies
4. **Docker** (optional) - For containerized testing

## Setup Local Testing Environment

### Option 1: Virtual Environment (Recommended)

```bash
# Create and activate virtual environment
python3 -m venv venv_test
source venv_test/bin/activate

# Install required dependencies
pip install homeassistant bleak bleak-retry-connector
```

### Option 2: Docker (Isolated Environment)

```bash
# Create docker-compose.override.yml for testing
docker-compose -f docker-compose.yml -f docker-compose.test.yml up
```

## Create Docker Compose for Testing

Let's create a test-specific docker compose file:

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  homeassistant_test:
    image: ghcr.io/home-assistant/home-assistant:stable
    container_name: homeassistant_test
    restart: unless-stopped
    privileged: true
    network_mode: host
    volumes:
      - ./test_config:/config
      - ./custom_components:/config/custom_components/skycooker
    environment:
      - TZ=Asia/Irkutsk
    devices:
      - /dev/ttyACM0:/dev/ttyACM0  # Your second Bluetooth adapter
      - /dev/ttyUSB0:/dev/ttyUSB0   # If using USB adapter
```

## Test Configuration Structure

```
test_config/
├── configuration.yaml
├── secrets.yaml
└── custom_components/
    └── skycooker/ -> ../../../custom_components/skycooker
```

## Create Test Configuration

### configuration.yaml

```yaml
# test_config/configuration.yaml
default_config:

logger:
  default: info
  logs:
    custom_components.skycooker: debug
    bleak: debug
    bleak_retry_connector: debug

bluetooth:
  auto_start: true
  scan_interval: 60
  scan_duration: 10

# Test integration
skycooker:
  devices:
    - mac: "DA:D8:9F:9E:0B:4C"
      key: "00000000"
      name: "Test Cooker"
```

### secrets.yaml

```yaml
# test_config/secrets.yaml
cooker_key: "00000000"
```

## Testing Scripts

### 1. Unit Testing (No HA Required)

```bash
# Run unit tests
python -m pytest tests/ -v
```

### 2. Integration Testing (With Test HA)

```bash
# Start test Home Assistant
cd test_config
homeassistant --config . --script ensure_config

# Or with Docker
docker-compose -f docker-compose.test.yml up
```

### 3. Bluetooth Connection Testing

```python
# test_bluetooth_connection.py
import asyncio
from bleak import BleakScanner

async def scan_devices():
    print("Scanning for Bluetooth devices...")
    devices = await BleakScanner.discover()
    
    for device in devices:
        if "RMC-M40S" in device.name or "DA:D8:9F:9E:0B:4C" in device.address:
            print(f"Found target device: {device.name} - {device.address}")
            print(f"RSSI: {device.rssi}")
            print(f"Metadata: {device.metadata}")
            return device
    
    print("Target device not found")
    return None

if __name__ == "__main__":
    device = asyncio.run(scan_devices())
```

## Test Automation

### Create Test Automation

```yaml
# test_config/automations.yaml
- alias: "Test Cooker Connection"
  trigger:
    - platform: homeassistant
      event: start
  action:
    - service: skycooker.update
      target:
        entity_id: all
    - delay: 5
    - service: notify.persistent_notification
      data:
        message: "Test cooker connection completed"
```

## Debugging Tips

### 1. Check Bluetooth Adapter

```bash
# List Bluetooth adapters
hciconfig -a

# Check connected devices
hcitool con

# Scan for devices
hcitool scan
```

### 2. Monitor Logs

```bash
# For virtual environment
tail -f test_config/home-assistant.log | grep -i "skycooker\|bluetooth"

# For Docker
docker logs homeassistant_test -f | grep -i "skycooker\|bluetooth"
```

### 3. Test Specific Device

```python
# test_device_connection.py
import sys
sys.path.insert(0, 'custom_components')

from skycooker.cooker_connection import CookerConnection

async def test_device():
    conn = CookerConnection(
        mac="DA:D8:9F:9E:0B:4C",
        key="00000000",
        persistent=False
    )
    
    try:
        # This will attempt connection
        await conn.update()
        print("Connection successful!")
        print(f"Status: {conn._status}")
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test_device())
```

## Best Practices

### 1. Use Different Bluetooth Adapter

Configure your test instance to use the second Bluetooth adapter:

```yaml
# test_config/configuration.yaml
bluetooth:
  adapter: "hci1"  # Your second adapter
```

### 2. Isolate Test Data

Keep test configuration separate from production:

```bash
# Create symlink for easy updates
ln -s ../custom_components/skycooker test_config/custom_components/skycooker
```

### 3. Use Test-Specific Configuration

```yaml
# test_config/configuration.yaml
recorder:
  db_url: !secret test_db_url
  purge_keep_days: 7

logger:
  logs:
    custom_components.skycooker: debug
```

### 4. Automate Testing

Create a test script:

```bash
#!/bin/bash
# run_tests.sh

echo "Running SkyCooker tests..."

# Run unit tests
python -m pytest tests/ -v

# Run integration tests
python test_connection_fixed.py

# Run Bluetooth scan
python test_bluetooth_connection.py

echo "Tests completed!"
```

## Troubleshooting

### Common Issues

1. **Bluetooth adapter not found**:
   - Check `hciconfig -a`
   - Make sure adapter is plugged in
   - Try `sudo systemctl restart bluetooth`

2. **Device not discovered**:
   - Check device is powered on
   - Move device closer to adapter
   - Check for Bluetooth interference

3. **Connection slots exhausted**:
   - Restart test Home Assistant
   - Reduce number of test devices
   - Use Bluetooth proxy

### Clean Up

```bash
# Stop test instance
docker-compose -f docker-compose.test.yml down

# Or for virtual environment
pkill -f homeassistant
```

## Advanced Testing

### Mock Testing

```python
# test_mock_connection.py
from unittest.mock import AsyncMock, MagicMock
import sys
sys.path.insert(0, 'custom_components')

from skycooker.cooker_connection import CookerConnection

async def test_mock():
    # Create mock Bluetooth device
    mock_device = MagicMock()
    mock_device.name = "Test Cooker"
    mock_device.address = "DA:D8:9F:9E:0B:4C"
    
    # Create connection with mock
    conn = CookerConnection(
        mac="DA:D8:9F:9E:0B:4C",
        key="00000000"
    )
    
    # Mock the connection
    conn._connect = AsyncMock()
    conn._client = MagicMock()
    conn._client.is_connected = True
    
    # Test update
    try:
        result = await conn.update()
        print(f"Mock test result: {result}")
    except Exception as e:
        print(f"Mock test failed: {e}")

asyncio.run(test_mock())
```

## Summary

With this setup, you can:

1. ✅ Test without affecting production HA
2. ✅ Use second Bluetooth adapter for testing
3. ✅ Run unit and integration tests locally
4. ✅ Debug Bluetooth connections
5. ✅ Automate testing process
6. ✅ Keep test configuration separate

This approach allows for rapid development and testing without the need to constantly restart your production Home Assistant instance.