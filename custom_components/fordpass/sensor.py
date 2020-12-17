import logging
from datetime import timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from . import FordPassEntity
from .const import CONF_UNIT, DOMAIN, SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    sensors = []
    for key, value in SENSORS.items():
        async_add_entities([CarSensor(entry, key, config_entry.options)], True)


class CarSensor(
    FordPassEntity,
    Entity,
):
    def __init__(self, coordinator, sensor, options):

        self.sensor = sensor
        self.options = options
        self._attr = {}
        self.coordinator = coordinator
        self._device_id = "fordpass_" + sensor

    def get_value(self, ftype):
        if ftype == "state":
            if self.sensor == "odometer":
                if self.options[CONF_UNIT] == "imperial":
                    return round(
                        float(self.coordinator.data[self.sensor]["value"]) / 1.60934
                    )
                else:
                    return self.coordinator.data[self.sensor]["value"]
            elif self.sensor == "fuel":
                return round(self.coordinator.data[self.sensor]["fuelLevel"])
            elif self.sensor == "battery":
                return self.coordinator.data[self.sensor]["batteryHealth"]["value"]
            elif self.sensor == "oil":
                return self.coordinator.data[self.sensor]["oilLife"]
            elif self.sensor == "tirePressure":
                return self.coordinator.data[self.sensor]["value"]
            elif self.sensor == "gps":
                if self.coordinator.data[self.sensor] == None:
                    return "Unsupported"
                return self.coordinator.data[self.sensor]["gpsState"]
            elif self.sensor == "alarm":
                return self.coordinator.data[self.sensor]["value"]
            elif self.sensor == "ignitionStatus":
                return self.coordinator.data[self.sensor]["value"]
            elif self.sensor == "doorStatus":
                for key, value in self.coordinator.data[self.sensor].items():
                    if value["value"] == "Invalid":
                        continue
                    if value["value"] != "Closed":
                        return "Open"
                return "Closed"
            elif self.sensor == "windowPosition":
                if self.coordinator.data[self.sensor] == None:
                    return "Unsupported"
                window_closed_status = ["Fully_Closed", "Fully_closed_position", "Undefined_window_position"]
                for key, value in self.coordinator.data[self.sensor].items():
                    if value["value"] not in window_closed_status:
                        return "Open"
                return "Closed"
            elif self.sensor == "lastRefresh":
                return self.coordinator.data[self.sensor]
            elif self.sensor == "elVeh":
                if self.coordinator.data["elVehDTE"] != None:
                    return self.coordinator.data["chargingStatus"]["value"]
                else:
                    return "Unsupported"
        elif ftype == "measurement":
            if self.sensor == "odometer":
                if self.options[CONF_UNIT] == "imperial":
                    return "mi"
                else:
                    return "km"
            elif self.sensor == "fuel":
                return "%"
            elif self.sensor == "battery":
                return None
            elif self.sensor == "oil":
                return None
            elif self.sensor == "tirePressure":
                return None
            elif self.sensor == "gps":
                return None
            elif self.sensor == "alarm":
                return None
            elif self.sensor == "ignitionStatus":
                return None
            elif self.sensor == "doorStatus":
                return None
            elif self.sensor == "windowsPosition":
                return None
            elif self.sensor == "lastRefresh":
                return None
        elif ftype == "attribute":
            if self.sensor == "odometer":
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "fuel":
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "battery":
                return {
                    "Battery Voltage": self.coordinator.data[self.sensor][
                        "batteryStatusActual"
                    ]["value"]
                }
            elif self.sensor == "oil":
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "tirePressure":
                if self.coordinator.data["TPMS"] != None:
                    return {
                        "leftFrontTirePressure": round(
                            float(
                                self.coordinator.data["TPMS"]["leftFrontTirePressure"][
                                    "value"
                                ]
                                or 0
                            )
                            * 0.1450377377
                        ),
                        "rightFrontTirePressure": round(
                            float(
                                self.coordinator.data["TPMS"]["rightFrontTirePressure"][
                                    "value"
                                ]
                                or 0
                            )
                            * 0.1450377377
                        ),
                        "outerLeftRearTirePressure": round(
                            float(
                                self.coordinator.data["TPMS"][
                                    "outerLeftRearTirePressure"
                                ]["value"]
                                or 0
                            )
                            * 0.1450377377
                        ),
                        "outerRightRearTirePressure": round(
                            float(
                                self.coordinator.data["TPMS"][
                                    "outerRightRearTirePressure"
                                ]["value"]
                                or 0
                            )
                            * 0.1450377377
                        ),
                    }
                return None
            elif self.sensor == "gps":
                if self.coordinator.data[self.sensor] == None:
                    return None
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "alarm":
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "ignitionStatus":
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "doorStatus":
                doors = dict()
                for key, value in self.coordinator.data[self.sensor].items():
                    doors[key] = value["value"]
                return doors
            elif self.sensor == "windowPosition":
                if self.coordinator.data[self.sensor] == None:
                    return None
                windows = dict()
                for key, value in self.coordinator.data[self.sensor].items():
                    windows[key] = value["value"]
                return windows
            elif self.sensor == "lastRefresh":
                return None
            elif self.sensor == "elVeh":
                if self.coordinator.data["elVehDTE"] != None:
                    return {
                        "Plug Status": self.coordinator.data["plugStatus"]["value"],
                        "Charge Start Time": self.coordinator.data["chargeStartTime"][
                            "value"
                        ],
                        "Charge End Time": self.coordinator.data["chargeEndTime"][
                            "value"
                        ],
                        "Battery Fill Level": self.coordinator.data["batteryFillLevel"][
                            "value"
                        ],
                        "Charger Power Type": self.coordinator.data["chargerPowertype"][
                            "value"
                        ],
                    }
                else:
                    return None

    @property
    def name(self):
        return "fordpass_" + self.sensor

    @property
    def state(self):
        return self.get_value("state")

    @property
    def device_id(self):
        return self.device_id

    @property
    def device_state_attributes(self):
        return self.get_value("attribute")

    @property
    def unit_of_measurement(self):
        return self.get_value("measurement")

    @property
    def icon(self):
        return SENSORS[self.sensor]["icon"]
