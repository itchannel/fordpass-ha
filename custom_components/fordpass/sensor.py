"""All vehicle sensors from the accessible by the API"""

import logging
from datetime import datetime, timedelta
import json

from homeassistant.const import (
    UnitOfTemperature,
    UnitOfLength
)
from homeassistant.util import dt

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass
)


from . import FordPassEntity
from .const import CONF_DISTANCE_UNIT, CONF_PRESSURE_UNIT, DOMAIN, SENSORS, COORDINATOR


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    sensors = []
    for key, value in SENSORS.items():
        sensor = CarSensor(entry, key, config_entry.options)
        api_key = value["api_key"]
        string =  isinstance(api_key, str)
        if string and api_key == "messages" or api_key == "lastRefresh":
            sensors.append(sensor)
        elif string:
            if api_key and api_key in sensor.coordinator.data.get("metrics", {}):
                sensors.append(sensor)
        else:
            for key in api_key:
                if key and key in sensor.coordinator.data.get("metrics", {}):
                    sensors.append(sensor)
                    continue
    _LOGGER.debug(hass.config.units)
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
        self.units = coordinator.hass.config.units
        self.data = coordinator.data["metrics"]
        self.events = coordinator.data["events"]
        self._device_id = "fordpass_" + sensor
        # Required for HA 2022.7
        self.coordinator_context = object()

    def get_value(self, ftype):
        """Get sensor value and attributes from coordinator data"""
        self.data = self.coordinator.data["metrics"]
        self.events = self.coordinator.data["events"]
        self.units = self.coordinator.hass.config.units
        if ftype == "state":
            if self.sensor == "odometer":
                return self.data.get("odometer", {}).get("value")
                    #return self.data.get("odometer", {}).get("value", {})
            if self.sensor == "fuel":
                fuel_level = self.data.get("fuelLevel", {}).get("value", 0)
                if fuel_level is not None:
                    return round(fuel_level)
                battery_soc = self.data.get("xevBatteryStateOfCharge", {}).get("value", 0)
                if battery_soc is not None:
                    return round(battery_soc)
                return None
            if self.sensor == "battery":
                return round(self.data.get("batteryStateOfCharge", {}).get("value", 0))
            if self.sensor == "oil":
                return round(self.data.get("oilLifeRemaining", {}).get("value", 0))
            if self.sensor == "tirePressure":
                return self.data.get("tirePressureSystemStatus", [{}])[0].get("value", "Unsupported")
            if self.sensor == "gps":
                return self.data.get("position", {}).get("value", "Unsupported")
            if self.sensor == "alarm":
                return self.data.get("alarmStatus", {}).get("value", "Unsupported")
            if self.sensor == "ignitionStatus":
                return self.data.get("ignitionStatus", {}).get("value", "Unsupported")
            if self.sensor == "firmwareUpgInProgress":
                return self.data.get("firmwareUpgradeInProgress", {}).get("value", "Unsupported")
            if self.sensor == "deepSleepInProgress":
                return self.data.get("deepSleepInProgress", {}).get("value", "Unsupported")
            if self.sensor == "doorStatus":
                for value in self.data.get("doorStatus", []):
                    if value["value"] in ["CLOSED", "Invalid", "UNKNOWN"]:
                        continue
                    return "Open"
                if  self.data.get("hoodStatus", {}).get("value") == "OPEN":
                    return "Open"
                return "Closed"
            if self.sensor == "windowPosition":
                for window in self.data.get("windowStatus", []):
                    windowrange = window.get("value", {}).get("doubleRange", {})
                    if windowrange.get("lowerBound", 0.0) != 0.0 or windowrange.get("upperBound", 0.0) != 0.0:
                        return "Open"
                return "Closed"
            if self.sensor == "lastRefresh":
                return dt.as_local(dt.parse_datetime(self.coordinator.data.get("updateTime", 0)))
            if self.sensor == "elVeh" and "xevBatteryRange" in self.data:
                return round(self.data.get("xevBatteryRange", {}).get("value"), 2)
            # SquidBytes: Added elVehCharging
            if self.sensor == "elVehCharging":
                return self.data.get("xevPlugChargerStatus", {}).get("value", "Unsupported")
            if self.sensor == "zoneLighting":
                return self.data("zoneLighting", {}).get("zoneStatusData", {}).get("value", "Unsupported")
            if self.sensor == "remoteStartStatus":
                countdown_timer = self.data.get("remoteStartCountdownTimer", {}).get("value", 0)
                return "Active" if countdown_timer > 0 else "Inactive"
            if self.sensor == "messages":
                messages = self.coordinator.data.get("messages")
                return len(messages) if messages is not None else None
            if self.sensor == "dieselSystemStatus":
                return self.data.get("dieselExhaustFilterStatus", {}).get("value", "Unsupported")
            if self.sensor == "exhaustFluidLevel":
                return self.data.get("dieselExhaustFluidLevel", {}).get("value", "Unsupported")
            if self.sensor == "speed":
                return self.data.get("speed", {}).get("value", "Unsupported")
            if self.sensor == "indicators":
                return sum(1 for indicator in self.data.get("indicators", {}).values() if indicator.get("value"))
            if self.sensor == "coolantTemp":
                return self.data.get("engineCoolantTemp", {}).get("value", "Unsupported")
            if self.sensor == "outsideTemp":
                return self.data.get("outsideTemperature", {}).get("value", "Unsupported")
            if self.sensor == "engineOilTemp":
                return self.data.get("engineOilTemp", {}).get("value", "Unsupported")
            return None
        if ftype == "measurement":
            return SENSORS.get(self.sensor, {}).get("measurement", None)
        if ftype == "attribute":
            if self.sensor == "odometer":
                return self.data.get("odometer", {})
            if self.sensor == "outsideTemp":
                ambient_temp = self.data.get("ambientTemp", {}).get("value")
                if ambient_temp is not None:
                    return { "Ambient Temp": ambient_temp}
                return None
            if self.sensor == "fuel":
                if "fuelRange" in self.data:
                    return {"fuelRange" : self.units.length(self.data.get("fuelRange", {}).get("value", 0),UnitOfLength.KILOMETERS)}
                if "xevBatteryRange" in self.data:
                    return {"batteryRange": self.units.length(self.data.get("xevBatteryRange", {}).get("value", 0),UnitOfLength.KILOMETERS)}
            if self.sensor == "battery":
                return {
                    "Battery Voltage": self.data.get("batteryVoltage", {}).get("value", 0)
                }
            if self.sensor == "oil":
                return self.data.get("oilLifeRemaining", {})
            if self.sensor == "tirePressure" and "tirePressure" in self.data:
                pressure_unit = self.fordoptions.get(CONF_PRESSURE_UNIT)
                if pressure_unit == "PSI":
                    conversion_factor = 0.1450377377
                    decimal_places = 0
                elif pressure_unit == "BAR":
                    conversion_factor = 0.01
                    decimal_places = 2
                elif pressure_unit == "kPa":
                    conversion_factor = 1
                    decimal_places = 0
                else:
                    conversion_factor = 1
                    decimal_places = 0
                tire_pressures = {}
                for value in self.data["tirePressure"]:
                    tire_pressures[value["vehicleWheel"]] = round(float(value["value"]) * conversion_factor, decimal_places)
                return tire_pressures
            if self.sensor == "gps":
                return self.data.get("position", {})
            if self.sensor == "alarm":
                return self.data.get("alarmStatus", {})
            if self.sensor == "ignitionStatus":
                return self.data.get("ignitionStatus", {})
            if self.sensor == "firmwareUpgInProgress":
                return self.data.get("firmwareUpgradeInProgress", {})
            if self.sensor == "deepSleepInProgress":
                return self.data.get("deepSleepInProgress", {})
            if self.sensor == "doorStatus":
                doors = {}
                for value in self.data.get(self.sensor, []):
                    if "vehicleSide" in value:
                        if value['vehicleDoor'] == "UNSPECIFIED_FRONT":
                            doors[value['vehicleSide']] = value['value']
                        else:
                            doors[value['vehicleDoor']] = value['value']
                    else:
                        doors[value["vehicleDoor"]] = value['value']
                if "hoodStatus" in self.data:
                    doors["HOOD"] = self.data["hoodStatus"]["value"]
                return doors or None
            if self.sensor == "windowPosition":
                windows = {}
                for window in self.data.get("windowStatus", []):
                    if window["vehicleWindow"] == "UNSPECIFIED_FRONT":
                        windows[window["vehicleSide"]] = window
                    else:
                        windows[window["vehicleWindow"]] = window
                return windows
            if self.sensor == "lastRefresh":
                return None
            if self.sensor == "elVeh":
                if "xevBatteryRange" not in self.data:
                    return None
                elecs = {}
                if "xevBatteryPerformanceStatus" in self.data:
                    elecs["Battery Performance Status"] = self.data.get("xevBatteryPerformanceStatus", {}).get("value", "Unsupported")

                if "xevBatteryStateOfCharge" in self.data:
                    elecs["Battery Charge"] = self.data.get("xevBatteryStateOfCharge", {}).get("value", 0)

                if "xevBatteryActualStateOfCharge" in self.data:
                    elecs["Battery Actual Charge"] = self.data.get("xevBatteryActualStateOfCharge", {}).get("value", 0)

                if "xevBatteryCapacity" in self.data:
                    elecs["Maximum Battery Capacity"] = self.data.get("xevBatteryCapacity", {}).get("value", 0)

                if "xevBatteryMaximumRange" in self.data:
                    elecs["Maximum Battery Range"] = self.units.length(self.data.get("xevBatteryMaximumRange", {}).get("value", 0),UnitOfLength.KILOMETERS)

                if "xevBatteryVoltage" in self.data:
                    elecs["Battery Voltage"] = float(self.data.get("xevBatteryVoltage", {}).get("value", 0))
                    batt_volt = elecs["Battery Voltage"]

                if "xevBatteryIoCurrent" in self.data:
                    elecs["Battery Amperage"] = float(self.data.get("xevBatteryIoCurrent", {}).get("value", 0))
                    batt_amps = elecs["Battery Amperage"]

                if batt_volt != 0 and batt_amps != 0:
                    elecs["Battery kW"] = round((batt_volt * batt_amps) / 1000, 2)

                if "xevTractionMotorVoltage" in self.data:
                    elecs["Motor Voltage"] = float(self.data.get("xevTractionMotorVoltage", {}).get("value", 0))
                    motor_volt = elecs["Motor Voltage"]

                if "xevTractionMotorCurrent" in self.data:
                    elecs["Motor Amperage"] = float(self.data.get("xevTractionMotorCurrent", {}).get("value", 0))
                    motor_amps = elecs["Motor Amperage"]

                # This will make Motor kW not display if vehicle is not in use. Not sure if that is bad practice
                if motor_volt != 0 and motor_amps != 0:
                    elecs["Motor kW"] = round((motor_volt * motor_amps) / 1000, 2)

                # tripXevBatteryChargeRegenerated should be a previous FordPass feature called "Driving Score". A % based on how much regen vs brake you use
                if "tripXevBatteryChargeRegenerated" in self.data:
                    elecs["Trip Driving Score"] = self.data.get("tripXevBatteryChargeRegenerated", {}).get("value", 0)

                if "tripXevBatteryRangeRegenerated" in self.data:
                    elecs["Trip Range Regenerated"] = self.units.length(self.data.get("tripXevBatteryRangeRegenerated", {}).get("value", 0),UnitOfLength.KILOMETERS)

                if "customEvents" in self.events:
                    tripDataStr = self.events.get("customEvents", {}).get("xev-key-off-trip-segment-data", {}).get("oemData", {}).get("trip_data", {}).get("stringArrayValue", [])
                    for dataStr in tripDataStr:
                        tripData = json.loads(dataStr)
                        if "ambient_temperature" in tripData:
                            elecs["Trip Ambient Temp"] = self.units.temperature(tripData["ambient_temperature"], UnitOfTemperature.CELSIUS)
                        if "outside_air_ambient_temperature" in tripData:
                            elecs["Trip Outside Air Ambient Temp"] = self.units.temperature(tripData["outside_air_ambient_temperature"], UnitOfTemperature.CELSIUS)
                        if "trip_duration" in tripData:
                            elecs["Trip Duration"] = tripData["trip_duration"] / 3600
                        if "cabin_temperature" in tripData:
                            elecs["Trip Cabin Temp"] = self.units.temperature(tripData["cabin_temperature"], UnitOfTemperature.CELSIUS)
                        if "energy_consumed" in tripData:
                            elecs["Trip Energy Consumed"] = round(tripData["energy_consumed"] / 1000, 2)
                        if "distance_traveled" in tripData:
                            elecs["Trip Distance Traveled"] = self.units.length(tripData["distance_traveled"], UnitOfLength.KILOMETERS)
                        if (
                            "energy_consumed" in tripData
                            and tripData["energy_consumed"] is not None
                            and "distance_traveled" in tripData
                            and tripData["distance_traveled"] is not None
                        ):
                            elecs["Trip Efficiency"] = elecs["Trip Distance Traveled"] / elecs["Trip Energy Consumed"]
                return elecs
            # SquidBytes: Added elVehCharging
            if self.sensor == "elVehCharging":
                if "xevPlugChargerStatus" not in self.data:
                    return None
                cs = {}

                if "xevPlugChargerStatus" in self.data:
                    cs["Plug Status"] = self.data.get("xevPlugChargerStatus", {}).get("value", "Unsupported")

                if "xevChargeStationCommunicationStatus" in self.data:
                    cs["Charging Station Status"] = self.data.get("xevChargeStationCommunicationStatus", {}).get("value", "Unsupported")

                if "xevBatteryChargeDisplayStatus" in self.data:
                    cs["Charging Status"] = self.data.get("xevBatteryChargeDisplayStatus", {}).get("value", "Unsupported")

                if "xevChargeStationPowerType" in self.data:
                    cs["Charging Type"] = self.data.get("xevChargeStationPowerType", {}).get("value", "Unsupported")

                # if "tripXevBatteryDistanceAccumulated" in self.data:
                #   cs["Distance Accumulated"] = self.units.length(self.data.get("tripXevBatteryDistanceAccumulated", {}).get("value", 0),UnitOfLength.KILOMETERS)

                if "xevBatteryChargerVoltageOutput" in self.data:
                    cs["Charging Voltage"] = float(self.data.get("xevBatteryChargerVoltageOutput", {}).get("value", 0))
                    ch_volt = cs["Charging Voltage"]

                if "xevBatteryChargerCurrentOutput" in self.data:
                    cs["Charging Amperage"] = float(self.data.get("xevBatteryChargerCurrentOutput", {}).get("value", 0))
                    ch_amps = cs["Charging Amperage"]

                # This will make Charging kW not display if vehicle is not charging. Not sure if that is bad practice by having it pop in and out
                if ch_volt != 0 and ch_amps != 0:
                    cs["Charging kW"] = round((ch_volt * ch_amps) / 1000, 2)

                if "xevBatteryTemperature" in self.data:
                    cs["Battery Temperature"] = self.units.temperature(self.data.get("xevBatteryTemperature", {}).get("value", 0), UnitOfTemperature.CELSIUS)

                if "xevBatteryStateOfCharge" in self.data:
                    cs["State of Charge"] = self.data.get("xevBatteryStateOfCharge", {}).get("value", 0)

                if "xevBatteryTimeToFullCharge" in self.data:
                    cs_update_time = dt.parse_datetime(self.data.get("xevBatteryTimeToFullCharge", {}).get("updateTime", 0))
                    cs_est_end_time = cs_update_time + timedelta(minutes=self.data.get("xevBatteryTimeToFullCharge", {}).get("value", 0))
                    cs["Estimated End Time"] = dt.as_local(cs_est_end_time)

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
                return {"Countdown:": self.data.get("remoteStartCountdownTimer", {}).get("value", 0)}
            if self.sensor == "messages":
                messages = {}
                for value in  self.coordinator.data.get("messages", []):
                    messages[value["messageSubject"]] = value["createdDate"]
                return messages
            if self.sensor == "dieselSystemStatus":
                if self.data.get("indicators", {}).get("dieselExhaustOverTemp", {}).get("value") is not None:
                    return {
                        "Diesel Exhaust Over Temp": self.data["indicators"]["dieselExhaustOverTemp"]["value"]
                    }
                return None
            if self.sensor == "exhaustFluidLevel":
                exhaustdata = {}
                if self.data.get("dieselExhaustFluidLevelRangeRemaining", {}).get("value") is not None:
                    exhaustdata["Exhaust Fluid Range"] = self.data["dieselExhaustFluidLevelRangeRemaining"]["value"]
                if self.data.get("indicators", {}).get("dieselExhaustFluidLow", {}).get("value") is not None:
                    exhaustdata["Exhaust Fluid Low"] = self.data["indicators"]["dieselExhaustFluidLow"]["value"]
                if self.data.get("indicators", {}).get("dieselExhaustFluidSystemFault", {}).get("value") is not None:
                    exhaustdata["Exhaust Fluid System Fault"] = self.data["indicators"]["dieselExhaustFluidSystemFault"]["value"]
                return exhaustdata or None
            if self.sensor == "speed":
                attribs = {}
                if "acceleratorPedalPosition" in self.data:
                    attribs["acceleratorPedalPosition"] = self.data["acceleratorPedalPosition"]["value"]
                if "brakePedalStatus" in self.data:
                    attribs["brakePedalStatus"] = self.data["brakePedalStatus"]["value"]
                if "brakeTorque" in self.data:
                    attribs["brakeTorque"] = self.data["brakeTorque"]["value"]
                if "engineSpeed" in self.data and "xevBatteryVoltage" not in self.data:
                    attribs["engineSpeed"] = self.data["engineSpeed"]["value"]
                if "gearLeverPosition" in self.data:
                    attribs["gearLeverPosition"] = self.data["gearLeverPosition"]["value"]
                if "parkingBrakeStatus" in self.data:
                    attribs["parkingBrakeStatus"] = self.data["parkingBrakeStatus"]["value"]
                if "torqueAtTransmission" in self.data:
                    attribs["torqueAtTransmission"] = self.data["torqueAtTransmission"]["value"]
                if "tripFuelEconomy" in self.data and "xevBatteryVoltage" not in self.data:
                    attribs["tripFuelEconomy"] = self.data["tripFuelEconomy"]["value"]
                return attribs or None
            if self.sensor == "indicators":
                alerts = {}
                for key, value in self.data.get("indicators", {}).items():
                    if value.get("value") is not None:
                        alerts[key] = value["value"]
                return alerts or None
        return None



    @property
    def name(self):
        """Return Sensor Name"""
        return "fordpass_" + self.sensor

    # @property
    # def state(self):
    #    """Return Sensor State"""
    #    return self.get_value("state")

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
    def native_value(self):
        """Return Native Value"""
        return self.get_value("state")

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
            if SENSORS[self.sensor]["state_class"] == "total_increasing":
                return SensorStateClass.TOTAL_INCREASING
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
            if SENSORS[self.sensor]["device_class"] == "battery":
                return SensorDeviceClass.BATTERY
            if SENSORS[self.sensor]["device_class"] == "speed":
                return SensorDeviceClass.SPEED
        return None
