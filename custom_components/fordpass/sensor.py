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
            if "xevBatteryCapacity" in sensor.coordinator.data["metrics"]:
                sensors.append(sensor)
        ## SquidBytes: Added elVehCharging
        elif key == "elVehCharging":
            if "xevBatteryChargeEvent" in sensor.coordinator.data["events"]:
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
        self.data = coordinator.data["metrics"]
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
                            return self.data[self.sensor]["value"]
                        return round(
                            float(self.data[self.sensor]["value"]) / 1.60934
                        )
                    return self.data[self.sensor]["value"]
                return self.data["odometer"]["value"]
            if self.sensor == "fuel":
                if "fuelLevel" in self.data:
                    if self.data["fuelLevel"] is None:
                        return None
                    return round(self.data["fuelLevel"]["value"])
                elif "xevBatteryStateOfCharge":
                    return round(self.data["xevBatteryStateOfCharge"]["value"])
                else:
                    return None
            if self.sensor == "battery":
                return round(self.data["batteryStateOfCharge"]["value"])
            if self.sensor == "oil":
                return round(self.data["oilLifeRemaining"]["value"])
            if self.sensor == "tirePressure":
                return self.data["tirePressureSystemStatus"][0]["value"]
            if self.sensor == "gps":
                if self.data["position"] is None:
                    return "Unsupported"
                return self.data["position"]["value"]
            if self.sensor == "alarm":
                return self.data["alarmStatus"]["value"]
            if self.sensor == "ignitionStatus":
                return self.data[self.sensor]["value"]
            if self.sensor == "firmwareUpgInProgress":
                return self.data[self.sensor]["value"]
            if self.sensor == "deepSleepInProgress":
                return self.data[self.sensor]["value"]
            if self.sensor == "doorStatus":
                for value in self.data["doorStatus"]:
                    if value["value"] == "Invalid":
                        continue
                    if value["value"] != "CLOSED":
                        return "Open"
                return "Closed"
            if self.sensor == "windowPosition":
                if "windowStatus" in self.data:
                    if self.data["windowStatus"] is None:
                        return "Unsupported"
                    status = "Closed"
                    for window in self.data["windowStatus"]:
                        windowrange = window["value"]["doubleRange"]
                        if windowrange["lowerBound"] != 0.0 and windowrange["upperBound"] != 0.0:
                            status = "Open"
                    return status
                return "Unsupported"
            if self.sensor == "lastRefresh":
                try:
                    return dt.as_local(
                        datetime.strptime(
                            self.coordinator.data["updateTime"], "%Y-%m-%dT%H:%M:%S.%fz"
                        )
                    )
                except:
                    _LOGGER.debug("%f conversion failed")
                try:
                    return dt.as_local(
                        datetime.strptime(
                            self.coordinator.data["updateTime"], "%Y-%m-%dT%H:%M:%Sz"
                        )
                    )
                except:
                    _LOGGER.debug("%s conversion failed")
                    refresh = ""
                
                return refresh
            if self.sensor == "elVeh":
                if "xevBatteryRange" in self.data:
                    if self.fordoptions[CONF_DISTANCE_UNIT] is not None:
                        if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                            return round(
                                float(self.data["xevBatteryRange"]["value"]) / 1.60934
                            )
                        return float(self.data["xevBatteryRange"]["value"])
                    return float(self.data["xevBatteryRange"]["value"])
                return "Unsupported"
            ## SquidBytes: Added elVehCharging
            if self.sensor == "elVehCharging":
                if "xevBatteryChargeDisplayStatus" in self.data:
                    ## Default sensor type is the status of charge (might be better to have the kW as the value, but for now I'll do this)
                    return self.data["xevBatteryChargeDisplayStatus"]["value"]
                return "Unsupported"                
            if self.sensor == "zoneLighting":
                if "zoneLighting" not in self.data:
                    return "Unsupported"
                if (
                    self.data["zoneLighting"] is not None and self.data["zoneLighting"]["activationData"] is not None
                ):
                    return self.data["zoneLighting"]["activationData"][
                        "value"
                    ]
                return "Unsupported"
            if self.sensor == "remoteStartStatus":
                if self.data["remoteStartCountdownTimer"] is None:
                    return None
                if self.data["remoteStartCountdownTimer"]["value"] > 0:
                    return "Active"
                return "Inactive"
            if self.sensor == "messages":
                if self.coordinator.data["messages"] is None:
                    return None
                return len(self.coordinator.data["messages"])
            if self.sensor == "dieselSystemStatus":
                if self.data["dieselSystemStatus"]["filterRegenerationStatus"] is not None:
                    return self.data["dieselSystemStatus"]["filterRegenerationStatus"]
                return "Not Supported"
            if self.sensor == "exhaustFluidLevel":
                if "value" in self.data["dieselSystemStatus"]["exhaustFluidLevel"]:
                    return self.data["dieselSystemStatus"]["exhaustFluidLevel"]["value"]
                return "Not Supported"
            if self.sensor == "speed":
                return self.data[self.sensor]["value"]
            return None
        if ftype == "measurement":
            if self.sensor == "odometer":
                if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                    return "mi"
                return "km"
            if self.sensor == "fuel":
                return "%"
            if self.sensor == "battery":
                return "%"
            if self.sensor == "oil":
                return "%"
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
            if self.sensor == "speed":
                if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                    return "mph"
                return "km/h"
            if self.sensor == "exhaustFluidLevel":
                return "%"
            return None
        if ftype == "attribute":
            if self.sensor == "odometer":
                return self.data[self.sensor].items()
            if self.sensor == "fuel":
                if "fuelRange" in self.data:
                    if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                        self.data["fuelRange"]["value"] = round(
                            float(self.data["fuelRange"]["value"]) / 1.60934
                        )
                    return {"fuelRange": self.data["fuelRange"]["value"]}
                elif "xevBatteryRange" in self.data:
                    if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                        self.data["xevBatteryRange"]["value"] = round(
                            float(self.data["xevBatteryRange"]["value"]) / 1.60934
                        )
                    return {"batteryRange": self.data["xevBatteryRange"]["value"]}
            if self.sensor == "battery":
                return {
                    "Battery Voltage": self.data["batteryVoltage"]["value"]
                }
            if self.sensor == "oil":
                return self.data["oilLifeRemaining"].items()
            if self.sensor == "tirePressure":
                if self.data["tirePressure"] is not None:
                    _LOGGER.debug(self.fordoptions[CONF_PRESSURE_UNIT])
                    if self.fordoptions[CONF_PRESSURE_UNIT] == "PSI":
                        _LOGGER.debug("PSIIIII")
                        sval = 0.1450377377
                        rval = 1
                        decimal = 0
                    elif self.fordoptions[CONF_PRESSURE_UNIT] == "BAR":
                        sval = 0.01
                        rval = 0.0689475729
                        decimal = 2
                    elif self.fordoptions[CONF_PRESSURE_UNIT] == "kPa":
                        sval = 1
                        rval = 6.8947572932
                        decimal = 0
                    else:
                        _LOGGER.debug("HITT")
                        sval = 1
                        rval = 1
                        decimal = 0
                    tirepress = {}
                    for value in self.data["tirePressure"]:
                            # if "recommended" in key:
                            # tirepress[key] = round(float(value["value"]) * rval, decimal)
                            # else:
                        tirepress[value["vehicleWheel"]] = round(float(value["value"]) * sval, decimal)
                    return tirepress
                return None
            if self.sensor == "gps":
                if self.data["position"] is None:
                    return None
                return self.data["position"].items()
            if self.sensor == "alarm":
                return self.data["alarmStatus"].items()
            if self.sensor == "ignitionStatus":
                return self.data[self.sensor].items()
            if self.sensor == "firmwareUpgInProgress":
                return self.data[self.sensor].items()
            if self.sensor == "deepSleepInProgress":
                return self.data[self.sensor].items()
            if self.sensor == "doorStatus":
                doors = {}
                for value in self.data[self.sensor]:
                    doors[value["vehicleDoor"]] = value["value"]
                return doors
            if self.sensor == "windowPosition":
                if "windowStatus" not in self.data:
                    return None
                windows = {}
                for window in self.data["windowStatus"]:
                    windows[window["vehicleWindow"]] = window
                return windows
            if self.sensor == "lastRefresh":
                return None
            if self.sensor == "elVeh":
                if "xevBatteryCapacity" not in self.data:
                    return None
                elecs = {}
                if (
                    self.data["xevBatteryCapacity"] is not None and self.data["xevBatteryCapacity"]["value"] is not None
                ):
                    elecs["xevBatteryCapacity"] = self.data["xevBatteryCapacity"]["value"]
                if (
                    self.data["xevPlugChargerStatus"] is not None and self.data["xevPlugChargerStatus"]["value"] is not None
                ):
                    elecs["Plug Status"] = self.data["xevPlugChargerStatus"][
                        "value"
                    ]

                if (
                    self.data["xevBatteryChargeDisplayStatus"] is not None and self.data["xevBatteryChargeDisplayStatus"]["value"] is not None
                ):
                    elecs["Charging Status"] = self.data[
                        "xevBatteryChargeDisplayStatus"
                    ]["value"]

                if (
                    self.data["xevChargeStationPowerType"] is not None and self.data["xevChargeStationPowerType"]["value"] is not None
                ):
                    elecs["Charger Power Type"] = self.data[
                        "xevChargeStationPowerType"
                    ]["value"]

                if (
                    self.data["xevChargeStationCommunicationStatus"] is not None and self.data["xevChargeStationCommunicationStatus"]["value"] is not None
                ):
                    elecs["Battery Charge Status"] = self.data[
                        "xevChargeStationCommunicationStatus"
                    ]["value"]

                if (
                    self.data["xevBatteryPerformanceStatus"] is not None and self.data["xevBatteryPerformanceStatus"]["value"] is not None
                ):
                    elecs["Battery Performance Status"] = self.data[
                        "xevBatteryPerformanceStatus"
                    ]["value"]

                if (
                    self.data["xevBatteryStateOfCharge"] is not None and self.data["xevBatteryStateOfCharge"]["value"] is not None
                ):
                    elecs["Battery Charge"] = self.data[
                        "xevBatteryStateOfCharge"
                    ]["value"]
                return elecs
            ## SquidBytes: Added elVehCharging
            if self.sensor == "elVehCharging":
                if "xevPlugChargerStatus" not in self.data:
                    return None

                cs = {}

                if (
                    self.data["xevBatteryStateOfCharge"] is not None and self.data["xevBatteryStateOfCharge"]["value"] is not None
                ):
                    cs["Charging State of Charge"] = self.data["xevBatteryStateOfCharge"]["value"]
                if (self.data["xevBatteryChargeDisplayStatus"] is not None and self.data["xevBatteryChargeDisplayStatus"]["value"] is not None
                ):
                    cs["Charging Status"] = self.data["xevBatteryChargeDisplayStatus"]["value"]
                if (
                    self.data["xevChargeStationPowerType"] is not None and self.data["xevChargeStationPowerType"]["value"] is not None
                ):
                    cs["Charging Type"] = self.data["xevChargeStationPowerType"]["value"]
                if (
                    self.data["xevChargeStationCommunicationStatus"] is not None and self.data["xevChargeStationCommunicationStatus"]["value"] is not None
                ):
                    cs["Charge Station Status"] = self.data["xevChargeStationCommunicationStatus"]["value"]
                if (
                    self.data["xevBatteryTemperature"] is not None and self.data["xevBatteryTemperature"]["value"] is not None
                ):
                    cs["Battery Temperature"] = self.data["xevBatteryTemperature"]["value"]
                if (
                    self.data["xevBatteryChargerVoltageOutput"] is not None and self.data["xevBatteryChargerVoltageOutput"]["value"] is not None
                ):
                    cs["Charging Voltage"] = float(self.data["xevBatteryChargerVoltageOutput"]["value"])
                    chVolt = cs["Charging Voltage"]
                if (
                    self.data["xevBatteryChargerCurrentOutput"] is not None and self.data["xevBatteryChargerCurrentOutput"]["value"] is not None
                ):
                    cs["Charging Amperage"] = float(self.data["xevBatteryChargerCurrentOutput"]["value"])
                    chAmps = cs["Charging Amperage"]
                if (
                    self.data["xevBatteryChargerCurrentOutput"]["value"] is not None and self.data["xevBatteryChargerVoltageOutput"]["value"] is not None
                ):
                    cs["Charging kW"] =  round((chVolt * chAmps) / 1000, 2)
            
                if (
                    self.data["xevBatteryTimeToFullCharge"] is not None and self.data["xevBatteryTimeToFullCharge"]["value"] is not None
                ):
                    cs["Time To Full Charge"] = self.data["xevBatteryTimeToFullCharge"]["value"]

                return cs
            if self.sensor == "zoneLighting":
                if "zoneLighting" not in self.data:
                    return None
                if (
                    self.data[self.sensor] is not None and self.data[self.sensor]["zoneStatusData"] is not None
                ):
                    zone = {}
                    if self.data[self.sensor]["zoneStatusData"] is not None:
                        for key, value in self.data[self.sensor][
                            "zoneStatusData"
                        ].items():
                            zone["zone_" + key] = value["value"]

                    if (
                        self.data[self.sensor]["lightSwitchStatusData"]
                        is not None
                    ):
                        for key, value in self.data[self.sensor][
                            "lightSwitchStatusData"
                        ].items():
                            if value is not None:
                                zone[key] = value["value"]

                    if (
                        self.data[self.sensor]["zoneLightingFaultStatus"]
                        is not None
                    ):
                        zone["zoneLightingFaultStatus"] = self.data[
                            self.sensor
                        ]["zoneLightingFaultStatus"]["value"]
                    if (
                        self.data[self.sensor][
                            "zoneLightingShutDownWarning"
                        ]
                        is not None
                    ):
                        zone["zoneLightingShutDownWarning"] = self.data[
                            self.sensor
                        ]["zoneLightingShutDownWarning"]["value"]
                    return zone
                return None
            if self.sensor == "remoteStartStatus":
                if self.data["remoteStartCountdownTimer"] is None:
                    return None
                return { "Countdown": self.data["remoteStartCountdownTimer"]["value"] }
            if self.sensor == "messages":
                if self.coordinator.data["messages"] is None:
                    return None
                messages = {}
                for value in self.coordinator.data["messages"]:

                    messages[value["messageSubject"]] = value["createdDate"]
                return messages
            if self.sensor == "dieselSystemStatus":
                return self.data["dieselSystemStatus"]
            if self.sensor == "exhaustFluidLevel":
                return self.data["dieselSystemStatus"]
            if self.sensor == "speed":
                return None
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
