# Bluetooth Connection Troubleshooting Guide

## Problem: "No backend with an available connection slot"

This error occurs when your Bluetooth adapter has run out of available connection slots. This is a common issue when using multiple Bluetooth devices with Home Assistant.

## Solutions

### 1. Add Bluetooth Proxies (Recommended)

The best solution is to add ESPHome Bluetooth proxies near your devices:

- **ESPHome Bluetooth Proxy**: https://esphome.github.io/bluetooth-proxies/
- **Installation Guide**: https://esphome.io/components/bluetooth_proxy.html
- **Required Hardware**: ESP32 board (e.g., ESP32-WROOM-32, ESP32-C3, ESP32-S3)

**Benefits**:
- Increases available connection slots
- Improves connection stability
- Extends Bluetooth range
- Distributes Bluetooth load

### 2. Use a Dedicated Bluetooth Adapter

Instead of using your system's built-in Bluetooth, use a dedicated USB Bluetooth adapter:

- **Recommended Adapters**:
  - ASUS USB-BT500 (Bluetooth 5.0)
  - TP-Link UB500 (Bluetooth 5.0)
  - Cambridge Silicon Radio (CSR) 4.0 adapters

**How to use**:
1. Plug in the USB Bluetooth adapter
2. Disable your system's built-in Bluetooth
3. Restart Home Assistant

### 3. Reduce Active Bluetooth Connections

Limit the number of simultaneously connected Bluetooth devices:

- Disable unused Bluetooth integrations
- Increase update intervals for Bluetooth devices
- Use passive Bluetooth scanning where possible

### 4. Restart Home Assistant

Sometimes a simple restart can help:

```bash
homeassistant restart
```

### 5. Check Bluetooth Adapter Status

Check if your adapter supports multiple connections:

```bash
# Check Bluetooth adapter info
hciconfig -a
hcitool dev

# Check connected devices
hcitool con
```

### 6. Move Closer to the Device

Bluetooth has limited range (typically 10 meters). Try moving your Home Assistant server closer to the device or use a USB extension cable for your Bluetooth adapter.

### 7. Check for Interference

Other wireless devices can interfere with Bluetooth:

- Wi-Fi routers (especially on 2.4GHz)
- Microwaves
- Wireless phones
- Baby monitors

Try changing the Wi-Fi channel or moving devices away from each other.

### 8. Update Bluetooth Firmware

Make sure your Bluetooth adapter has the latest firmware:

```bash
# For Linux systems
sudo apt update && sudo apt upgrade
sudo systemctl restart bluetooth
```

### 9. Use Multiple Bluetooth Adapters

You can use multiple Bluetooth adapters simultaneously:

1. Plug in multiple USB Bluetooth adapters
2. Each adapter will provide additional connection slots
3. Home Assistant will automatically distribute connections

### 10. Check System Logs

For more detailed troubleshooting:

```bash
# View Bluetooth service logs
journalctl -u bluetooth -f

# View Home Assistant logs
tail -f /config/home-assistant.log | grep -i bluetooth
```

## Advanced Configuration

### Increase Bluetooth Connection Slots

Some adapters allow increasing connection slots via configuration:

```yaml
# configuration.yaml
bluetooth:
  auto_start: true
  scan_interval: 60
  scan_duration: 10
```

### Use Bluetooth Proxy Integration

```yaml
# configuration.yaml
bluetooth_proxy:
  active_scan: true
  report_unknown_devices: false
```

## Common Error Messages

### "No backend with an available connection slot"
- **Cause**: Bluetooth adapter has no free connection slots
- **Solution**: Add Bluetooth proxies or reduce active connections

### "Device not found"
- **Cause**: Device is out of range or powered off
- **Solution**: Move closer to device or check device power

### "Connection timeout"
- **Cause**: Device is not responding
- **Solution**: Restart device or check Bluetooth interference

### "Authentication failed"
- **Cause**: Incorrect pairing key or device not in pairing mode
- **Solution**: Put device in pairing mode and try again

## Support

If you continue to experience issues:

1. Check the [Home Assistant Bluetooth documentation](https://www.home-assistant.io/integrations/bluetooth/)
2. Visit the [Home Assistant Community Forum](https://community.home-assistant.io/)
3. Open an issue on the [SkyCooker GitHub repository](https://github.com/kai-zer-ru/skycooker-ha/issues)

Include your:
- Home Assistant version
- Bluetooth adapter model
- Full error logs
- Device information
