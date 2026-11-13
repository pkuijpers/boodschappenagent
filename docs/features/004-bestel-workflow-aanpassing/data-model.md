# Data Model: Bestel Workflow Aanpassing

## Sessiestate entiteiten

Deze feature voegt één nieuw sessiestate-object toe aan `app.state`. Het is bewust geen frozen dataclass — het volgt het bestaande `app.state.boodschappenlijst` patroon (list[dict]).

---

### IngredientSelectieItem (app.state.ingredient_selectie)

**Opgeslagen als**: `app.state.ingredient_selectie: list[dict]`
**Levensduur**: Zolang de gebruiker actief is in de bestelflow (initialisatie bij GET /ingredient-selectie; niet gewist bij POST /ingredient-selectie/bevestig zodat back-navigatie werkt)
**Persistentie**: Geen (in-memory only)

```python
{
    "id": str,            # UUID; uniek per item; gebruikt voor HTMX swap target
    "recept_naam": str,   # Naam van het recept; voor visuele groepering in template
    "naam": str,          # Rauwe ingredientnaam uit recept (niet genormaliseerd)
    "hoeveelheid": float, # Geschaald naar personen; door gebruiker aanpasbaar
    "eenheid": str,       # Eenheid (bijv. "g", "stuks", "el")
    "geselecteerd": bool, # True = bestellen; False = overgeslagen; default True
}
```

**Initialisatie** (bij GET /ingredient-selectie, alleen als nog niet aanwezig):
```
voor elke dag in week_menu.geplande_dagen:
    scaled = dag.recept.scale_to_portions(dag.personen)
    voor elk ingredient in scaled.ingredienten:
        item = { id: uuid4(), recept_naam: dag.recept.naam, naam: ing.naam,
                 hoeveelheid: ing.hoeveelheid, eenheid: ing.eenheid, geselecteerd: True }
```

**State transitions**:
- `geselecteerd`: True ↔ False via `POST /ingredient-selectie/{id}/toggle`
- `hoeveelheid`: any float via `PATCH /ingredient-selectie/{id}/hoeveelheid`

---

## Aggregatie naar Boodschappenlijst

Bij `POST /voorraad/bevestig` worden de geselecteerde items geaggregeerd:

```
gefilterd = [item for item in ingredient_selectie if item["geselecteerd"]]

per (norm_naam, norm_eenheid):
    hoeveelheid = som van item["hoeveelheid"] (tenzij is_niet_aggregeerbaar → 1.0)
    originele_namen = verzameling van item["naam"]
    recepten = geordende lijst van item["recept_naam"] (zonder duplicaten)

BoodschappenRegel(naam=norm_naam, hoeveelheid=round_quantity(...), eenheid=norm_eenheid, ...)
```

Gevolgd door `BoodschappenlijstFilter.voeg_pantry_toe(lijst)` om pantry-items toe te voegen.

---

## Bestaande entiteiten (ongewijzigd)

| Entiteit | Locatie | Rol in nieuwe flow |
|----------|---------|-------------------|
| WeekMenu | `planner/models.py` | Input voor ingredient-selectie initialisatie |
| BoodschappenlijstGenerator | `boodschappenlijst/generator.py` | Niet meer gebruikt in hoofdflow; blijft bestaan |
| BoodschappenlijstFilter | `voorraadbeheer/filter.py` | Nieuwe methode `voeg_pantry_toe()` toegevoegd |
| Boodschappenlijst | `boodschappenlijst/models.py` | Ongewijzigd; output van aggregatiestap |
| MatchReviewItem | `ah/preferences.py` | Ongewijzigd; output van matching-stap |

---

## Wijzigingen aan bestaande entiteiten

### BoodschappenlijstFilter — nieuwe methode

```python
def voeg_pantry_toe(self, lijst: Boodschappenlijst) -> Boodschappenlijst:
    """Voeg VERS_BASIS en HOUDBAAR items toe die niet op voorraad zijn.

    Stap 1 (filteren op voorraad) wordt NIET uitgevoerd — de gebruiker
    heeft al via ingredient-selectie beslist wat er besteld wordt.
    """
    bestaande_namen = {r.naam for r in lijst.regels}
    regels = list(lijst.regels)
    # stap 2: VERS_BASIS (zelfde logica als filter_op_voorraad stappen 2+3)
    # stap 3: HOUDBAAR
    # stap 4: sorteer alfabetisch
    return Boodschappenlijst(week_start=lijst.week_start, regels=regels)
```

---

## Dataflow diagram

```
WeekMenu (app.state)
    │
    ▼ GET /ingredient-selectie (initialisatie, eenmalig)
IngredientSelectieItems (app.state.ingredient_selectie)
    │ ← POST .../toggle (toggle geselecteerd)
    │ ← PATCH .../hoeveelheid (aanpassen hoeveelheid)
    │
    ▼ POST /voorraad/bevestig
[geselecteerde items + aggregatie + IngredientNormalizer]
    │
    ▼ + BoodschappenlijstFilter.voeg_pantry_toe()
Boodschappenlijst (gecombineerd)
    │
    ▼ AHIntegratie.zoek_producten()
MatchReviewItems (app.state.match_review_items)
    │
    ▼ GET /boodschappen/match-review (bestaande 003-flow)
```
