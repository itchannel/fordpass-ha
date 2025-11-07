"""All vehicle sensors from the accessible by the API"""

import logging
from datetime import timedelta
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
from .const import CONF_PRESSURE_UNIT, DOMAIN, SENSORS, COORDINATOR


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    sensors = []
    for key, value in SENSORS.items():
        sensor = CarSensor(entry, key, config_entry.options)
        api_key = value["api_key"]
        api_class = value.get("api_class", None)
        sensor_type = value.get("sensor_type", None)
        string = isinstance(api_key, str)
        if string and sensor_type == "single":
            sensors.append(sensor)
        elif string:
            if api_key and api_class and api_key in sensor.coordinator.data.get(api_class, {}):
                sensors.append(sensor)
                continue
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
        self.data = coordinator.data.get("metrics", {})
        self.events = coordinator.data.get("events", {})
        self.states = coordinator.data.get("states", {})
        self._device_id = "fordpass_" + sensor
        # Required for HA 2022.7
        self.coordinator_context = object()

    def get_value(self, ftype):
        """Get sensor value and attributes from coordinator data"""
        self.data = self.coordinator.data.get("metrics", {})
        self.events = self.coordinator.data.get("events", {})
        self.states = self.coordinator.data.get("states", {})
        self.units = self.coordinator.hass.config.units
        if ftype == "state":
            if self.sensor == "odometer":
                return self.data.get("odometer", {}).get("value")
                # return self.data.get("odometer", {}).get("value", {})
            if self.sensor == "fuel":
                fuel_level = self.data.get("fuelLevel", {}).get("value")
                if fuel_level is not None:
                    return round(fuel_level)
                battery_soc = self.data.get("xevBatteryStateOfCharge", {}).get("value")
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
                if self.data.get("hoodStatus", {}).get("value") == "OPEN":
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
            if self.sensor == "deepSleep":
                state = self.states.get("commandPreclusion", {}).get("value", {}).get("toState", "Unsupported")
                if state == "COMMANDS_PRECLUDED":
                    return "ACTIVE"
                elif state == "COMMANDS_PERMITTED":
                    return "DISABLED"
                else:
                    return state
            if self.sensor == "events":
                return len(self.events)
            if self.sensor == "states":
                return len(self.states)
            if self.sensor == "vehicles":
                return len(self.coordinator.data.get("vehicles", {}))
            if self.sensor == "metrics":
                return len(self.data)
            return None
        if ftype == "measurement":
            return SENSORS.get(self.sensor, {}).get("measurement", None)
        if ftype == "attribute":
            if self.sensor == "odometer":
                return self.data.get("odometer", {})
            if self.sensor == "outsideTemp":
                ambient_temp = self.data.get("ambientTemp", {}).get("value")
                if ambient_temp is not None:
                    return {"Ambient Temp": ambient_temp}
                return None
            if self.sensor == "fuel":
                fuel = {}
                fuel_range = self.data.get("fuelRange", {}).get("value", 0)
                battery_range = self.data.get("xevBatteryRange", {}).get("value", 0)
                if fuel_range != 0:
                    # Display fuel range for both Gas and Hybrid (assuming its not 0)
                    fuel["fuelRange"] = self.units.length(fuel_range, UnitOfLength.KILOMETERS)
                if battery_range != 0:
                    # Display Battery range for EV and Hybrid
                    fuel["batteryRange"] = self.units.length(battery_range, UnitOfLength.KILOMETERS)
                return fuel
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
            if self.sensor == "deepSleep":
                return None
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
                    elecs["Maximum Battery Range"] = self.units.length(self.data.get("xevBatteryMaximumRange", {}).get("value", 0), UnitOfLength.KILOMETERS)

                if "xevBatteryVoltage" in self.data:
                    elecs["Battery Voltage"] = float(self.data.get("xevBatteryVoltage", {}).get("value", 0))
                    batt_volt = elecs.get("Battery Voltage", 0)

                if "xevBatteryIoCurrent" in self.data:
                    elecs["Battery Amperage"] = float(self.data.get("xevBatteryIoCurrent", {}).get("value", 0))
                    batt_amps = elecs.get("Battery Amperage", 0)

                # Returning 0 in else - to prevent attribute from not displaying
                if "xevBatteryIoCurrent" in self.data and "xevBatteryVoltage" in self.data:
                    if batt_volt != 0 and batt_amps != 0:
                        elecs["Battery kW"] = round((batt_volt * batt_amps) / 1000, 2)
                    else:
                        elecs["Battery kW"] = 0

                if "xevTractionMotorVoltage" in self.data:
                    elecs["Motor Voltage"] = float(self.data.get("xevTractionMotorVoltage", {}).get("value", 0))
                    motor_volt = elecs.get("Motor Voltage", 0)

                if "xevTractionMotorCurrent" in self.data:
                    elecs["Motor Amperage"] = float(self.data.get("xevTractionMotorCurrent", {}).get("value", 0))
                    motor_amps = elecs.get("Motor Amperage", 0)

                # Returning 0 in else - to prevent attribute from not displaying
                if "xevTractionMotorVoltage" in self.data and "xevTractionMotorCurrent" in self.data:
                    if motor_volt != 0 and motor_amps != 0:
                        elecs["Motor kW"] = round((motor_volt * motor_amps) / 1000, 2)
                    else:
                        elecs["Motor kW"] = 0

                # tripXevBatteryChargeRegenerated should be a previous FordPass feature called "Driving Score". A % based on how much regen vs brake you use
                if "tripXevBatteryChargeRegenerated" in self.data:
                    elecs["Trip Driving Score"] = self.data.get("tripXevBatteryChargeRegenerated", {}).get("value", 0)

                if "tripXevBatteryRangeRegenerated" in self.data:
                    elecs["Trip Range Regenerated"] = self.units.length(self.data.get("tripXevBatteryRangeRegenerated", {}).get("value", 0), UnitOfLength.KILOMETERS)

                if "customMetrics" in self.data and "xevBatteryCapacity" in self.data:
                    for key in self.data.get("customMetrics", {}):
                        if "accumulated-vehicle-speed-cruising-coaching-score" in key:
                            elecs["Trip Speed Score"] = self.data.get("customMetrics", {}).get(key, {}).get("value")
                        if "accumulated-deceleration-coaching-score" in key:
                            elecs["Trip Deceleration Score"] = self.data.get("customMetrics", {}).get(key, {}).get("value")
                        if "accumulated-acceleration-coaching-score" in key:
                            elecs["Trip Acceleration Score"] = self.data.get("customMetrics", {}).get(key, {}).get("value")
                        if "custom:vehicle-electrical-efficiency" in key:
                            # Still don't know what this value is, but if I add it and get more data it could help to figure it out
                            elecs["Trip Electrical Efficiency"] = self.data.get("customMetrics", {}).get(key, {}).get("value")

                if "customEvents" in self.events:
                    tripDataStr = self.events.get("customEvents", {}).get("xev-key-off-trip-segment-data", {}).get("oemData", {}).get("trip_data", {}).get("stringArrayValue", [])
                    for dataStr in tripDataStr:
                        tripData = json.loads(dataStr)
                        if "ambient_temperature" in tripData:
                            elecs["Trip Ambient Temp"] = self.units.temperature(tripData["ambient_temperature"], UnitOfTemperature.CELSIUS)
                        if "outside_air_ambient_temperature" in tripData:
                            elecs["Trip Outside Air Ambient Temp"] = self.units.temperature(tripData["outside_air_ambient_temperature"], UnitOfTemperature.CELSIUS)
                        if "trip_duration" in tripData:
                            elecs["Trip Duration"] = str(dt.parse_duration(str(tripData["trip_duration"])))
                        if "cabin_temperature" in tripData:
                            elecs["Trip Cabin Temp"] = self.units.temperature(tripData["cabin_temperature"], UnitOfTemperature.CELSIUS)
                        if "energy_consumed" in tripData:
                            elecs["Trip Energy Consumed"] = round(tripData["energy_consumed"] / 1000, 2)
                        if "distance_traveled" in tripData:
                            elecs["Trip Distance Traveled"] = self.units.length(tripData["distance_traveled"], UnitOfLength.KILOMETERS)
                        if ("energy_consumed" in tripData and tripData["energy_consumed"] is not None and "distance_traveled" in tripData and tripData["distance_traveled"] is not None):
                            if elecs["Trip Distance Traveled"] == 0 or elecs["Trip Energy Consumed"] == 0:
                                elecs["Trip Efficiency"] = 0
                            else:
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

                # Returning 0 in else - to prevent attribute from not displaying
                if "xevBatteryChargerVoltageOutput" in self.data and "xevBatteryChargerCurrentOutput" in self.data:

                    # Get Battery Io Current for DC Charging calculation
                    if "xevBatteryIoCurrent" in self.data:
                        batt_amps = float(self.data.get("xevBatteryIoCurrent", {}).get("value", 0))

                    # AC Charging calculation
                    if ch_volt != 0 and ch_amps != 0:
                        cs["Charging kW"] = round((ch_volt * ch_amps) / 1000, 2)
                    # DC Charging calculation: Use absolute value for amperage to handle negative values
                    elif ch_volt != 0 and batt_amps != 0:
                        cs["Charging kW"] = round((ch_volt * abs(batt_amps)) / 1000, 2)
                    else:
                        cs["Charging kW"] = 0

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
                return {"Countdown": self.data.get("remoteStartCountdownTimer", {}).get("value", 0)}
            if self.sensor == "messages":
                messages = {}
                for value in self.coordinator.data.get("messages", []):
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
            if self.sensor == "events":
                return self.events
            if self.sensor == "states":
                return self.states
            if self.sensor == "vehicles":
                return self.coordinator.data.get("vehicles", {})
            if self.sensor == "metrics":
                return self.data
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

    @property
    def entity_registry_enabled_default(self):
        """Return if entity should be enabled when first added to the entity registry."""
        if "debug" in SENSORS[self.sensor]:
            return False
        return True
