"""Coordinator for Pont Chaban-Delmas data."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, DOMAIN, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

TZ_PARIS = ZoneInfo("Europe/Paris")


def _parse_closure(record: dict) -> dict | None:
    """Parse a single API record into a closure dict with aware datetimes.

    Handles midnight crossing: if re_ouverture <= fermeture, re_ouverture is next day.
    """
    try:
        date_str = record["date_passage"]                          # "2026-04-11"
        close_str = record["fermeture_a_la_circulation"]           # "14:19"
        open_str = record["re_ouverture_a_la_circulation"]         # "15:42"

        close_dt = datetime.strptime(
            f"{date_str} {close_str}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=TZ_PARIS)

        open_dt = datetime.strptime(
            f"{date_str} {open_str}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=TZ_PARIS)

        # Handle midnight crossing (e.g. fermeture 23:00, réouverture 05:00)
        if open_dt <= close_dt:
            open_dt += timedelta(days=1)

        duration_minutes = int((open_dt - close_dt).total_seconds() / 60)

        return {
            "bateau": record.get("bateau", "Inconnu"),
            "close_dt": close_dt,
            "open_dt": open_dt,
            "duration_minutes": duration_minutes,
            "type_fermeture": record.get("type_de_fermeture", ""),
        }
    except (KeyError, ValueError) as err:
        _LOGGER.warning("Failed to parse closure record %s: %s", record, err)
        return None


class PontChabanCoordinator(DataUpdateCoordinator):
    """Fetches and processes Pont Chaban closure data."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from API and compute derived values."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    API_URL, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    resp.raise_for_status()
                    raw = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching Pont Chaban data: {err}") from err

        closures = [
            parsed
            for record in raw.get("results", [])
            if (parsed := _parse_closure(record)) is not None
        ]

        # Sort by closing datetime ascending (API should already return sorted)
        closures.sort(key=lambda c: c["close_dt"])

        now = datetime.now(TZ_PARIS)
        limit_24h = now + timedelta(hours=24)

        # Is the bridge currently closed?
        current_closure = next(
            (c for c in closures if c["close_dt"] <= now < c["open_dt"]), None
        )
        is_closed_now = current_closure is not None

        # Next closure starting strictly in the future (not currently happening)
        next_24h = next(
            (c for c in closures if now < c["close_dt"] < limit_24h), None
        )

        _LOGGER.debug(
            "Pont Chaban: %d closures loaded. Closed now: %s. Next 24h: %s.",
            len(closures),
            is_closed_now,
            next_24h["close_dt"].isoformat() if next_24h else None,
        )

        return {
            "closures": closures,
            "is_closed_now": is_closed_now,
            "current_closure": current_closure,
            "next_24h": next_24h,
        }
