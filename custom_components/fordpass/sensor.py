import logging
from datetime import datetime, timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle, dt

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass
)

from . import FordPassEntity
from .const import CONF_DISTANCE_UNIT, CONF_PRESSURE_UNIT, DOMAIN, SENSORS


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    for key, value in SENSORS.items():
        sensor = CarSensor(entry, key, config_entry.options)
        # Add support for only adding compatible sensors for the given vehicle
        _LOGGER.debug(sensor.coordinator.data)
        if key == "zoneLighting":
            if "zoneLighting" in sensor.coordinator.data:
                async_add_entities([sensor], True)
        elif key == "elVeh":
            if sensor.coordinator.data["elVehDTE"] != None:
                async_add_entities([sensor], True)
        else:
            async_add_entities([sensor], True)


class CarSensor(
    FordPassEntity,
    SensorEntity,
):
    def __init__(self, coordinator, sensor, options):

        self.sensor = sensor
        self.fordoptions = options
        self._attr = {}
        self.coordinator = coordinator
        self._device_id = "fordpass_" + sensor
        # Required for HA 2022.7
        self.coordinator_context = object()

    def get_value(self, ftype):
        if ftype == "state":
            if self.sensor == "odometer":
                if self.fordoptions[CONF_DISTANCE_UNIT] != None:
                    if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                        return round(
                            float(self.coordinator.data[self.sensor]["value"]) / 1.60934
                        )
                    else:
                        return self.coordinator.data[self.sensor]["value"]
                else:
                    return self.coordinator.data[self.sensor]["value"]
            elif self.sensor == "fuel":
                if self.coordinator.data[self.sensor] == None:
                    return None
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
            elif self.sensor == "firmwareUpgInProgress":
                return self.coordinator.data[self.sensor]["value"]
            elif self.sensor == "deepSleepInProgress":
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
                for key, value in self.coordinator.data[self.sensor].items():
                    if "open" in value["value"].lower():
                        return "Open"
                    elif "closed" in value["value"].lower():
                        return "Closed"
                return "Unsupported"
            elif self.sensor == "lastRefresh":
                return dt.as_local(
                    datetime.strptime(
                        self.coordinator.data[self.sensor], "%m-%d-%Y %H:%M:%S"
                    )
                )
            elif self.sensor == "elVeh":
                if self.coordinator.data["elVehDTE"] != None:
                    if self.fordoptions[CONF_DISTANCE_UNIT] != None:
                        if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                            return round(
                                float(self.coordinator.data["elVehDTE"]["value"])
                                / 1.60934
                            )
                        else:
                            return float(self.coordinator.data["elVehDTE"]["value"])
                    else:
                        return float(self.coordinator.data["elVehDTE"]["value"])
                else:
                    return "Unsupported"
            elif self.sensor == "zoneLighting":
                if "zoneLighting" not in self.coordinator.data:
                    return "Unsupported"
                if (
                    self.coordinator.data["zoneLighting"] != None
                    and self.coordinator.data["zoneLighting"]["activationData"] != None
                ):
                    return self.coordinator.data["zoneLighting"]["activationData"][
                        "value"
                    ]
                else:
                    return "Unsupported"
            elif self.sensor == "remoteStartStatus":
                if self.coordinator.data["remoteStartStatus"] == None:
                    return None
                else:
                    if self.coordinator.data["remoteStartStatus"]["value"] == 1:
                        return "Active"
                    else:
                        return "Inactive"
            elif self.sensor == "messages":
                if self.coordinator.data["messages"] == None:
                    return None
                else:
                    return len(self.coordinator.data["messages"])
        elif ftype == "measurement":
            if self.sensor == "odometer":
                if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
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
            elif self.sensor == "firmwareUpgInProgress":
                return None
            elif self.sensor == "deepSleepInProgress":
                return None
            elif self.sensor == "doorStatus":
                return None
            elif self.sensor == "windowsPosition":
                return None
            elif self.sensor == "lastRefresh":
                return None
            elif self.sensor == "zoneLighting":
                return None
            elif self.sensor == "remoteStartStatus":
                return None
            elif self.sensor == "messages":
                return "Messages"
        elif ftype == "attribute":
            if self.sensor == "odometer":
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "fuel":
                if self.coordinator.data[self.sensor] == None:
                    return None
                if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                    self.coordinator.data["fuel"]["distanceToEmpty"] = round(
                        float(self.coordinator.data["fuel"]["distanceToEmpty"])
                        / 1.60934
                    )
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

                    if self.fordoptions[CONF_PRESSURE_UNIT] == "PSI":
                        sval = 0.1450377377
                        rval = 1
                        decimal = 0
                    if self.fordoptions[CONF_PRESSURE_UNIT] == "BAR":
                        sval = 0.01
                        rval = 0.0689475729
                        decimal = 2
                    else:
                        sval = 1
                        rval = 6.8947572932
                        decimal = 0
                    tirepress = {}
                    for key, value in self.coordinator.data["TPMS"].items():
                        if "TirePressure" in key and value is not None and value is not '':
                            if "recommended" in key:
                                tirepress[key] = round(float(value["value"]) * rval, decimal)
                            else:
                                tirepress[key] = round(float(value["value"]) * sval, decimal)
                    return tirepress
                return None
            elif self.sensor == "gps":
                if self.coordinator.data[self.sensor] == None:
                    return None
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "alarm":
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "ignitionStatus":
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "firmwareUpgInProgress":
                return self.coordinator.data[self.sensor].items()
            elif self.sensor == "deepSleepInProgress":
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
                    if "open" in value["value"].lower():
                        if "btwn" in value["value"].lower():
                            windows[key] = "Open-Partial"
                        else:
                            windows[key] = "Open"
                    elif "closed" in value["value"].lower():
                        windows[key] = "Closed"
                return windows
            elif self.sensor == "lastRefresh":
                return None
            elif self.sensor == "elVeh":
                if self.coordinator.data["elVehDTE"] == None:
                    return None
                else:
                    elecs = dict()
                    if (
                        self.coordinator.data["elVehDTE"] != None
                        and self.coordinator.data["elVehDTE"]["value"] != None
                    ):
                        elecs["elVehDTE"] = self.coordinator.data["elVehDTE"]["value"]
                    if (
                        self.coordinator.data["plugStatus"] != None
                        and self.coordinator.data["plugStatus"]["value"] != None
                    ):
                        elecs["Plug Status"] = self.coordinator.data["plugStatus"][
                            "value"
                        ]

                    if (
                        self.coordinator.data["chargingStatus"] != None
                        and self.coordinator.data["chargingStatus"]["value"] != None
                    ):
                        elecs["Charging Status"] = self.coordinator.data[
                            "chargingStatus"
                        ]["value"]

                    if (
                        self.coordinator.data["chargeStartTime"] != None
                        and self.coordinator.data["chargeStartTime"]["value"] != None
                    ):
                        elecs["Charge Start Time"] = self.coordinator.data[
                            "chargeStartTime"
                        ]["value"]

                    if (
                        self.coordinator.data["chargeEndTime"] != None
                        and self.coordinator.data["chargeEndTime"]["value"] != None
                    ):
                        elecs["Charge End Time"] = self.coordinator.data[
                            "chargeEndTime"
                        ]["value"]

                    if (
                        self.coordinator.data["batteryFillLevel"] != None
                        and self.coordinator.data["batteryFillLevel"]["value"] != None
                    ):
                        elecs["Battery Fill Level"] = int(self.coordinator.data[
                            "batteryFillLevel"
                        ]["value"])

                    if (
                        self.coordinator.data["chargerPowertype"] != None
                        and self.coordinator.data["chargerPowertype"]["value"] != None
                    ):
                        elecs["Charger Power Type"] = self.coordinator.data[
                            "chargerPowertype"
                        ]["value"]

                    if (
                        self.coordinator.data["batteryChargeStatus"] != None
                        and self.coordinator.data["batteryChargeStatus"]["value"]
                        != None
                    ):
                        elecs["Battery Charge Status"] = self.coordinator.data[
                            "batteryChargeStatus"
                        ]["value"]

                    if (
                        self.coordinator.data["batteryPerfStatus"] != None
                        and self.coordinator.data["batteryPerfStatus"]["value"] != None
                    ):
                        elecs["Battery Performance Status"] = self.coordinator.data[
                            "batteryPerfStatus"
                        ]["value"]

                    return elecs
            elif self.sensor == "zoneLighting":
                if "zoneLighting" not in self.coordinator.data:
                    return None
                if (
                    self.coordinator.data[self.sensor] != None
                    and self.coordinator.data[self.sensor]["zoneStatusData"] != None
                ):
                    zone = dict()
                    if self.coordinator.data[self.sensor]["zoneStatusData"] != None:
                        for key, value in self.coordinator.data[self.sensor][
                            "zoneStatusData"
                        ].items():
                            zone["zone_" + key] = value["value"]

                    if (
                        self.coordinator.data[self.sensor]["lightSwitchStatusData"]
                        != None
                    ):
                        for key, value in self.coordinator.data[self.sensor][
                            "lightSwitchStatusData"
                        ].items():
                            if value is not None:
                                zone[key] = value["value"]

                    if (
                        self.coordinator.data[self.sensor]["zoneLightingFaultStatus"]
                        != None
                    ):
                        zone["zoneLightingFaultStatus"] = self.coordinator.data[
                            self.sensor
                        ]["zoneLightingFaultStatus"]["value"]
                    if (
                        self.coordinator.data[self.sensor][
                            "zoneLightingShutDownWarning"
                        ]
                        != None
                    ):
                        zone["zoneLightingShutDownWarning"] = self.coordinator.data[
                            self.sensor
                        ]["zoneLightingShutDownWarning"]["value"]
                    return zone
                else:
                    return None
            elif self.sensor == "remoteStartStatus":
                if self.coordinator.data["remoteStart"] == None:
                    return None
                else:
                    return self.coordinator.data["remoteStart"].items()
            elif self.sensor == "messages":
                if self.coordinator.data["messages"] == None:
                    return None
                else:
                    messages = dict()
                    for value in self.coordinator.data["messages"]:

                        messages[value["messageSubject"]] = value["createdDate"]
                    return messages

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
    def extra_state_attributes(self):
        return self.get_value("attribute")

    @property
    def native_unit_of_measurement(self):
        return self.get_value("measurement")

    @property
    def icon(self):
        return SENSORS[self.sensor]["icon"]

    @property
    def state_class(self):
        if "state_class" in SENSORS[self.sensor]:
            if SENSORS[self.sensor]["state_class"] is "total":
                return SensorStateClass.TOTAL
            elif SENSORS[self.sensor]["state_class"] is "measurement":
                return SensorStateClass.MEASUREMENT
            else:
                return None
        else:
            return None

    @property
    def device_class(self):
        if "device_class" in SENSORS[self.sensor]:
            if SENSORS[self.sensor]["device_class"] is "distance":
                return SensorDeviceClass.DISTANCE
            else:
                return None