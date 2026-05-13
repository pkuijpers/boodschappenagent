# Data Model: Handmatig toegevoegde artikelen meesturen naar AH

**Date**: 2026-05-13

## Bestaande entiteiten (geen wijzigingen)

### BoodschappenRegel (bestaand, ongewijzigd)

Frozen dataclass in `src/boodschappenagent/boodschappenlijst/models.py`.

| Veld | Type | Validatie | Gebruik bij AH-sync |
|------|------|-----------|---------------------|
| `naam` | `str` | Non-empty | Zoekterm in `smart_search()` |
| `hoeveelheid` | `float` | — | Berekening via `bereken_aantal()` |
| `eenheid` | `str` | Non-empty | Berekening via `bereken_aantal()` |
| `originele_namen` | `frozenset[str]` | Non-empty | Niet gebruikt door AH |
| `opmerkingen` | `list[str]` | — | Niet gebruikt door AH |
| `recepten` | `tuple[str, ...]` | — | Niet gebruikt door AH |

**Voor handmatige items**: `originele_namen = frozenset({naam})`, `recepten = ()`, `opmerkingen = []`.

### Boodschappenlijst (bestaand, ongewijzigd)

Frozen dataclass in `src/boodschappenagent/boodschappenlijst/models.py`.

| Veld | Type | Validatie |
|------|------|-----------|
| `week_start` | `str` | ISO date, non-empty |
| `regels` | `list[BoodschappenRegel]` | — |

### UI-itemsdict (bestaand, ongewijzigd)

Mutable dict in `app.state.boodschappenlijst`. Na de fix is dit de single source of truth voor de AH-verzending.

| Veld | Type | Handmatig | Menu-gegenereerd |
|------|------|-----------|-----------------|
| `id` | `str` | uuid4 | uuid4 |
| `naam` | `str` | gebruikersinput | generator |
| `hoeveelheid` | `float` | gebruikersinput | generator |
| `eenheid` | `str` | gebruikersinput | generator |
| `checked` | `bool` | False | False |
| `handmatig` | `bool` | **True** | False |
| `eerste_recept` | `str \| None` | None | receptnaam |
| `extra_aantal` | `int` | 0 | aantal extra recepten |

## Logische dataflow na de fix

```
app.state.boodschappenlijst (list[dict])
    │
    ├── filter: item["checked"] == False
    │
    ▼
niet-gecheckte items (list[dict])
    │
    ├── per item: BoodschappenRegel(naam, hoeveelheid, eenheid, originele_namen={naam})
    │
    ▼
Boodschappenlijst(week_start=..., regels=[...])
    │
    ▼
AHIntegratie.sync_naar_lijst()
```

## State-invarianten na de fix

- `boodschappenlijst_model` in `app.state` wordt niet meer gebruikt door `verstuur_naar_ah()`.
- `boodschappenlijst` (list[dict]) is de enige bron voor AH-verzending.
- `boodschappenlijst_model` blijft bestaan in state voor backward compatibility (bestaande tests spelen erop in).
- Geen nieuwe velden of entiteiten vereist.
