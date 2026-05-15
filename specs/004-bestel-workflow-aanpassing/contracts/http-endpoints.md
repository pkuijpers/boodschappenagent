# HTTP Endpoint Contracts: Bestel Workflow Aanpassing

Enkel de gewijzigde en nieuwe endpoints worden hier gedocumenteerd.

---

## Nieuwe endpoints

### GET /ingredient-selectie

**Beschrijving**: Toont het ingredient-selectiescherm met alle recept-ingrediënten gegroepeerd per recept.

**Precondities**:
- `app.state.week_menu` aanwezig → anders 303 redirect naar `/week`

**Request**:
```
GET /ingredient-selectie
Headers (optioneel):
  HX-Request: true   → retourneert fragment (zonder <html>)
```

**Response (full page)**:
```
200 OK
Content-Type: text/html
Body: pages/ingredient_selectie.html
  - Header "Ingrediënten selecteren" met back button → /week
  - Voor elke receptgroep:
    - Receptnaam (h2)
    - Per ingredient: checkbox + naam + hoeveelheid-input + eenheid
  - "Verder naar voorraadcheck" button → POST /ingredient-selectie/bevestig
```

**Response (HTMX fragment)**:
```
200 OK
Content-Type: text/html
Body: fragments/ingredient_selectie_content.html (geen <html>)
```

**Initialisatie**: Als `app.state.ingredient_selectie` niet bestaat of leeg is, wordt het gebouwd uit `app.state.week_menu`. Als het al bestaat (terug-navigatie), wordt de bestaande selectie getoond.

**Template context**:
```python
{
    "groepen": [
        {
            "recept_naam": str,
            "items": [IngredientSelectieItem, ...]
        },
        ...
    ],
    "totaal_geselecteerd": int,
}
```

---

### POST /ingredient-selectie/{item_id}/toggle

**Beschrijving**: Toggle de `geselecteerd`-status van één ingredient.

**Precondities**:
- `app.state.ingredient_selectie` bestaat
- `item_id` bestaat in de lijst → anders 404

**Request**:
```
POST /ingredient-selectie/{item_id}/toggle
Content-Type: application/x-www-form-urlencoded
Body:
  geselecteerd: "true" | "false"
```

**Response**:
```
200 OK
Content-Type: text/html
Body: components/ingredient_selectie_item.html (enkelvoudig item)
  - Checkbox state bijgewerkt
  - Visueel: uitgegrijsd/doorgestreept als geselecteerd=False
```

---

### PATCH /ingredient-selectie/{item_id}/hoeveelheid

**Beschrijving**: Pas de hoeveelheid van één ingredient aan.

**Precondities**:
- `app.state.ingredient_selectie` bestaat
- `item_id` bestaat → anders 404

**Request**:
```
PATCH /ingredient-selectie/{item_id}/hoeveelheid
Content-Type: application/x-www-form-urlencoded
Body:
  hoeveelheid: float
```

**Response**:
```
200 OK
Content-Type: text/html
Body: components/ingredient_selectie_item.html (enkelvoudig item met nieuwe hoeveelheid)
```

---

### POST /ingredient-selectie/bevestig

**Beschrijving**: Sla de huidige selectie op (al in app.state) en ga door naar voorraadcheck.

**Precondities**:
- `app.state.week_menu` aanwezig → anders 303 redirect naar `/week`

**Request**:
```
POST /ingredient-selectie/bevestig
```

**Response**:
```
303 See Other
Location: /voorraad
```

**Note**: app.state.ingredient_selectie wordt NIET gewist — dit garandeert dat back-navigatie vanuit /voorraad de bestaande selectie toont (FR-011).

---

## Gewijzigde endpoints

### POST /week/bevestig (menu.py)

**Wijziging**: Redirect target verandert van `/voorraad` naar `/ingredient-selectie`.

**Oud**:
```
303 See Other
Location: /voorraad
```

**Nieuw**:
```
303 See Other
Location: /ingredient-selectie
```

---

### POST /voorraad/bevestig (voorraad.py)

**Wijziging**: In plaats van redirect naar `/boodschappen`, wordt nu de matching gestart.

**Nieuwe precondities**:
- `app.state.week_menu` aanwezig → anders 303 redirect naar `/week`
- AH authenticated → anders 303 redirect naar `/ah/login`
- `app.state.ingredient_selectie` bevat minstens één geselecteerd item OF VoorraadRepository heeft pantry-items die niet op voorraad zijn → anders foutmelding

**Nieuwe request**:
```
POST /voorraad/bevestig
```

**Nieuwe response (success)**:
```
303 See Other
Location: /boodschappen/match-review
```

**Nieuwe response (lege lijst)**:
```
200 OK
Content-Type: text/html
Body: pages/ah_error.html
  context: {"error_type": "lege_lijst"}
```

**Nieuwe response (API fout)**:
```
200 OK
Content-Type: text/html
Body: pages/ah_error.html
  context: {"error_type": "api_error"}
```

**Interne logica**:
1. Lees `app.state.ingredient_selectie`, filter `geselecteerd=True`
2. Aggregeer per `(norm_naam, norm_eenheid)` met `IngredientNormalizer`
3. Maak `Boodschappenlijst` van geaggregeerde regels
4. Roep `BoodschappenlijstFilter.voeg_pantry_toe(lijst)` aan (stappen 2+3 only)
5. Lege-lijst check
6. Sla op in `app.state.boodschappenlijst_model` en `app.state.boodschappenlijst`
7. Roep `AHIntegratie.zoek_producten(lijst, voorkeuren_repo)` aan
8. Sla `match_review_items` op in `app.state`
9. Redirect naar `/boodschappen/match-review`

**Dependencies toegevoegd**:
- `get_ah_token_manager` (auth check)
- `get_ah_integratie` (matching)
- `get_match_voorkeuren_repository` (voorkeuren)
- `get_boodschappenlijst_filter` (pantry toevoegen)
- `get_boodschappenlijst_generator` (IngredientNormalizer toegang)

---

## Ongewijzigde endpoints (ter referentie)

| Endpoint | Status |
|----------|--------|
| `GET /boodschappen` | Ongewijzigd; buiten hoofdflow |
| `GET /boodschappen/match-review` | Ongewijzigd (003-flow) |
| `POST /boodschappen/bevestig-matches` | Ongewijzigd (003-flow) |
| `GET /voorraad` | Ongewijzigd (template back button update wel) |
| `POST /voorraad/{product_id}/status` | Ongewijzigd |
| `POST /week/bevestig` | Gewijzigd redirect target |
