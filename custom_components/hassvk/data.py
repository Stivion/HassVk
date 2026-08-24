"""Типы данных для VK бота."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .api import VkBotApi
    from .long_poll import VkBotLongPoll


type VkBotConfigEntry = ConfigEntry[VkBotData]


@dataclass
class VkBotData:
    """Данные VK бота."""

    api: VkBotApi
    long_poll: VkBotLongPoll
