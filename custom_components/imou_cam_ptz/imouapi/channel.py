"""High level API to discover and interacting with Imou camera channels and their sensors."""
import asyncio
import logging
import re
from typing import Any, Dict, List, Union
import pprint

from .api import ImouAPIClient
from .const import (
    WAIT_AFTER_WAKE_UP,
    CAMERA_WAIT_BEFORE_DOWNLOAD,
    ONLINE_STATUS,
    BUTTONS,
    SENSORS,
)
from .channel_entity import (
    ImouButton,
    ImouSensor,
    ImouEntity,
    ImouSelect
)

from .exceptions import InvalidResponse, ImouException

_LOGGER: logging.Logger = logging.getLogger(__package__)

class ImouCamChannel:
    """A abstraction of an IMOU Camera Chanel."""

    def __init__(
        self,
        api_client: ImouAPIClient,
        device_id: str,
        channel_id: str
    ) -> None:
        """
        Initialize the instance.

        Parameters:
            api_client: an ImouAPIClient instance
            device_id: device id
            channel_id: channel_id
        """
        self._api_client = api_client
        self._device_id = device_id
        self._channel_id = channel_id

        self._status = "unknown"
        self._channel_name = "N.A"
        self._device_name = "N.A"
        self._device_model = "N.A"

        self._full_name = "N.A"
        self._given_name = ""

        self._collections: list[dict] = []

        self._sensor_instances: Dict[str, list] = {
            "sensor": [],
            "button": [],
            "select": [],
        }

        self._initialized = False
        self._enabled = True
        self._sleepable = False
        self._wait_after_wakeup = WAIT_AFTER_WAKE_UP
        self._camera_wait_before_download = CAMERA_WAIT_BEFORE_DOWNLOAD

    def get_device_id(self) -> str:
        """Get device id."""
        return self._device_id

    def get_channel_id(self) -> str:
        """Get channel id."""
        return self._channel_id

    def get_model(self) -> str:
        """Get model."""
        return self._device_model

    def get_api_client(self) -> ImouAPIClient:
        """Get api client."""
        return self._api_client

    def get_name(self) -> str:
        """Get channel name."""
        if self._given_name != "":
            return self._given_name
        return self._full_name

    def set_name(self, given_name: str) -> None:
        """Set device name."""
        self._given_name = given_name

    def set_enabled(self, value: bool) -> None:
        """Set enable."""
        self._enabled = value

    def is_enabled(self) -> bool:
        """Is enabled."""
        return self._enabled

    def get_status(self) -> str:
        """Get status."""
        return self._status

    def is_online(self) -> bool:
        """Get online status."""
        return ONLINE_STATUS[self._status] == "Online" or ONLINE_STATUS[self._status] == "Dormant"

    def get_sleepable(self) -> bool:
        """Get sleepable."""
        return self._sleepable

    def set_wait_after_wakeup(self, value: float) -> None:
        """Set wait after wakeup."""
        self._wait_after_wakeup = value

    def get_wait_after_wakeup(self) -> float:
        """Get wait after wakeup."""
        return self._wait_after_wakeup

    def set_camera_wait_before_download(self, value: float) -> None:
        """Set camera wait before download."""
        self._camera_wait_before_download = value

    def get_camera_wait_before_download(self) -> float:
        """Get camera wait before download."""
        return self._camera_wait_before_download

    def get_all_sensors(self) -> List[ImouEntity]:
        """Get all the sensor instances."""
        sensors = []
        for (
            platform,  # pylint: disable=unused-variable
            sensor_instances_array,
        ) in self._sensor_instances.items():
            for sensor_instance in sensor_instances_array:
                sensors.append(sensor_instance)
        return sensors

    def get_sensors_by_platform(self, platform: str) -> List[ImouEntity]:
        """Get sensor instances associated to a given platform."""
        if platform not in self._sensor_instances:
            return []
        return self._sensor_instances[platform]

    def get_sensor_by_name(
        self, type:str, name: str
    ) -> Union[ImouSensor, ImouButton, ImouSelect, None]:
        """Get sensor instance with a given name."""
        for (
            platform,  # pylint: disable=unused-variable
            sensor_instances_array,
        ) in self._sensor_instances.items():
            for sensor_instance in sensor_instances_array:
                if sensor_instance.get_name() == type and sensor_instance.channel_name == name:
                    return sensor_instance
        return None


    def to_string(self) -> str:
        """Return the object as a string."""
        return f"{self._full_name} ({self._device_model}, serial {self._device_id}, channel {self._channel_id})"

    def _add_sensor_instance(self, platform, instance):
        """Add a sensor instance."""
        instance.set_device(self)
        self._sensor_instances[platform].append(instance)

    async def async_initialize(self) -> None:
        """Initialize the instance by retrieving the channel details and associated collections."""
        try:
            # get the details for this device from the API
            device_array = await self._api_client.async_api_deviceBaseDetailList([self._device_id])
            if "deviceList" not in device_array or len(device_array["deviceList"]) != 1:
                raise InvalidResponse(f"deviceList not found in {str(device_array)}")

            # reponse is an array, our data is in the first element
            device_data = device_array["deviceList"][0]

            self._device_name = device_data["name"]
            self._device_model = device_data["deviceModel"]

            # get channel details
            channel_data = next((c for c in device_data["channels"] if c["channelId"] == self._channel_id), None)
            if channel_data is None:
                raise InvalidResponse(f" invalid channel id {self._channel_id}")

            self._channel_name = channel_data["channelName"]
            self._full_name = f"{self._device_name} - {self._channel_name}"

            _LOGGER.debug("Retrieved channel: %s", self.to_string())

            # get collections of the channel
            favourites = await self._api_client.async_api_getCollection(self._device_id, self._channel_id)
            _LOGGER.debug(f"found {len(favourites["collections"])} collection points")
            self._collections = favourites["collections"]

            # add status sensor
            self._add_sensor_instance(
                "sensor",
                ImouSensor(
                    self._api_client,
                    self._device_id,
                    self._channel_id,
                    "status",
                    ""
                ),
            )

            # add restartDevice button
            self._add_sensor_instance(
                "button",
                ImouButton(
                    self._api_client,
                    self._device_id,
                    self._channel_id,
                    "restartDevice",
                    ""
                ),
            )
            # turn to collection point buttons
            for collection in self._collections:
                self._add_sensor_instance(
                    "button",
                    ImouButton(
                        self._api_client,
                        self._device_id,
                        self._channel_id,
                        "turnCollection",
                        collection["name"]
                    ),
                )
            # turn to collection point select
            self._add_sensor_instance(
                "select",
                ImouSelect(
                    self._api_client,
                    self._device_id,
                    self._channel_id,
                    "turnCollection",
                    ""
                ),
            )

        except ImouException as exception:
            _LOGGER.error(f"Exception: {exception.to_string()}")

        # keep track that we have already asked for the device details
        self._initialized = True

    async def async_refresh_status(self) -> None:
        """Refresh status attribute."""
        device_data = await self._api_client.async_api_deviceOnline(self._device_id)
        if "onLine" not in device_data or device_data["onLine"] not in ONLINE_STATUS:
            raise InvalidResponse(f"onLine not valid in {device_data}")

        channel_data = next((c for c in device_data["channels"] if c.get("channelId") == self._channel_id), None)
        if channel_data is None or "onLine" not in channel_data or channel_data["onLine"] not in ONLINE_STATUS:
            raise InvalidResponse(f"onLine not valid in {channel_data}")

        self._status = channel_data["onLine"]

    async def async_wakeup(self) -> bool:
        """Wake up a dormant device."""
        # if this is a regular device, just return
        if not self._sleepable:
            return True
        # if the device is already online, return
        await self.async_refresh_status()
        if ONLINE_STATUS[self._status] == "Online":
            return True
        # wake up the device
        _LOGGER.debug("[%s] waking up the dormant device", self.get_name())
        await self._api_client.async_api_setDeviceCameraStatus(self._device_id, "closeDormant", True)
        # wait for the device to be fully up
        await asyncio.sleep(self._wait_after_wakeup)
        # ensure the device is up
        await self.async_refresh_status()
        if ONLINE_STATUS[self._status] == "Online":
            _LOGGER.debug("[%s] device is now online", self.get_name())
            return True
        _LOGGER.warning("[%s] failed to wake up dormant device", self.get_name())
        return False

    async def async_get_data(self) -> bool:
        """Update device properties and its sensors."""
        if not self._enabled:
            return False
        if not self._initialized:
            # get the details of the device first
            await self.async_initialize()
        _LOGGER.debug("[%s] update requested", self.get_name())

        # check if the device is online
        await self.async_refresh_status()

        # update the status of all the sensors (if the device is online)
        # TO BE IMPLEMENTED

        return True

class ImouDiscoverService:
    """Class for discovering IMOU camera channels."""

    def __init__(self, api_client: ImouAPIClient) -> None:
        """
        Initialize the instance.

        Parameters:
            api_client: an ImouAPIClient instance
        """
        self._api_client = api_client

    async def async_discover_channels(self) -> dict:
        """Discover registered camera channels and return a dict device name -> device object."""
        _LOGGER.debug("Starting discovery")

        try:
            devices_data = await self._api_client.async_api_deviceBaseList()
            if "deviceList" not in devices_data or "count" not in devices_data:
                raise InvalidResponse(f"deviceList or count not found in {devices_data}")
            _LOGGER.debug("Discovered %d registered devices", devices_data["count"])

            channels = {}
            for device_data in devices_data["deviceList"]:
                # create a a device instance from the device id and initialize it
                # _LOGGER.debug("deviceId = %s", device_data["deviceId"])
                device_detailed_data_array = await self._api_client.async_api_deviceBaseDetailList([device_data["deviceId"]])
                if "deviceList" not in device_detailed_data_array or len(device_detailed_data_array["deviceList"]) != 1:
                    raise InvalidResponse(f"deviceList not found in {str(device_detailed_data_array)}")

                # reponse is an array, our data is in the first element
                device_detailed_data = device_detailed_data_array["deviceList"][0]
                # _LOGGER.debug("\n%s", pprint.pformat(device_detailed_data))

                # _LOGGER.debug(f"{len(device_detailed_data["channels"])} channels in device {device_data["deviceId"]}")
                for channel_data in device_detailed_data["channels"]:
                    # _LOGGER.debug("channelId = %s", channel_data["channelId"])
                    # _LOGGER.debug("\n%s", pprint.pformat(channel_data))

                    channel = ImouCamChannel(self._api_client, channel_data["deviceId"], channel_data["channelId"])
                    await channel.async_initialize()
                    channels[f"{channel.get_name()}"] = channel

                    # _LOGGER.debug(f"{channel.get_name()}")

        except InvalidResponse as exception:
            _LOGGER.warning("Skipping unrecognized or unsupported device: ", exception.to_string(),)

        except ImouException as exception:
            _LOGGER.error(f"Exception: {exception.to_string()}")

        # return a dict with channel full name -> channel instance
        return channels

