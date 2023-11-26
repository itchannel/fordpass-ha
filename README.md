# Fordpass Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/itchannel)


# Important Update: New Ford API Challenges and Updates

Dear FordPass Integration Users,

We want to keep you informed about the latest developments regarding the integration. Ford has recently introduced a new API, which has presented both opportunities and challenges. Here are some key points to note:

## Challenges and Issues:

- **Increased Complexity:** The new API has brought about several challenges and complexities. While it has enabled new attributes and sensors for different vehicles, it has also made integration more intricate.

- **Vehicle Variety:** In addition to an entirely new data structure, it is difficult to determine the variety of vehicles that can be supported - without knowing their capabilities. We are assessing which vehicles contain the information necessary to enable different sensors.

- **Unstable Nature of the New API:** Currently, the API appears to be unstable and/or changing. Any changes to its structure can disrupt sensor data. It is difficult to determine why: vehicles may still be in the process of migration, needing an update, or have a different data structure. Either way, instability has been noticed, and any updates or changes to the API can impact this integration.

## Ongoing Work and Future Updates:

- **Ongoing Work:** We both want to continue enhancing the integration and ensuring its functionality. However, it's important to note that we have limited time to allocate to this effort.

- **Future Updates:** We are continuing our efforts to adapt to new changes and persue further enhancments.


#### Please understand that there may be issues, or disruptions, to different sensors during this process.

If you have any questions or concerns, please either open a new issue or comment on an existing issue related to yours.

Thank you,

itchannel and SquidBytes

## Credit 
- https://github.com/clarkd - Initial Home Assistant automation idea and Python code (Lock/Unlock)
- https://github.com/pinballnewf - Figuring out the application ID issue
- https://github.com/degrashopper - Fixing 401 error for certain installs
- https://github.com/tonesto7 - Extra window statuses and sensors
- https://github.com/JacobWasFramed - Updated unit conversions
- https://github.com/heehoo59 - French Translation
- https://github.com/SquidBytes - EV updates and documentation

## Account Warning (Sep 2023)
A number of users have encountered their accounts being banned for containing "+" symbols in their email. It appears Ford thinks this is a disposable email. So if you have a + in your email I recommend changing it.

## **Changelog**
[Updates](info.md)

## Installation
Use [HACS](https://hacs.xyz/) to add this repository as a custom repo. Upon installation navigate to your integrations, and follow the configuration options. You will need to provide:
- Username (Fordpass App)
- Password (Fordpass App)
- Region (Where you are based, required for tokens to work correctly)

## Requirement
Your car must have the lastest onboard modem functionality and have registered/authorised the fordpass application

## Services

 ### Car Refresh
I have added a service to poll the car for updates, due to the battery drain I have left this up to you to set the interval. The service to be called is "refresh_status" and can be accessed in home assistant using "fordpass.refresh_status". 

Optionally you can add the "vin" parameter followed by your VIN number to only refresh one vehicle. By default this service will refresh all registered cars in HA.

**This will take up to 5 mins to update from the car once the service has been run**

### Unit Conversion
Click on options and choose imperial or metric to display in km/miles. Takes effect on next restart of home assistant. Default is Metric

### Clear Tokens
If you are experiencing any sign in issues, please trying clearing your tokens using the "clear_tokens" service call.

### Poll API
This service allows you to manually refresh/poll the API without waiting the set poll interval. Handy if you need quicker updates e.g. when driving for gps coordinates


## Currently Working
Depending on your vehicles capability

### Switches
- Guard Mode
- Lock/Unlock
- Remote Start

### Sensors
- Alarm Status
- Battery Status (12v)
- Coolant Temperature
- Deep sleep status
- Diesel System
- Door Status
- Electric Vehicle Support
- Firmware Update Status
- Fuel Level
- Ignition Status
- Indicators (Value of various vehicles indicators)
- Last Refresh
- FordPass messages and alerts
- Odometer
- Oil Status
- Outside Temperature
- Speed
- Tyre Status
- TPMS Sensors
- Car Tracker
- Window Status

## Disclaimer
This integration is not officially supported by Ford and as such using this integration could result in your account being locked out!
