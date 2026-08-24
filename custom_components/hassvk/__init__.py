"""
Интеграция ботов VK в Home Assistant.

Основная цель - получение сообщений из VK и отправки их как событий в Home Assistant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.hassvk.long_poll import VkBotLongPoll

from .api import VkBotApi
from .const import CONF_GROUP_ID, CONF_LONG_POLL_WAIT_SECONDS
from .data import VkBotConfigEntry, VkBotData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VkBotConfigEntry,
) -> bool:
    """Настройка интеграции через UI."""
    long_poll = VkBotLongPoll(hass, entry)
    entry.runtime_data = VkBotData(
        api=VkBotApi(
            access_token=entry.data[CONF_ACCESS_TOKEN],
            group_id=entry.data[CONF_GROUP_ID],
            wait=entry.data[CONF_LONG_POLL_WAIT_SECONDS],
            session=async_get_clientsession(hass),
        ),
        long_poll=long_poll,
    )

    await entry.runtime_data.long_poll.start_polling()

    return True


async def async_unload_entry(_: HomeAssistant, entry: VkBotConfigEntry) -> bool:
    """Остановка поллинга при выгрузке интеграции."""
    await entry.runtime_data.long_poll.stop_polling()
    return True
