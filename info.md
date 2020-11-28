
# **Changelog**
### Version 1.07
- Support for multiple regions (Fixes unavaliable bug)
- Token renamed to fordpass_token

**In order to support regions you will need to reinstall the integration to change region** (Existing installs will default to North America)

### Version 1.06 
- Minor bug fix
### Version 1.05
- Added device_tracker type (fordpass_tracker)
- Added imperial or metric selection
- Change fuel reading to %
- Renamed lock entity from "lock.lock" to "lock.fordpass_doorlock"


### Version 1.04
- Added window position status
- Added service "fresh_status" to allow for polling the car at a set interval or event
- Added Last Refreshed sensor, so you can see when the car was last polled for data
- Added some more debug logging

### Version 1.03
- Added door status
- Added token saving
- Added car poll refresh


Fordpass can be configured via Integrations UI

## Integration page

1. From Home Assistant UI go to Configuration > Integrations
2. Click the orange + icon at the bottom right to bring up new integration window
3. Find and click on fordpass
4. Enter required information and click Submit

