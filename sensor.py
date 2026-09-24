"""Sensor platform for DSBmobile Vertretungsplan."""
from __future__ import annotations

import logging


from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN, CONF_CLASS
from .coordinator import DSBDataUpdateCoordinator
from .dsb_api import DSBMobileAPI, SubstitutionEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DSBmobile sensors from a config entry."""
    class_input = entry.data.get(CONF_CLASS, "")
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Parse comma-separated classes, create one sensor per class
    classes = [c.strip() for c in class_input.split(",") if c.strip()]

    sensors: list[DSBVertretungsplanSensor] = []
    if classes:
        for cls in classes:
            sensors.append(DSBVertretungsplanSensor(coordinator, entry, cls))
    else:
        # No filter — one sensor for all entries
        sensors.append(DSBVertretungsplanSensor(coordinator, entry, ""))

    async_add_entities(sensors)


class DSBVertretungsplanSensor(CoordinatorEntity[DSBDataUpdateCoordinator], SensorEntity):
    """Sensor showing substitution entries, optionally filtered by class."""

    _attr_icon = "mdi:school"

    def __init__(
        self,
        coordinator: DSBDataUpdateCoordinator,
        entry: ConfigEntry,
        class_filter: str,
    ) -> None:
        super().__init__(coordinator)
        self._class_filter = class_filter
        suffix = f" {class_filter}" if class_filter else ""
        self._attr_name = f"Vertretungsplan{suffix}"
        self._attr_unique_id = f"{entry.entry_id}_vertretungsplan_{class_filter or 'all'}"

    def _filtered_entries(self) -> list[SubstitutionEntry]:
        """Return entries filtered by this sensor's class."""
        if not self.coordinator.data:
            return []
        if not self._class_filter:
            return self.coordinator.data
        return [
            e for e in self.coordinator.data
            if DSBMobileAPI._matches_class(e.class_name, self._class_filter)
        ]

    @property
    def native_value(self) -> int:
        """Return the number of substitution entries."""
        return len(self._filtered_entries())

    @property
    def extra_state_attributes(self) -> dict:
        """Return detailed substitution entries as attributes."""
        filtered = self._filtered_entries()
        entries = [
            {
                "day": e.day,
                "art": e.art,
                "class": e.class_name,
                "lesson": e.lesson,
                "subject": e.subject,
                "teacher": e.teacher,
                "room": e.room,
                "vertr_von": e.vertr_von,
                "nach": e.nach,
                "text": e.text,
            }
            for e in filtered
        ]

        other_plans = [
            {"title": p.title, "date": p.date, "url": p.url}
            for p in self.coordinator.api.last_plans
            if not p.is_html
        ]

        return {
            **self.coordinator.freshness_attributes,
            "class_filter": self._class_filter,
            "count": len(entries),
            "entries": entries,
            "other_plans": other_plans,
        }
