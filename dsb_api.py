"""API client for DSBmobile using the Web API."""
from __future__ import annotations

import logging
import re
from urllib.parse import urlsplit
import json
import gzip
import base64
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import aiohttp
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

LOGIN_URL = "https://www.dsbmobile.de/Login.aspx"
WEB_API_URL = "https://www.dsbmobile.de/jhw-1fd98248-440c-4283-bef6-dc82fe769b61.ashx/GetData"


@dataclass
class SubstitutionEntry:
    """A single substitution plan entry."""

    day: str
    art: str
    class_name: str
    lesson: str
    subject: str
    room: str
    vertr_von: str
    nach: str
    text: str
    raw_text: str
    teacher: str = ""


@dataclass
class PlanInfo:
    """Metadata about a plan."""

    title: str
    date: str
    url: str
    is_html: bool = False


class DSBMobileAPI:
    """Client for DSBmobile using the Web API."""

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession) -> None:
        self._username = username
        self._password = password
        self._session = session
        self._logged_in = False
        self.last_plans: list[PlanInfo] = []

    async def _web_login(self) -> bool:
        """Login via the web form to get session cookies."""
        try:
            async with self._session.get(LOGIN_URL) as resp:
                html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")
            vs = soup.find("input", {"name": "__VIEWSTATE"})
            vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
            ev = soup.find("input", {"name": "__EVENTVALIDATION"})

            if not vs or not ev:
                _LOGGER.error("Login page missing form fields")
                return False

            form = {
                "__VIEWSTATE": vs["value"],
                "__VIEWSTATEGENERATOR": vsg["value"] if vsg else "",
                "__EVENTVALIDATION": ev["value"],
                "txtUser": self._username,
                "txtPass": self._password,
                "ctl03": "Anmelden",
            }

            async with self._session.post(LOGIN_URL, data=form, allow_redirects=True) as resp:
                text = await resp.text()
                if "default.aspx" in str(resp.url) or "<title>DSBmobile</title>" in text:
                    _LOGGER.debug("Web login successful")
                    self._logged_in = True
                    return True
                _LOGGER.error("Web login failed — still on login page")
                return False

        except aiohttp.ClientError as err:
            _LOGGER.error("Web login error: %s", err)
            return False

    async def authenticate(self) -> bool:
        """Authenticate via web login + Web API call."""
        if not await self._web_login():
            return False

        # Test the API call
        data = await self._call_web_api()
        return data is not None and data.get("Resultcode") == 0

    async def _call_web_api(self) -> dict | None:
        """Retry a failed API request once with a fresh login."""
        for attempt in range(2):
            data = await self._call_web_api_once()
            if data is not None:
                return data
            self._logged_in = False
            if attempt == 0:
                _LOGGER.warning("DSBmobile fetch failed; retrying once with a fresh login")
        return None

    async def _call_web_api_once(self) -> dict | None:
        """Call the Web API GetData endpoint."""
        # Reuse the authenticated session; do not log in twice during setup.
        if not self._logged_in and not await self._web_login():
            return None

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        payload = {
            "UserId": self._username,
            "UserPw": self._password,
            "AppVersion": "2.3",
            "Language": "de",
            "OsVersion": "Mozilla/5.0",
            "AppId": str(uuid.uuid4()),
            "Device": "WebApp",
            "BundleId": "de.heinekingmedia.inhouse.dsbmobile.web",
            "Date": now,
            "LastUpdate": now,
            "PushId": "",
        }

        compressed = gzip.compress(json.dumps(payload).encode("utf-8"))
        encoded = base64.b64encode(compressed).decode("utf-8")
        body = {"req": {"Data": encoded, "DataType": 1}}

        try:
            async with self._session.post(
                WEB_API_URL,
                json=body,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Referer": "https://www.dsbmobile.de/default.aspx",
                },
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error("Web API returned status %s", resp.status)
                    return None

                result = await resp.json(content_type=None)
                resp_data = result.get("d", "")
                if not resp_data:
                    _LOGGER.error("Web API returned no data, session may have expired")
                    self._logged_in = False
                    return None

                decoded = gzip.decompress(base64.b64decode(resp_data))
                data = json.loads(decoded)

                if data.get("Resultcode") != 0:
                    _LOGGER.error("Web API error: %s", data.get("ResultStatusInfo"))
                    return None

                _LOGGER.debug("Web API call successful")
                return data

        except (aiohttp.ClientError, Exception) as err:
            _LOGGER.error("Web API call failed: %s", err)
            self._logged_in = False
            return None

    async def get_plans(self) -> list[PlanInfo]:
        """Extract plan URLs from the Web API response."""
        data = await self._call_web_api()
        if data is None:
            raise RuntimeError("DSBmobile API unavailable after login and retry")

        plans: list[PlanInfo] = []

        for menu in data.get("ResultMenuItems", []):
            for section in menu.get("Childs", []):
                method = section.get("MethodName", "")
                root = section.get("Root", {})

                _LOGGER.debug("Section: %s (method=%s)", section.get("Title"), method)

                for item in root.get("Childs", []):
                    title = item.get("Title", "")
                    date = item.get("Date", "")

                    for child in item.get("Childs", []):
                        detail = child.get("Detail", "")
                        if not detail:
                            continue

                        is_html = urlsplit(detail).path.lower().endswith((".htm", ".html"))
                        plans.append(PlanInfo(
                            title=child.get("Title", title),
                            date=date,
                            url=detail,
                            is_html=is_html,
                        ))
                        _LOGGER.debug(
                            "  Found: %s (html=%s) -> %s",
                            child.get("Title", ""), is_html, detail[:80],
                        )

        self.last_plans = plans
        _LOGGER.debug("Total plans found: %d", len(plans))
        return plans

    async def get_substitutions(self, class_filter: str = "") -> list[SubstitutionEntry]:
        """Fetch and parse HTML substitution plans."""
        plans = await self.get_plans()
        entries: list[SubstitutionEntry] = []

        for plan in plans:
            if not plan.is_html:
                _LOGGER.debug("Skipping non-HTML plan: %s -> %s", plan.title, plan.url[:60])
                continue

            try:
                async with self._session.get(plan.url) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"Substitution plan returned HTTP {resp.status}")

                    content_type = resp.headers.get("Content-Type", "")
                    if "image" in content_type:
                        _LOGGER.debug("Skipping image content: %s", plan.url)
                        plan.is_html = False
                        continue

                    # Pass bytes through so the parser can try UTF-8 before
                    # Windows-1252/Latin-1. This export has an incorrect UTF-8 meta tag.
                    html = await resp.read()
                    _LOGGER.debug("Fetched HTML plan: %s (%d bytes)", plan.title, len(html))

            except aiohttp.ClientError as err:
                raise RuntimeError("Failed to fetch substitution plan") from err

            entries.extend(self._parse_plan_html(html, class_filter))

        _LOGGER.debug("Total substitution entries: %d (filter='%s')", len(entries), class_filter)
        return entries

    @staticmethod
    def _parse_plan_html(html: str | bytes, class_filter: str = "") -> list[SubstitutionEntry]:
        """Parse column-based and class-grouped Untis tables.

        Only mon_list tables are data. Class-grouped exports put the class in
        an inline_header cell spanning the table, not in each substitution row.
        Field names are resolved from headers rather than fixed positions.
        day keeps the displayed date/day/week, without the page counter.
        """
        if isinstance(html, bytes):
            # Prefer strict UTF-8; Latin-1 would accept every byte sequence.
            # The supplied Untis pages declare UTF-8 but contain Latin-1 bytes.
            for encoding in ("utf-8-sig", "cp1252", "iso-8859-1"):
                try:
                    html = html.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
        soup = BeautifulSoup(html, "html.parser")
        results: list[SubstitutionEntry] = []
        aliases = {
            "art": "art", "vertretungsart": "art",
            "klasse": "class_name", "klassen": "class_name",
            "stunde": "lesson", "stunden": "lesson", "std": "lesson",
            "fach": "subject", "raum": "room", "räume": "room",
            "lehrer": "teacher", "le": "teacher",
            "vertrvon": "vertr_von", "vertretungvon": "vertr_von",
            "lenach": "nach", "nach": "nach",
            "text": "text", "vertretungstext": "text", "bemerkung": "text",
        }

        def header_key(cell):
            return re.sub(r"[^\w]", "", cell.get_text(" ", strip=True).casefold())

        tables = soup.select("table.mon_list")
        if not tables and soup.find("iframe"):
            _LOGGER.warning(
                "DSB wrapper contains iframe links, not plan rows. "
                "Fetch the linked subst_*.htm documents before parsing."
            )

        for table in tables:
            title = table.find_previous(class_="mon_title")
            current_day = " ".join(title.stripped_strings) if title else ""
            current_day = re.sub(
                r"\s*\(Seite\s+\d+\s*/\s*\d+\)\s*$", "", current_day,
                flags=re.IGNORECASE,
            ).strip()
            current_class = ""
            columns: dict[str, int] = {}
            width = 0

            for row in table.find_all("tr"):
                if row.find_parent("table") is not table:
                    continue
                cells = row.find_all(["th", "td"], recursive=False)
                if not cells:
                    continue

                # These rows carry context for all following data rows.
                if len(cells) == 1 and "inline_header" in cells[0].get("class", []):
                    current_class = cells[0].get_text(" ", strip=True)
                    continue

                mapped = {aliases[key]: i for i, cell in enumerate(cells)
                          if (key := header_key(cell)) in aliases}
                if "lesson" in mapped and "art" in mapped:
                    columns = mapped
                    width = len(cells)
                    continue
                if not columns:
                    continue
                if any(cell.name == "th" for cell in cells):
                    continue
                # Do not turn separator, note or malformed rows into entries.
                if len(cells) != width or any(
                    cell.get("colspan", "1") != "1" for cell in cells
                ):
                    continue

                values = {name: DSBMobileAPI._cell_text(cells[index])
                          for name, index in columns.items()}
                class_name = values.get("class_name", "") or current_class
                if class_filter and not DSBMobileAPI._matches_class(class_name, class_filter):
                    continue
                if not values.get("lesson"):
                    continue
                results.append(SubstitutionEntry(
                    day=current_day,
                    art=values.get("art", ""),
                    class_name=class_name,
                    lesson=values.get("lesson", ""),
                    subject=values.get("subject", ""),
                    room=values.get("room", ""),
                    vertr_von=values.get("vertr_von", ""),
                    nach=values.get("nach", ""),
                    text=values.get("text", ""),
                    raw_text=row.get_text(" ", strip=True),
                    teacher=values.get("teacher", ""),
                ))
        return results

    @staticmethod
    def _matches_class(class_name: str, class_filter: str) -> bool:
        """Match class names, not incidental text elsewhere in the row.

        Leading zeroes and case are ignored: 7g2 matches 07G2.
        Slash is preserved because Q1/2 is itself a class/group name.
        """
        def normalize(value):
            value = value.strip().casefold()
            return re.sub(r"^0+(?=\d)", "", value)

        wanted = normalize(class_filter)
        return wanted == normalize(class_name) or any(
            normalize(part) == wanted
            for part in re.split(r"[,;\s]+", class_name)
        )

    @staticmethod
    def _cell_text(cell) -> str:
        """Keep nested strikethrough as Markdown and normalize whitespace."""
        # Work on a copy so that raw_text and subsequent reads stay unchanged.
        copy = BeautifulSoup(str(cell), "html.parser")
        for tag in copy.find_all(["s", "strike", "del"]):
            if tag.parent is None:
                continue
            text = tag.get_text(" ", strip=True)
            tag.replace_with(f"~~{text}~~" if text else "")
        return " ".join(copy.get_text(" ", strip=True).split())
