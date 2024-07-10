"""Sensors for Proliphix."""

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import ProliphixDataUpdateCoordinator, ProliphixEntity
from .const import DOMAIN
from .proliphix.const import TemperatureScale

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProliphixSensorDescriptionMixin:
    """Mixin for Proliphix sensor."""

    value_fn: Callable[[ProliphixEntity], StateType]


@dataclass(frozen=True)
class ProliphixSensorDescription(
    SensorEntityDescription, ProliphixSensorDescriptionMixin
):
    """Class describing Proliphix sensor entities."""


SENSORS: tuple[ProliphixSensorDescription, ...] = (
    ProliphixSensorDescription(
        key="temperature_local",
        name="Temperature",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda entity: entity.proliphix.temperature_local,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Proliphix sensors from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        ProliphixSensorEntity(coordinator, entity_description)
        for entity_description in SENSORS
    ]
    async_add_entities(entities)


class ProliphixSensorEntity(ProliphixEntity, SensorEntity):
    """Representation of an Proliphix sensor."""

    entity_description: ProliphixSensorDescription

    def __init__(
        self,
        coordinator: ProliphixDataUpdateCoordinator,
        entity_description: ProliphixSensorDescription,
    ) -> None:
        """Set up the instance."""
        self.entity_description = entity_description
        super().__init__(coordinator)

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        return self.entity_description.value_fn(self)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the native unit of measurement."""
        unit = self.entity_description.native_unit_of_measurement
        if self.device_class == SensorDeviceClass.TEMPERATURE:
            if self.proliphix.temperature_scale == TemperatureScale.FARENHEIT:
                unit = UnitOfTemperature.FAHRENHEIT
            elif self.proliphix.temperature_scale == TemperatureScale.CELSIUS:
                unit = UnitOfTemperature.CELSIUS
        return unit
