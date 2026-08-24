"""Модуль для фонового Long Poll."""

from typing import TYPE_CHECKING

from .const import DOMAIN, EVENT_PREFIX

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import VkBotConfigEntry


class VkBotLongPoll:
    """Логика фонового Long Poll для бота."""

    def __init__(self, hass: HomeAssistant, entry: VkBotConfigEntry) -> None:
        self.entry = entry
        self.hass = hass
        self.task = None

    async def start_polling(self) -> None:
        """Начинает фоновую задачу Long Poll."""
        if self.task is not None:
            return

        self.task = self.entry.async_create_background_task(
            self.hass, self.__start_polling(), f"{DOMAIN}_long_poll"
        )

    async def stop_polling(self) -> None:
        """Останавливает фоновую задачу Long Poll."""
        if self.task is not None:
            self.task.cancel()
            self.task = None

    async def __start_polling(self) -> None:
        while True:
            poll_results = await self.entry.runtime_data.api.async_poll()
            for upd in poll_results.updates:
                if upd.type == "message_new":
                    peer_id = upd.object["message"]["peer_id"]
                    await self.entry.runtime_data.api.async_mark_as_read(peer_id)

                self.hass.bus.async_fire(
                    f"{EVENT_PREFIX}_{upd.type}",
                    {"object": upd.object},
                )
