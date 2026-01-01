# SkyCooker Troubleshooting Guide

## Connection Problems

### Error: "No backend with an available connection slot" / "BleakOutOfConnectionSlotsError"

**Cause:** Bluetooth adapter has exhausted the limit of simultaneous connections. This can happen when:
- Other Bluetooth integrations are present (e.g., ha_kettler)
- Too frequent device polling
- Incorrect connection management

**Solution:**
1. **Increase polling interval** in integration settings (recommended 30-60 seconds)
2. **Enable persistent connection** in integration settings
3. **Restart Bluetooth adapter:**
   ```bash
   sudo systemctl restart bluetooth
   ```
4. **Restart HomeAssistant**
5. **Check other Bluetooth integrations** - temporarily disable other Bluetooth devices for testing
6. **Ensure device is powered on** and in pairing mode

**For users with multiple Bluetooth devices:**
- **Consider using Bluetooth proxy** (if possible)
- **Increase polling intervals** for all Bluetooth devices (recommended 60+ seconds)
- **Use persistent connections** only for critical devices
- **Temporarily disable other Bluetooth integrations** for testing
- **Restart Bluetooth adapter** when problems occur:
  ```bash
  sudo systemctl restart bluetooth
  ```
- **Check physical device placement** - Bluetooth adapter may not handle multiple devices at distance

### Error: "BleakClient.connect() called without bleak-retry-connector"

**Cause:** Integration cannot use bleak-retry-connector for reliable connection.

**Solution:**
1. **Check dependencies** - ensure bleak-retry-connector is installed:
   ```bash
   pip3 list | grep bleak-retry-connector
   ```
2. **Restart HomeAssistant** to load dependencies
3. **Check manifest.json** - ensure dependency is specified:
   ```json
   "requirements": ["bleak-retry-connector>=1.0.0"]
   ```
4. **If problem persists** - try reinstalling the integration

### Error: "Device with MAC address XX:XX:XX:XX:XX:XX not found"

**Cause:** HomeAssistant cannot find device by MAC address.

**Solution:**
1. Check device MAC address
2. Ensure device is powered on and within range
3. Check that Bluetooth adapter is working:
   ```bash
   hcitool scan
   ```
4. Restart device and try again

### Error: "Auth failed"

**Cause:** Incorrect authorization key or device not in pairing mode.

**Solution:**
1. Ensure device is in pairing mode (usually indicator blinks)
2. Try default key "000000"
3. If not working, try other variants: "123456", "111111"
4. Restart device and retry

## Control Problems

### Commands not executed

**Cause:** Connection or protocol problems.

**Solution:**
1. Check connection status in HomeAssistant interface
2. Enable persistent connection in integration settings
3. Try restarting integration:
   - Settings → Integrations → SkyCooker → Remove
   - Add integration again

### Incorrect readings

**Cause:** Device doesn't support requested data.

**Solution:**
1. Check that your model is supported
2. Try restarting device
3. Check HomeAssistant logs for errors

## Performance Problems

### Frequent connection drops

**Cause:** Weak Bluetooth signal or interference.

**Solution:**
1. Reduce distance between device and HomeAssistant server
2. Remove obstacles between devices
3. Disable other Bluetooth devices that may cause interference
4. Enable persistent connection in settings

### Slow response

**Cause:** High system load or Bluetooth problems.

**Solution:**
1. Check CPU and memory load on server
2. Increase polling interval in integration settings
3. Restart HomeAssistant

## Bluetooth Check

### Check Bluetooth availability

```bash
# Check Bluetooth status
systemctl status bluetooth

# Scan devices
hcitool scan

# Check adapter
hciconfig -a
```

### Check access rights

```bash
# Check Bluetooth rights
ls -la /dev/ttyACM*

# Add user to Bluetooth group
sudo usermod -a -G bluetooth homeassistant
```

## Logs and Diagnostics

### Enable debug logging

For detailed diagnostics, enable debug logging:

#### Via configuration.yaml
Add to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.skycooker: debug
    homeassistant.components.bluetooth: debug
```

#### Via UI (HomeAssistant 2021.6+)
1. Go to Settings → System → Logs
2. Click "Load Full Home Assistant Log"
3. Click "Add Filter"
4. Add filter for `custom_components.skycooker` with level `DEBUG`
5. Click "Start Logging"

### What debug logs show

- **Device connection**: `🔗 Starting connection to cooker`, `✅ Successfully connected`
- **Authentication**: `🔑 Performing authentication`, `✅ Authentication successful`
- **Commands**: `📡 Sending command`, `📥 Received response`
- **Status**: `📊 Requesting device status`, `✅ Status retrieved`
- **Errors**: `❌ Connection failed`, `⚠️ Connection attempt failed`

### Check HomeAssistant logs

1. Settings → System → Logs
2. Filter: `skycooker`
3. Look for error messages
4. For debug logs use filter: `custom_components.skycooker`

### Example useful logs

#### Successful connection
```
🔗 Starting connection to cooker DA:D8:9F:9E:0B:4C (model: RMC-M40S)
✅ Device found: RMC-M40S (DA:D8:9F:9E:0B:4C)
🔌 Connection attempt 1/5...
✅ Successfully connected to cooker (attempt 1)
📡 Starting notifications on RX characteristic...
✅ Subscribed to RX notifications
🔑 Performing authentication...
✅ Authentication successful
📋 Getting device version...
📋 Device version: (1, 0)
⏰ Synchronizing device time...
✅ Time synchronized: 2026-01-01 17:00:00 (GMT+8.00)
✅ Authentication and setup completed successfully
```

#### Connection errors
```
❌ Failed to connect to cooker DA:D8:9F:9E:0B:4C after 5 attempts: [Errno 110] Operation timed out
⚠️ Connection attempt 1 failed: [Errno 110] Operation timed out
❌ Bluetooth connection slots exhausted for DA:D8:9F:9E:0B:4C
❌ Auth failed. You need to enable pairing mode on the cooker.
❌ Command failed: not connected
❌ Failed to get status: [Errno 110] Operation timed out
```

#### Commands and responses
```
⚙️ Setting main mode: mode=2 (Rice/Cereals), target_temp=60, boil_time=0
📦 Packed data for RMC-M40S: 55 01 05 02 3c 80 aa
📡 Sending command 05, data: [02 3c 80]
📤 Data sent successfully
📥 Received response: 55 01 05 01 aa
✅ Mode set successfully: mode=2 (Rice/Cereals), target_temp=60, boil_time=0
```

## Integration Status Check

1. Settings → Integrations → SkyCooker
2. Check connection status
3. Check available entities
4. Enable debug logs for detailed information (see section above)

## Support

If problems are not resolved:

1. Collect HomeAssistant logs with filter `skycooker`
2. Check that your device model is supported
3. Create issue in repository with problem description and logs
4. Specify device model, HomeAssistant version, and system

## Frequently Asked Questions

**Q: Why doesn't integration see my device?**
A: Check that device is powered on, in pairing mode, and within Bluetooth range.

**Q: Can I use multiple devices?**
A: Yes, each device is added separately with unique MAC address.

**Q: Do I need to keep connection active?**
A: Persistent connection is recommended for better performance, but increases power consumption.

**Q: What to do if device stops working after update?**
A: Try removing and re-adding integration, check for integration updates.

## Language Versions

- [Русская версия](TROUBLESHOOTING.md)
- [English version](TROUBLESHOOTING_EN.md)