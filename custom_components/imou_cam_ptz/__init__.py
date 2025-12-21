"""
Custom integration to integrate Imou PTZ Camera with Home Assistant.

For more details about this integration, please refer to
https://github.com/hoangminh1109/imou_cam_ptz
"""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from .imouapi.api import ImouAPIClient
from .imouapi.channel import ImouCamChannel
from .imouapi.exceptions import ImouException

from .const import (
    CONF_API_URL,
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_DEVICE_ID,
    CONF_CHANNEL_ID,
    CONF_CHANNEL_NAME,
    DEFAULT_API_URL,
    DOMAIN,
    OPTION_API_TIMEOUT,
    OPTION_API_URL,
    OPTION_CAMERA_WAIT_BEFORE_DOWNLOAD,
    OPTION_WAIT_AFTER_WAKE_UP,
    OPTION_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS
)
from .coordinator import ImouDataUpdateCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
    session = async_get_clientsession(hass)

    # retrieve the configuration entry parameters
    _LOGGER.debug("Loading entry %s", entry.entry_id)
    name = entry.data.get(CONF_CHANNEL_NAME)
    api_url = entry.data.get(CONF_API_URL)
    app_id = entry.data.get(CONF_APP_ID)
    app_secret = entry.data.get(CONF_APP_SECRET)
    device_id = entry.data.get(CONF_DEVICE_ID)
    channel_id = entry.data.get(CONF_CHANNEL_ID)
    _LOGGER.debug("Setting up device %s (%s)", name, device_id)

    # create an imou api client instance
    api_client = ImouAPIClient(api_url, app_id, app_secret, session)
    timeout = entry.options.get(OPTION_API_TIMEOUT, None)
    if isinstance(timeout, str):
        timeout = None if timeout == "" else int(timeout)
    if timeout is not None:
        _LOGGER.debug("Setting API timeout to %d", timeout)
        api_client.set_timeout(timeout)

    # create an imou device instance
    channel = ImouCamChannel(api_client, device_id, channel_id)
    if name is not None:
        channel.set_name(name)
    camera_wait_before_download = entry.options.get(
        OPTION_CAMERA_WAIT_BEFORE_DOWNLOAD, None
    )
    if camera_wait_before_download is not None:
        _LOGGER.debug(
            "Setting camera wait before download to %f", camera_wait_before_download
        )
        channel.set_camera_wait_before_download(camera_wait_before_download)
    wait_after_wakeup = entry.options.get(OPTION_WAIT_AFTER_WAKE_UP, None)
    if wait_after_wakeup is not None:
        _LOGGER.debug("Setting wait after wakeup to %f", wait_after_wakeup)
        channel.set_wait_after_wakeup(wait_after_wakeup)

    # initialize the device so to discover all the sensors
    try:
        await channel.async_initialize()
    except ImouException as exception:
        _LOGGER.error(exception.to_string())
        raise ImouException() from exception
    # at this time, all sensors must be disabled (will be enabled individually by async_added_to_hass())
    for sensor_instance in channel.get_all_sensors():
        sensor_instance.set_enabled(False)

    # create a coordinator
    coordinator = ImouDataUpdateCoordinator(
        hass, channel, entry.options.get(OPTION_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    # fetch the data
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    # store the coordinator so to be accessible by each platform
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # for each enabled platform, forward the configuration entry for its setup
    for platform in PLATFORMS:
        coordinator.platforms.append(platform)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    _LOGGER.debug("Unloading entry %s", entry.entry_id)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
