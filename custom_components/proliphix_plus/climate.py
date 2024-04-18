"""Climate for Proliphix."""

import logging

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_ON,
    PRESET_AWAY,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PRECISION_TENTHS, PRECISION_WHOLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ProliphixDataUpdateCoordinator, ProliphixEntity
from .const import (
    DOMAIN,
    FAN_SCHEDULE,
    PRESET_HOLD,
    PRESET_IN,
    PRESET_OUT,
    PRESET_OVERRIDE,
)
from .proliphix.const import (
    # Activity as PlxActivity,
    FanMode as PlxFanMode,
    HVACMode as PlxHVACMode,
    HVACState as PlxHVACState,
    ScheduleClass as PlxScheduleClass,
    SetbackStatus as PlxSetBackStatus,
    TemperatureScale as PlxTemperatureScale,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Proliphix climates from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([ProliphixClimate(coordinator)])


class ProliphixClimate(ProliphixEntity, ClimateEntity):
    """Representation of an Proliphix climate entity."""

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_precision = PRECISION_TENTHS
    _attr_temperature_step = PRECISION_WHOLE
    _attr_name = "Thermostat"

    def __init__(
        self,
        coordinator: ProliphixDataUpdateCoordinator,
    ) -> None:
        """Set up the instance."""
        super().__init__(coordinator)

    @property
    def supported_features(self):
        """Return the supported features."""
        features = ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.PRESET_MODE
        if self.proliphix.hvac_mode == PlxHVACMode.AUTO:
            features = features | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        elif self.proliphix.hvac_mode in [PlxHVACMode.HEAT, PlxHVACMode.COOL]:
            features = features | ClimateEntityFeature.TARGET_TEMPERATURE
        return features

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        scale = self.proliphix.temperature_scale
        if scale == PlxTemperatureScale.CELSIUS:
            unit = UnitOfTemperature.CELSIUS
        elif scale == PlxTemperatureScale.FARENHEIT:
            unit = UnitOfTemperature.FAHRENHEIT
        else:
            unit = None
        return unit

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self.proliphix.temperature_local

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        target = self.proliphix.temperature_local
        if self.proliphix.hvac_mode == PlxHVACMode.AUTO:
            if self.proliphix.hvac_state in [
                PlxHVACState.HEAT,
                PlxHVACState.HEAT_2,
                PlxHVACState.HEAT_3,
            ]:
                target = self.proliphix.setback_heat
            elif self.proliphix.hvac_state in [PlxHVACState.COOL, PlxHVACState.COOL_2]:
                target = self.proliphix.setback_cool

        if self.proliphix.hvac_mode == PlxHVACMode.HEAT:
            target = self.proliphix.setback_heat

        if self.proliphix.hvac_mode == PlxHVACMode.COOL:
            target = self.proliphix.setback_cool

        return target

    @property
    def target_temperature_high(self) -> float:
        """Return the high target temperature."""
        return self.proliphix.setback_cool

    @property
    def target_temperature_low(self) -> float:
        """Return the low target temperature."""
        return self.proliphix.setback_heat

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        raise NotImplementedError
        # if self.proliphix.hvac_mode == PlxHVACMode.HEAT:
        #     temperature = kwargs.get("temperature")
        #     if temperature is not None:
        #         await self.proliphix.set_temperature(heat=temperature)
        # if "temperature" in kwargs:
        #     temperature = kwargs["temperature"]
        #     await self.proliphix.set_temperature(temperature=temperature)
        # elif "target_temp_low" in kwargs and "target_temp_high" in kwargs:
        #     temperature_heat = kwargs["target_temp_low"]
        #     temperature_cool = kwargs["target_temp_high"]
        #     await self.proliphix.set_temperature(
        #         temperature_heat=temperature_heat, temperature_cool=temperature_cool
        #     )

    @property
    def current_humidity(self) -> float:
        """Return the current humidity."""
        return self.proliphix.relative_humidity

    @property
    def hvac_action(self):
        """Return the current HVAC action."""
        action = None
        if self.proliphix.hvac_mode == PlxHVACMode.OFF:
            action = HVACAction.OFF
        elif self.proliphix.hvac_state in [
            PlxHVACState.INITIALIZING,
            PlxHVACState.OFF,
            PlxHVACState.DELAY,
            PlxHVACState.RESET_RELAYS,
        ]:
            action = HVACAction.IDLE
        elif self.proliphix.hvac_state in [
            PlxHVACState.HEAT,
            PlxHVACState.HEAT_2,
            PlxHVACState.HEAT_3,
        ]:
            action = HVACAction.HEATING
        elif self.proliphix.hvac_state == [PlxHVACState.COOL, PlxHVACState.COOL_2]:
            action = HVACAction.COOLING
        else:
            action = HVACAction.IDLE
        return action

    @property
    def hvac_modes(self):
        """Return the list of available HVAC operation modes."""
        return [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
            HVACMode.HEAT_COOL,
            HVACMode.FAN_ONLY,
        ]

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        mode_map = {
            PlxHVACMode.OFF: HVACMode.OFF,
            PlxHVACMode.HEAT: HVACMode.HEAT,
            PlxHVACMode.COOL: HVACMode.COOL,
            PlxHVACMode.AUTO: HVACMode.HEAT_COOL,
        }
        return mode_map.get(self.proliphix.hvac_mode, HVACMode.OFF)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        raise NotImplementedError
        # _LOGGER.debug("Set hvac mode: %s", hvac_mode)
        # mode_map = {
        #     HVACMode.OFF: InfHVACMode.OFF,
        #     HVACMode.HEAT: InfHVACMode.HEAT,
        #     HVACMode.COOL: InfHVACMode.COOL,
        #     HVACMode.HEAT_COOL: InfHVACMode.AUTO,
        #     HVACMode.FAN_ONLY: InfHVACMode.FAN_ONLY,
        # }
        # mode = mode_map.get(hvac_mode)
        # if mode is None:
        #     _LOGGER.error("Invalid hvac mode: %s", hvac_mode)
        # else:
        #     await self.proliphix.system.set_hvac_mode(mode)

    @property
    def fan_modes(self):
        """Return the list of available HVAC operation modes."""
        return [FAN_AUTO, FAN_ON, FAN_SCHEDULE]

    @property
    def fan_mode(self):
        """Return current fan mode."""
        mode_map = {
            PlxFanMode.AUTO: FAN_AUTO,
            PlxFanMode.ON: FAN_ON,
            PlxFanMode.SCHEDULE: FAN_SCHEDULE,
        }
        return mode_map.get(self.proliphix.fan_mode, PlxFanMode.AUTO)

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        raise NotImplementedError
        # _LOGGER.debug("Set fan mode: %s", fan_mode)
        # mode_map = {
        #     FAN_AUTO: InfFanMode.AUTO,
        #     FAN_HIGH: InfFanMode.HIGH,
        #     FAN_MEDIUM: InfFanMode.MEDIUM,
        #     FAN_LOW: InfFanMode.LOW,
        # }
        # mode = mode_map.get(fan_mode)
        # if mode is None:
        #     _LOGGER.error("Invalid fan mode: %s", fan_mode)
        # else:
        #     await self.proliphix.set_fan_mode(mode)

    @property
    def preset_modes(self) -> list:
        """Return available preset modes."""
        return [
            PRESET_IN,
            PRESET_OUT,
            PRESET_AWAY,
            PRESET_HOLD,
            PRESET_OVERRIDE,
        ]

    @property
    def preset_mode(self):
        """Return current preset mode."""
        mode = None
        if self.proliphix.setback_status == PlxSetBackStatus.NORMAL:
            if self.proliphix.current_class == PlxScheduleClass.IN:
                mode = PRESET_IN
            if self.proliphix.current_class == PlxScheduleClass.OUT:
                mode = PRESET_OUT
            if self.proliphix.current_class == PlxScheduleClass.AWAY:
                mode = PRESET_AWAY
        elif self.proliphix.setback_status == PlxSetBackStatus.HOLD:
            mode = PRESET_HOLD
        elif self.proliphix.setback_status == PlxSetBackStatus.OVERRIDE:
            mode = PRESET_OVERRIDE
        return mode

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        raise NotImplementedError
        # _LOGGER.debug("Set preset mode: %s", preset_mode)
        # if preset_mode == PRESET_SCHEDULE:
        #     # Remove all holds to restore the normal schedule
        #     await self.proliphix.set_hold_mode(mode=InfHoldMode.OFF)
        # elif preset_mode == PRESET_HOME:
        #     # Set to home until the next scheduled activity
        #     await self.proliphix.set_hold_mode(
        #         mode=InfHoldMode.UNTIL, activity=InfActivity.HOME
        #     )
        # elif preset_mode == PRESET_AWAY:
        #     # Set to away until the next scheduled activity
        #     await self.proliphix.set_hold_mode(
        #         mode=InfHoldMode.UNTIL, activity=InfActivity.AWAY
        #     )
        # elif preset_mode == PRESET_SLEEP:
        #     # Set to sleep until the next scheduled activity
        #     await self.proliphix.set_hold_mode(
        #         mode=InfHoldMode.UNTIL, activity=InfActivity.SLEEP
        #     )
        # elif preset_mode == PRESET_WAKE:
        #     # Set to wake until the next scheduled activity
        #     await self.proliphix.set_hold_mode(
        #         mode=InfHoldMode.UNTIL, activity=InfActivity.WAKE
        #     )
        # elif preset_mode == PRESET_HOLD:
        #     # Set to manual and hold indefinitely
        #     await self.proliphix.set_hold_mode(
        #         mode=InfHoldMode.INDEFINITE, activity=InfActivity.MANUAL
        #     )
        # elif preset_mode == PRESET_HOLD_UNTIL:
        #     # Set to manual and hold indefinitely
        #     await self.proliphix.set_hold_mode(
        #         mode=InfHoldMode.UNTIL, activity=InfActivity.MANUAL
        #     )
        # else:
        #     _LOGGER.error("Invalid preset mode: %s", preset_mode)

    async def async_set_hold_mode(self, mode, activity, until):
        """Set the hold mode."""
        raise NotImplementedError
        # hold_mode = next((m for m in InfHoldMode if m.value == mode), None)
        # hold_activity = next((a for a in InfActivity if a.value == activity), None)
        # today = self.system.local_time.replace(
        #     hour=0, minute=0, second=0, microsecond=0
        # )
        # hold_until = today + timedelta(seconds=until)
        # await self.proliphix.set_hold_mode(
        #     mode=hold_mode, activity=hold_activity, until=hold_until
        # )
