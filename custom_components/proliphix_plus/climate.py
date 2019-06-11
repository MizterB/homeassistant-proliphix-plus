"""
Support for Proliphix  Thermostats.

This is a custom platform
"""
from homeassistant.components.climate import ClimateDevice, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    STATE_COOL, STATE_HEAT, STATE_IDLE, SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_HIGH, SUPPORT_TARGET_TEMPERATURE_LOW,
    SUPPORT_OPERATION_MODE,
    SUPPORT_AWAY_MODE, SUPPORT_HOLD_MODE, SUPPORT_FAN_MODE,
    STATE_AUTO, STATE_FAN_ONLY)
from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_PASSWORD, CONF_USERNAME, PRECISION_TENTHS, TEMP_FAHRENHEIT,
    ATTR_TEMPERATURE, STATE_ON, STATE_OFF)

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

'''
SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_TARGET_TEMPERATURE_HIGH | SUPPORT_TARGET_TEMPERATURE_LOW |
				 SUPPORT_AWAY_MODE | SUPPORT_HOLD_MODE | SUPPORT_FAN_MODE |
				 SUPPORT_OPERATION_MODE)
'''
SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE |
                 SUPPORT_AWAY_MODE | SUPPORT_HOLD_MODE | SUPPORT_FAN_MODE |
                 SUPPORT_OPERATION_MODE)

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

        # Initialize the object
        self.update()
        self._fixClockDrift()
        self._setHoldDuration(0)

    async def async_added_to_hass(self):
        """Handle all entity which are about to be added."""
        await super().async_added_to_hass()
        # Restore a saved state and process as needed
        restoredState = await self.async_get_last_state()
        self._restoreState(restoredState)

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._serial

    @property
    def supported_features(self):
        """Return the list of supported features."""
        supportFlags = SUPPORT_FLAGS
        if self._configAwayModeEnabled:
            supportFlags = (supportFlags | SUPPORT_AWAY_MODE)
        return supportFlags

    @property
    def should_poll(self):
        """Set up polling needed for thermostat."""
        return True

    def update(self):
        """Update the data from the thermostat."""

        # Use this to determine if something was set directly on the thermostat
        self._previousData = self._data

        self._data = self._device.get(OID_MAP)
        self._serial = self._data["serialNumber"]
        self._model = self._data["systemMimModelNumber"]
        self._deviceName = self._data["commonDevName"]
        self._siteName = self._data["siteName"]
        self._temperature = float(self._data["thermSensorTempLocal"])
        self._remoteSensorTemperature = self._data["thermSensorTempRemote1"]
        self._remoteSensorState = self._data["thermSensorStateRemote1"]
        self._hvacMode = self._data["thermHvacMode"]
        self._hvacState = self._data["thermHvacState"]
        self._fanMode = self._data["thermFanMode"]
        self._fanState = self._data["thermFanState"]
        self._setbackHeat = self._data["thermSetbackHeat"]
        self._setbackCool = self._data["thermSetbackCool"]
        self._setbackStatus = self._data["thermSetbackStatus"]
        self._currentPeriod = self._data["thermCurrentPeriod"]
        self._currentClass = self._data["thermCurrentClass"]
        self._relativeHumidity = float(self._data["thermRelativeHumidity"])
        self._holdDuration = int(self._data["thermHoldDuration"])
        self._classPeriodSchedule = {
            "In": {
                "Morning": self._computeScheduleDateTime(self._data["thermPeriodStartInMorning"]),
                "Day": self._computeScheduleDateTime(self._data["thermPeriodStartInDay"]),
                "Evening": self._computeScheduleDateTime(self._data["thermPeriodStartInEvening"]),
                "Night": self._computeScheduleDateTime(self._data["thermPeriodStartInNight"])
            },
            "Out": {
                "Morning": self._computeScheduleDateTime(self._data["thermPeriodStartOutMorning"]),
                "Day": self._computeScheduleDateTime(self._data["thermPeriodStartOutDay"]),
                "Evening": self._computeScheduleDateTime(self._data["thermPeriodStartOutEvening"]),
                "Night": self._computeScheduleDateTime(self._data["thermPeriodStartOutNight"])
            },
            "Away": {
                "Morning": self._computeScheduleDateTime(self._data["thermPeriodStartAwayMorning"]),
                "Day": self._computeScheduleDateTime(self._data["thermPeriodStartAwayDay"]),
                "Evening": self._computeScheduleDateTime(self._data["thermPeriodStartAwayEvening"]),
                "Night": self._computeScheduleDateTime(self._data["thermPeriodStartAwayNight"])
            }
        }
        self._nextPeriod, self._nextPeriodStart = self._getNextPeriodSchedule()
        self._holdUntil = self._getHoldUntil()
        self._scheduleSummary = self._getScheduleSummary()

    @property
    def name(self):
        """Return the name of the thermostat."""
        if self._siteName == "":
            return self._deviceName
        return "{}: {}".format(self._siteName, self._deviceName)

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_TENTHS

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        attributes = {
            "manufacturer": self._manufacturer,
            "serial": self._serial,
            "model": self._model,
            "device_name": self._deviceName,
            "site_name": self._siteName,
            "admin_url": "http://%s:%s/" % (self._device._hostname, self._device._port),
            "current_period": THERM_CURRENT_PERIOD_MAP[self._currentPeriod],
            "current_class": THERM_CURRENT_CLASS_MAP[self._currentClass],
            "hold_hours": self._holdDuration,
            "fan_state": THERM_FAN_STATE_MAP[self._fanMode],
            "setback_status": THERM_SETBACK_STATUS_MAP[self._setbackStatus],
            "next_period" : self._nextPeriod,
            "next_period_start" : self._nextPeriodStart,
            "hold_until": self._holdUntil,
            "schedule_summary": self._scheduleSummary
        }
        if self._model in ["NT150", "NT160"]:
            attributes["humidity"] = self._relativeHumidity
        if self._model not in ["NT10"]:
            attributes["remote_sensor_state"] = THERM_SENSOR_STATE_MAP[self._remoteSensorState]
            if THERM_SENSOR_STATE_MAP[self._remoteSensorState] == "Enabled":
                attributes["remote_sensor_temperature"] = float(self._remoteSensorTemperature) / 10
        return attributes

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_FAHRENHEIT

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return float(self._temperature) / 10

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if THERM_HVAC_MODE_MAP[self._hvacMode] == "Auto":
            hvacStateName = THERM_HVAC_STATE_MAP[self._hvacState]
            if hvacStateName.startswith("Cool"):
                return float(self._setbackCool) / 10
            elif hvacStateName.startswith("Heat"):
                return float(self._setbackHeat) / 10
            else:
                return None
        elif THERM_HVAC_MODE_MAP[self._hvacMode] == "Heat":
            return float(self._setbackHeat) / 10
        elif THERM_HVAC_MODE_MAP[self._hvacMode] == "Cool":
            return float(self._setbackCool) / 10
        return None

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        if THERM_HVAC_MODE_MAP[self._hvacMode] == "Auto":
            return float(self._setbackCool) / 10
        return None

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        if THERM_HVAC_MODE_MAP[self._hvacMode] == "Auto":
            return float(self._setbackHeat) / 10
        return None

    @property
    def current_humidity(self):
        """Return the current humidity."""
        if self._model in ["NT150", "NT160"]:
            return self._relativeHumidity
        return None

    @property
    def state(self):
        """Return the current state."""
        if THERM_HVAC_MODE_MAP[self._hvacMode] == "Off":
            return STATE_OFF

        hvacStateName = THERM_HVAC_STATE_MAP[self._hvacState]
        if hvacStateName.startswith("Heat"):
            return STATE_HEAT
        elif hvacStateName.startswith("Cool"):
            return STATE_COOL
        else:
            return STATE_IDLE

    @property
    def current_operation(self):
        """Return the current state of the thermostat."""
        if self._isEcoModeOn():
            return "eco"

        return THERM_HVAC_MODE_MAP[self._hvacMode].lower()

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        opmodes =  [op.lower() for op in list(THERM_HVAC_MODE_MAP.values())]

        if self._configEcoModeEnabled:
            opmodes.append("eco")

        return opmodes

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        if THERM_CURRENT_CLASS_MAP[self._currentClass] != "In":
            return True

    @property
    def current_hold_mode(self):
        """Return hold mode setting."""
        return THERM_SETBACK_STATUS_MAP[self._setbackStatus]

    @property
    def is_on(self):
        """Return true if the device is on."""
        return THERM_HVAC_MODE_MAP[self._hvacMode] != "Off"

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        return THERM_FAN_MODE_MAP[self._fanMode]

    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        return list(THERM_FAN_MODE_MAP.values())

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
        settings = {targetSetback: targetTemp}

        # Setting the temperature while Eco mode is on
        if self._isEcoModeOn():
            # Turn off hold - enable override (3)
            settings["thermSetbackStatus"] = "3"
        self._device.set(settings)

    def set_fan_mode(self, fan):
        """Set new fan mode."""
        for value, label in THERM_FAN_MODE_MAP.items():
            if label == fan:
                self._device.set({"4.1.3": value})

    def set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        if operation_mode == "eco":
            self._turnOnEcoMode()
            return

        # Enable selected mode & return to 'normal' status (no hold or override)
        for value, label in THERM_HVAC_MODE_MAP.items():
            if label.lower() == operation_mode:
                self._device.set({"thermHvacMode": value, "thermSetbackStatus": 1})

    def turn_away_mode_on(self):
        """Turn away mode on by setting the default weekly schedule for each day to OUT."""
        self._device.set(
            {"4.4.3.2.1": "2", "4.4.3.2.2": "2", "4.4.3.2.3": "2", "4.4.3.2.4": "2", "4.4.3.2.5": "2", "4.4.3.2.6": "2",
             "4.4.3.2.7": "2"})
        time.sleep(1)   # Allow time for change to process, then force update
        self.update()

    def turn_away_mode_off(self):
        """Turn away mode off by setting the default weekly schedule for each day to IN."""
        self._device.set(
            {"4.4.3.2.1": "1", "4.4.3.2.2": "1", "4.4.3.2.3": "1", "4.4.3.2.4": "1", "4.4.3.2.5": "1", "4.4.3.2.6": "1",
             "4.4.3.2.7": "1"})
        time.sleep(1)   # Allow time for change to process, then force update
        self.update()

    def set_hold_mode(self, hold):
        """Update hold mode."""
        # TODO: this can be enhanced
        for value, label in THERM_SETBACK_STATUS_MAP.items():
            if label == hold:
                self._device.set({"thermSetbackStatus": value, "thermHoldDuration": "0"})

    def _restoreState(self, restoredState):
        '''
        Use this to restore custom computed attributes, such as holdUntil, scheduleSummary
        :param restoredState:
        :return:
        '''
        if not restoredState:
            return

        pass

    def _computeScheduleDateTime(self, minsAfterMidnight=0):
        minsAfterMidnight = int(minsAfterMidnight)
        result = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            minutes=minsAfterMidnight)
        # If the time is in the past, result should be same time tomorrow
        if result < datetime.datetime.now():
            result = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
                days=1, minutes=minsAfterMidnight)
        return result

    def _getNextPeriodSchedule(self):
        currentClass = THERM_CURRENT_CLASS_MAP[self._currentClass]
        nextPeriod = "Unknown"
        nextPeriodStart = datetime.datetime.max
        for period, startDateTime in self._classPeriodSchedule[currentClass].items():
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
        drift = now - int(self._data['systemTimeSecs'])

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

        if self.is_on == False:
            return "Off"
        elif self._isEcoModeOn():
            summary = "Eco mode"
        elif setbackStatusLabel == "Normal":
            summary = "{} - {} until {}".format(THERM_CURRENT_CLASS_MAP[self._currentClass],
                                                                   THERM_CURRENT_PERIOD_MAP[self._currentPeriod],
                                                                   self._relativeDateTime(self._getNextPeriodSchedule()[1]))
        elif setbackStatusLabel == "Hold":
            if int(self._holdDuration) == 0:
                summary = "Hold indefinitely"
            else:
                summary = "Hold until {}".format(self._relativeDateTime(self._holdUntil))
        elif setbackStatusLabel == "Override":
            summary = "Override {} - {} until {}".format(THERM_CURRENT_CLASS_MAP[self._currentClass],
                                                         THERM_CURRENT_PERIOD_MAP[self._currentPeriod],
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
        if THERM_SETBACK_STATUS_MAP[self._data["thermSetbackStatus"]] == "Hold":
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