"""Constants for interacting with a Proliphix thermostat."""

from enum import Enum

MANUFACTURER = "Proliphix"


class OID(Enum):
    """Object ID."""

    # State Related Objects
    THERM_HVAC_MODE = "OID4.1.1"
    THERM_HVAC_STATE = "OID4.1.2"
    THERM_FAN_MODE = "OID4.1.3"
    THERM_FAN_STATE = "OID4.1.4"
    THERM_SETBACK_HEAT = "OID4.1.5"
    THERM_SETBACK_COOL = "OID4.1.6"
    THERM_CONFIG_HUMIDITY_COOL = "OID4.2.22"  # NT150 only
    THERM_SETBACK_STATUS = "OID4.1.9"
    THERM_CURRENT_PERIOD = "OID4.1.10"
    THERM_ACTIVE_PERIOD = "OID4.1.12"
    THERM_CURRENT_CLASS = "OID4.1.11"

    # Alarms
    COMMON_ALARM_STATUS_LOW_TEMP_ALARM = "OID1.13.2.1"
    COMMON_ALARM_STATUS_HIGH_TEMP_ALARM = "OID1.13.2.2"
    COMMON_ALARM_STATUS_FILTER_REMINDER = "OID1.13.2.3"
    COMMON_ALARM_STATUS_HIGH_HUMIDITY = "OID1.13.2.4"  # NT150 only
    THERM_CONFIG_LOW_TEMP_PENDING = "OID4.2.11"
    THERM_CONFIG_HIGH_TEMP_PENDING = "OID4.2.13"
    THERM_CONFIG_FILTER_REMINDER_PENDING = "OID4.2.9"
    THERM_CONFIG_HIGH_HUMIDITY_PENDING = "OID4.2.17"

    # Sensors
    THERM_SENSOR_CORRECTION_REMOTE_1 = "OID4.3.4.2"
    THERM_SENSOR_CORRECTION_REMOTE_2 = "OID4.3.4.3"
    THERM_SENSOR_NAME_REMOTE_1 = "OID4.3.5.2"
    THERM_SENSOR_NAME_REMOTE_2 = "OID4.3.5.3"
    THERM_SENSOR_STATE_LOCAL = "OID4.3.6.1"
    THERM_SENSOR_STATE_REMOTE_1 = "OID4.3.6.2"
    THERM_SENSOR_STATE_REMOTE_2 = "OID4.3.6.3"
    THERM_SENSOR_AVERAGE_LOCAL = "OID4.3.8.1"
    THERM_SENSOR_AVERAGE_REMOTE_1 = "OID4.3.8.2"
    THERM_SENSOR_AVERAGE_REMOTE_2 = "OID4.3.8.3"
    THERM_SENSOR_TYPE_REMOTE_1 = "OID4.3.9.2"
    THERM_SENSOR_TYPE_REMOTE_2 = "OID4.3.9.3"

    # Temperature Related Objects
    THERM_AVERAGE_TEMP = "OID4.1.13"
    THERM_SENSOR_TEMP_LOCAL = "OID4.3.2.1"
    THERM_SENSOR_TEMP_REMOTE_1 = "OID4.3.2.2"
    THERM_SENSOR_TEMP_REMOTE_2 = "OID4.3.2.3"
    THERM_RELATIVE_HUMIDITY = "OID4.1.14"

    # System Related Objects
    SYSTEM_UPTIME = "OID2.1.1"
    SYSTEM_TIME_SECS = "OID2.5.1"
    COMMON_DEV_NAME = "OID1.2"
    SYSTEM_MIM_MODEL_NUMBER = "OID2.7.1"

    # Schedule
    THERM_PERIOD_START_IN_PERIOD_1 = "OID4.4.1.3.1.1"
    THERM_PERIOD_START_IN_PERIOD_2 = "OID4.4.1.3.1.2"
    THERM_PERIOD_START_IN_PERIOD_3 = "OID4.4.1.3.1.3"
    THERM_PERIOD_START_IN_PERIOD_4 = "OID4.4.1.3.1.4"
    THERM_PERIOD_START_OUT_PERIOD_1 = "OID4.4.1.3.2.1"
    THERM_PERIOD_START_OUT_PERIOD_2 = "OID4.4.1.3.2.2"
    THERM_PERIOD_START_OUT_PERIOD_3 = "OID4.4.1.3.2.3"
    THERM_PERIOD_START_OUT_PERIOD_4 = "OID4.4.1.3.2.4"
    THERM_PERIOD_START_AWAY_PERIOD_1 = "OID4.4.1.3.3.1"
    THERM_PERIOD_START_AWAY_PERIOD_2 = "OID4.4.1.3.3.2"
    THERM_PERIOD_START_AWAY_PERIOD_3 = "OID4.4.1.3.3.3"
    THERM_PERIOD_START_AWAY_PERIOD_4 = "OID4.4.1.3.3.4"
    THERM_PERIOD_SETBACK_COOL_IN_PERIOD_1 = "OID4.4.1.5.1.1"
    THERM_PERIOD_SETBACK_COOL_IN_PERIOD_2 = "OID4.4.1.5.1.2"
    THERM_PERIOD_SETBACK_COOL_IN_PERIOD_3 = "OID4.4.1.5.1.3"
    THERM_PERIOD_SETBACK_COOL_IN_PERIOD_4 = "OID4.4.1.5.1.4"
    THERM_PERIOD_SETBACK_COOL_OUT_PERIOD_1 = "OID4.4.1.5.2.1"
    THERM_PERIOD_SETBACK_COOL_OUT_PERIOD_2 = "OID4.4.1.5.2.2"
    THERM_PERIOD_SETBACK_COOL_OUT_PERIOD_3 = "OID4.4.1.5.2.3"
    THERM_PERIOD_SETBACK_COOL_OUT_PERIOD_4 = "OID4.4.1.5.2.4"
    THERM_PERIOD_SETBACK_COOL_AWAY_PERIOD_1 = "OID4.4.1.5.3.1"
    THERM_PERIOD_SETBACK_COOL_AWAY_PERIOD_2 = "OID4.4.1.5.3.2"
    THERM_PERIOD_SETBACK_COOL_AWAY_PERIOD_3 = "OID4.4.1.5.3.3"
    THERM_PERIOD_SETBACK_COOL_AWAY_PERIOD_4 = "OID4.4.1.5.3.4"
    THERM_PERIOD_SETBACK_HEAT_IN_PERIOD_1 = "OID4.4.1.4.1.1"
    THERM_PERIOD_SETBACK_HEAT_IN_PERIOD_2 = "OID4.4.1.4.1.2"
    THERM_PERIOD_SETBACK_HEAT_IN_PERIOD_3 = "OID4.4.1.4.1.3"
    THERM_PERIOD_SETBACK_HEAT_IN_PERIOD_4 = "OID4.4.1.4.1.4"
    THERM_PERIOD_SETBACK_HEAT_OUT_PERIOD_1 = "OID4.4.1.4.2.1"
    THERM_PERIOD_SETBACK_HEAT_OUT_PERIOD_2 = "OID4.4.1.4.2.2"
    THERM_PERIOD_SETBACK_HEAT_OUT_PERIOD_3 = "OID4.4.1.4.2.3"
    THERM_PERIOD_SETBACK_HEAT_OUT_PERIOD_4 = "OID4.4.1.4.2.4"
    THERM_PERIOD_SETBACK_HEAT_AWAY_PERIOD_1 = "OID4.4.1.4.3.1"
    THERM_PERIOD_SETBACK_HEAT_AWAY_PERIOD_2 = "OID4.4.1.4.3.2"
    THERM_PERIOD_SETBACK_HEAT_AWAY_PERIOD_3 = "OID4.4.1.4.3.3"
    THERM_PERIOD_SETBACK_HEAT_AWAY_PERIOD_4 = "OID4.4.1.4.3.4"
    THERM_PERIOD_SETBACK_FAN_IN_PERIOD_1 = "OID4.4.1.6.1.1"
    THERM_PERIOD_SETBACK_FAN_IN_PERIOD_2 = "OID4.4.1.6.1.2"
    THERM_PERIOD_SETBACK_FAN_IN_PERIOD_3 = "OID4.4.1.6.1.3"
    THERM_PERIOD_SETBACK_FAN_IN_PERIOD_4 = "OID4.4.1.6.1.4"
    THERM_PERIOD_SETBACK_FAN_OUT_PERIOD_1 = "OID4.4.1.6.2.1"
    THERM_PERIOD_SETBACK_FAN_OUT_PERIOD_2 = "OID4.4.1.6.2.2"
    THERM_PERIOD_SETBACK_FAN_OUT_PERIOD_3 = "OID4.4.1.6.2.3"
    THERM_PERIOD_SETBACK_FAN_OUT_PERIOD_4 = "OID4.4.1.6.2.4"
    THERM_PERIOD_SETBACK_FAN_AWAY_PERIOD_1 = "OID4.4.1.6.3.1"
    THERM_PERIOD_SETBACK_FAN_AWAY_PERIOD_2 = "OID4.4.1.6.3.2"
    THERM_PERIOD_SETBACK_FAN_AWAY_PERIOD_3 = "OID4.4.1.6.3.3"
    THERM_PERIOD_SETBACK_FAN_AWAY_PERIOD_4 = "OID4.4.1.6.3.4"
    THERM_DEFAULT_CLASS_ID_SUNDAY = "OID4.4.3.2.1"
    THERM_DEFAULT_CLASS_ID_MONDAY = "OID4.4.3.2.2"
    THERM_DEFAULT_CLASS_ID_TUESDAY = "OID4.4.3.2.3"
    THERM_DEFAULT_CLASS_ID_WEDNESDAY = "OID4.4.3.2.4"
    THERM_DEFAULT_CLASS_ID_THURSDAY = "OID4.4.3.2.5"
    THERM_DEFAULT_CLASS_ID_FRIDAY = "OID4.4.3.2.6"
    THERM_DEFAULT_CLASS_ID_SATURDAY = "OID4.4.3.2.7"

    # Special Days
    THERM_SCHEDULE_SPECIAL_INDEX_1 = "OID4.4.4.1.1"
    THERM_SCHEDULE_SPECIAL_START_DAY_1 = "OID4.4.4.2.1"
    THERM_SCHEDULE_SPECIAL_MONTH_1 = "OID4.4.4.3.1"
    THERM_SCHEDULE_SPECIAL_YEAR_1 = "OID4.4.4.4.1"
    THERM_SCHEDULE_SPECIAL_DURATION_1 = "OID4.4.4.5.1"
    THERM_SCHEDULE_SPECIAL_CLASS_1 = "OID4.4.4.6.1"
    THERM_SCHEDULE_SPECIAL_INDEX_2 = "OID4.4.4.1.2"
    THERM_SCHEDULE_SPECIAL_START_DAY_2 = "OID4.4.4.2.2"
    THERM_SCHEDULE_SPECIAL_MONTH_2 = "OID4.4.4.3.2"
    THERM_SCHEDULE_SPECIAL_YEAR_2 = "OID4.4.4.4.2"
    THERM_SCHEDULE_SPECIAL_DURATION_2 = "OID4.4.4.5.2"
    THERM_SCHEDULE_SPECIAL_CLASS_2 = "OID4.4.4.6.2"
    THERM_SCHEDULE_SPECIAL_INDEX_3 = "OID4.4.4.1.3"
    THERM_SCHEDULE_SPECIAL_START_DAY_3 = "OID4.4.4.2.3"
    THERM_SCHEDULE_SPECIAL_MONTH_3 = "OID4.4.4.3.3"
    THERM_SCHEDULE_SPECIAL_YEAR_3 = "OID4.4.4.4.3"
    THERM_SCHEDULE_SPECIAL_DURATION_3 = "OID4.4.4.5.3"
    THERM_SCHEDULE_SPECIAL_CLASS_3 = "OID4.4.4.6.3"
    THERM_SCHEDULE_SPECIAL_INDEX_4 = "OID4.4.4.1.4"
    THERM_SCHEDULE_SPECIAL_START_DAY_4 = "OID4.4.4.2.4"
    THERM_SCHEDULE_SPECIAL_MONTH_4 = "OID4.4.4.3.4"
    THERM_SCHEDULE_SPECIAL_YEAR_4 = "OID4.4.4.4.4"
    THERM_SCHEDULE_SPECIAL_DURATION_4 = "OID4.4.4.5.4"
    THERM_SCHEDULE_SPECIAL_CLASS_4 = "OID4.4.4.6.4"
    THERM_SCHEDULE_SPECIAL_INDEX_5 = "OID4.4.4.1.5"
    THERM_SCHEDULE_SPECIAL_START_DAY_5 = "OID4.4.4.2.5"
    THERM_SCHEDULE_SPECIAL_MONTH_5 = "OID4.4.4.3.5"
    THERM_SCHEDULE_SPECIAL_YEAR_5 = "OID4.4.4.4.5"
    THERM_SCHEDULE_SPECIAL_DURATION_5 = "OID4.4.4.5.5"
    THERM_SCHEDULE_SPECIAL_CLASS_5 = "OID4.4.4.6.5"
    THERM_SCHEDULE_SPECIAL_INDEX_6 = "OID4.4.4.1.6"
    THERM_SCHEDULE_SPECIAL_START_DAY_6 = "OID4.4.4.2.6"
    THERM_SCHEDULE_SPECIAL_MONTH_6 = "OID4.4.4.3.6"
    THERM_SCHEDULE_SPECIAL_YEAR_6 = "OID4.4.4.4.6"
    THERM_SCHEDULE_SPECIAL_DURATION_6 = "OID4.4.4.5.6"
    THERM_SCHEDULE_SPECIAL_CLASS_6 = "OID4.4.4.6.6"
    THERM_SCHEDULE_SPECIAL_INDEX_7 = "OID4.4.4.1.7"
    THERM_SCHEDULE_SPECIAL_START_DAY_7 = "OID4.4.4.2.7"
    THERM_SCHEDULE_SPECIAL_MONTH_7 = "OID4.4.4.3.7"
    THERM_SCHEDULE_SPECIAL_YEAR_7 = "OID4.4.4.4.7"
    THERM_SCHEDULE_SPECIAL_DURATION_7 = "OID4.4.4.5.7"
    THERM_SCHEDULE_SPECIAL_CLASS_7 = "OID4.4.4.6.7"
    THERM_SCHEDULE_SPECIAL_INDEX_8 = "OID4.4.4.1.8"
    THERM_SCHEDULE_SPECIAL_START_DAY_8 = "OID4.4.4.2.8"
    THERM_SCHEDULE_SPECIAL_MONTH_8 = "OID4.4.4.3.8"
    THERM_SCHEDULE_SPECIAL_YEAR_8 = "OID4.4.4.4.8"
    THERM_SCHEDULE_SPECIAL_DURATION_8 = "OID4.4.4.5.8"
    THERM_SCHEDULE_SPECIAL_CLASS_8 = "OID4.4.4.6.8"
    THERM_SCHEDULE_SPECIAL_INDEX_9 = "OID4.4.4.1.9"
    THERM_SCHEDULE_SPECIAL_START_DAY_9 = "OID4.4.4.2.9"
    THERM_SCHEDULE_SPECIAL_MONTH_9 = "OID4.4.4.3.9"
    THERM_SCHEDULE_SPECIAL_YEAR_9 = "OID4.4.4.4.9"
    THERM_SCHEDULE_SPECIAL_DURATION_9 = "OID4.4.4.5.9"
    THERM_SCHEDULE_SPECIAL_CLASS_9 = "OID4.4.4.6.9"
    THERM_SCHEDULE_SPECIAL_INDEX_10 = "OID4.4.4.1.10"
    THERM_SCHEDULE_SPECIAL_START_DAY_10 = "OID4.4.4.2.10"
    THERM_SCHEDULE_SPECIAL_MONTH_10 = "OID4.4.4.3.10"
    THERM_SCHEDULE_SPECIAL_YEAR_10 = "OID4.4.4.4.10"
    THERM_SCHEDULE_SPECIAL_DURATION_10 = "OID4.4.4.5.10"
    THERM_SCHEDULE_SPECIAL_CLASS_10 = "OID4.4.4.6.10"
    THERM_SCHEDULE_SPECIAL_INDEX_11 = "OID4.4.4.1.11"
    THERM_SCHEDULE_SPECIAL_START_DAY_11 = "OID4.4.4.2.11"
    THERM_SCHEDULE_SPECIAL_MONTH_11 = "OID4.4.4.3.11"
    THERM_SCHEDULE_SPECIAL_YEAR_11 = "OID4.4.4.4.11"
    THERM_SCHEDULE_SPECIAL_DURATION_11 = "OID4.4.4.5.11"
    THERM_SCHEDULE_SPECIAL_CLASS_11 = "OID4.4.4.6.11"
    THERM_SCHEDULE_SPECIAL_INDEX_12 = "OID4.4.4.1.12"
    THERM_SCHEDULE_SPECIAL_START_DAY_12 = "OID4.4.4.2.12"
    THERM_SCHEDULE_SPECIAL_MONTH_12 = "OID4.4.4.3.12"
    THERM_SCHEDULE_SPECIAL_YEAR_12 = "OID4.4.4.4.12"
    THERM_SCHEDULE_SPECIAL_DURATION_12 = "OID4.4.4.5.12"
    THERM_SCHEDULE_SPECIAL_CLASS_12 = "OID4.4.4.6.12"
    THERM_SCHEDULE_SPECIAL_INDEX_13 = "OID4.4.4.1.13"
    THERM_SCHEDULE_SPECIAL_START_DAY_13 = "OID4.4.4.2.13"
    THERM_SCHEDULE_SPECIAL_MONTH_13 = "OID4.4.4.3.13"
    THERM_SCHEDULE_SPECIAL_YEAR_13 = "OID4.4.4.4.13"
    THERM_SCHEDULE_SPECIAL_DURATION_13 = "OID4.4.4.5.13"
    THERM_SCHEDULE_SPECIAL_CLASS_13 = "OID4.4.4.6.13"
    THERM_SCHEDULE_SPECIAL_INDEX_14 = "OID4.4.4.1.14"
    THERM_SCHEDULE_SPECIAL_START_DAY_14 = "OID4.4.4.2.14"
    THERM_SCHEDULE_SPECIAL_MONTH_14 = "OID4.4.4.3.14"
    THERM_SCHEDULE_SPECIAL_YEAR_14 = "OID4.4.4.4.14"
    THERM_SCHEDULE_SPECIAL_DURATION_14 = "OID4.4.4.5.14"
    THERM_SCHEDULE_SPECIAL_CLASS_14 = "OID4.4.4.6.14"
    THERM_SCHEDULE_SPECIAL_INDEX_15 = "OID4.4.4.1.15"
    THERM_SCHEDULE_SPECIAL_START_DAY_15 = "OID4.4.4.2.15"
    THERM_SCHEDULE_SPECIAL_MONTH_15 = "OID4.4.4.3.15"
    THERM_SCHEDULE_SPECIAL_YEAR_15 = "OID4.4.4.4.15"
    THERM_SCHEDULE_SPECIAL_DURATION_15 = "OID4.4.4.5.15"
    THERM_SCHEDULE_SPECIAL_CLASS_15 = "OID4.4.4.6.15"
    THERM_SCHEDULE_SPECIAL_INDEX_16 = "OID4.4.4.1.16"
    THERM_SCHEDULE_SPECIAL_START_DAY_16 = "OID4.4.4.2.16"
    THERM_SCHEDULE_SPECIAL_MONTH_16 = "OID4.4.4.3.16"
    THERM_SCHEDULE_SPECIAL_YEAR_16 = "OID4.4.4.4.16"
    THERM_SCHEDULE_SPECIAL_DURATION_16 = "OID4.4.4.5.16"
    THERM_SCHEDULE_SPECIAL_CLASS_16 = "OID4.4.4.6.16"
    THERM_SCHEDULE_SPECIAL_INDEX_17 = "OID4.4.4.1.17"
    THERM_SCHEDULE_SPECIAL_START_DAY_17 = "OID4.4.4.2.17"
    THERM_SCHEDULE_SPECIAL_MONTH_17 = "OID4.4.4.3.17"
    THERM_SCHEDULE_SPECIAL_YEAR_17 = "OID4.4.4.4.17"
    THERM_SCHEDULE_SPECIAL_DURATION_17 = "OID4.4.4.5.17"
    THERM_SCHEDULE_SPECIAL_CLASS_17 = "OID4.4.4.6.17"
    THERM_SCHEDULE_SPECIAL_INDEX_18 = "OID4.4.4.1.18"
    THERM_SCHEDULE_SPECIAL_START_DAY_18 = "OID4.4.4.2.18"
    THERM_SCHEDULE_SPECIAL_MONTH_18 = "OID4.4.4.3.18"
    THERM_SCHEDULE_SPECIAL_YEAR_18 = "OID4.4.4.4.18"
    THERM_SCHEDULE_SPECIAL_DURATION_18 = "OID4.4.4.5.18"
    THERM_SCHEDULE_SPECIAL_CLASS_18 = "OID4.4.4.6.18"
    THERM_SCHEDULE_SPECIAL_INDEX_19 = "OID4.4.4.1.19"
    THERM_SCHEDULE_SPECIAL_START_DAY_19 = "OID4.4.4.2.19"
    THERM_SCHEDULE_SPECIAL_MONTH_19 = "OID4.4.4.3.19"
    THERM_SCHEDULE_SPECIAL_YEAR_19 = "OID4.4.4.4.19"
    THERM_SCHEDULE_SPECIAL_DURATION_19 = "OID4.4.4.5.19"
    THERM_SCHEDULE_SPECIAL_CLASS_19 = "OID4.4.4.6.19"
    THERM_SCHEDULE_SPECIAL_INDEX_20 = "OID4.4.4.1.20"
    THERM_SCHEDULE_SPECIAL_START_DAY_20 = "OID4.4.4.2.20"
    THERM_SCHEDULE_SPECIAL_MONTH_20 = "OID4.4.4.3.20"
    THERM_SCHEDULE_SPECIAL_YEAR_20 = "OID4.4.4.4.20"
    THERM_SCHEDULE_SPECIAL_DURATION_20 = "OID4.4.4.5.20"
    THERM_SCHEDULE_SPECIAL_CLASS_20 = "OID4.4.4.6.20"

    # Usage Statistics
    THERM_HEAT_1_USAGE = "OID4.5.1"
    THERM_HEAT_2_USAGE = "OID4.5.2"
    THERM_COOL_1_USAGE = "OID4.5.3"
    THERM_COOL_2_USAGE = "OID4.5.4"
    THERM_FAN_USAGE = "OID4.5.5"
    THERM_LAST_USAGE_RESET = "OID4.5.6"
    THERM_EXTERNAL_USAGE = "OID4.5.7"
    THERM_USAGE_OPTIONS = "OID4.5.8"
    THERM_HEAT_3_USAGE = "OID4.5.9"

    # Reverse Engineeered Objects
    FIRMWARE_VERSION = "OID1.1"
    SERIAL_NUMBER = "OID1.8"
    DISPLAY_CONTRAST = "OID2.2.3"  # 20-40, steps of 2
    REMOTE_ACCESS_STATE = "OID1.10.1"
    REMOTE_SERVER_ADDRESS = "OID1.10.3"
    REMOTE_SERVER_PORT = "OID1.10.4"
    REMOTE_SERVER_INTERVAL = "OID1.10.5"  # 60-1440, steps of 60
    SITE_NAME = "OID1.10.9"
    THERM_HOLD_MODE = "OID4.1.8"
    TEMPERATURE_SCALE = "OID4.1.21"
    THERM_HOLD_DURATION = "OID4.1.22"

    @classmethod
    def get_by_val(cls, value):
        """Look up an OID by its value."""
        return cls._value2member_map_.get(value)


class HVACMode(Enum):
    """HVAC Mode."""

    OFF = "1"
    HEAT = "2"
    COOL = "3"
    AUTO = "4"


class HVACState(Enum):
    """HVAC State."""

    INITIALIZING = "1"
    OFF = "2"
    HEAT = "3"
    HEAT_2 = "4"
    HEAT_3 = "5"
    COOL = "6"
    COOL_2 = "7"
    DELAY = "8"
    RESET_RELAYS = "9"


class FanMode(Enum):
    """Fan Mode."""

    AUTO = "1"
    ON = "2"
    SCHEDULE = "3"


class FanState(Enum):
    """Fan State."""

    INIT = "0"
    OFF = "1"
    ON = "2"


class SetbackStatus(Enum):
    """Setback_Status."""

    NORMAL = "1"
    HOLD = "2"
    OVERRIDE = "3"
    UNKNOWN_1 = "4"
    UNKNOWN_2 = "5"
    UNKNOWN_3 = "6"
    UNKNOWN_4 = "7"


class CurrentPeriod(Enum):
    """Current Period."""

    MORNING = "1"
    DAY = "2"
    EVENING = "3"
    NIGHT = "4"


class ScheduleClass(Enum):
    """Combination of Current Class and Default Class."""

    IN = "1"
    OUT = "2"
    AWAY = "3"
    OTHER = "4"  # Only used by CurrentClass


class ActivePeriod(Enum):
    """Active Period."""

    MORNING = "1"
    DAY = "2"
    EVENING = "3"
    NIGHT = "4"
    HOLD = "5"
    OVERRIDE = "6"


class SensorState(Enum):
    """Sensor State."""

    NOT_PRESENT = "0"
    DISABLED = "1"
    ENABLED = "2"


class SensorAverage(Enum):
    """Sensor Average."""

    DISABLED = "1"
    ENABLED = "2"


class SensorType(Enum):
    """Sensor Type."""

    ANALOG = "1"
    THERMISTOR = "2"


class CommonAlarmStatus(Enum):
    """Commmon Alarm Status."""

    GREEN = "1"
    YELLOW = "2"
    RED = "3"


class AlarmPendingState(Enum):
    """Alarm Pending State."""

    NO = "1"
    YES = "2"
    CLEAR = "3"


class FanSetback(Enum):
    """Fan Setback."""

    DISABLE = "0"
    MINUTES_15 = "15"
    MINUTES_30 = "30"
    MINUTES_45 = "45"
    ON = "60"


class ThermUsageOption(Enum):
    """Therm Usage Option."""

    INCLUDE_HEAT = "1"
    EXCLUDE_HEAT = ""


class TemperatureScale(Enum):
    """Temperature Scale."""

    FARENHEIT = "1"
    CELSIUS = "2"
