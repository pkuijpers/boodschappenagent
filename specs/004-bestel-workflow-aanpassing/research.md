# Research: Bestel Workflow Aanpassing

## Codebase Analysis

### Huidige bestelflow

**Decision**: De huidige flow is `Weekmenu → Voorraadcheck → Boodschappenlijst → Matching`.

Bronnen:
- `menu.py:192` — `POST /week/bevestig` redirect naar `/voorraad`
- `voorraad.py:103` — `POST /voorraad/bevestig` redirect naar `/boodschappen`
- `boodschappen.py:80-113` — `GET /boodschappen` genereert de boodschappenlijst via `BoodschappenlijstGenerator` + `BoodschappenlijstFilter`

**Rationale**: De nieuwe flow plaatst ingredient-selectie vóór de voorraadcheck, zodat de gebruiker eerst per recept bepaalt wat er besteld moet worden.

---

### Sessiestate pattern

**Decision**: In-memory `app.state` als `list[dict]` (geen frozen dataclass, geen JSON persistentie).

**Rationale**: `app.state.boodschappenlijst` in `boodschappen.py:75` volgt precies dit patroon. Ingredient-selectie heeft dezelfde levensduur (één bestelflow-sessie), geen persistentie nodig.

**Dict schema per item**:
```python
{
    "id": str,          # UUID voor HTMX targeting
    "recept_naam": str, # voor groepering in template
    "naam": str,        # rauwe ingredientnaam uit recept
    "hoeveelheid": float,
    "eenheid": str,
    "geselecteerd": bool,  # default True
}
```

---

### Ingredient normalisatie en aggregatie

**Decision**: Normalisatie via `IngredientNormalizer` + aggregatie per `(norm_naam, norm_eenheid)` — zelfde logica als `BoodschappenlijstGenerator.genereer()`.

**Rationale**: `BoodschappenlijstGenerator` (`generator.py:35-93`) implementeert al de correcte aggregatielogica inclusief `is_niet_aggregeerbaar` en `PortionCalculator.round_quantity`. Om duplicatie te voorkomen wordt dezelfde normalisatie toegepast in `POST /voorraad/bevestig`.

**Alternatief overwogen**: Nieuwe methode op `BoodschappenlijstGenerator` die een flat list accepteert in plaats van een `WeekMenu`. Afgewezen: overgeneralisatie — het enige gebruik is in `POST /voorraad/bevestig`.

---

### BoodschappenlijstFilter: nieuwe methode `voeg_pantry_toe()`

**Decision**: Voeg `voeg_pantry_toe(lijst)` toe aan `BoodschappenlijstFilter` die alleen stappen 2+3 uitvoert (VERS_BASIS en HOUDBAAR toevoegen), zonder stap 1 (filteren op voorraad).

**Rationale**: In de nieuwe flow heeft de gebruiker al via ingredient-selectie bepaald wat er besteld wordt — stap 1 van de huidige `filter_op_voorraad` (verwijder items die op voorraad zijn) past niet meer. Stap 1 is voor het weghalen van recipe-ingrediënten die al in huis zijn; in de nieuwe flow doet de gebruiker dit handmatig via de vinkjes. Stappen 2+3 (pantry items toevoegen) zijn ongewijzigd.

**Alternatief overwogen**: Refactor `filter_op_voorraad` om `voeg_pantry_toe` intern aan te roepen. Afgewezen: de bestaande functie heeft zijn eigen tests en contract; een aparte methode is veiliger.

---

### HTMX interactiepatroon

**Decision**: Vier endpoints voor ingredient-selectie:
1. `GET /ingredient-selectie` — full page + HTMX fragment (zelfde patroon als `/boodschappen`)
2. `POST /ingredient-selectie/{item_id}/toggle` — toggle geselecteerd, retourneert enkelvoudig item-component
3. `PATCH /ingredient-selectie/{item_id}/hoeveelheid` — update hoeveelheid, retourneert enkelvoudig item-component
4. `POST /ingredient-selectie/bevestig` — redirect naar `/voorraad`

**Rationale**: Exact zelfde HTMX-patronen als de bestaande boodschappen-endpoints (`boodschappen.py:141-168`). Geen nieuwe patronen nodig.

---

### Lege boodschappenlijst validatie (FR-008)

**Decision**: Lege-lijst check in `POST /voorraad/bevestig`, vóór de matching-aanroep.

**Rationale**: Op dit punt is de definitieve gecombineerde lijst bekend. De check geeft een foutmelding terug (bestaande `pages/ah_error.html` met nieuw `error_type`).

---

### AH auth in `POST /voorraad/bevestig`

**Decision**: Authenticatiecheck in `POST /voorraad/bevestig` (net als in de huidige `POST /boodschappen/verstuur-naar-ah`).

**Rationale**: De voorraad-pagina zelf vereist al AH-auth. Als de token expireert tussen de voorraadcheck en de bevestiging, redirect terug naar login.

---

### Route-volgorde in FastAPI

**Decision**: `POST /ingredient-selectie/bevestig` moet vóór `POST /ingredient-selectie/{item_id}/toggle` geregistreerd zijn.

**Rationale**: FastAPI matcht routes op volgorde van definitie (specifieke routes vóór parametrische). Bestaande voorbeeld: `boodschappen.py` definieert `/boodschappen/toevoegen` en `/boodschappen/verstuur-naar-ah` vóór `/boodschappen/{item_id}`.

---

### Navigatie back-buttons

**Decision**:
- Ingredient-selectie: back button → `/week`
- Voorraad: back button → `/ingredient-selectie` (was `/week`)

**Rationale**: De nieuwe canonieke volgorde is Week → Ingredient-selectie → Voorraad. Terug-navigatie moet deze volgorde volgen. FR-011 vereist dat selectie bewaard blijft bij terug-navigatie vanuit voorraad.

---

### Bestaande boodschappenlijst-route

**Decision**: `GET /boodschappen` blijft bestaan maar valt buiten de normale bestelflow.

**Rationale**: De route kan nog steeds handmatig worden opgeroepen. Verwijderen zou tests breken en levert geen directe waarde op voor deze feature.

---

### Te updaten bestaande tests

**Decision**: Twee bestaande tests breken door de flow-wijziging en moeten worden aangepast:

1. `test_week_bevestig.py` — `test_bevestig_redirect_naar_voorraad` → nieuwe assertie: redirect naar `/ingredient-selectie`
2. `test_voorraadcheck.py` — `TestVoorraadBevestig.test_s8_1_redirect_naar_boodschappen` → nieuwe assertie: redirect naar `/boodschappen/match-review` (of verwijderd)

**Rationale**: Deze tests valideren de navigatiestroom; na de flow-wijziging zijn de assertions incorrect.
