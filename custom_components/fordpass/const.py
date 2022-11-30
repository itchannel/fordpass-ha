"""Constants for the FordPass integration."""

DOMAIN = "fordpass"

VIN = "vin"

MANUFACTURER = "Ford Motor Company"

VEHICLE = "Ford Vehicle"

DEFAULT_PRESSURE_UNIT = "kPa"
DEFAULT_DISTANCE_UNIT = "km"

CONF_PRESSURE_UNIT = "pressure_unit"
CONF_DISTANCE_UNIT = "distance_unit"

PRESSURE_UNITS = ["PSI", "kPa"]
DISTANCE_UNITS = ["mi", "km"]

UPDATE_INTERVAL = "update_interval"
UPDATE_INTERVAL_DEFAULT = 900


REGION = "region"

REGION_OPTIONS = ["UK&Europe", "Australia", "North America & Canada"]

SENSORS = {
    "odometer": {"icon": "mdi:counter", "state_class": "total", "device_class": "distance"},
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
    "deepSleepInProgress": {
        "icon": "mdi:power-sleep",
        "name": "Deep Sleep Mode Active",
    },
    "firmwareUpgInProgress": {
        "icon": "mdi:one-up",
        "name": "Firmware Update In Progress",
    },
    "remoteStartStatus": {"icon": "mdi:remote"},
    "zoneLighting": {"icon": "mdi:spotlight-beam"},
    "messages": {"icon": "mdi:message-text"},
}

SWITCHES = {"ignition": {"icon": "hass:power"}, "guardmode": {"icon": "mdi:shield-key"}}

WINDOW_POSITIONS = {
    "CLOSED": {
        "Fully_Closed": "Closed",
        "Fully_closed_position": "Closed",
        "Fully closed position": "Closed",
    },
    "OPEN": {
        "Fully open position": "Open",
        "Fully_Open": "Open",
        "Btwn 10% and 60% open": "Open-Partial",
    },
}

SWITCHES = {"ignition": {"icon": "hass:power"}, "guardmode": {"icon": "mdi:shield-key"}}
