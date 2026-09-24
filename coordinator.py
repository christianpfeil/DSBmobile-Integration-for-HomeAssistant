"""Shared data coordinator for sensors and calendars."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .dsb_api import DSBMobileAPI, SubstitutionEntry
_LOGGER = logging.getLogger(__name__)

class DSBDataUpdateCoordinator(DataUpdateCoordinator[list[SubstitutionEntry]]):
    """Coordinator to fetch ALL DSBmobile entries (unfiltered)."""

    def __init__(self, hass: HomeAssistant, api: DSBMobileAPI) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.data_stale = False
        self.last_successful_update: datetime | None = None
        self.last_error: str | None = None

    @property
    def freshness_attributes(self) -> dict:
        return {
            "data_stale": self.data_stale,
            "last_successful_update": (
                self.last_successful_update.isoformat()
                if self.last_successful_update else None
            ),
            "last_error": self.last_error,
        }

    async def _async_update_data(self) -> list[SubstitutionEntry]:
        """Fetch all substitution data without class filter."""
        previous_plans = list(self.api.last_plans)
        try:
            entries = await self.api.get_substitutions("")
            _LOGGER.debug("Fetched %d total substitution entries", len(entries))
            self.data_stale = False
            self.last_error = None
            self.last_successful_update = datetime.now(timezone.utc)
            return entries
        except Exception as err:
            _LOGGER.error("Error fetching DSBmobile data: %s", err)
            self.api.last_plans = previous_plans
            self.data_stale = True
            self.last_error = str(err)
            if self.data is not None:
                return self.data
            raise UpdateFailed(str(err)) from err


