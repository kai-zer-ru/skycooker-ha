# Troubleshooting Guide

## Connection Issues

### "Basic connection test failed"
**Cause:** Device is not responding to commands

**Solution:**
1. Ensure multicooker is in Bluetooth pairing mode (blinking indicator)
2. Check distance - no more than 3-5 meters from Home Assistant server
3. Restart multicooker and Home Assistant
4. Verify Bluetooth is enabled on server
5. Consider using ESPHome Bluetooth proxy for better stability

### "Device not found"
**Cause:** Home Assistant cannot find the device

**Solution:**
1. Check MAC address for typos
2. Ensure multicooker is powered and in pairing mode
3. Restart Bluetooth adapter
4. Check for interference from other Bluetooth/WiFi devices

### "Authentication failed"
**Cause:** Wrong password or device not in pairing mode

**Solution:**
1. Ensure multicooker is in pairing mode
2. Check password correctness (HEX format, 8 bytes)
3. Try standard passwords: `0000000000000000`, `1111111111111111`
4. Restart multicooker and try again

### "No backend with an available connection slot"
**Cause:** Bluetooth adapter is overloaded

**Solution:**
1. Restart Home Assistant
2. Reduce number of connected Bluetooth devices
3. Move closer to multicooker
4. Consider using ESPHome Bluetooth proxy

## Control Issues

### Device doesn't respond to commands
**Cause:** Connection or protocol problems

**Solution:**
1. Check connection status in logs
2. Ensure device is powered on
3. Try reconnecting
4. Check if battery is low (if applicable)

### Incorrect temperature readings
**Cause:** Temperature sensor not synchronized

**Solution:**
1. Restart device
2. Wait several minutes for synchronization
3. Check if mode is detected correctly

### Modes don't switch
**Cause:** Protocol or device state problems

**Solution:**
1. Ensure device is turned off before changing mode
2. Verify selected mode is supported by your model
3. Try restarting device

## Diagnostics

### Enable debug logging
Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.skycooker: debug
```

### Check Bluetooth connection
1. Ensure Bluetooth is enabled: `bluetoothctl`
2. Check device visibility: `bluetoothctl scan on`
3. Check connection: `bluetoothctl info [MAC]`

### Test connection
1. Put multicooker in pairing mode
2. Start integration
3. Check logs for errors
4. Restart device if necessary

## ESPHome Bluetooth Proxy

For improved connection stability, use ESPHome Bluetooth proxy:

1. Install ESPHome on ESP32
2. Configure Bluetooth proxy
3. Set ESP32 as Bluetooth proxy in Home Assistant
4. Reconnect integration

**Benefits:**
- Better connection stability
- Less load on main server
- Longer range
- Multiple device support

## Frequently Asked Questions

### Q: Why doesn't integration see my device?
A: Ensure device is in pairing mode and within Bluetooth range.

### Q: Can I use multiple multicookers?
A: Yes, but ESPHome Bluetooth proxy is recommended for stable operation.

### Q: Why does connection sometimes drop?
A: This is normal for Bluetooth devices. Integration automatically reconnects.

### Q: How to find device MAC address?
A: MAC address can be found in Redmond app or in your device Bluetooth settings.

## Support

If problems persist:
1. Collect logs with debug level enabled
2. Describe problem and reproduction steps
3. Create issue in repository with logs and description