"""Константы."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "hassvk"
VK_API_VERSION = "5.199"
EVENT_NAME = "vk_event"

CONF_GROUP_ID = "group_id"
CONF_LONG_POLL_WAIT_SECONDS = "long_poll_wait_seconds"
CONF_LONG_POLL_WAIT_SECONDS_DEFAULT = 25

ERR_LONG_POLL_API_DISABLED = "long_poll_api_disabled"
