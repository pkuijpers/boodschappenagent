# Data Model: Voorraadlijst Sortering op Categorie

**Feature**: 005-voorraad-categorie-sortering
**Date**: 2026-05-27

## Nieuwe entiteit: `Afdeling`

```
Afdeling (enum)
├── KOELKAST    sort_key=1  label="Koelkast"
├── VOORRAADKAST sort_key=2  label="Voorraadkast"
├── DIEPVRIES   sort_key=3  label="Diepvries"
└── OVERIG      sort_key=4  label="Overig"
```

**Locatie**: `src/boodschappenagent/ah/afdeling.py`  
**Type**: `str` enum (voor directe Jinja2-output)  
**Eigenschappen**:
- `sort_key: int` — bepaalt sorteervolgorde (1–4)
- `label: str` — weergavenaam voor sectieheader in template

---

## Nieuwe functie: `categorie_naar_afdeling`

```
categorie_naar_afdeling(category: str) -> Afdeling
```

**Locatie**: `src/boodschappenagent/ah/afdeling.py`  
**Signatuur**: pure functie, geen I/O, geen state  
**Logica**:
1. Lege string of None → OVERIG
2. Extraheer hoofdcategorie: `category.split("/")[0].strip()` (case-sensitief, exacte match)
3. Opzoeken in `HOOFD_CATEGORIE_NAAR_AFDELING` dict → directe mapping
4. Onbekende hoofdcategorie → OVERIG (dict `.get(..., Afdeling.OVERIG)`)

De mapping-dict bevat alle 23 bekende AH-hoofdcategorieën (gevalideerd via API-steekproef 2026-05-27). Zie spec.md voor de volledige tabel en rationale per keuze.

---

## Gewijzigde context: voorraad template

**Huidig**:
```python
voorraad_items: list[dict]  # {naam, id, context, op_voorraad}
```

**Nieuw**:
```python
voorraad_items: list[dict]  # {naam, id, context, op_voorraad, afdeling: str}
                             # gesorteerd op Afdeling.sort_key
```

Het `afdeling` veld bevat het `Afdeling` enum-waarde (als str). De template gebruikt:
```jinja
{% for afdeling_naam, items in voorraad_items | groupby('afdeling') %}
```

---

## Gewijzigde router-helper

**`_haal_voorraad_producten()`** — uitgebreid met `category`:
```python
{"naam": p.title, "id": str(p.id), "category": p.category}
```

**`_build_voorraad_context()`** — uitgebreid:
1. Voeg `afdeling` toe via `categorie_naar_afdeling(item["category"])`
2. Sorteer `items` op `afdeling.sort_key`

---

## Gewijzigde test fixtures

**`tests/web/conftest.py` — `TEST_VOORRAAD_PRODUCTEN`**: uitgebreid met (exacte AH-categorienamen):
- Melk → `category="Zuivel, eieren"` (KOELKAST)
- Kipfilet → `category="Vlees"` (KOELKAST)
- Pasta → `category="Pasta, rijst, wereldkeuken"` (VOORRAADKAST)
- Soep → `category="Soepen, sauzen, kruiden, olie"` (VOORRAADKAST)
- Diepvriesgroenten → `category="Diepvries"` (DIEPVRIES)

---

## Geen wijzigingen aan

- `Product` dataclass (heeft al `category` veld)
- `AHIntegratie` (façade ongewijzigd)
- `AHClient` GraphQL queries (category al opgehaald)
- `voorraad_toggle` endpoint
- `voorraaditem.html` component
