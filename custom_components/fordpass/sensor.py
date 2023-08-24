"""All vehicle sensors from the accessible by the API"""
import logging
from datetime import datetime

from homeassistant.util import dt

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass
)

from . import FordPassEntity
from .const import CONF_DISTANCE_UNIT, CONF_PRESSURE_UNIT, DOMAIN, SENSORS, COORDINATOR, DISTANCE_CONVERSION_DISABLED


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    sensors = []
    for key in SENSORS:
        sensor = CarSensor(entry, key, config_entry.options)
        # Add support for only adding compatible sensors for the given vehicle
        if key == "zoneLighting":
            if "zoneLighting" in sensor.coordinator.data:
                sensors.append(sensor)
        elif key == "elVeh":
            if sensor.coordinator.data["elVehDTE"] is not None:
                sensors.append(sensor)
        elif key == "dieselSystemStatus":
            if sensor.coordinator.data.get("dieselSystemStatus", {}):
                if sensor.coordinator.data.get("dieselSystemStatus", {}).get("filterRegenerationStatus"):
                    sensors.append(sensor)
        elif key == "exhaustFluidLevel":
            if sensor.coordinator.data.get("dieselSystemStatus", {}):
                if sensor.coordinator.data.get("dieselSystemStatus", {}).get("exhaustFluidLevel"):
                    sensors.append(sensor)
        else:
            sensors.append(sensor)
    async_add_entities(sensors, True)


class CarSensor(
    FordPassEntity,
    SensorEntity,
):
    def __init__(self, coordinator, sensor, options):

        super().__init__(
            device_id="fordpass_" + sensor,
            name="fordpass_" + sensor,
            coordinator=coordinator
        )

        self.sensor = sensor
        self.fordoptions = options
        self._attr = {}
        self.coordinator = coordinator
        self._device_id = "fordpass_" + sensor
        # Required for HA 2022.7
        self.coordinator_context = object()

    def get_value(self, ftype):
        """Get sensor value and attributes from coordinator data"""
        if ftype == "state":
            if self.sensor == "odometer":
                if self.fordoptions[CONF_DISTANCE_UNIT] is not None:
                    if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                        if DISTANCE_CONVERSION_DISABLED in self.fordoptions and self.fordoptions[DISTANCE_CONVERSION_DISABLED] is True:
                            return self.coordinator.data[self.sensor]["value"]
                        return round(
                            float(self.coordinator.data[self.sensor]["value"]) / 1.60934
                        )
                    return self.coordinator.data[self.sensor]["value"]
                return self.coordinator.data[self.sensor]["value"]
            if self.sensor == "fuel":
                if self.coordinator.data[self.sensor] is None:
                    return None
                return round(self.coordinator.data[self.sensor]["fuelLevel"])
            if self.sensor == "battery":
                return self.coordinator.data[self.sensor]["batteryHealth"]["value"]
            if self.sensor == "oil":
                return self.coordinator.data[self.sensor]["oilLife"]
            if self.sensor == "tirePressure":
                return self.coordinator.data[self.sensor]["value"]
            if self.sensor == "gps":
                if self.coordinator.data[self.sensor] is None:
                    return "Unsupported"
                return self.coordinator.data[self.sensor]["gpsState"]
            if self.sensor == "alarm":
                return self.coordinator.data[self.sensor]["value"]
            if self.sensor == "ignitionStatus":
                return self.coordinator.data[self.sensor]["value"]
            if self.sensor == "firmwareUpgInProgress":
                return self.coordinator.data[self.sensor]["value"]
            if self.sensor == "deepSleepInProgress":
                return self.coordinator.data[self.sensor]["value"]
            if self.sensor == "doorStatus":
                for key, value in self.coordinator.data[self.sensor].items():
                    if value["value"] == "Invalid":
                        continue
                    if value["value"] != "Closed":
                        return "Open"
                return "Closed"
            if self.sensor == "windowPosition":
                if self.coordinator.data[self.sensor] is None:
                    return "Unsupported"
                status = "Closed"
                for key, value in self.coordinator.data[self.sensor].items():
                    if "open" in value["value"].lower():
                        status = "Open"
                return status
            if self.sensor == "lastRefresh":
                return dt.as_local(
                    datetime.strptime(
                        self.coordinator.data[self.sensor] + "+0000", "%m-%d-%Y %H:%M:%S%z"
                    )
                )
            if self.sensor == "elVeh":
                if self.coordinator.data["elVehDTE"] is not None:
                    if self.fordoptions[CONF_DISTANCE_UNIT] is not None:
                        if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                            return round(
                                float(self.coordinator.data["elVehDTE"]["value"]) / 1.60934
                            )
                        return float(self.coordinator.data["elVehDTE"]["value"])
                    return float(self.coordinator.data["elVehDTE"]["value"])
                return "Unsupported"
            if self.sensor == "zoneLighting":
                if "zoneLighting" not in self.coordinator.data:
                    return "Unsupported"
                if (
                    self.coordinator.data["zoneLighting"] is not None and self.coordinator.data["zoneLighting"]["activationData"] is not None
                ):
                    return self.coordinator.data["zoneLighting"]["activationData"][
                        "value"
                    ]
                return "Unsupported"
            if self.sensor == "remoteStartStatus":
                if self.coordinator.data["remoteStartStatus"] is None:
                    return None
                if self.coordinator.data["remoteStartStatus"]["value"] == 1:
                    return "Active"
                return "Inactive"
            if self.sensor == "messages":
                if self.coordinator.data["messages"] is None:
                    return None
                return len(self.coordinator.data["messages"])
            if self.sensor == "dieselSystemStatus":
                if self.coordinator.data["dieselSystemStatus"]["filterRegenerationStatus"] is not None:
                    return self.coordinator.data["dieselSystemStatus"]["filterRegenerationStatus"]
                return "Not Supported"
            if self.sensor == "exhaustFluidLevel":
                if "value" in self.coordinator.data["dieselSystemStatus"]["exhaustFluidLevel"]:
                    return self.coordinator.data["dieselSystemStatus"]["exhaustFluidLevel"]["value"]
                return "Not Supported"
            return None
        if ftype == "measurement":
            if self.sensor == "odometer":
                if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                    return "mi"
                return "km"
            if self.sensor == "fuel":
                return "%"
            if self.sensor == "battery":
                return None
            if self.sensor == "oil":
                return None
            if self.sensor == "tirePressure":
                return None
            if self.sensor == "gps":
                return None
            if self.sensor == "alarm":
                return None
            if self.sensor == "ignitionStatus":
                return None
            if self.sensor == "firmwareUpgInProgress":
                return None
            if self.sensor == "deepSleepInProgress":
                return None
            if self.sensor == "doorStatus":
                return None
            if self.sensor == "windowsPosition":
                return None
            if self.sensor == "lastRefresh":
                return None
            if self.sensor == "zoneLighting":
                return None
            if self.sensor == "remoteStartStatus":
                return None
            if self.sensor == "messages":
                return "Messages"
            if self.sensor == "elVeh":
                if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                    return "mi"
                return "km"
            if self.sensor == "exhaustFluidLevel":
                return "%"
            return None
        if ftype == "attribute":
            if self.sensor == "odometer":
                return self.coordinator.data[self.sensor].items()
            if self.sensor == "fuel":
                if self.coordinator.data[self.sensor] is None:
                    return None
                if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                    self.coordinator.data["fuel"]["distanceToEmpty"] = round(
                        float(self.coordinator.data["fuel"]["distanceToEmpty"]) / 1.60934
                    )
                return self.coordinator.data[self.sensor].items()
            if self.sensor == "battery":
                return {
                    "Battery Voltage": self.coordinator.data[self.sensor][
                        "batteryStatusActual"
                    ]["value"]
                }
            if self.sensor == "oil":
                return self.coordinator.data[self.sensor].items()
            if self.sensor == "tirePressure":
                if self.coordinator.data["TPMS"] is not None:
                    if self.fordoptions[CONF_PRESSURE_UNIT] == "PSI":
                        sval = 0.1450377377
                        rval = 1
                        decimal = 0
                    if self.fordoptions[CONF_PRESSURE_UNIT] == "BAR":
                        sval = 0.01
                        rval = 0.0689475729
                        decimal = 2
                    if self.fordoptions[CONF_PRESSURE_UNIT] == "kPa":
                        sval = 1
                        rval = 6.8947572932
                        decimal = 0
                    else:
                        sval = 1
                        rval = 1
                        decimal = 0
                    tirepress = {}
                    for key, value in self.coordinator.data["TPMS"].items():
                        if "TirePressure" in key and value is not None and value != '':
                            if "recommended" in key:
                                tirepress[key] = round(float(value["value"]) * rval, decimal)
                            else:
                                tirepress[key] = round(float(value["value"]) * sval, decimal)
                    return tirepress
                return None
            if self.sensor == "gps":
                if self.coordinator.data[self.sensor] is None:
                    return None
                return self.coordinator.data[self.sensor].items()
            if self.sensor == "alarm":
                return self.coordinator.data[self.sensor].items()
            if self.sensor == "ignitionStatus":
                return self.coordinator.data[self.sensor].items()
            if self.sensor == "firmwareUpgInProgress":
                return self.coordinator.data[self.sensor].items()
            if self.sensor == "deepSleepInProgress":
                return self.coordinator.data[self.sensor].items()
            if self.sensor == "doorStatus":
                doors = {}
                for key, value in self.coordinator.data[self.sensor].items():
                    doors[key] = value["value"]
                return doors
            if self.sensor == "windowPosition":
                if self.coordinator.data[self.sensor] is None:
                    return None
                windows = {}
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
            if self.sensor == "lastRefresh":
                return None
            if self.sensor == "elVeh":
                if self.coordinator.data["elVehDTE"] is None:
                    return None
                elecs = {}
                if (
                    self.coordinator.data["elVehDTE"] is not None and self.coordinator.data["elVehDTE"]["value"] is not None
                ):
                    elecs["elVehDTE"] = self.coordinator.data["elVehDTE"]["value"]
                if (
                    self.coordinator.data["plugStatus"] is not None and self.coordinator.data["plugStatus"]["value"] is not None
                ):
                    elecs["Plug Status"] = self.coordinator.data["plugStatus"][
                        "value"
                    ]

                if (
                    self.coordinator.data["chargingStatus"] is not None and self.coordinator.data["chargingStatus"]["value"] is not None
                ):
                    elecs["Charging Status"] = self.coordinator.data[
                        "chargingStatus"
                    ]["value"]

                if (
                    self.coordinator.data["chargeStartTime"] is not None and self.coordinator.data["chargeStartTime"]["value"] is not None
                ):
                    elecs["Charge Start Time"] = self.coordinator.data[
                        "chargeStartTime"
                    ]["value"]

                if (
                    self.coordinator.data["chargeEndTime"] is not None and self.coordinator.data["chargeEndTime"]["value"] is not None
                ):
                    elecs["Charge End Time"] = self.coordinator.data[
                        "chargeEndTime"
                    ]["value"]

                if (
                    self.coordinator.data["batteryFillLevel"] is not None and self.coordinator.data["batteryFillLevel"]["value"] is not None
                ):
                    elecs["Battery Fill Level"] = int(self.coordinator.data[
                        "batteryFillLevel"
                    ]["value"])

                if (
                    self.coordinator.data["chargerPowertype"] is not None and self.coordinator.data["chargerPowertype"]["value"] is not None
                ):
                    elecs["Charger Power Type"] = self.coordinator.data[
                        "chargerPowertype"
                    ]["value"]

                if (
                    self.coordinator.data["batteryChargeStatus"] is not None and self.coordinator.data["batteryChargeStatus"]["value"] is not None
                ):
                    elecs["Battery Charge Status"] = self.coordinator.data[
                        "batteryChargeStatus"
                    ]["value"]

                if (
                    self.coordinator.data["batteryPerfStatus"] is not None and self.coordinator.data["batteryPerfStatus"]["value"] is not None
                ):
                    elecs["Battery Performance Status"] = self.coordinator.data[
                        "batteryPerfStatus"
                    ]["value"]

                return elecs
            if self.sensor == "zoneLighting":
                if "zoneLighting" not in self.coordinator.data:
                    return None
                if (
                    self.coordinator.data[self.sensor] is not None and self.coordinator.data[self.sensor]["zoneStatusData"] is not None
                ):
                    zone = {}
                    if self.coordinator.data[self.sensor]["zoneStatusData"] is not None:
                        for key, value in self.coordinator.data[self.sensor][
                            "zoneStatusData"
                        ].items():
                            zone["zone_" + key] = value["value"]

                    if (
                        self.coordinator.data[self.sensor]["lightSwitchStatusData"]
                        is not None
                    ):
                        for key, value in self.coordinator.data[self.sensor][
                            "lightSwitchStatusData"
                        ].items():
                            if value is not None:
                                zone[key] = value["value"]

                    if (
                        self.coordinator.data[self.sensor]["zoneLightingFaultStatus"]
                        is not None
                    ):
                        zone["zoneLightingFaultStatus"] = self.coordinator.data[
                            self.sensor
                        ]["zoneLightingFaultStatus"]["value"]
                    if (
                        self.coordinator.data[self.sensor][
                            "zoneLightingShutDownWarning"
                        ]
                        is not None
                    ):
                        zone["zoneLightingShutDownWarning"] = self.coordinator.data[
                            self.sensor
                        ]["zoneLightingShutDownWarning"]["value"]
                    return zone
                return None
            if self.sensor == "remoteStartStatus":
                if self.coordinator.data["remoteStart"] is None:
                    return None
                return self.coordinator.data["remoteStart"].items()
            if self.sensor == "messages":
                if self.coordinator.data["messages"] is None:
                    return None
                messages = {}
                for value in self.coordinator.data["messages"]:

                    messages[value["messageSubject"]] = value["createdDate"]
                return messages
            if self.sensor == "dieselSystemStatus":
                return self.coordinator.data["dieselSystemStatus"]
            if self.sensor == "exhaustFluidLevel":
                return self.coordinator.data["dieselSystemStatus"]
            return None
        return None

    @property
    def name(self):
        """Return Sensor Name"""
        return "fordpass_" + self.sensor

    @property
    def state(self):
        """Return Sensor State"""
        return self.get_value("state")

    @property
    def device_id(self):
        """Return Sensor Device ID"""
        return self.device_id

    @property
    def extra_state_attributes(self):
        """Return sensor attributes"""
        return self.get_value("attribute")

    @property
    def native_unit_of_measurement(self):
        """Return sensor measurement"""
        return self.get_value("measurement")

    @property
    def icon(self):
        """Return sensor icon"""
        return SENSORS[self.sensor]["icon"]

    @property
    def state_class(self):
        """Return sensor state_class for statistics"""
        if "state_class" in SENSORS[self.sensor]:
            if SENSORS[self.sensor]["state_class"] == "total":
                return SensorStateClass.TOTAL
            if SENSORS[self.sensor]["state_class"] == "measurement":
                return SensorStateClass.MEASUREMENT
            return None
        return None

    @property
    def device_class(self):
        """Return sensor device class for statistics"""
        if "device_class" in SENSORS[self.sensor]:
            if SENSORS[self.sensor]["device_class"] == "distance":
                return SensorDeviceClass.DISTANCE
            if SENSORS[self.sensor]["device_class"] == "timestamp":
                return SensorDeviceClass.TIMESTAMP
        return None
