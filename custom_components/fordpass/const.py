"""Constants for the FordPass integration."""

DOMAIN = "fordpass"

VIN = "vin"

MANUFACTURER = "Ford Motor Company"

VEHICLE = "Ford Vehicle"

DEFAULT_UNIT = "metric"
CONF_UNIT = "units"

CONF_UNITS = ["imperial", "metric"]


REGION = "region"

REGION_OPTIONS = ["UK&Europe", "Australia", "North America & Canada"]

SENSORS = {
    "odometer": {"icon": "mdi:counter"},
    "fuel": {"icon": "mdi:gas-station"},
    "battery": {"icon": "mdi:car-battery"},
    "oil": {"icon": "mdi:oil"},
    "tirePressure": {"icon": "mdi:car-tire-alert"},
    "gps": {"icon": "mdi:radar"},
    "alarm": {"icon": "mdi:bell"},
    "ignitionStatus": {"icon": "hass:power"},
    "doorStatus": {"icon": "mdi:car-door"},
    "windowPosition": {"icon": "mdi:car-door"},
    "lastRefresh": {"icon": "mdi:clock"},
    "elVeh": {"icon": "mdi:ev-station"},
}

SWITCHES = {"ignition": {"icon": "hass:power"}, "guardmode": {"icon": "mdi:shield-key"}}
