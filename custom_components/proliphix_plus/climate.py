"""
Support for Proliphix  Thermostats.

This is a custom platform
"""
from homeassistant.components.climate import ClimateDevice, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_HEAT_COOL, HVAC_MODE_FAN_ONLY,
    FAN_AUTO, FAN_ON,
    CURRENT_HVAC_OFF, CURRENT_HVAC_HEAT, CURRENT_HVAC_COOL, CURRENT_HVAC_IDLE,
    ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW,
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_TARGET_TEMPERATURE_RANGE, SUPPORT_FAN_MODE, SUPPORT_PRESET_MODE)
from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_PASSWORD, CONF_USERNAME, PRECISION_TENTHS, TEMP_FAHRENHEIT,
    ATTR_TEMPERATURE)

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.restore_state import RestoreEntity

import time, datetime, dateutil.parser
import requests
from urllib.parse import urlencode

_LOGGER = logging.getLogger(__name__)

'''
Mapping of Proliphix OID values to friendly names
'''
# Data to be retrieved whenever polling the thermostat status
OID_MAP = {
    "1.2": "commonDevName",
    "1.8": "serialNumber",
    "1.10.9": "siteName",
    "2.5.1": "systemTimeSecs",
    "2.7.1": "systemMimModelNumber",
    "4.3.2.1": "thermSensorTempLocal",
    "4.3.2.2": "thermSensorTempRemote1",
    "4.3.6.2": "thermSensorStateRemote1",
    "4.1.1": "thermHvacMode",
    "4.1.2": "thermHvacState",
    "4.1.3": "thermFanMode",
    "4.1.4": "thermFanState",
    "4.1.5": "thermSetbackHeat",
    "4.1.6": "thermSetbackCool",
    "4.1.9": "thermSetbackStatus",
    "4.1.10": "thermCurrentPeriod",
    "4.1.11": "thermCurrentClass",
    "4.1.14": "thermRelativeHumidity",
    "4.1.22": "thermHoldDuration",
    "4.1.8": "thermHoldMode",
    "4.4.1.3.1.1": "thermPeriodStartInMorning",
    "4.4.1.3.1.2": "thermPeriodStartInDay",
    "4.4.1.3.1.3": "thermPeriodStartInEvening",
    "4.4.1.3.1.4": "thermPeriodStartInNight",
    "4.4.1.3.2.1": "thermPeriodStartOutMorning",
    "4.4.1.3.2.2": "thermPeriodStartOutDay",
    "4.4.1.3.2.3": "thermPeriodStartOutEvening",
    "4.4.1.3.2.4": "thermPeriodStartOutNight",
    "4.4.1.3.3.1": "thermPeriodStartAwayMorning",
    "4.4.1.3.3.2": "thermPeriodStartAwayDay",
    "4.4.1.3.3.3": "thermPeriodStartAwayEvening",
    "4.4.1.3.3.4": "thermPeriodStartAwayNight"
}

THERM_HVAC_MODE_MAP = {
    '1': 'Off',
    '2': 'Heat',
    '3': 'Cool',
    '4': 'Auto'
}

THERM_HVAC_STATE_MAP = {
    '1': 'Initializing',
    '2': 'Off',
    '3': 'Heat',
    '4': 'Heat2',
    '5': 'Heat3',
    '6': 'Cool',
    '7': 'Cool2',
    '8': 'Delay',
    '9': 'ResetRelays'
}

THERM_FAN_MODE_MAP = {
    '1': 'Auto',
    '2': 'On',
    '3': 'Schedule'
}

THERM_FAN_STATE_MAP = {
    '0': 'Init',
    '1': 'Off',
    '2': 'On'
}

THERM_SETBACK_STATUS_MAP = {
    '1': 'Normal',
    '2': 'Hold',
    '3': 'Override',
    '4': 'Unknown',
    '5': 'Unknown',
    '6': 'Unknown',
    '7': 'Unknown'
}

THERM_CURRENT_PERIOD_MAP = {
    '1': 'Morning',
    '2': 'Day',
    '3': 'Evening',
    '4': 'Night'
}

THERM_CURRENT_CLASS_MAP = {
    '1': 'In',
    '2': 'Out',
    '3': 'Away',
    '4': 'Other'
}

THERM_ACTIVE_PERIOD_MAP = {
    '1': 'Morning',
    '2': 'Day',
    '3': 'Evening',
    '4': 'Night',
    '5': 'Hold',
    '6': 'Override'
}

THERM_SENSOR_STATE_MAP = {
    '0': 'NotPresent',
    '1': 'Disabled',
    '2': 'Enabled'
}

FAN_SCHEDULE = "Schedule"

# Preset modes supported by this component
PRESET_SCHEDULE = "Schedule"        # Restore the normal daily schedule
PRESET_IN = "In"                    # Switch to 'In' schedule
PRESET_OUT = "Out"                  # Switch to 'Out' schedule
PRESET_AWAY = "Away"                # Switch to 'Away' schedule
PRESET_ECO = "Eco"                  # Switch to 'Eco' mode
PRESET_MANUAL_TEMP = "Override"     # Override currently scheduled activity until the next schedule change
PRESET_MANUAL_PERM = "Hold"         # Override the schedule indefinitely

PRESET_MODES = [PRESET_IN, PRESET_OUT, PRESET_AWAY,
                PRESET_MANUAL_TEMP, PRESET_MANUAL_PERM]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=80): cv.port,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Proliphix thermostat"""
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    port = config.get(CONF_PORT)
    hostname = config.get(CONF_HOST)

    add_devices([ProliphixThermostat(hostname, port, username, password)])


class ProliphixDevice():

    def __init__(self, hostname, port, username, password):
        self._hostname = hostname
        self._port = port
        self._username = username
        self._password = password

    '''
    Retrieve one or many values from the device.  Argument 'oids' can be any of the following:
    - A single OID string ("4.3.2.1")
    - A list of OID strings (["4.3.2.1", "1.2"])
    - A dict of OID strings, mapped to friendly names ({"4.3.2.1" : "thermSensorTempLocal", "1.2" : "commonDevName"})
    Return value is a dict of OID mapped to its value.  The OID will be be converted to the friendly name if it was provided. 
    '''

    def get(self, oids):
        valueDict = {}
        oidList = []
        remapOIDNames = False

        if isinstance(oids, str):
            oidList = [oids]
        elif isinstance(oids, list):
            oidList = list(oids)
        elif isinstance(oids, dict):
            oidList = list(oids.keys())
            remapOIDNames = True

        url = "http://%s:%s/get" % (self._hostname, str(self._port))
        data = "&".join([("OID" + oid + "=") for oid in oidList])
        try:
            response = requests.post(url, auth=(self._username, self._password), data=data)
            for pair in response.text.split('&'):
                if len(pair) == 0:
                    continue
                oid, value = pair.split('=')
                oid = oid[3:]  # Strip 'OID' from the key
                # Remap code to friendly name
                if remapOIDNames:
                    oid = oids[oid]
                valueDict[oid] = value
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to connect to {}".format(url))
        
        return valueDict

    '''
    Set values on the device.  Argument 'oids' can be any of the following:
    - Dict of OIDs mapped to values ({"4.1.1" : "1"})
    - Dict of querystring-style OIDs mapped to values ({"OID4.1.1" : "1"})
    - Dict of friendly names mapped to values ({"thermHvacMode" : "1"})
    '''

    def set(self, oids):
        valueDict = {}
        _LOGGER.info("SET oids: %s", oids)
        for key, value in oids.items():
            if key[0:3] == "OID":
                valueDict[key] = value
            elif key[0:1].isdigit():
                valueDict["OID%s" % key] = value
            else:
                oid = self._oidNameToID(key)
                if oid is not None:
                    valueDict["OID%s" % oid] = value
        url = "http://%s:%s/pdp" % (self._hostname, str(self._port))
        data = urlencode(valueDict)
        data += "&submit=Submit"
        _LOGGER.debug("SET Request: %s Data: %s", url, data)
        requests.post(url, auth=(self._username, self._password), data=data)

    def _oidNameToID(self, oidName):
        for id, name in OID_MAP.items():
            if name == oidName:
                return id
        return None

    def _oidIDToName(self, oidID):
        oidID = oidID.replace("OID", "")  # Strip out the OID prefix if included
        for id, name in OID_MAP.items():
            if id == oidID:
                return name
        return None


class ProliphixThermostat(ClimateDevice, RestoreEntity):
    """Representation a Proliphix thermostat."""

    def __init__(self, hostname, port, username, password):
        """Initialize the thermostat."""
        self._device = ProliphixDevice(hostname, port, username, password)
        self._data = {}

        self._manufacturer = "Proliphix"
        self._serial = None
        self._deviceName = None
        self._siteName = None
        self._model = None
        self._temperature = None
        self._remoteSensorTemperature = None
        self._remoteSensorState = None
        self._hvacMode = None
        self._hvacState = None
        self._fanMode = None
        self._fanState = None
        self._setbackHeat = None
        self._setbackCool = None
        self._setbackStatus = None
        self._currentPeriod = None
        self._currentClass = None
        self._relativeHumidity = None
        self._holdDuration = None
        self._classPeriodSchedule = None
        self._nextPeriodSchedule = None

        # TODO: Make these configurable and update logic
        self._configEcoModeEnabled = True
        self._configEcoModeTemperature = 50
        self._configAwayModeEnabled = True

        # Custom extensions
        self._holdUntil = None
        self._scheduleText = None

        self._preset_mode = None

        # Initialize the object
        self.update()
        self._fixClockDrift()
        self._setHoldDuration(0)

    async def async_added_to_hass(self):
        """Handle all entity which are about to be added."""
        await super().async_added_to_hass()
        # Restore a saved state and process as needed
        last_state = await self.async_get_last_state()
        self._restore_last_state(last_state)

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._serial

    @property
    def name(self):
        """Return the name of the thermostat."""
        if self._siteName == "":
            return self._deviceName
        return "{}: {}".format(self._siteName, self._deviceName)

    @property
    def should_poll(self):
        """Set up polling needed for thermostat."""
        return True

    def update(self):
        """Update the data from the thermostat."""
        time.sleep(1)

        # Use this to determine if something was set directly on the thermostat
        self._previousData = self._data

        self._data = self._device.get(OID_MAP)
        self._serial = self._data.get("serialNumber")
        self._model = self._data.get("systemMimModelNumber")
        self._deviceName = self._data.get("commonDevName")
        self._siteName = self._data.get("siteName")
        self._temperature = float(self._data.get("thermSensorTempLocal", 0))
        self._remoteSensorTemperature = self._data.get("thermSensorTempRemote1", 0)
        self._remoteSensorState = self._data.get("thermSensorStateRemote1", 0)
        self._hvacMode = self._data.get("thermHvacMode", 1)
        self._hvacState = self._data.get("thermHvacState", 2)
        self._fanMode = self._data.get("thermFanMode", 1)
        self._fanState = self._data.get("thermFanState", 1)
        self._setbackHeat = self._data.get("thermSetbackHeat", 0)
        self._setbackCool = self._data.get("thermSetbackCool", 0)
        self._setbackStatus = self._data.get("thermSetbackStatus", 1)
        self._currentPeriod = self._data.get("thermCurrentPeriod", 1)
        self._currentClass = self._data.get("thermCurrentClass", 1)
        self._relativeHumidity = float(self._data.get("thermRelativeHumidity", 0))
        self._holdDuration = int(self._data.get("thermHoldDuration", 0))
        self._classPeriodSchedule = {
            "In": {
                "Morning": self._computeScheduleDateTime(self._data.get("thermPeriodStartInMorning", 0)),
                "Day": self._computeScheduleDateTime(self._data.get("thermPeriodStartInDay", 0)),
                "Evening": self._computeScheduleDateTime(self._data.get("thermPeriodStartInEvening", 0)),
                "Night": self._computeScheduleDateTime(self._data.get("thermPeriodStartInNight", 0))
            },
            "Out": {
                "Morning": self._computeScheduleDateTime(self._data.get("thermPeriodStartOutMorning", 0)),
                "Day": self._computeScheduleDateTime(self._data.get("thermPeriodStartOutDay", 0)),
                "Evening": self._computeScheduleDateTime(self._data.get("thermPeriodStartOutEvening", 0)),
                "Night": self._computeScheduleDateTime(self._data.get("thermPeriodStartOutNight", 0))
            },
            "Away": {
                "Morning": self._computeScheduleDateTime(self._data.get("thermPeriodStartAwayMorning", 0)),
                "Day": self._computeScheduleDateTime(self._data.get("thermPeriodStartAwayDay", 0)),
                "Evening": self._computeScheduleDateTime(self._data.get("thermPeriodStartAwayEvening", 0)),
                "Night": self._computeScheduleDateTime(self._data.get("thermPeriodStartAwayNight", 0))
            }
        }
        self._nextPeriod, self._nextPeriodStart = self._getNextPeriodSchedule()
        self._holdUntil = self._getHoldUntil()
        self._scheduleSummary = self._getScheduleSummary()


        # Compute current preset based on setback status and current class
        # Normal
        if self._setbackStatus == "1":
            # In
            if self._currentClass == "1":
                self._preset_mode = PRESET_IN
            # Out
            if self._currentClass == "2":
                self._preset_mode = PRESET_OUT
            # Away
            if self._currentClass == "3":
                self._preset_mode = PRESET_AWAY
        # Hold
        elif self._setbackStatus == "2":
            self._preset_mode = PRESET_MANUAL_PERM
        # Override
        elif self._setbackStatus == "3":
            self._preset_mode = PRESET_MANUAL_TEMP

    @property
    def state(self):
        """Return the current state."""
        return super().state

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_TENTHS

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        default_attributes = super().state_attributes
        custom_attributes = {
            "manufacturer": self._manufacturer,
            "serial": self._serial,
            "model": self._model,
            "device_name": self._deviceName,
            "site_name": self._siteName,
            "admin_url": "http://%s:%s/" % (self._device._hostname, self._device._port),
            "current_period": THERM_CURRENT_PERIOD_MAP.get(self._currentPeriod),
            "current_class": THERM_CURRENT_CLASS_MAP.get(self._currentClass),
            "hold_hours": self._holdDuration,
            "fan_state": THERM_FAN_STATE_MAP.get(self._fanMode),
            "setback_status": THERM_SETBACK_STATUS_MAP.get(self._setbackStatus),
            "next_period" : self._nextPeriod,
            "next_period_start" : self._nextPeriodStart,
            "hold_until": self._holdUntil,
            "schedule_summary": self._scheduleSummary
        }
        if self._model in ["NT150", "NT160"]:
            custom_attributes["humidity"] = self._relativeHumidity
        if self._model not in ["NT10"]:
            custom_attributes["remote_sensor_state"] = THERM_SENSOR_STATE_MAP.get(self._remoteSensorState)
            if THERM_SENSOR_STATE_MAP.get(self._remoteSensorState) == "Enabled":
                custom_attributes["remote_sensor_temperature"] = float(self._remoteSensorTemperature) / 10
        attributes = {}
        attributes.update(default_attributes)
        attributes.update(custom_attributes)
        return attributes

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_FAHRENHEIT

    @property
    def current_humidity(self):
        """Return the current humidity."""
        if self._model in ["NT150", "NT160"]:
            return self._relativeHumidity
        else:
            return super().target_humidity

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return super().target_humidity

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.
        Need to be one of HVAC_MODE_*.
        """
        # TODO: Re-enable Fan mode
        if self._hvacMode == '2':
            return HVAC_MODE_HEAT
        elif self._hvacMode == '3':
            return HVAC_MODE_COOL
        elif self._hvacMode == '4':
            return HVAC_MODE_HEAT_COOL
        elif self._hvacMode == '1':
            return HVAC_MODE_OFF
        else:
            return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.
        Need to be a subset of HVAC_MODES.
        """
        # TODO: Re-enable Fan mode
        return [HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_HEAT_COOL]

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.
        Need to be one of CURRENT_HVAC_*.
        """
        # TODO: Add logic for fan
        if self.hvac_mode == HVAC_MODE_OFF:
            return CURRENT_HVAC_OFF
        elif self._hvacState in ['1', '2', '8', '9']:
            return CURRENT_HVAC_IDLE
        elif self._hvacState in ['3', '4', '5']:
            return CURRENT_HVAC_HEAT
        elif self._hvacState in ['6', '7']:
            return CURRENT_HVAC_COOL
        else:
            return CURRENT_HVAC_IDLE

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return float(self._temperature) / 10

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if THERM_HVAC_MODE_MAP.get(self._hvacMode) == "Auto":
            hvacStateName = THERM_HVAC_STATE_MAP.get(self._hvacState)
            if hvacStateName.startswith("Cool"):
                return float(self._setbackCool) / 10
            elif hvacStateName.startswith("Heat"):
                return float(self._setbackHeat) / 10
            else:
                return None
        elif THERM_HVAC_MODE_MAP.get(self._hvacMode) == "Heat":
            return float(self._setbackHeat) / 10
        elif THERM_HVAC_MODE_MAP.get(self._hvacMode) == "Cool":
            return float(self._setbackCool) / 10
        return None

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        if THERM_HVAC_MODE_MAP.get(self._hvacMode) == "Auto":
            return float(self._setbackCool) / 10
        return None

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        if THERM_HVAC_MODE_MAP.get(self._hvacMode) == "Auto":
            return float(self._setbackHeat) / 10
        return None

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp.
        Requires SUPPORT_PRESET_MODE.
        """
        return self._preset_mode

    @property
    def preset_modes(self):
        """Return a list of available preset modes.
        Requires SUPPORT_PRESET_MODE.
        """
        return PRESET_MODES

    @property
    def is_aux_heat(self):
        """Return true if aux heater.
        Requires SUPPORT_AUX_HEAT.
        """
        raise NotImplementedError

    @property
    def fan_mode(self):
        """Return the fan setting.
        Requires SUPPORT_FAN_MODE.
        Infinity's internal value of 'off' displays as 'auto' on the thermostat
        """
        if self._fanMode == "1":
            return FAN_AUTO
        elif self._fanMode == "2":
            return FAN_ON
        elif self._fanMode == "3":
            return FAN_SCHEDULE


    @property
    def fan_modes(self):
        """Return the list of available fan modes.
        Requires SUPPORT_FAN_MODE.
        """
        return [FAN_AUTO, FAN_ON, FAN_SCHEDULE]

    @property
    def swing_mode(self):
        """Return the swing setting.
        Requires SUPPORT_SWING_MODE.
        """
        raise NotImplementedError

    @property
    def swing_modes(self):
        """Return the list of available swing modes.
        Requires SUPPORT_SWING_MODE.
        """
        raise NotImplementedError

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        targetTemp = int(kwargs.get(ATTR_TEMPERATURE) * 10)
        if self._hvacMode == "2":
            targetSetback = "thermSetbackHeat"
        elif self._hvacMode == "3":
            targetSetback = "thermSetbackCool"
        elif self._hvacMode == "4":
            # TODO: Determine the right setting to change when in Auto mode
            pass
        else:
            return
        # Enable a temporary override at the selected temperature
        self._device.set({targetSetback: targetTemp, "thermSetbackStatus": '2'})

    def set_humidity(self, humidity):
        """Set new target humidity."""
        raise NotImplementedError

    def set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        for value, label in THERM_FAN_MODE_MAP.items():
            if label == fan_mode:
                self._device.set({"4.1.3": value})

    def set_hvac_mode(self, hvac_mode):
        """Set new operation mode."""

        # Enable selected mode & return to 'normal' status (no hold or override)
        for value, label in THERM_HVAC_MODE_MAP.items():
            if label.lower() == hvac_mode:
                self._device.set({"thermHvacMode": value, "thermSetbackStatus": 1})

    def set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        raise NotImplementedError

    def set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        # Skip if no change
        if preset_mode == self._preset_mode:
            return

        # Set the normal weekly schedule to In/Out/Away based on preset
        if preset_mode == PRESET_IN:
            self._device.set(
                {"4.1.9": "1", "4.4.3.2.1": "1", "4.4.3.2.2": "1", "4.4.3.2.3": "1", "4.4.3.2.4": "1",
                 "4.4.3.2.5": "1", "4.4.3.2.6": "1", "4.4.3.2.7": "1"})
        elif preset_mode == PRESET_OUT:
            self._device.set(
                {"4.1.9": "1", "4.4.3.2.1": "2", "4.4.3.2.2": "2", "4.4.3.2.3": "2", "4.4.3.2.4": "2",
                 "4.4.3.2.5": "2", "4.4.3.2.6": "2", "4.4.3.2.7": "2"})
        elif preset_mode == PRESET_AWAY:
            self._device.set(
                {"4.1.9": "1", "4.4.3.2.1": "3", "4.4.3.2.2": "3", "4.4.3.2.3": "3", "4.4.3.2.4": "3",
                 "4.4.3.2.5": "3", "4.4.3.2.6": "3", "4.4.3.2.7": "3"})
        elif preset_mode == PRESET_MANUAL_TEMP:
            self._set_hold_mode('Override')
        elif preset_mode == PRESET_MANUAL_PERM:
            self._set_hold_mode('Hold')
        elif preset_mode == PRESET_ECO:
            self._turnOnEcoMode()
        else:
            _LOGGER.error("Invalid preset mode: {}".format(preset_mode))
            return

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        raise NotImplementedError

    def turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        raise NotImplementedError

    @property
    def supported_features(self):
        """Return the list of supported features."""
        baseline_features = (SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE)
        if self.hvac_mode == HVAC_MODE_HEAT_COOL:
            return baseline_features | SUPPORT_TARGET_TEMPERATURE_RANGE
        elif self.hvac_mode in [HVAC_MODE_HEAT, HVAC_MODE_COOL]:
            return baseline_features | SUPPORT_TARGET_TEMPERATURE
        else:
            return baseline_features

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return super().min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return super().max_temp

    @property
    def min_humidity(self):
        """Return the minimum humidity."""
        return super().min_humidity

    @property
    def max_humidity(self):
        """Return the maximum humidity."""
        return super().max_humidity

    def _turn_away_mode_on(self):
        """Turn away mode on by setting the default weekly schedule for each day to OUT."""
        self._device.set(
            {"4.4.3.2.1": "2", "4.4.3.2.2": "2", "4.4.3.2.3": "2", "4.4.3.2.4": "2", "4.4.3.2.5": "2", "4.4.3.2.6": "2",
             "4.4.3.2.7": "2"})
        time.sleep(1)   # Allow time for change to process, then force update
        self.update()

    def _turn_away_mode_off(self):
        """Turn away mode off by setting the default weekly schedule for each day to IN."""
        self._device.set(
            {"4.4.3.2.1": "1", "4.4.3.2.2": "1", "4.4.3.2.3": "1", "4.4.3.2.4": "1", "4.4.3.2.5": "1", "4.4.3.2.6": "1",
             "4.4.3.2.7": "1"})
        time.sleep(1)   # Allow time for change to process, then force update
        self.update()

    def _set_hold_mode(self, hold):
        """Update hold mode."""
        # TODO: this can be enhanced
        for value, label in THERM_SETBACK_STATUS_MAP.items():
            if label == hold:
                self._device.set({"thermSetbackStatus": value, "thermHoldDuration": "0"})

    def _restore_last_state(self, restoredState):
        '''
        Use this to restore custom computed attributes, such as holdUntil, scheduleSummary
        :param restoredState:
        :return:
        '''
        if not restoredState:
            return

        pass

    def _computeScheduleDateTime(self, minsAfterMidnight=0):
        if minsAfterMidnight is None:
            minsAfterMidnight = 0
        minsAfterMidnight = int(minsAfterMidnight)
        result = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            minutes=minsAfterMidnight)
        # If the time is in the past, result should be same time tomorrow
        if result < datetime.datetime.now():
            result = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
                days=1, minutes=minsAfterMidnight)
        return result

    def _getNextPeriodSchedule(self):
        currentClass = THERM_CURRENT_CLASS_MAP.get(self._currentClass, 1)
        nextPeriod = "Unknown"
        nextPeriodStart = datetime.datetime.max
        for period, startDateTime in self._classPeriodSchedule.get(currentClass, {}).items():
            if startDateTime >= datetime.datetime.now() and startDateTime <= nextPeriodStart:
                nextPeriod = period
                nextPeriodStart = startDateTime
        return (nextPeriod, nextPeriodStart)

    def _fixClockDrift(self):
        """Lifted from https://github.com/sdague/proliphix/blob/master/proliphix/proliphix.py"""
        now = int(time.time())
        is_dst = time.localtime().tm_isdst
        set_now = now - time.timezone
        if is_dst == 1:
            now -= time.altzone
        else:
            now -= time.timezone
        drift = now - int(self._data.get('systemTimeSecs', now))

        if drift > 60:
            _LOGGER.warning("{} {} time drifted by {} seconds, resetting".format(self._siteName, self._deviceName, drift))
            self._device.set({"systemTimeSecs": set_now})

    def _setHoldDuration(self, hours):
        currentHoldDuration = int(self._holdDuration)
        if hours != currentHoldDuration:
            self._device.set({"thermHoldDuration": int(hours)})
            strCurrent = "indefinite" if currentHoldDuration == 0 else "{} hours".format(currentHoldDuration)
            strNew = "indefinite" if hours == 0 else "{} hours".format(hours)
            _LOGGER.info("{} {} hold duration changed from {} to {}".format(self._siteName, self._deviceName, strCurrent, strNew))

    def _getScheduleSummary(self):
        summary = ""
        setbackStatusLabel = THERM_SETBACK_STATUS_MAP.get(self._setbackStatus, "")

        if self._hvacMode == '1':   # Off
            return "Off"
        #elif self._isEcoModeOn():
        #    summary = "Eco mode"
        elif setbackStatusLabel == "Normal":
            summary = "{} - {} until {}".format(THERM_CURRENT_CLASS_MAP.get(self._currentClass),
                                                                   THERM_CURRENT_PERIOD_MAP.get(self._currentPeriod),
                                                                   self._relativeDateTime(self._getNextPeriodSchedule()[1]))
        elif setbackStatusLabel == "Hold":
            if int(self._holdDuration) == 0:
                summary = "Hold indefinitely"
            else:
                summary = "Hold until {}".format(self._relativeDateTime(self._holdUntil))
        elif setbackStatusLabel == "Override":
            summary = "Override {} - {} until {}".format(THERM_CURRENT_CLASS_MAP.get(self._currentClass),
                                                         THERM_CURRENT_PERIOD_MAP.get(self._currentPeriod),
                                                         self._relativeDateTime(self._getNextPeriodSchedule()[1]))
        return summary

    def _relativeDateTime(self, dt):
        if isinstance(dt, str):
            dt = dateutil.parser.parse(dt)
        dayString = ""
        if dt.date() == datetime.date.today():
            dayString = ""
        elif dt.date() == datetime.date.today() + datetime.timedelta(days=1):
            dayString ="tomorrow"
        elif dt.date() == datetime.date.today() + datetime.timedelta(days=-1):
            dayString = "yesterday"
        else:
            dayDiff = (dt.date() - datetime.date.today()).days
            if dayDiff > 0 and dayDiff < 7:
                dayString = dt.strftime("%A")
            elif dayDiff > 0 and dayDiff < -7:
                dayString = "Last {}".format(dt.strftime("%A"))
            else:
                dayString = dt.strftime("%b %d")
        if len(dayString) > 0:
            result = "{}, {}".format(dayString, dt.strftime("%I:%M%p").lstrip('0'))
        else:
            result = "{}".format(dt.strftime("%I:%M%p").lstrip('0'))
        return result.capitalize()

    def _getHoldUntil(self):
        holdUntil = None
        if THERM_SETBACK_STATUS_MAP.get(self._data.get("thermSetbackStatus")) == "Hold":
            # If hold was just enabled, compute a new 'until' datetime
            if self._data.get("thermSetbackStatus") != self._previousData.get("thermSetbackStatus"):
                if int(self._holdDuration) == 0:
                    holdUntil = "indefinitely"
                else:
                    holdUntil = datetime.datetime.now() + datetime.timedelta(hours=int(self._holdDuration))
        else:
            holdUntil = None
        return holdUntil

    def _isEcoModeOn(self):
        if self._configEcoModeEnabled:
            if int(self._setbackHeat)/10 == self._configEcoModeTemperature and \
            THERM_SETBACK_STATUS_MAP.get(self._setbackStatus, "") == "Hold" and \
            self._holdDuration == 0:
                return True
        else:
            return False

    def _turnOnEcoMode(self):
        # Heat with indefinite hold at eco temperature
        self._device.set({"thermHvacMode": "2", "thermHoldDuration": "0",
                          "thermSetbackStatus": "2",
                          "thermSetbackHeat": str(self._configEcoModeTemperature * 10)})