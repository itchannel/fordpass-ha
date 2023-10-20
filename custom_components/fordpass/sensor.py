"""All vehicle sensors from the accessible by the API"""

import logging
from datetime import datetime, timedelta
import json

from homeassistant.const import UnitOfTemperature, UnitOfLength, UnitOfPressure
from homeassistant.util import dt
from homeassistant.util.unit_conversion import TemperatureConverter

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
                return self.data.get("xevBatteryRange", {}).get("value")
            # SquidBytes: Added elVehCharging
            if self.sensor == "elVehCharging":
                return self.data.get("xevBatteryChargeDisplayStatus", {}).get("value", "Unsupported")
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
                    "xevBatteryActualStateOfCharge" in self.data and self.data["xevBatteryActualStateOfCharge"] is not None and self.data["xevBatteryActualStateOfCharge"]["value"] is not None
                ):
                    elecs["Battery Actual Charge"] = self.data[
                        "xevBatteryActualStateOfCharge"
                    ]["value"]

                # tripXevBatteryChargeRegenerated should be a previous FordPass feature called "Driving Score". A % based on how much regen vs brake you use
                if (
                    "tripXevBatteryChargeRegenerated" in self.data and self.data["tripXevBatteryChargeRegenerated"] is not None and self.data["tripXevBatteryChargeRegenerated"]["value"] is not None
                ):
                    elecs["Driving Score"] = self.data["tripXevBatteryChargeRegenerated"]["value"]

                if (
                    "tripXevBatteryRangeRegenerated" in self.data and self.data["tripXevBatteryRangeRegenerated"] is not None and self.data["tripXevBatteryRangeRegenerated"]["value"] is not None
                ):
                    if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                        elecs["Range Regenerated"] = round(float(self.data["tripXevBatteryRangeRegenerated"]["value"]) / 1.60934)
                    else:
                        elecs["Range Regenerated"] = self.data["tripXevBatteryRangeRegenerated"]["value"]

                if (
                    "xevBatteryCapacity" in self.data and self.data["xevBatteryCapacity"] is not None and self.data["xevBatteryCapacity"]["value"] is not None
                ):
                    elecs["Maximum Battery Capacity"] = self.data["xevBatteryCapacity"]["value"]

                if (
                    "xevBatteryMaximumRange" in self.data and self.data["xevBatteryMaximumRange"] is not None and self.data["xevBatteryMaximumRange"]["value"] is not None
                ):
                    if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                        elecs["Maximum Battery Range"] = round(float(self.data["xevBatteryMaximumRange"]["value"]) / 1.60934)
                    else:
                        elecs["Maximum Battery Range"] = self.data["xevBatteryMaximumRange"]["value"]

                if (
                    "xevBatteryVoltage" in self.data and self.data["xevBatteryVoltage"] is not None and self.data["xevBatteryVoltage"]["value"] is not None
                ):
                    elecs["Battery Voltage"] = float(self.data["xevBatteryVoltage"]["value"])
                    batt_volt = elecs["Battery Voltage"]

                if (
                    "xevBatteryIoCurrent" in self.data and self.data["xevBatteryIoCurrent"] is not None and self.data["xevBatteryIoCurrent"]["value"] is not None
                ):
                    elecs["Battery Amperage"] = float(self.data["xevBatteryIoCurrent"]["value"])
                    batt_amps = elecs["Battery Amperage"]
                if (
                    "xevBatteryIoCurrent" in self.data and self.data["xevBatteryIoCurrent"] is not None and self.data["xevBatteryIoCurrent"]["value"] is not None
                    and "xevBatteryVoltage" in self.data and self.data["xevBatteryVoltage"] is not None and self.data["xevBatteryVoltage"]["value"] is not None
                ):
                    elecs["Battery kW"] = round((batt_volt * batt_amps) / 1000, 2)
                if (
                    "xevTractionMotorVoltage" in self.data and self.data["xevTractionMotorVoltage"] is not None and self.data["xevTractionMotorVoltage"]["value"] is not None
                ):
                    elecs["Motor Voltage"] = float(self.data["xevTractionMotorVoltage"]["value"])
                    motor_volt = elecs["Motor Voltage"]
                if (
                    "xevTractionMotorCurrent" in self.data and self.data["xevTractionMotorCurrent"] is not None and self.data["xevTractionMotorCurrent"]["value"] is not None
                ):
                    elecs["Motor Amperage"] = float(self.data["xevTractionMotorCurrent"]["value"])
                    motor_amps = elecs["Motor Amperage"]
                if (
                    "xevTractionMotorVoltage" in self.data and self.data["xevTractionMotorVoltage"] is not None and self.data["xevTractionMotorVoltage"]["value"] is not None
                    and "xevTractionMotorCurrent" in self.data and self.data["xevTractionMotorCurrent"] is not None and self.data["xevTractionMotorCurrent"]["value"] is not None
                ):
                    elecs["Motor kW"] = round((motor_volt * motor_amps) / 1000, 2)
                if (
                    "customEvents" in self.events 
                    and self.events["customEvents"] is not None
                    and self.events["customEvents"]["xev-key-off-trip-segment-data"] is not None
                    and self.events["customEvents"]["xev-key-off-trip-segment-data"]["oemData"] is not None
                    and self.events["customEvents"]["xev-key-off-trip-segment-data"]["oemData"]["trip_data"] is not None
                    and self.events["customEvents"]["xev-key-off-trip-segment-data"]["oemData"]["trip_data"]["stringArrayValue"] is not None
                ):
                    tripDataStr = self.events["customEvents"]["xev-key-off-trip-segment-data"]["oemData"]["trip_data"]["stringArrayValue"]
                    for dataStr in tripDataStr:
                        tripData = json.loads(dataStr)
                        tempConvert = TemperatureConverter()
                        if "ambient_temperature" in tripData:
                            if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                                elecs["Trip Ambient Temp"] = round(tempConvert.convert(float(tripData["ambient_temperature"]), UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT))
                            else:
                                elecs["Trip Ambient Temp"] = tripData["ambient_temperature"]
                        if "outside_air_ambient_temperature" in tripData:
                            if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                                elecs["Trip Outside Air Ambient Temp"] = round(tempConvert.convert(float(tripData["outside_air_ambient_temperature"]), UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT))
                            else:
                                elecs["Trip Outside Air Ambient Temp"] = tripData["outside_air_ambient_temperature"]
                        if "trip_duration" in tripData:
                            elecs["Trip Duration"] = tripData["trip_duration"] / 3600
                        if "cabin_temperature" in tripData:
                            if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                                elecs["Trip Cabin Temp"] = round(tempConvert.convert(float(tripData["cabin_temperature"]), UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT))
                            else:
                                elecs["Trip Cabin Temp"] = tripData["cabin_temperature"]
                        if "energy_consumed" in tripData:
                            elecs["Trip Energy Consumed"] = round(tripData["energy_consumed"] / 1000, 2)
                        if "distance_traveled" in tripData:
                            if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                                elecs["Trip Distance Traveled"] = round(float(tripData["distance_traveled"] / 1.60934))
                            else:
                                elecs["Trip Distance Traveled"] = tripData["distance_traveled"]
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

                if (
                    "xevPlugChargerStatus" in self.data and self.data["xevPlugChargerStatus"] is not None and self.data["xevPlugChargerStatus"]["value"] is not None
                ):
                    cs["Plug Status"] = self.data["xevPlugChargerStatus"]["value"]
                if (
                    "xevChargeStationCommunicationStatus" in self.data and self.data["xevChargeStationCommunicationStatus"] is not None and self.data["xevChargeStationCommunicationStatus"]["value"] is not None
                ):
                    cs["Charging Station Status"] = self.data["xevChargeStationCommunicationStatus"]["value"]
                if (
                    "xevBatteryChargeDisplayStatus" in self.data and self.data["xevBatteryChargeDisplayStatus"] is not None and self.data["xevBatteryChargeDisplayStatus"]["value"] is not None
                ):
                    cs["Charging Status"] = self.data["xevBatteryChargeDisplayStatus"]["value"]
                if (
                    "xevChargeStationPowerType" in self.data and self.data["xevChargeStationPowerType"] is not None and self.data["xevChargeStationPowerType"]["value"] is not None
                ):
                    cs["Charging Type"] = self.data["xevChargeStationPowerType"]["value"]

                # if (
                #     "tripXevBatteryDistanceAccumulated" in self.data and self.data["tripXevBatteryDistanceAccumulated"] is not None and self.data["tripXevBatteryDistanceAccumulated"]["value"] is not None
                # ):
                #     if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                #         cs["Distance Accumulated"] = round(
                #                 float(self.data["tripXevBatteryDistanceAccumulated"]["value"]) / 1.60934
                #             )
                #     else:
                #         cs["Distance Accumulated"] = self.data["tripXevBatteryDistanceAccumulated"]["value"]
                if (
                    "xevBatteryChargerVoltageOutput" in self.data and self.data["xevBatteryChargerVoltageOutput"] is not None and self.data["xevBatteryChargerVoltageOutput"]["value"] is not None
                ):
                    cs["Charging Voltage"] = float(self.data["xevBatteryChargerVoltageOutput"]["value"])
                    ch_volt = cs["Charging Voltage"]

                if (
                    "xevBatteryChargerCurrentOutput" in self.data and self.data["xevBatteryChargerCurrentOutput"] is not None and self.data["xevBatteryChargerCurrentOutput"]["value"] is not None

                ):
                    cs["Charging Amperage"] = float(self.data["xevBatteryChargerCurrentOutput"]["value"])
                    ch_amps = cs["Charging Amperage"]

                if (
                    "xevBatteryChargerCurrentOutput" in self.data and self.data["xevBatteryChargerCurrentOutput"]["value"] is not None and self.data["xevBatteryChargerVoltageOutput"]["value"] is not None
                    and "xevBatteryChargerVoltageOutput" in self.data and self.data["xevBatteryChargerVoltageOutput"] is not None and self.data["xevBatteryChargerVoltageOutput"]["value"] is not None
                ):
                    cs["Charging kW"] = round((ch_volt * ch_amps) / 1000, 2)

                if (
                    "xevBatteryTemperature" in self.data and self.data["xevBatteryTemperature"] is not None and self.data["xevBatteryTemperature"]["value"] is not None
                ):
                    if self.fordoptions[CONF_DISTANCE_UNIT] == "mi":
                        tempConvert = TemperatureConverter()
                        cs["Battery Temperature"] = round(tempConvert.convert(float(self.data["xevBatteryTemperature"]["value"]), UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT))
                    else:
                        cs["Battery Temperature"] = self.data["xevBatteryTemperature"]["value"]

                if (
                    "xevBatteryStateOfCharge" in self.data and self.data["xevBatteryStateOfCharge"] is not None and self.data["xevBatteryStateOfCharge"]["value"] is not None
                ):
                    cs["State of Charge"] = self.data["xevBatteryStateOfCharge"]["value"]

                if (
                    "xevBatteryTimeToFullCharge" in self.data and self.data["xevBatteryTimeToFullCharge"] is not None and self.data["xevBatteryTimeToFullCharge"]["value"] is not None
                    and self.data["xevBatteryTimeToFullCharge"]["updateTime"] is not None
                ):
                    cs_update_time = dt.parse_datetime(self.data["xevBatteryTimeToFullCharge"]["updateTime"])
                    cs_est_end_time = cs_update_time + timedelta(minutes=self.data["xevBatteryTimeToFullCharge"]["value"])
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
