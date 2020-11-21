# Fordpass Home Assistant Integration

## Credit 
https://github.com/clarkd - Initial Home Assistant automation idea and Python code (Lock/Unlock)

## Install
Use HACS and add as a custom repo. Once the integration is installed go to your integrations and follow the configuration options to specify the below:
- Username (Fordpass App)
- Password (Fordpass App)
- VIN Number

## Usage
Your car must have the lastest onboard modem functionality and have registered/authorised the fordpass application

### Car Refresh
I have added a service to poll the car for updates, due to the battery drain I have left this up to you to set the interval. The service to be called is "


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


## Coming Soon

- Code tidy up
- Alarm event (Anyone have the json output for this event would be appreciated :) )
