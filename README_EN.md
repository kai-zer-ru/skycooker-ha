# SkyCooker Integration for HomeAssistant

Integration for managing Redmond SkyCooker devices via Bluetooth in HomeAssistant.

## Inspiration

This project is inspired by the [SkyKettle](https://github.com/ClusterM/skykettle-ha) integration for managing Redmond kettles. SkyCooker extends the functionality to support multicookers and other Redmond devices.

## Supported Devices

### Multicookers
- **RMC-M40S** - Primary supported model (fully tested and optimized)

**Note:** Other models are planned for future support but currently only RMC-M40S is fully functional.

## Features

### For Multicookers (RMC-M40S)
- Program management (13 cooking programs)
- Temperature control (35°C - 90°C)
- Timer control (hours and minutes)
- Real-time status monitoring
- Start/stop cooking
- Current temperature monitoring
- Device authentication and pairing

### Supported Cooking Programs
- Standby (Ожидание)
- Multi-chef (Мультиповар)
- Rice/Cereals (Рис/Крупы)
- Languor (Томление)
- Pilaf (Плов)
- Frying (Жарка)
- Stewing (Тушение)
- Pasta (Макароны)
- Baking (Выпечка)
- Steaming (На пару)
- Yogurt (Йогурт)
- Dough (Тесто)
- Keep Warm (Поддержание тепла)

## Installation

### Method 1: Manual Installation
1. Copy the `custom_components/skycooker` folder to your HomeAssistant `custom_components` directory
2. Restart HomeAssistant
3. Add integration via UI: Settings → Integrations → Add Integration → SkyCooker

### Method 2: HACS Installation (Recommended)
1. Open HACS in HomeAssistant
2. Go to Integrations
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add repository URL: `https://github.com/your-repo/skycooker-ha`
6. Set Category to "Integration"
7. Click "Add"
8. Install the SkyCooker integration from HACS
9. Restart HomeAssistant
10. Add integration via UI: Settings → Integrations → Add Integration → SkyCooker

## Configuration

### Required Settings
- **Device MAC Address** - Bluetooth address of your RMC-M40S (format: AA:BB:CC:DD:EE:FF)
- **Authorization Key** - Usually "000000" (default pairing code)

### Device Preparation
1. Power on your RMC-M40S
2. Ensure it's in pairing mode (bluetooth indicator blinking)
3. Keep the device within Bluetooth range (5-10 meters recommended)

## Debug Logging

To enable detailed debug logging for troubleshooting:

### Via Configuration.yaml
Add to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.skycooker: debug
    homeassistant.components.bluetooth: debug
```

### Via UI (HomeAssistant 2021.6+)
1. Go to Settings → System → Logs
2. Click "Load Full Home Assistant Log"
3. Click "Add Filter"
4. Add filter for `custom_components.skycooker` with level `DEBUG`
5. Click "Start Logging"

### What Debug Logs Show
- Device connection attempts and status
- Bluetooth communication details
- Command sending and responses
- Authentication process
- Status updates and parsing
- Error details and troubleshooting information

## Troubleshooting

### Common Issues
1. **Device not found**: Ensure Bluetooth is enabled and device is in pairing mode
2. **Authentication failed**: Check pairing mode and try default key "000000"
3. **Connection timeout**: Move closer to device, check Bluetooth interference
4. **Commands not working**: Verify device is powered and connected

### Getting Help
1. Enable debug logging as described above
2. Check HomeAssistant logs for detailed error messages
3. Verify device compatibility (currently only RMC-M40S is supported)
4. Ensure HomeAssistant has Bluetooth permissions
5. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide

## Development

### Based on
- [ESPHome-Ready4Sky](https://github.com/KomX/ESPHome-Ready4Sky) - Protocol definitions
- [ha_kettler](https://github.com/mavrikkk/ha_kettler) - Architecture patterns
- [SkyKettle](https://github.com/ClusterM/skykettle-ha) - Inspiration and architecture

### Current Status
- **RMC-M40S**: Fully supported and tested
- **Other models**: Planned for future releases

## License

MIT License

## Support

For issues and support:
1. Check the troubleshooting section above
2. Enable debug logging for detailed information
3. Report issues with debug logs included
4. Ensure you're using a supported device (RMC-M40S)