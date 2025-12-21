"""Xonfig flow for Imou PTZ."""

import logging

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .imouapi.api import ImouAPIClient
from .imouapi.channel import ImouDiscoverService
from .imouapi.exceptions import ImouException
import voluptuous as vol

from .const import (
    CONF_API_URL,
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_DEVICE_ID,
    CONF_CHANNEL_ID,
    CONF_CHANNEL_NAME,
    CONF_DISCOVERED_CHANNEL,
    DEFAULT_API_URL,
    DOMAIN,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)

class ImouFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for imou_ptz."""

    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize."""
        self._api_url = None
        self._app_id = None
        self._app_secret = None
        self._api_client = None
        self._session = None
        self._discovered_channels = {}
        self._discover_service = None
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        return await self.async_step_login()

    # Step: login
    async def async_step_login(self, user_input=None):
        """Ask and validate app id and app secret."""
        self._errors = {}
        if user_input is not None:
            # create an imou discovery service
            self._session = async_create_clientsession(self.hass)
            self._api_client = ImouAPIClient(
                user_input[CONF_API_URL], user_input[CONF_APP_ID], user_input[CONF_APP_SECRET], self._session
            )
            self._discover_service = ImouDiscoverService(self._api_client)
            valid = False
            # check if the provided credentails are working
            try:
                await self._api_client.async_connect()
                valid = True
            except ImouException as exception:
                self._errors["base"] = exception.get_title()
                _LOGGER.error(exception.to_string())
            # valid credentials provided
            if valid:
                # store app id and secret for later steps
                self._api_url = user_input[CONF_API_URL]
                self._app_id = user_input[CONF_APP_ID]
                self._app_secret = user_input[CONF_APP_SECRET]
                return await self.async_step_discover()

        # by default show up the form
        return self.async_show_form(
            step_id="login",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
                    vol.Required(CONF_APP_ID, default = ""): str,
                    vol.Required(CONF_APP_SECRET, default = ""): str,
                }
            ),
            errors=self._errors,
        )

    # Step: discover

    async def async_step_discover(self, user_input=None):
        """Discover devices and ask the user to select one."""
        self._errors = {}
        if user_input is not None:
            # get the device instance from the selected input
            channel = self._discovered_channels[user_input[CONF_DISCOVERED_CHANNEL]]
            if channel is not None:
                # set the name
                name = (
                    f"{user_input[CONF_CHANNEL_NAME]}"
                    if CONF_CHANNEL_NAME in user_input
                    and user_input[CONF_CHANNEL_NAME] != ""
                    else channel.get_name()
                )
                # create the entry
                data = {
                    CONF_API_URL: self._api_url,
                    CONF_CHANNEL_NAME: name,
                    CONF_APP_ID: self._app_id,
                    CONF_APP_SECRET: self._app_secret,
                    CONF_DEVICE_ID: channel.get_device_id(),
                    CONF_CHANNEL_ID: channel.get_channel_id()
                }
                await self.async_set_unique_id(f"{channel.get_device_id()}-{channel.get_channel_id()}")
                return self.async_create_entry(title=name, data=data)

        # discover registered devices
        try:
            self._discovered_channels = await self._discover_service.async_discover_channels()
        except ImouException as exception:
            self._errors["base"] = exception.get_title()
            _LOGGER.error(exception.to_string())

        return self.async_show_form(
            step_id="discover",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DISCOVERED_CHANNEL): vol.In(
                        self._discovered_channels.keys()
                    ),
                    vol.Optional(CONF_CHANNEL_NAME): str,
                }
            ),
            errors=self._errors,
        )
