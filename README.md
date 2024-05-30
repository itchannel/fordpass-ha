# Fordpass Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/itchannel)

<!-- Wrote up a little note thing for the breaking change. Not sure if you want to use it but I figured this could be a good start or something since I was already editing the readme. -->
> [!WARNING]
> # Breaking Change
> There is a new token obtaining system.
> 
> The token used by this integration is currently removed whenever the integration is updated. With this 1.70 update, the token will be wiped during every update, requiring users to manually add the token during the initial setup.
> 
> To prevent this issue, we will be moving the token file outside of the FordPass directory. This change will ensure that the token is preserved during updates. This will require reconfiguration of your setup.
> Please see the Installation section, or the Wiki for help.

<!-- Tried to update the update with the new information -->
> [!IMPORTANT]  
> # FordConnect API
>
> Dear FordPass Integration Users,
> As you know there have been many challenges with the Ford API. We > are actively working on developments but please note that these developments **will take time.**
> - **FordConnect API:** Ford has enabled developer accounts and released their `FordConnect API`. However, this API and its documentation currently **lack many data points** or **are not fully >implemented**. It is presently supported only in North America. 
> - **FordPass APP:** Ford has also released their refreshed `FordPass App`. This refreshed app includes some new features while also >removing certain items, similar to the FordConnect API.
> 
> It is important to understand that our integration depends on the data provided by either the `FordConnect API` or the `FordPass App`, >which may limit some functionalities.

## Future Updates:

- **Enhancements:** We are committed to enhancing the integration and ensuring its functionality. However, we both have limited time to allocate to this effort.

- **Implementation:** We are actively working on integrating the new `FordConnect API` to ensure users who can access it will benefit from its features. At the same time, we will maintain functionality for users who are unable to use this new API.

#### Please be aware that there may be issues or disruptions during this process.

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

## **Changelog**
[Updates](info.md)

## Installation
Use [HACS](https://hacs.xyz/) to add this repository as a custom repo. 

Upon installation navigate to your integrations, and follow the configuration options. You will need to provide:
- Fordpass Email
- Region (Where you are based, required for tokens to work correctly)

You will then be prompted with `Setup Token` 

Follow the instructions on the [Wiki](https://github.com/itchannel/fordpass-ha/wiki/Obtaining-Tokens-(As-of-25-05-2024)) to obtain your token

## Usage
Your car must have the lastest onboard modem functionality and have registered/authorised the fordpass application

## Services
<!-- I haven't looked into these services, but it might be easier to maintain a Wiki with the various services compared to the README. Just a thought. -->
### Car Refresh
I have added a service to poll the car for updates, due to the battery drain I have left this up to you to set the interval. The service to be called is "refresh_status" and can be accessed in home assistant using "fordpas.refresh_status". 

Optionally you can add the "vin" parameter followed by your VIN number to only refresh one vehicle. By default this service will refresh all registered cars in HA.

**This will take up to 5 mins to update from the car once the service has been run**

###
Click on options and choose imperial or metric to display in km/miles. Takes effect on next restart of home assistant. Default is Metric
<!-- These might need to be updated since its now different -->
### Clear Tokens
If you are experiencing any sign in issues, please trying clearing your tokens using the "clear_tokens" service call.

### Poll API
This service allows you to manually refresh/poll the API without waiting the set poll interval. Handy if you need quicker updates e.g. when driving for gps coordinates


## Sensors
### Currently Working
**Sensors may change as the integration is being developed**
<!-- Keeping this the same, but it will probably change and update alongside Fordconnect and the new app features -->

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
