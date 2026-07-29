# Home Assistant Integration - Bordeaux Métropole - Pont Chaban-Delmas

Le pont Chaban-Delmas s'ouvre régulièrement pour laisser passer les bateaux, coupant la circulation routière. Cette intégration interroge le jeu de données [prévisions_pont_chaban](https://datahub.bordeaux-metropole.fr/explore/dataset/previsions_pont_chaban/table/) de Bordeaux Métropole pour exposer dans Home Assistant l'état actuel du pont ainsi que les prochaines fermetures prévues (horaires, durée, bateau concerné).

## Installation

Aucune clé n'est nécessaire. Ajoutez l'intégration depuis **Paramètres > Appareils et services > Ajouter une intégration > Pont Chaban-Delmas**. Les données sont rafraîchies toutes les minutes.

## Entités exposées

| Entité | Valeur | Attributs |
|---|---|---|
| `sensor.pont_chaban_etat_actuel` | `Ouvert` / `Fermé` | `bateau`, `reouverture`, `duree_minutes`, `type_fermeture` (si fermé) |
| `sensor.pont_chaban_prochaine_fermeture` | Horodatage ISO de la prochaine fermeture | `bateau`, `reouverture`, `duree_minutes`, `type_fermeture` |
| `sensor.pont_chaban_bateau` | Nom du bateau concerné | — |
| `sensor.pont_chaban_duree_fermeture` | Durée en minutes | `fermeture`, `reouverture` |
| `sensor.pont_chaban_reouverture` | Horodatage ISO de réouverture | `bateau`, `fermeture`, `type_fermeture` |

## Exemples

### Carte Lovelace

```yaml
type: entities
title: Pont Chaban-Delmas
entities:
  - entity: sensor.pont_chaban_etat_actuel
  - entity: sensor.pont_chaban_prochaine_fermeture
  - entity: sensor.pont_chaban_bateau
  - entity: sensor.pont_chaban_duree_fermeture
  - entity: sensor.pont_chaban_reouverture
```

### Automatisation : notification avant une fermeture

```yaml
automation:
  - alias: "Pont Chaban - Alerte fermeture imminente"
    trigger:
      - platform: template
        value_template: >
          {{ (as_timestamp(states('sensor.pont_chaban_prochaine_fermeture')) - as_timestamp(now())) / 60 <= 15 }}
    condition:
      - condition: state
        entity_id: sensor.pont_chaban_etat_actuel
        state: "Ouvert"
    action:
      - service: notify.mobile_app
        data:
          title: "Pont Chaban-Delmas"
          message: >
            Fermeture imminente pour laisser passer {{ state_attr('sensor.pont_chaban_prochaine_fermeture', 'bateau') }}
            (durée estimée : {{ state_attr('sensor.pont_chaban_prochaine_fermeture', 'duree_minutes') }} min).
```
