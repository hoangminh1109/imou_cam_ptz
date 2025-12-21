"""Binary sensor platform for Imou."""

from collections.abc import Callable
import logging

from homeassistant.components.button import ENTITY_ID_FORMAT, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import ImouEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)

# async def async_setup_entry(hass, entry, async_add_devices):
async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: Callable
):
    """Configure platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    channel = coordinator.channel
    sensors = []
    for sensor_instance in channel.get_sensors_by_platform("button"):
        sensor = ImouButton(coordinator, entry, sensor_instance, ENTITY_ID_FORMAT)
        sensors.append(sensor)
        coordinator.entities.append(sensor)
        _LOGGER.debug(
            "[%s] Adding button %s", channel.get_name(), sensor_instance.get_description()
        )
    async_add_devices(sensors)


class ImouButton(ImouEntity, ButtonEntity):
    """imou button class."""

    async def async_press(self) -> None:
        """Handle the button press."""
        # press the button
        await self.sensor_instance.async_press()
        _LOGGER.debug(
            "[%s] Pressed %s",
            self.channel.get_name(),
            self.sensor_instance.get_description(),
        )

    @property
    def device_class(self) -> str:
        """Device device class."""
        if self.sensor_instance.get_type() == "restartDevice":
            return "restart"
        return None
