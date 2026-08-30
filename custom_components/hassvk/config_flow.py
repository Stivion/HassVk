"""Модуль содержит логику конфигурирования интеграции VK бота."""

from __future__ import annotations

import voluptuous as vol
from aiohttp import ClientResponseError
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import VkApiError, VkBotApi
from .const import (
    CONF_GROUP_ID,
    CONF_LONG_POLL_WAIT_SECONDS,
    CONF_LONG_POLL_WAIT_SECONDS_DEFAULT,
    DOMAIN,
    ERR_LONG_POLL_API_DISABLED,
    LOGGER,
)


class VkBotFlowHandler(ConfigFlow, domain=DOMAIN):
    """Конфигурация VK бота."""

    VERSION = 1
    MINOR_VERSION = 0

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> ConfigFlowResult:
        """Конфигурация из UI."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api = VkBotApi(
                user_input[CONF_ACCESS_TOKEN],
                user_input[CONF_GROUP_ID],
                user_input[CONF_LONG_POLL_WAIT_SECONDS],
                async_get_clientsession(self.hass),
            )

            try:
                long_poll_settings = await api.async_get_long_poll_settings()
                if not long_poll_settings.is_enabled:
                    errors["base"] = ERR_LONG_POLL_API_DISABLED
            except VkApiError as err:
                LOGGER.error(err)
                errors["base"] = err.message
            except ClientResponseError as err:
                LOGGER.error(err)
                errors["base"] = err.message

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        integration = async_get_loaded_integration(self.hass, DOMAIN)

        if integration.documentation is None:
            error_text = f"Integration {DOMAIN} has no documentation URL"
            raise RuntimeError(error_text)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, vol.UNDEFINED),
                    ): str,
                    vol.Required(
                        CONF_ACCESS_TOKEN,
                        default=(user_input or {}).get(
                            CONF_ACCESS_TOKEN, vol.UNDEFINED
                        ),
                    ): str,
                    vol.Required(
                        CONF_GROUP_ID,
                        default=(user_input or {}).get(CONF_GROUP_ID, vol.UNDEFINED),
                    ): str,
                    vol.Required(
                        CONF_LONG_POLL_WAIT_SECONDS,
                        default=(user_input or {}).get(
                            CONF_LONG_POLL_WAIT_SECONDS,
                            CONF_LONG_POLL_WAIT_SECONDS_DEFAULT,
                        ),
                    ): int,
                }
            ),
            description_placeholders={"documentation": integration.documentation},
            errors=errors,
        )
