"""Constants for the FordPass integration."""

DOMAIN = "fordpass"

VIN = "vin"

MANUFACTURER = "Ford Motor Company"

VEHICLE = "Ford Vehicle"

DEFAULT_PRESSURE_UNIT = "kPa"
DEFAULT_DISTANCE_UNIT = "km"

CONF_PRESSURE_UNIT = "pressure_unit"
CONF_DISTANCE_UNIT = "distance_unit"

PRESSURE_UNITS = ["PSI", "kPa", "BAR"]
DISTANCE_UNITS = ["mi", "km"]
DISTANCE_CONVERSION_DISABLED = "distance_conversion"
DISTANCE_CONVERSION_DISABLED_DEFAULT = False

UPDATE_INTERVAL = "update_interval"
UPDATE_INTERVAL_DEFAULT = 900

COORDINATOR = "coordinator"


REGION = "region"

REGION_OPTIONS = ["UK&Europe", "Australia", "North America & Canada"]

SENSORS = {
    "odometer": {"icon": "mdi:counter", "state_class": "total", "device_class": "distance"},
    "fuel": {"icon": "mdi:gas-station"},
    "battery": {"icon": "mdi:car-battery"},
    "oil": {"icon": "mdi:oil"},
    "tirePressure": {"icon": "mdi:car-tire-alert"},
    # "gps": {"icon": "mdi:radar"},
    "alarm": {"icon": "mdi:bell"},
    "ignitionStatus": {"icon": "hass:power"},
    "doorStatus": {"icon": "mdi:car-door"},
    "windowPosition": {"icon": "mdi:car-door"},
    "lastRefresh": {"icon": "mdi:clock", "device_class": "timestamp"},
    "elVeh": {"icon": "mdi:ev-station"},
    "elVehCharging": {"icon": "mdi:ev-station"},
    "speed": {"icon": "mdi:speedometer"},
    "indicators": {"icon": "mdi:engine-outline"},
    "coolantTemp" : {"icon": "mdi:coolant-temperature", "state_class": "measurement", "device_class": "temperature"},
    "outsideTemp" : {"icon": "mdi:thermometer", "state_class": "measurement", "device_class": "temperature"},
    "engineOilTemp" : {"icon": "mdi:oil-temperature", "state_class": "measurement", "device_class": "temperature"},
    # "deepSleepInProgress": {
    #     "icon": "mdi:power-sleep",
    #    "name": "Deep Sleep Mode Active",
    # },
    # "firmwareUpgInProgress": {
    #    "icon": "mdi:one-up",
    #   "name": "Firmware Update In Progress",
    # },
    "remoteStartStatus": {"icon": "mdi:remote"},
    # "zoneLighting": {"icon": "mdi:spotlight-beam"},
    "messages": {"icon": "mdi:message-text"},
    "dieselSystemStatus": {"icon": "mdi:smoking-pipe"},
    "exhaustFluidLevel": {"icon": "mdi:barrel"}
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

SWITCHES = {
    "ignition": {"icon": "hass:power"},
    # "guardmode": {"icon": "mdi:shield-key"}
}
