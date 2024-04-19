"""The Proliphix integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN
from .proliphix.api import Proliphix

# PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR]
PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = 15
UPDATE_TIMEOUT = 30


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Proliphix from a config entry."""

    coordinator = ProliphixDataUpdateCoordinator(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_SSL],
    )
    try:
        await coordinator.connect()
    except Exception as ex:
        _LOGGER.error("Error connecting to Proliphix: %s", ex)
        raise ConfigEntryNotReady from ex

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class ProliphixDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for Proliphix."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, ssl: bool) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{host}:{port}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        session = async_get_clientsession(hass)
        self.proliphix: Proliphix = Proliphix(
            host=host, port=port, ssl=ssl, session=session
        )

    async def connect(self) -> None:
        """Connect to Proliphix."""
        await self.proliphix.connect()
        await self.proliphix.refresh_state()
        await self.proliphix.refresh_schedule()

    async def _async_update_data(self) -> None:
        """Fetch data from Proliphix."""
        try:
            await self.proliphix.refresh_state()
            await self.proliphix.refresh_schedule()
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout while communicating with API: {err}") from err


class ProliphixEntity(CoordinatorEntity[ProliphixDataUpdateCoordinator]):
    """Base class for Proliphix entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ProliphixDataUpdateCoordinator,
        **kwargs,
    ) -> None:
        """Init Proliphix entity."""
        self.proliphix = coordinator.proliphix
        super().__init__(coordinator)

    @property
    def unique_id(self) -> str:
        """Return the unique id."""
        return f"{self.proliphix.serial}_{self.name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""

        return DeviceInfo(
            identifiers={(DOMAIN, self.proliphix.serial)},
            serial_number=self.proliphix.serial,
            manufacturer=self.proliphix.manufacturer,
            model=self.proliphix.model,
            name=(
                self.proliphix.name if self.proliphix.name else self.proliphix.serial
            ),
            sw_version=self.proliphix.firmware,
            configuration_url=f"{self.proliphix.url}",
        )
