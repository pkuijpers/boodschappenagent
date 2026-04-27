# Design: HelloFresh standaard op dinsdag, woensdag en donderdag

## Samenvatting

Bij het aanmaken van een vers weekmenu (eerste keer in de week, geen bestaand menu) worden dinsdag, woensdag en donderdag automatisch als HelloFresh-dag ingesteld. Bij het reshufflen via "Genereer" blijft de bestaande HelloFresh-selectie bewaard.

## Context

`hellofresh_dagen` is een `set[int]` in `app.state.hellofresh_dagen` (en gepersisteerd in `current_menu.json`). De waarden zijn weekdagnummers: 0=maandag, 1=dinsdag, 2=woensdag, 3=donderdag, etc.

In `_generate_week_menu` (menu.py) wordt al gedetecteerd of er een bestaand menu is via `bestaand = getattr(request.app.state, "week_menu", None)`. Als `bestaand is None` is het een verse generatie.

## Wijziging

**Bestand:** `src/boodschappenagent/web/routers/menu.py`  
**Functie:** `_generate_week_menu`

Na de `bestaand`-check:

```python
if bestaand is None:
    request.app.state.hellofresh_dagen = {1, 2, 3}
```

Dit wordt vóór `_save_state(request)` toegevoegd zodat de defaults direct worden opgeslagen.

## Gedrag

| Scenario | Resultaat |
|---|---|
| Eerste bezoek nieuwe week (geen bestaand menu) | `hellofresh_dagen = {1, 2, 3}` |
| Gebruiker klikt "Genereer" (reshuffle) | `hellofresh_dagen` ongewijzigd |
| Bestaand menu geladen van disk | `hellofresh_dagen` geladen uit JSON |

## Tests

1. Fresh generatie (geen bestaand menu) → `hellofresh_dagen == {1, 2, 3}` na aanroep
2. Reshuffle (bestaand menu aanwezig, HF-dagen `{0, 4}`) → `hellofresh_dagen == {0, 4}` na aanroep
