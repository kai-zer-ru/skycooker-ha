# SkyCooker Integration for Home Assistant

⚠️ **IMPORTANT: The integration is under active development!** ⚠️

**It is not recommended to install this integration in a working HomeAssistant system.**
Use only for testing and development.

Integration for managing Redmond RMC series multicookers via Bluetooth.

## Supported Models

- **RMC-M40S** (primary support)
- **RMC-M42S** (experimental support)

## Development Status

- ✅ Basic connection and authentication
- ✅ Power on/off control
- ⚠️ Program control (requires improvements)
- ⚠️ Status monitoring (limited support)
- ⚠️ RMC-M40S support (requires testing)

## Requirements

- Home Assistant 2025.12.5+
- Bluetooth adapter
- Redmond RMC-M40S multicooker in Bluetooth pairing mode

## Installation (for development only!)

1. Download integration to `custom_components/skycooker` folder
2. Restart Home Assistant
3. Go to Settings → Integrations → Add Integration
4. Select "SkyCooker"
5. Enter device MAC address and password

## Configuration

### Device MAC Address
Find your multicooker MAC address in your device Bluetooth settings.

### Password
Password should be in HEX format, 8 bytes length. You can:
- Use generator: https://crypt-online.ru/crypts/text2hex/
- Or try standard passwords: `0000000000000000`, `1111111111111111`

### Pairing Mode
1. Turn on multicooker
2. Hold pairing button until indicator starts blinking
3. Start integration adding process in Home Assistant

## Features

- Turn on/off multicooker
- Control cooking modes
- Set temperature
- Cooking time control
- Status monitoring
- Usage statistics

## Cooking Modes

- Standby
- Multi-chef
- Rice/Cereals
- Languor
- Pilaf
- Frying
- Stewing
- Pasta
- Baking
- Steaming
- Yogurt
- Dough
- Keep Warm

## Troubleshooting

### Problem: "Basic connection test failed"
**Solution:**
1. Ensure multicooker is in Bluetooth pairing mode
2. Check distance (no more than 3-5 meters)
3. Restart multicooker and Home Assistant
4. Consider using ESPHome Bluetooth proxy for better stability

### Problem: "Device not found"
**Solution:**
1. Check if Bluetooth is enabled on Home Assistant server
2. Ensure multicooker is powered and in pairing mode
3. Verify MAC address for typos

### Problem: "Authentication failed"
**Solution:**
1. Ensure multicooker is in pairing mode
2. Check password correctness
3. Try restarting multicooker

## Testing

For testing the integration:

```bash
# Run tests
python -m pytest tests/test_skycooker.py -v

# Run with detailed logging
python -m pytest tests/test_skycooker.py -v -s --log-cli-level=DEBUG
```

## Logging

Enable debug logging for troubleshooting in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.skycooker: debug
```

## Support

If you have issues:
1. Check "Troubleshooting" section above
2. Enable logging and check logs
3. Create issue in repository with problem description and logs

## License

MIT License

## Acknowledgments

- [ESPHome-Ready4Sky](https://github.com/KomX/ESPHome-Ready4Sky) - for protocol
- [ha_kettler](https://github.com/mavrikkk/ha_kettler) - for architecture
- [skykettle-ha](https://github.com/ClusterM/skykettle-ha) - for inspiration