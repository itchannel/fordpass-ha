# Fordpass Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/itchannel)

## Credit 
- https://github.com/clarkd - Initial Home Assistant automation idea and Python code (Lock/Unlock)
- https://github.com/pinballnewf - Figuring out the application ID issue
- https://github.com/degrashopper - Fixing 401 error for certain installs
- https://github.com/tonesto7 - Extra window statuses and sensors
- https://github.com/JacobWasFramed - Updated unit conversions
- https://github.com/heehoo59 - French Translation

## 1.50 Change
As of 1.50 VIN number is no longer required for setup. Integration should display a list of vehicles associated with your Fordpass account

## 1.47 Change
If you are experiencing issues with the odometer displaying wrong, please try enabling the checkbox in options for "Disable Distance Conversion"


## Install
Use HACS and add as a custom repo. Once the integration is installed go to your integrations and follow the configuration options to specify the below:
- Username (Fordpass App)
- Password (Fordpass App)
- VIN Number (Not required in 1.50)
- Region (Where you are based, required for tokens to work correctly)

## Usage
Your car must have the lastest onboard modem functionality and have registered/authorised the fordpass application

### Car Refresh
I have added a service to poll the car for updates, due to the battery drain I have left this up to you to set the interval. The service to be called is "refresh_status" and can be accessed in home assistant using "fordpas.refresh_status". 

Optionally you can add the "vin" parameter followed by your VIN number to only refresh one vehicle. By default this service will refresh all registered cars in HA.

**This will take up to 5 mins to update from the car once the service has been run**
###
Click on options and choose imperial or metric to display in km/miles. Takes effect on next restart of home assistant. Default is Metric

### Clear Tokens
If you are experiencing any sign in issues, please trying clearing your tokens using the "clear_tokens" service call.

### Poll API
This service allows you to manually refresh/poll the API without waiting the set poll interval. Handy if you need quicker updates e.g. when driving for gps coordinates


## Currently Working

- Fuel Level
- Odometer
- Lock/Unlock
- Oil Status
- Last known GPS Coordinates/Map
- Tyre Status
- Battery Status
- Ignition Status
- Alarm Status
- Individual door statuses
- Remote Start
- Window Status (Only if your car supports it!)
- Last Car Refresh status
- Car Tracker
- Supports Multiple Regions
- Electric Vehicle Support
- TPMS Sensors
- Guard Mode (Only supported cars)
- Deep sleep status
- Fordpass messages and alerts



## Disclaimer

This integration is not officially supported by Ford and as such using this integration could result in your account being locked out!
