
# **Changelog**
## Version 1.34
- Change oauth flow for latest Fordpass changes
## Version 1.33
- Fix occasional hacs error due to git tag issue
## Version 1.32
- Fix auth flow to comply with new endpoints
**Warning - If you encounter auth errors please delete the token file located in the install directory or use the "delete_token" service**
## Version 1.31
- Fix for multiple accounts
## Version 1.30
- Fix for elvDTE error
### Version 1.29
- Disabled guard mode
- Fixed elvDTE units
- set Vin check on install to warning only (Lincoln cars don't show in ford database)
### Version 1.28
- Added vin check on setup (Will check if given VIN is linked to the credentials)
### Version 1.27
- Fix fuel level error
- Add code for Vin debugging
### Version 1.25
- Updated user agent
- Added messages sensor to show current messages in fordpass

### Version 1.24
- Change device_state_attributes to extra_state_attributes (HA 2020.12.1)
- Changed session timeout to cope with timeouts in fordpass API (Helps prevent 403 error's)

### Version 1.23
**Breaking Change**

When installing this new version please go to "integrations" and click configure on Fordpass and choose your preferred units. Not doing this will result in an error!!

- Fixed tyre pressure status when sensor missing or broke
- Add DistanceToEmpty Imperial Conversion (Thanks @JacobWasFramed )
- Seperated pressure and distance measurement unit selection (Thanks @JacobWasFramed)
### Version 1.22
- Fix for custom config locations on certain HA installs

### Version 1.21
- Error handling for null fuel and elVehDTE attributes. Thanks @wietseschmitt

### Version 1.20
- Fixed incorrect reporting of guardmode switch status

### Version 1.19
- Added null guard status handling (effects some vehicles)

### Version 1.18
- Fix Guard mode error (Missing data array)

### Version 1.17
- Added VIN option to UI
- Added Guard mode switch (Need people to test as don't have access to a guard mode enabled vehicle)
- Added extra sensors (Credit @tonesto7)
    - Zonelighting (Supported models only)
    - Deep sleep status
    - Remote start status
    - Firmware update status
- Added partial opening status for windows (Credit @tonesto7)
- Added logic to only add supported sensors (Still in Beta)


### Version 1.16
- Fixed json error when adding multiple cars
- Added "vin" option to "refresh" service to allow for refreshing of individual cars
- Fixed service bug calling the wrong variable
- Updated manifest for latest HA requirements

### Version 1.15
- Added Version attribute to manifest.json

### Version 1.14
- Converted "lastrefresh" to home assistant local time

### Version 1.13
- Fixed window status for Undefined
- Tire pressure now reports based on region
- Fixed 401 error for certain token refreshes
- Token file has been moved to same folder as install (Can be changed by changing the token_location variable)

### Version 1.12
- Fixed window status reporting as Open

### Version 1.11
- Added check for "Undefined_window_position" window value
- Fixed bug when TMPS value was 0 (Some cars return 0 on individual tyre pressures)

### Version 1.10
- Fixed door open bug 2.0 (New position value)
- Added a check to see if a vehicle supports GPS before adding the entity

### Version 1.09
- Added individual TMPS Support
- Fixed door open bug

### Version 1.08
- Added Icons for each entity
- Added "clear_tokens" service call
- Added Electric Vehicle features
- Fixed "Invalid" lock status

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

