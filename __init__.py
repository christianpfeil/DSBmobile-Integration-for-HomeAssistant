"""DSBmobile integration for Home Assistant."""
from __future__ import annotations

import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD
from .coordinator import DSBDataUpdateCoordinator
from .dsb_api import DSBMobileAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DSBmobile from a config entry."""
    _LOGGER.debug("DSBmobile calendar build 2: initializing sensor and calendar platforms")
    hass.data.setdefault(DOMAIN, {})
    session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar())
    api = DSBMobileAPI(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], session)
    coordinator = DSBDataUpdateCoordinator(hass, api)
    hass.data[DOMAIN][entry.entry_id] = {"session": session, "coordinator": coordinator}
    try:
        await coordinator.async_config_entry_first_refresh()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        await session.close()
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        # Close the aiohttp session
        session = entry_data.get("session")
        if session and not session.closed:
            await session.close()
    return unload_ok
