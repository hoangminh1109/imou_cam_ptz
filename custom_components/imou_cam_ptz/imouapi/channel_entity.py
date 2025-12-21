"""Classes for representing entities beloging to an Imou channel."""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Union

from .api import ImouAPIClient
from .const import (
    BUTTONS,
    ONLINE_STATUS,
    SENSORS,
    SELECTS,
)
from .exceptions import APIError, InvalidResponse, NotConnected

_LOGGER: logging.Logger = logging.getLogger(__package__)

class ImouEntity(ABC):
    """A representation of a sensor within an Imou Channel."""

    def __init__(
        self,
        api_client: ImouAPIClient,
        device_id: str,
        channel_id: str,
        sensor_type: str,
        sensor_param: str,
        sensor_description: str,
    ) -> None:
        """Initialize common parameters."""
        self.api_client = api_client
        self._device_id = device_id
        self._channel_id = channel_id
        self._sensor_param = sensor_param
        self._sensor_type = sensor_type
        self._description = sensor_description
        self._enabled = True
        self._updated = False
        self._device_instance = None
        self._attributes: Dict[str, str] = {}

    def get_device_id(self) -> str:
        """Get device id."""
        return self._device_id

    def get_channel_id(self) -> str:
        """Get channel id."""
        return self._channel_id

    def get_type(self) -> str:
        """Get type."""
        return self._sensor_type

    def get_name(self) -> str:
        """Get name."""
        return f"{self._sensor_type} {self._sensor_param}"

    def get_description(self) -> str:
        """Get description."""
        return self._description

    def set_enabled(self, value: bool) -> None:
        """Set enable."""
        self._enabled = value

    def is_enabled(self) -> bool:
        """If enabled."""
        return self._enabled

    def is_updated(self) -> bool:
        """If has been updated at least once."""
        return self._updated

    def set_device(self, device_instance) -> None:
        """Set the device instance this entity is belonging to."""
        self._device_instance = device_instance

    def get_attributes(self) -> dict:
        """Entity attributes."""
        return self._attributes

    async def _async_is_ready(self) -> bool:
        """Check if the sensor is fully ready."""
        # check if the sensor is enabled
        if not self._enabled:
            return False
        # wake up the device if a dormant device and sleeping
        if self._device_instance is not None:
            awake = await self._device_instance.async_wakeup()
            if awake:
                return True
            return False
        return True

    @abstractmethod
    async def async_update(self, **kwargs):
        """Update the entity."""


class ImouSensor(ImouEntity):
    """A representation of a sensor within an IMOU Device."""

    def __init__(
        self,
        api_client: ImouAPIClient,
        device_id: str,
        channel_id: str,
        sensor_type: str,
        sensor_param: str,
    ) -> None:
        """
        Initialize the instance.

        Parameters:
            api_client: an instance ofthe API client
            device_id: the device id
            device_name: the device name
            sensor_type: the sensor type from const SENSORS
        """
        super().__init__(api_client, device_id, channel_id, sensor_type, sensor_param, f"{SENSORS[sensor_type]} {sensor_param}")
        # keep track of the status of the sensor
        self._state = None

    async def async_update(self, **kwargs):
        """Update the entity."""
        if not await self._async_is_ready():
            return

        # status sensor
        if self._sensor_type == "status":
            # get the device and channel status
            device_data = await self.api_client.async_api_deviceOnline(self._device_id)
            if "onLine" not in device_data:
                raise InvalidResponse(f"onLine not found in {device_data}")
            if device_data["onLine"] in ONLINE_STATUS:
                channel_data = next((c for c in device_data["channels"] if c["channelId"] == self._channel_id), None)
                if channel_data is not None and channel_data["onLine"] in ONLINE_STATUS:
                    self._state = ONLINE_STATUS[channel_data["onLine"]]
                else:
                    self._state = ONLINE_STATUS["UNKNOWN"]
            else:
                self._state = ONLINE_STATUS["UNKNOWN"]

        _LOGGER.debug(
            "[%s] updating %s, value is %s",
            self.get_name(),
            self.get_description(),
            self._state,
        )
        if not self._updated:
            self._updated = True

    def get_state(self) -> Optional[str]:
        """Return the state."""
        return self._state

class ImouButton(ImouEntity):
    """A representation of a button within an IMOU Device."""

    def __init__(
        self,
        api_client: ImouAPIClient,
        device_id: str,
        channel_id: str,
        sensor_type: str,
        sensor_param: str,
    ) -> None:
        """
        Initialize the instance.

        Parameters:
            api_client: an instance ofthe API client
            device_id: the device id
            channel_name: the channel name
            sensor_type: the sensor type from const BUTTON
        """
        super().__init__(api_client, device_id, channel_id, sensor_type, sensor_param, f"{BUTTONS[sensor_type]} {sensor_param}")

    async def async_press(self) -> None:
        """Press action."""
        if not await self._async_is_ready():
            return

        if self._sensor_type == "restartDevice":
            # restart the device
            await self.api_client.async_api_restartDevice(self._device_id)

        elif self._sensor_type == "turnCollection":
            # turn to collection
            await self.api_client.async_api_turnCollection(self._device_id, self._channel_id, self._sensor_param)

        _LOGGER.debug(
            "[%s] pressed button %s",
            self.get_name(),
            self.get_description(),
        )
        if not self._updated:
            self._updated = True

    async def async_update(self, **kwargs):
        """Update the entity."""
        return


class ImouSelect(ImouEntity):
    """A representation of a select within an IMOU Device."""

    def __init__(
        self,
        api_client: ImouAPIClient,
        device_id: str,
        channel_id: str,
        sensor_type: str,
        sensor_param: str,
    ) -> None:
        """
        Initialize the instance.

        Parameters:
            api_client: an instance ofthe API client
            device_id: the device id
            device_name: the device name
            sensor_type: the sensor type from const SELECT
        """
        super().__init__(api_client, device_id, channel_id, sensor_type, sensor_param, f"{SELECTS[sensor_type]} {sensor_param}")
        # keep track of the status of the sensor
        self._current_option: Union[str, None] = None
        self._available_options: List[str] = []

    async def async_update(self, **kwargs):
        """Update the entity."""
        if not await self._async_is_ready():
            return

        if self._sensor_type == "turnCollection":
            # get collections
            favourites = await self.api_client.async_api_getCollection(self._device_id, self._channel_id)
            _LOGGER.debug(f"found {len(favourites["collections"])} collection points")
            collections = ["⬇ Select a point ⬇"] + [c["name"] for c in favourites["collections"]]

            self._available_options = collections
            self._current_option = self._available_options[0]
        _LOGGER.debug(
            "[%s] updating %s, value is %s %s",
            self.get_name(),
            self.get_description(),
            self._current_option,
            self._attributes,
        )
        if not self._updated:
            self._updated = True

    def get_current_option(self) -> Optional[str]:
        """Return the current option."""
        return self._current_option

    def get_available_options(self) -> List[str]:
        """Return the available options."""
        return self._available_options

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""

        if option == self._available_options[0]:
            return

        if not await self._async_is_ready():
            return

        _LOGGER.debug("[%s] %s setting to %s", self.get_name(), self.get_description(), option)
        if self._sensor_type == "turnCollection":
            await self.api_client.async_api_turnCollection(self._device_id, self._channel_id, option)
            # self._current_option = option
            self._current_option = self._available_options[0]
