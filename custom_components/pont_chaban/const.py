"""Constants for Pont Chaban-Delmas integration."""

DOMAIN = "pont_chaban"

API_URL = (
    "https://datahub.bordeaux-metropole.fr/api/explore/v2.1/catalog/datasets/"
    "previsions_pont_chaban/records"
    "?limit=100"
    "&order_by=date_passage%20asc%2Cfermeture_a_la_circulation%20asc"
)

SCAN_INTERVAL_MINUTES = 1

SENSOR_FERME_NOW = "pont_ferme"
SENSOR_NEXT = "prochaine_fermeture"
SENSOR_BATEAU = "bateau"
SENSOR_DUREE = "duree_fermeture"
SENSOR_REOUVERTURE = "reouverture"
