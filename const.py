"""Constants for the DSBmobile integration."""

DOMAIN = "dsbmobile"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CLASS = "class_name"

DEFAULT_SCAN_INTERVAL = 1800  # 30 minutes

# Stable keys are used in entity IDs; labels match the school's Art column.
CONF_CALENDAR_TYPES = "calendar_types"
CALENDAR_TYPES = {
    "betreuung": "Betreuung",
    "vertretung": "Vertretung",
    "raum_vtr": "Raum-Vtr.",
    "entfall": "Entfall",
    "verlegung": "Verlegung",
}


def calendar_unique_id(entry_id: str, class_filter: str, art_key: str = "") -> str:
    """Keep existing total-calendar IDs unchanged."""
    base = f"{entry_id}_calendar_{class_filter or 'all'}"
    return f"{base}_art_{art_key}" if art_key else base
