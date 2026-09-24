"""Read-only all-day calendars for the currently published substitution plan."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
import re
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (CONF_CLASS, DOMAIN, CONF_CALENDAR_TYPES, CALENDAR_TYPES, calendar_unique_id)
from .coordinator import DSBDataUpdateCoordinator
from .dsb_api import DSBMobileAPI


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Create total and optionally type-filtered calendars per configured class."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    classes = [c.strip() for c in entry.data.get(CONF_CLASS, "").split(",") if c.strip()]
    selected = entry.data.get(CONF_CALENDAR_TYPES, [])
    art_keys = [""] + [key for key in CALENDAR_TYPES if key in selected]
    calendars = [
        DSBVertretungsplanCalendar(coordinator, entry, cls, art_key)
        for cls in dict.fromkeys(classes or [""])
        for art_key in art_keys
    ]
    _LOGGER.debug("Calendar platform loaded: adding %d calendar(s)", len(calendars))
    async_add_entities(calendars)


def _plain(value: str) -> str:
    """Calendar text is plain text; label old values explicitly."""
    return re.sub(r"~~(.*?)~~", r"(bisher: \1)", value)


class DSBVertretungsplanCalendar(CoordinatorEntity[DSBDataUpdateCoordinator], CalendarEntity):
    """Expose the latest plan as all-day events, without inventing lesson times."""

    _attr_icon = "mdi:calendar-school"

    def __init__(self, coordinator, entry: ConfigEntry, class_filter: str, art_key: str = "") -> None:
        super().__init__(coordinator)
        self._class_filter = class_filter
        self._art_filter = CALENDAR_TYPES.get(art_key)
        self._attr_name = f"Vertretungsplan {class_filter}".strip()
        if self._art_filter:
            self._attr_name += f" – {self._art_filter}"
        self._attr_unique_id = calendar_unique_id(entry.entry_id, class_filter, art_key)

    @property
    def extra_state_attributes(self) -> dict:
        return self.coordinator.freshness_attributes

    def _events(self) -> list[CalendarEvent]:
        events = []
        seen = set()
        for entry in self.coordinator.data or []:
            if self._art_filter and " ".join((entry.art or "").split()).casefold() != self._art_filter.casefold():
                continue
            if self._class_filter and not DSBMobileAPI._matches_class(
                entry.class_name, self._class_filter
            ):
                continue
            match = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b", entry.day)
            if not match:
                continue
            try:
                day, month, year = map(int, match.groups())
                start = date(year, month, day)
            except ValueError:
                continue
            subject = _plain(entry.subject)
            summary = f"{entry.class_name}: {entry.art} – {entry.lesson}. Std."
            if subject:
                summary += f" · {subject}"
            fields = [
                ("Klasse", entry.class_name), ("Tag", entry.day),
                ("Art", entry.art), ("Stunde", entry.lesson),
                ("Fach", entry.subject), ("Lehrer", entry.teacher),
                ("Raum", entry.room), ("Vertr. von", entry.vertr_von),
                ("Nach", entry.nach), ("Hinweis", entry.text),
            ]
            description = "\n".join(f"{label}: {_plain(value)}" for label, value in fields if value)
            location = _plain(entry.room)
            key = (start, summary, description, location)
            if key in seen:
                continue
            seen.add(key)
            events.append(CalendarEvent(
                start=start, end=start + timedelta(days=1), summary=summary,
                description=description, location=location,
            ))
        return sorted(events, key=lambda event: (event.start, event.summary))

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next event, using the HA local date."""
        today = dt_util.now().date()
        return next((event for event in self._events() if event.end > today), None)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return overlapping events; both range boundaries are exclusive at edges."""
        return [
            event for event in self._events()
            if datetime.combine(event.end, time.min, tzinfo=start_date.tzinfo) > start_date
            and datetime.combine(event.start, time.min, tzinfo=start_date.tzinfo) < end_date
        ]
