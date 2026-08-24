"""Модуль содержит логику интеграции с VK API."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .const import LOGGER, VK_API_VERSION

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass(frozen=True)
class GetLongPollSettingsResult:
    """Результат вызова groups.getLongPollSettings."""

    is_enabled: bool
    events: dict[str, int]


@dataclass(frozen=True)
class GetGroupResult:
    """Результат вызова groups.getById."""

    id: int
    name: str


@dataclass
class GetLongPollServerResult:
    """Результат вызова groups.getLongPollServer."""

    key: str
    server: str
    ts: str


@dataclass(frozen=True)
class PollResponse:
    """Изменения в состоянии. Результат поллинга."""

    ts: str
    updates: list[Update]


@dataclass
class Update:
    """Метаданные изменений."""

    group_id: int
    type: str
    event_id: str
    v: str
    object: dict


class VkApiError(Exception):
    """Базовое исключение для ошибок VK API."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class VkBotApi:
    """Клиент для работы с VK API."""

    VK_API_HISTORY_OUTDATED_ERROR_CODE = 1
    VK_API_KEY_EXPIRED_ERROR_CODE = 2
    VK_API_SERVER_LOST_ERROR_CODE = 3

    def __init__(
        self,
        access_token: str,
        group_id: str,
        wait: int,
        session: ClientSession,
    ) -> None:
        self.access_token = access_token
        self.group_id = group_id
        self.wait = wait
        self.session = session
        self.server_info: GetLongPollServerResult | None = None

    async def async_get_long_poll_settings(self) -> GetLongPollSettingsResult:
        """Возвращает настройки бота для сообщества."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        body = {"v": VK_API_VERSION, "group_id": self.group_id}
        async with self.session.post(
            "https://api.vk.com/method/groups.getLongPollSettings",
            headers=headers,
            data=body,
        ) as response:
            data: dict = await response.json()

        if "error" in data:
            raise VkApiError(data["error"]["error_msg"])

        return GetLongPollSettingsResult(
            is_enabled=data["response"]["is_enabled"], events=data["response"]["events"]
        )

    async def async_poll(self) -> PollResponse:
        """Возвращает новые изменения - результат поллинга."""
        if not self.server_info:
            self.server_info = await self.__async_get_long_poll_server()

        async with self.session.get(
            f"{self.server_info.server}?act=a_check&key={self.server_info.key}&ts={self.server_info.ts}&wait={self.wait}"
        ) as response:
            data: dict = await response.json()

        if "failed" in data:
            fail_reason = data["failed"]
            if fail_reason == self.VK_API_HISTORY_OUTDATED_ERROR_CODE:
                """
                История событий устарела или была частично утеряна.
                Приложение может получать события, с новым значением ts из ответа.
                """
                self.server_info.ts = data["ts"]
                LOGGER.info("История устарела, повтор поллинга.")
                return await self.async_poll()

            if fail_reason in (
                self.VK_API_KEY_EXPIRED_ERROR_CODE,
                self.VK_API_SERVER_LOST_ERROR_CODE,
            ):
                """
                Истекло время действия ключа или информация утрачена.
                Нужно заново получить key и server методом groups.getLongPollServer.
                """
                self.server_info = await self.__async_get_long_poll_server()
                LOGGER.info("Ключ истек или информация утрачена, повтор поллинга.")
                return await self.async_poll()

        self.server_info.ts = data["ts"]
        updates = (
            Update(
                group_id=u["group_id"],
                type=u["type"],
                event_id=u["event_id"],
                v=u["v"],
                object=u["object"],
            )
            for u in data["updates"]
        )
        return PollResponse(ts=data["ts"], updates=list(updates))

    async def async_mark_as_read(self, peer_id: int) -> bool:
        """Отмечает диалог как прочитанный."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        body = {"v": VK_API_VERSION, "group_id": self.group_id, "peer_id": peer_id}
        async with self.session.post(
            "https://api.vk.com/method/messages.markAsRead",
            headers=headers,
            data=body,
        ) as response:
            data: dict = await response.json()

        if "error" in data:
            raise VkApiError(data["error"]["error_msg"])

        return data["response"] == 1

    async def __async_get_long_poll_server(self) -> GetLongPollServerResult:
        """Возвращает информацию о сервере для Long Poll."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        body = {"v": VK_API_VERSION, "group_id": self.group_id}
        async with self.session.post(
            "https://api.vk.com/method/groups.getLongPollServer",
            headers=headers,
            data=body,
        ) as response:
            data: dict = await response.json()

        if "error" in data:
            raise VkApiError(data["error"]["error_msg"])

        return GetLongPollServerResult(
            key=data["response"]["key"],
            server=data["response"]["server"],
            ts=data["response"]["ts"],
        )
