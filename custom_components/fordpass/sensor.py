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
            if "xevBatteryRange" in sensor.coordinator.data["metrics"]:
                sensors.append(sensor)
        ## SquidBytes: Added elVehCharging
        elif key == "elVehCharging":
            if "xevBatteryChargeDisplayStatus" in sensor.coordinator.data["metrics"]:
                sensors.append(sensor)                        
        elif key == "dieselSystemStatus":
            if "dieselExhaustFilterStatus" in sensor.coordinator.data["metrics"]:
                sensors.append(sensor)
        elif key == "exhaustFluidLevel":
            if "dieselExhaustFluidLevel" in sensor.coordinator.data["metrics"]:
                sensors.append(sensor)
        elif key == "indicators":
            if "indicators" in sensor.coordinator.data["metrics"]:
                sensors.append(sensor)
        elif key == "coolantTemp":
            if "engineCoolantTemp" in sensor.coordinator.data["metrics"]:
                sensors.append(sensor)
        elif key == "outsideTemp":
            if "outsideTemperature" in sensor.coordinator.data["metrics"]:
                sensors.append(sensor)
        elif key == "engineOilTemp":
            if "engineOilTemp" in sensor.coordinator.data["metrics"]:
                sensors.append(sensor)
        elif key == "windowPosition":
            if "windowStatus" in sensor.coordinator.data["metrics"]:
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
        self.data = self.coordinator.data["metrics"]
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
                elif "xevBatteryStateOfCharge" in self.data:
                    return round(self.data["xevBatteryStateOfCharge"]["value"])
                else:
                    return None
            if self.sensor == "battery":
                return round(self.data["batteryStateOfCharge"]["value"])
            if self.sensor == "oil":
                return round(self.data["oilLifeRemaining"]["value"])
            if self.sensor == "tirePressure":
                if "tirePressureSystemStatus" in self.data:
                    return self.data["tirePressureSystemStatus"][0]["value"]
                return "Not Supported"
            if self.sensor == "gps":
                if "position" in self.data :
                    return self.data["position"]["value"]
                return "Unsupported"
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
                if "dieselExhaustFilterStatus" in self.data:
                    return self.data["dieselExhaustFilterStatus"]["value"]
                return "Not Supported"
            if self.sensor == "exhaustFluidLevel":
                if "dieselExhaustFluidLevel" in self.data:
                    return self.data["dieselExhaustFluidLevel"]["value"]
                return "Not Supported"
            if self.sensor == "speed":
                return self.data[self.sensor]["value"]
            if self.sensor == "indicators":
                alerts = 0
                for key, indicator in self.data["indicators"].items():
                    if "value" in indicator:
                        if indicator["value"] == True:
                            alerts +=1
                return alerts
            if self.sensor == "coolantTemp":
                return self.data["engineCoolantTemp"]["value"]
            if self.sensor == "outsideTemp":
                return self.data["outsideTemperature"]["value"]
            if self.sensor == "engineOilTemp":
                return self.data["engineOilTemp"]["value"]
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
            if self.sensor == "coolantTemp":
                return "°C"
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
                        return {"fuelRange": round(
                            float(self.data["fuelRange"]["value"]) / 1.60934
                        )}
                    return {"fuelRange": self.data["fuelRange"]["value"]}
                elif "xevBatteryRange" in self.data:
                    if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                        return {"batteryRange": round(
                            float(self.data["xevBatteryRange"]["value"]) / 1.60934
                        )}
                    return {"batteryRange": self.data["xevBatteryRange"]["value"]}
            if self.sensor == "battery":
                return {
                    "Battery Voltage": self.data["batteryVoltage"]["value"]
                }
            if self.sensor == "oil":
                return self.data["oilLifeRemaining"].items()
            if self.sensor == "tirePressure":
                if "tirePressure" in self.data :
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
                if "position" in self.data:
                    return self.data["position"].items()
                return None
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
                    _LOGGER.debug(value)
                    if "vehicleSide" in value:
                        if value['vehicleDoor'] == "UNSPECIFIED_FRONT":
                            doors[value['vehicleSide']] = value['value']
                        else:
                            doors[value['vehicleDoor']] = value['value']
                    elif value['vehicleDoor'] == "INNER_TAILGATE":
                        if "xevBatteryCapacity" in self.data:
                            value['vehicleDoor'] = "FRUNK" 
                            doors[value['vehicleDoor']] = value['value']
                    else:
                        doors[value["vehicleDoor"]] = value['value']
                if "hoodStatus" in self.data:
                    doors["Hood"] = self.data["hoodStatus"]["value"]
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
                if "xevBatteryRange" not in self.data:
                    return None
                elecs = {}                    
                if (
                    "xevPlugChargerStatus" in self.data and self.data["xevPlugChargerStatus"] is not None and self.data["xevPlugChargerStatus"]["value"] is not None
                ):
                    elecs["Plug Status"] = self.data["xevPlugChargerStatus"][
                        "value"
                    ]

                if (
                    "xevBatteryChargeDisplayStatus" in self.data and self.data["xevBatteryChargeDisplayStatus"] is not None and self.data["xevBatteryChargeDisplayStatus"]["value"] is not None
                ):
                    elecs["Charging Status"] = self.data[
                        "xevBatteryChargeDisplayStatus"
                    ]["value"]

                if (
                    "xevChargeStationPowerType" in self.data and self.data["xevChargeStationPowerType"] is not None and self.data["xevChargeStationPowerType"]["value"] is not None
                ):
                    elecs["Charger Power Type"] = self.data[
                        "xevChargeStationPowerType"
                    ]["value"]

                if (
                    "xevChargeStationCommunicationStatus" in self.data and self.data["xevChargeStationCommunicationStatus"] is not None and self.data["xevChargeStationCommunicationStatus"]["value"] is not None
                ):
                    elecs["Battery Charge Status"] = self.data[
                        "xevChargeStationCommunicationStatus"
                    ]["value"]

                if (
                    "xevBatteryPerformanceStatus" in self.data and self.data["xevBatteryPerformanceStatus"] is not None and self.data["xevBatteryPerformanceStatus"]["value"] is not None
                ):
                    elecs["Battery Performance Status"] = self.data[
                        "xevBatteryPerformanceStatus"
                    ]["value"]

                if (
                    "xevBatteryStateOfCharge" in self.data and self.data["xevBatteryStateOfCharge"] is not None and self.data["xevBatteryStateOfCharge"]["value"] is not None
                ):
                    elecs["Battery Charge"] = self.data[
                        "xevBatteryStateOfCharge"
                    ]["value"]

                if (
                    "xevBatteryCapacity" in self.data and self.data["xevBatteryCapacity"] is not None and self.data["xevBatteryCapacity"]["value"] is not None
                ):
                    elecs["Maximum Battery Capacity"] = self.data["xevBatteryCapacity"]["value"]

                if (
                    "xevBatteryMaximumRange" in self.data and self.data["xevBatteryMaximumRange"] is not None and self.data["xevBatteryMaximumRange"]["value"] is not None
                ):
                    if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                        elecs["Maximum Battery Range"] = round(
                                float(self.data["xevBatteryMaximumRange"]["value"]) / 1.60934
                            )
                    else:
                        elecs["Maximum Battery Range"] = self.data["xevBatteryMaximumRange"]["value"]
                return elecs
                    
            ## SquidBytes: Added elVehCharging
            if self.sensor == "elVehCharging":
                if "xevPlugChargerStatus" not in self.data:
                    return None

                cs = {}

                if (
                    "xevBatteryStateOfCharge" in self.data and self.data["xevBatteryStateOfCharge"] is not None and self.data["xevBatteryStateOfCharge"]["value"] is not None
                ):
                    cs["Charging State of Charge"] = self.data["xevBatteryStateOfCharge"]["value"]
                if ("xevBatteryChargeDisplayStatus" in self.data and self.data["xevBatteryChargeDisplayStatus"] is not None and self.data["xevBatteryChargeDisplayStatus"]["value"] is not None
                ):
                    cs["Charging Status"] = self.data["xevBatteryChargeDisplayStatus"]["value"]
                if (
                    "xevChargeStationPowerType" in self.data and self.data["xevChargeStationPowerType"] is not None and self.data["xevChargeStationPowerType"]["value"] is not None
                ):
                    cs["Charging Type"] = self.data["xevChargeStationPowerType"]["value"]
                if (
                    "xevChargeStationCommunicationStatus" in self.data and self.data["xevChargeStationCommunicationStatus"] is not None and self.data["xevChargeStationCommunicationStatus"]["value"] is not None
                ):
                    cs["Charge Station Status"] = self.data["xevChargeStationCommunicationStatus"]["value"]
                if (
                    "xevBatteryTemperature" in self.data and self.data["xevBatteryTemperature"] is not None and self.data["xevBatteryTemperature"]["value"] is not None
                ):
                    cs["Battery Temperature"] = self.data["xevBatteryTemperature"]["value"]
                if (
                    "xevBatteryChargerVoltageOutput" in self.data and self.data["xevBatteryChargerVoltageOutput"] is not None and self.data["xevBatteryChargerVoltageOutput"]["value"] is not None
                ):
                    cs["Charging Voltage"] = float(self.data["xevBatteryChargerVoltageOutput"]["value"])
                    chVolt = cs["Charging Voltage"]
                if (
                    "xevBatteryChargerCurrentOutput" in self.data and self.data["xevBatteryChargerCurrentOutput"] is not None and self.data["xevBatteryChargerCurrentOutput"]["value"] is not None
                ):
                    cs["Charging Amperage"] = float(self.data["xevBatteryChargerCurrentOutput"]["value"])
                    chAmps = cs["Charging Amperage"]
                if (
                    "xevBatteryChargerCurrentOutput" in self.data and self.data["xevBatteryChargerCurrentOutput"]["value"] is not None and self.data["xevBatteryChargerVoltageOutput"]["value"] is not None
                ):
                    cs["Charging kW"] =  round((chVolt * chAmps) / 1000, 2)
            
                if (
                    "xevBatteryTimeToFullCharge" in self.data and self.data["xevBatteryTimeToFullCharge"] is not None and self.data["xevBatteryTimeToFullCharge"]["value"] is not None
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
                    if "indicators" in self.data and "dieselExhaustOverTemp" in self.data["indicators"]:
                        return {
                            "Diesel Exhaust Over Temp": self.data["indicators"]["dieselExhaustOverTemp"]["value"]
                        }
                    return None
            if self.sensor == "exhaustFluidLevel":
                exhaustdata = {}
                if "dieselExhaustFluidLevelRangeRemaining" in self.data:
                    exhaustdata["Exhaust Fluid Range"] = self.data["dieselExhaustFluidLevelRangeRemaining"]["value"]
                if "indicators" in self.data and "dieselExhaustFluidLow" in self.data["indicators"]:
                    exhaustdata["Exhaust Fluid Low"] = self.data["indicators"]["dieselExhaustFluidLow"]["value"]
                if "indicators" in self.data and "dieselExhaustFluidSystemFault" in self.data["indicators"]:
                    exhaustdata["Exhaust Fluid System Fault"] = self.data["indicators"]["dieselExhaustFluidSystemFault"]["value"]
                return exhaustdata
            if self.sensor == "speed":
                attribs = {}
                if "acceleratorPedalPosition" in self.data:
                    attribs["acceleratorPedalPosition"] = self.data["acceleratorPedalPosition"]["value"]
                if "brakePedalStatus" in self.data:
                    attribs["brakePedalStatus"] = self.data["brakePedalStatus"]["value"]
                if "brakeTorque" in self.data:
                    attribs["brakeTorque"] = self.data["brakeTorque"]["value"]
                if "engineSpeed" in self.data:
                    attribs["engineSpeed"] = self.data["engineSpeed"]["value"]
                if "gearLeverPosition" in self.data:
                    attribs["gearLeverPosition"] = self.data["gearLeverPosition"]["value"]
                if "parkingBrakeStatus" in self.data:
                    attribs["parkingBrakeStatus"] = self.data["parkingBrakeStatus"]["value"]
                if "torqueAtTransmission" in self.data:
                    attribs["torqueAtTransmission"] = self.data["torqueAtTransmission"]["value"]
                return attribs
            if self.sensor == "indicators":
                alerts = {}
                for key, value in self.data["indicators"].items():
                    if "value" in value:
                        alerts[key] = value["value"]
                return alerts
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
            if SENSORS[self.sensor]["device_class"] == "temperature":
                return SensorDeviceClass.TEMPERATURE
        return None
