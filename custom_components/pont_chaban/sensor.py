"""Sensors for Pont Chaban-Delmas."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PontChabanCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry (UI)."""
    coordinator: PontChabanCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PontFermeSensor(coordinator),
            ProchainesFermetureSensor(coordinator),
            BateauSensor(coordinator),
            DureeSensor(coordinator),
            ReouvertureSensor(coordinator),
        ],
        update_before_add=True,
    )


class _PontBase(CoordinatorEntity, SensorEntity):
    """Base class for all Pont Chaban sensors."""

    def __init__(self, coordinator: PontChabanCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def _data(self) -> dict:
        return self.coordinator.data or {}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "pont_chaban_delmas")},
            "name": "Pont Chaban-Delmas",
            "manufacturer": "Bordeaux Métropole",
            "model": "Prévisions de fermeture",
            "configuration_url": (
                "https://datahub.bordeaux-metropole.fr/explore/dataset/"
                "previsions_pont_chaban/table/"
            ),
        }


class PontFermeSensor(_PontBase):
    """Sensor: pont fermé en ce moment (Ouvert / Fermé)."""

    _attr_name = "Pont Chaban - État actuel"
    _attr_unique_id = "pont_chaban_ferme_now"
    _attr_icon = "mdi:bridge"

    @property
    def native_value(self) -> str:
        return "Fermé" if self._data.get("is_closed_now") else "Ouvert"

    @property
    def extra_state_attributes(self) -> dict:
        closure = self._data.get("current_closure")
        if closure:
            return {
                "bateau": closure["bateau"],
                "reouverture": closure["open_dt"].isoformat(),
                "duree_minutes": closure["duration_minutes"],
                "type_fermeture": closure["type_fermeture"],
            }
        return {}


class ProchainesFermetureSensor(_PontBase):
    """Sensor: datetime ISO de la prochaine fermeture dans les 24h."""

    _attr_name = "Pont Chaban - Prochaine fermeture"
    _attr_unique_id = "pont_chaban_prochaine"
    _attr_icon = "mdi:clock-alert-outline"

    @property
    def _closure(self) -> dict | None:
        return self._data.get("current_closure") or self._data.get("next_24h")

    @property
    def native_value(self) -> str | None:
        c = self._closure
        return c["close_dt"].isoformat() if c else None

    @property
    def extra_state_attributes(self) -> dict:
        c = self._closure
        if c:
            return {
                "bateau": c["bateau"],
                "reouverture": c["open_dt"].isoformat(),
                "duree_minutes": c["duration_minutes"],
                "type_fermeture": c["type_fermeture"],
            }
        return {}


class BateauSensor(_PontBase):
    """Sensor: nom du bateau pour la fermeture en cours ou la prochaine."""

    _attr_name = "Pont Chaban - Bateau"
    _attr_unique_id = "pont_chaban_bateau"
    _attr_icon = "mdi:ferry"

    def _closure(self) -> dict | None:
        return self._data.get("current_closure") or self._data.get("next_24h")

    @property
    def native_value(self) -> str:
        c = self._closure()
        return c["bateau"] if c else "Aucun"


class DureeSensor(_PontBase):
    """Sensor: durée en minutes de la fermeture en cours ou la prochaine."""

    _attr_name = "Pont Chaban - Durée fermeture"
    _attr_unique_id = "pont_chaban_duree"
    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "min"

    def _closure(self) -> dict | None:
        return self._data.get("current_closure") or self._data.get("next_24h")

    @property
    def native_value(self) -> int:
        c = self._closure()
        return c["duration_minutes"] if c else 0

    @property
    def extra_state_attributes(self) -> dict:
        c = self._closure()
        if c:
            return {
                "fermeture": c["close_dt"].isoformat(),
                "reouverture": c["open_dt"].isoformat(),
            }
        return {}


class ReouvertureSensor(_PontBase):
    """Sensor: heure de réouverture (pont fermé → réouverture en cours, sinon prochaine fermeture)."""

    _attr_name = "Pont Chaban - Réouverture"
    _attr_unique_id = "pont_chaban_reouverture"
    _attr_icon = "mdi:clock-check-outline"

    @property
    def native_value(self) -> str | None:
        # Si le pont est actuellement fermé, retourne l'heure de réouverture de la fermeture en cours
        current = self._data.get("current_closure")
        if current:
            return current["open_dt"].isoformat()
        # Sinon, retourne l'heure de réouverture de la prochaine fermeture dans les 24h
        next_c = self._data.get("next_24h")
        if next_c:
            return next_c["open_dt"].isoformat()
        return None

    @property
    def extra_state_attributes(self) -> dict:
        current = self._data.get("current_closure")
        if current:
            return {
                "bateau": current["bateau"],
                "fermeture": current["close_dt"].isoformat(),
                "type_fermeture": current["type_fermeture"],
            }
        next_c = self._data.get("next_24h")
        if next_c:
            return {
                "bateau": next_c["bateau"],
                "fermeture": next_c["close_dt"].isoformat(),
                "type_fermeture": next_c["type_fermeture"],
            }
        return {}
