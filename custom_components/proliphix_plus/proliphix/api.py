"""Define a base client for interacting with a Proliphix thermostat."""

import asyncio
from datetime import UTC, datetime, timedelta
import logging
from urllib.parse import parse_qs, urlencode

from aiohttp import BasicAuth, ClientSession
from aiohttp.client_exceptions import ClientError

from .const import (
    MANUFACTURER,
    OID,
    CurrentPeriod,
    FanMode,
    FanState,
    HVACMode,
    HVACState,
    ScheduleClass,
    SetbackStatus,
    TemperatureScale,
)

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT: int = 30
UPDATE_TIMEOUT: int = 30


OIDS_CORE = [
    OID.SERIAL_NUMBER,
    OID.SYSTEM_MIM_MODEL_NUMBER,
    OID.FIRMWARE_VERSION,
    OID.COMMON_DEV_NAME,
    OID.SITE_NAME,
    OID.TEMPERATURE_SCALE,
]

OIDS_SCHEDULE = [
    OID.THERM_PERIOD_START_IN_PERIOD_1,
    OID.THERM_PERIOD_START_IN_PERIOD_2,
    OID.THERM_PERIOD_START_IN_PERIOD_3,
    OID.THERM_PERIOD_START_IN_PERIOD_4,
    OID.THERM_PERIOD_START_OUT_PERIOD_1,
    OID.THERM_PERIOD_START_OUT_PERIOD_2,
    OID.THERM_PERIOD_START_OUT_PERIOD_3,
    OID.THERM_PERIOD_START_OUT_PERIOD_4,
    OID.THERM_PERIOD_START_AWAY_PERIOD_1,
    OID.THERM_PERIOD_START_AWAY_PERIOD_2,
    OID.THERM_PERIOD_START_AWAY_PERIOD_3,
    OID.THERM_PERIOD_START_AWAY_PERIOD_4,
]

OIDS_STATE = [
    OID.SYSTEM_TIME_SECS,
    OID.THERM_SENSOR_TEMP_LOCAL,
    OID.THERM_SENSOR_TEMP_REMOTE_1,
    OID.THERM_SENSOR_TEMP_REMOTE_2,  # Added
    # OID.THERM_SENSOR_STATE_REMOTE_1,
    OID.THERM_HVAC_MODE,
    OID.THERM_HVAC_STATE,
    OID.THERM_FAN_MODE,
    OID.THERM_FAN_STATE,
    OID.THERM_SETBACK_HEAT,
    OID.THERM_SETBACK_COOL,
    OID.THERM_SETBACK_STATUS,
    OID.THERM_CURRENT_PERIOD,
    OID.THERM_CURRENT_CLASS,
    OID.THERM_RELATIVE_HUMIDITY,
    OID.THERM_HOLD_DURATION,
    OID.THERM_HOLD_MODE,
    OID.THERM_PERIOD_START_IN_PERIOD_1,
    OID.THERM_PERIOD_START_IN_PERIOD_2,
    OID.THERM_PERIOD_START_IN_PERIOD_3,
    OID.THERM_PERIOD_START_IN_PERIOD_4,
    OID.THERM_PERIOD_START_OUT_PERIOD_1,
    OID.THERM_PERIOD_START_OUT_PERIOD_2,
    OID.THERM_PERIOD_START_OUT_PERIOD_3,
    OID.THERM_PERIOD_START_OUT_PERIOD_4,
    OID.THERM_PERIOD_START_AWAY_PERIOD_1,
    OID.THERM_PERIOD_START_AWAY_PERIOD_2,
    OID.THERM_PERIOD_START_AWAY_PERIOD_3,
    OID.THERM_PERIOD_START_AWAY_PERIOD_4,
]


class Proliphix:
    """Object representing a Proliphix thermostat."""

    def __init__(
        self,
        host: str,
        port: int = 80,
        username: str = "admin",
        password: str = "admin",
        ssl: bool = False,
        *,
        session: ClientSession | None = None,
    ) -> None:
        """Initialize the Proliphix object."""
        self.host: str = host
        self.port: str = port
        self.username = username
        self.password = password
        self.ssl = ssl

        self._cache = {}
        self._change_callbacks = {}

        self._auth: BasicAuth = BasicAuth(self.username, self.password)
        self._session: ClientSession = session
        if not self._session or self._session.closed:
            self._session = ClientSession()

        self._hold_until = None
        self._schedule = None

        self._register_change_callback(
            [OID.THERM_SETBACK_STATUS, OID.THERM_HOLD_DURATION], self._update_hold_until
        )
        self._register_change_callback(
            [*OIDS_SCHEDULE, OID.SYSTEM_TIME_SECS], self._update_current_schedule
        )

    @property
    def url(self):
        """Get the base URL to connect to the thermostat."""
        protocol = "http"
        if self.ssl:
            protocol = "https"
        return f"{protocol}://{self.host}:{self.port}"

    async def _post(self, endpoint: str, data: dict, **kwargs) -> dict:
        """Make a POST request to the thermostat."""
        url = f"{self.url}{endpoint}"
        try:
            _LOGGER.debug("POST %s with %s and %s", url, data, kwargs)
            async with self._session.post(
                url, data=data, auth=self._auth, **kwargs
            ) as resp:
                resp_text = await resp.text()
                resp_dict = parse_qs(resp_text)
                _LOGGER.debug(
                    "POST RESPONSE from %s with %s and %s is: %s",
                    url,
                    data,
                    kwargs,
                    resp_text,
                )
                resp.raise_for_status()
                return resp_dict
        except ClientError as e:
            _LOGGER.error(e)

    def _register_change_callback(self, oids: OID | list[OID], callback) -> None:
        """Register a callback for a changed OID."""
        oids = oids if isinstance(oids, list) else [oids]
        for oid in oids:
            self._change_callbacks[oid] = callback

    def _process_response(self, response: dict) -> dict[OID, str]:
        """Map a get/set response back to OIDs."""
        resp = {}
        for oid_str, value in response.items():
            oid_obj = OID.get_by_val(oid_str)
            resp[oid_obj] = value[0] if value else ""
        return resp

    def _update_cache(self, oid_dict: dict) -> None:
        """Update the cache with OID data."""
        changes = {}
        for oid, new_value in oid_dict.items():
            if new_value != self._cache.get(oid):
                old_value = self._cache.get(oid)
                changes[oid] = [old_value, new_value]
        _LOGGER.debug("Updating cache with these changes: %s", changes)
        # First update all of the cache values
        for oid, change in changes.items():
            new_value = change[1]
            self._cache[oid] = new_value
        # Then call any change callbacks
        for oid, change in changes.items():
            if oid in self._change_callbacks:
                old_value = change[0]
                new_value = change[1]
                callback = self._change_callbacks[oid]
                callback(oid, old_value, new_value)

    async def get_oids(self, oids: OID | list[OID]) -> dict[OID, str]:
        """Get the values of OIDs."""
        oids = oids if isinstance(oids, list) else [oids]
        data = urlencode({k.value: None for k in oids})
        resp = await self._post("/get", data=data)
        resp = self._process_response(resp)
        self._update_cache(resp)
        return resp

    async def set_oids(self, oid_values: dict[OID, str]) -> dict[OID, str]:
        """Set the values of OIDs."""
        data = urlencode({k.value: v for k, v in oid_values.items()}) + "&submit=Submit"
        resp = await self._post("/pdp", data=data)
        resp = self._process_response(resp)
        self._update_cache(resp)
        return resp

    async def connect(self) -> None:
        """Connect to the thermostat."""
        try:
            async with asyncio.timeout(CONNECT_TIMEOUT):
                _LOGGER.debug("Connecting to Proliphix thermostat at %s", self.url)
                await self.get_oids(OIDS_CORE)
        except TimeoutError as e:
            _LOGGER.error(
                "Failed to connect to Proliphix thermostat at %s after %s seconds",
                self.url,
                CONNECT_TIMEOUT,
            )
            raise ConnectionError(e) from e

    async def refresh_state(self) -> None:
        """Update the themostat state attributes."""
        try:
            async with asyncio.timeout(CONNECT_TIMEOUT):
                _LOGGER.debug("Refreshing state attributes")
                await self.get_oids(OIDS_STATE)
        except TimeoutError as e:
            _LOGGER.error(
                "Failed to refresh state attributes after %s seconds",
                CONNECT_TIMEOUT,
            )
            raise ConnectionError(e) from e

    async def refresh_schedule(self) -> None:
        """Update the themostat schedule atributes."""
        try:
            async with asyncio.timeout(CONNECT_TIMEOUT):
                _LOGGER.debug("Refreshing schedule attributes")
                await self.get_oids(OIDS_SCHEDULE)
        except TimeoutError as e:
            _LOGGER.error(
                "Failed to refresh schedule attributes after %s seconds",
                CONNECT_TIMEOUT,
            )
            raise ConnectionError(e) from e

    @property
    def manufacturer(self) -> str | None:
        """Manufacturer name."""
        return MANUFACTURER

    @property
    def model(self) -> str | None:
        """Model name."""
        val = self._cache.get(OID.SYSTEM_MIM_MODEL_NUMBER)
        if not val:
            return None
        return str(val)

    @property
    def serial(self) -> str | None:
        """Serial number."""
        val = self._cache.get(OID.SERIAL_NUMBER)
        if not val:
            return None
        return str(val)

    @property
    def firmware(self) -> str | None:
        """Firmware version."""
        val = self._cache.get(OID.FIRMWARE_VERSION)
        if not val:
            return None
        return str(val)

    @property
    def name(self) -> str | None:
        """Device name."""
        val = self._cache.get(OID.COMMON_DEV_NAME)
        if not val:
            return None
        return str(val)

    @property
    def site_name(self) -> str | None:
        """Site name."""
        val = self._cache.get(OID.SITE_NAME)
        if not val:
            return None
        return str(val)

    @property
    def temperature_scale(self) -> TemperatureScale | None:
        """Temperature scale (units)."""
        val = self._cache.get(OID.TEMPERATURE_SCALE)
        if not val:
            return None
        return next((s for s in TemperatureScale if s.value == val), None)

    @property
    def system_time(self) -> datetime | None:
        """Current system time of the thermostat."""
        val = self._cache.get(OID.SYSTEM_TIME_SECS)
        if not val:
            return None
        # The system time is in local time, but without offset data
        systime = datetime.fromtimestamp(int(val), UTC)
        # Prevent value conversions by overrding the timezone to the correct local one
        local_tzinfo = datetime.now().astimezone().tzinfo
        return systime.replace(tzinfo=local_tzinfo)

    @property
    def temperature_local(self) -> float | None:
        """Local temperature of the thermostat."""
        val = self._cache.get(OID.THERM_SENSOR_TEMP_LOCAL)
        if not val:
            return None
        return float(val) / 10

    @property
    def temperature_remote_1(self) -> float | None:
        """Temperature of remote sensor 1."""
        val = self._cache.get(OID.THERM_SENSOR_TEMP_REMOTE_1)
        if not val or val == "FAILED5":
            return None
        return float(val) / 10

    @property
    def temperature_remote_2(self) -> float | None:
        """Temperature of remote sensor 2."""
        val = self._cache.get(OID.THERM_SENSOR_TEMP_REMOTE_2)
        if not val or val == "FAILED5":
            return None
        return float(val) / 10

    @property
    def hvac_mode(self) -> HVACMode | None:
        """HVAC mode of the thermostat."""
        val = self._cache.get(OID.THERM_HVAC_MODE)
        if not val:
            return None
        return next((m for m in HVACMode if m.value == val), None)

    @property
    def hvac_state(self) -> HVACState | None:
        """HVAC state of the thermostat."""
        val = self._cache.get(OID.THERM_HVAC_STATE)
        if not val:
            return None
        return next((s for s in HVACState if s.value == val), None)

    @property
    def fan_mode(self) -> FanMode | None:
        """Fan mode of the thermostat."""
        val = self._cache.get(OID.THERM_FAN_MODE)
        if not val:
            return None
        return next((m for m in FanMode if m.value == val), None)

    @property
    def fan_state(self) -> FanState | None:
        """Fan state of the thermostat."""
        val = self._cache.get(OID.THERM_FAN_STATE)
        if not val:
            return None
        return next((f for f in FanState if f.value == val), None)

    @property
    def setback_heat(self) -> float | None:
        """Target heating temperature."""
        val = self._cache.get(OID.THERM_SETBACK_HEAT)
        if not val:
            return None
        return float(val) / 10

    @property
    def setback_cool(self) -> float | None:
        """Target cooling temperature."""
        val = self._cache.get(OID.THERM_SETBACK_COOL)
        if not val:
            return None
        return float(val) / 10

    @property
    def setback_status(self) -> SetbackStatus | None:
        """Setback status (normal, hold, override)."""
        val = self._cache.get(OID.THERM_SETBACK_STATUS)
        if not val:
            return None
        return next((s for s in SetbackStatus if s.value == val), None)

    @property
    def current_period(self) -> CurrentPeriod | None:
        """Current schedule period."""
        val = self._cache.get(OID.THERM_CURRENT_PERIOD)
        if not val:
            return None
        return next((p for p in CurrentPeriod if p.value == val), None)

    @property
    def current_class(self) -> ScheduleClass | None:
        """Current schedule class (in, out, away)."""
        val = self._cache.get(OID.THERM_CURRENT_CLASS)
        if not val:
            return None
        return next((c for c in ScheduleClass if c.value == val), None)

    @property
    def relative_humidity(self) -> float | None:
        """Relative humidity at the thermostat."""
        if self.model != "NT150":
            return None
        val = self._cache.get(OID.THERM_RELATIVE_HUMIDITY)
        if not val:
            return None
        return float(val) / 10

    @property
    def hold_duration(self) -> int | None:
        """Hours to hold."""
        val = self._cache.get(OID.THERM_HOLD_DURATION)
        if not val:
            return None
        return int(val)

    @property
    def next_period(self) -> str | None:
        """Next period."""
        return self._next_period

    @property
    def next_period_start(self) -> str | None:
        """Next period start."""
        return self._next_period_start

    @property
    def hold_until(self) -> str | None:
        """Hold until datetime (computed property)."""
        return self._hold_until

    @property
    def current_schedule(self) -> str | None:
        """Current schedule (computed property)."""
        return self._current_schedule

    def _update_hold_until(self, oid: OID, from_val: str, to_val: str) -> None:
        """Update the hold until time."""
        _LOGGER.debug("Updating hold until time due to change in %s", oid)
        if self.setback_status == SetbackStatus.HOLD and self.hold_duration is not None:
            if self.hold_duration == 0:
                self._hold_until = datetime.max
            else:
                self._hold_until = self.system_time + timedelta(
                    hours=self.hold_duration
                )
        else:
            self._hold_until = None

    def _update_current_schedule(self, oid: OID, from_val: str, to_val: str) -> None:
        today = self.system_time.replace(hour=0, minute=0, second=0, microsecond=0)

        def get_dt(oid: OID) -> datetime:
            mins_after_midnight = int(self._cache.get(oid, 0))
            result = today + timedelta(minutes=mins_after_midnight)
            if result < self.system_time:
                result = today + timedelta(days=1, minutes=mins_after_midnight)
            return result

        current_schedule = {
            ScheduleClass.IN: {
                CurrentPeriod.MORNING: get_dt(OID.THERM_PERIOD_START_IN_PERIOD_1),
                CurrentPeriod.DAY: get_dt(OID.THERM_PERIOD_START_IN_PERIOD_2),
                CurrentPeriod.EVENING: get_dt(OID.THERM_PERIOD_START_IN_PERIOD_3),
                CurrentPeriod.NIGHT: get_dt(OID.THERM_PERIOD_START_IN_PERIOD_4),
            },
            ScheduleClass.OUT: {
                CurrentPeriod.MORNING: get_dt(OID.THERM_PERIOD_START_OUT_PERIOD_1),
                CurrentPeriod.DAY: get_dt(OID.THERM_PERIOD_START_OUT_PERIOD_2),
                CurrentPeriod.EVENING: get_dt(OID.THERM_PERIOD_START_OUT_PERIOD_3),
                CurrentPeriod.NIGHT: get_dt(OID.THERM_PERIOD_START_OUT_PERIOD_4),
            },
            ScheduleClass.AWAY: {
                CurrentPeriod.MORNING: get_dt(OID.THERM_PERIOD_START_AWAY_PERIOD_1),
                CurrentPeriod.DAY: get_dt(OID.THERM_PERIOD_START_AWAY_PERIOD_2),
                CurrentPeriod.EVENING: get_dt(OID.THERM_PERIOD_START_AWAY_PERIOD_3),
                CurrentPeriod.NIGHT: get_dt(OID.THERM_PERIOD_START_AWAY_PERIOD_4),
            },
        }
        self._current_schedule = current_schedule

        next_period = None
        next_period_start = datetime.max.replace(tzinfo=UTC)
        for period, start in current_schedule[self.current_class].items():
            if start > self.system_time and start <= next_period_start:
                next_period = period
                next_period_start = start
        self._next_period = next_period
        self._next_period_start = next_period_start

    async def set_temperature(self, heat: float, cool: float) -> None:
        """Set the target heating and cooling temperatures."""
        temps = {}
        if heat:
            temps[OID.THERM_SETBACK_HEAT] = str(int(heat * 10))
        if cool:
            temps[OID.THERM_SETBACK_COOL] = str(int(cool * 10))
        await self.set_oids(temps)
