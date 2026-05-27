# Implementation Plan: Voorraadlijst Sortering op Categorie

**Branch**: `005-voorraad-categorie-sortering` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/005-voorraad-categorie-sortering/spec.md`

## Summary

Sorteer de items op de voorraadpagina op winkellocatie: koelkast (1) → voorraadkast (2) → diepvries (3), met een zichtbare sectieheader per gevulde groep. De AH-categorie is al beschikbaar op het `Product.category` veld maar wordt momenteel weggegooid bij de routerverwerking. De aanpak: nieuwe `Afdeling` enum + mapping-functie in `ah/afdeling.py`, `category` doorgeven in de voorraad-itemdicts, sortering en groupby in router respectievelijk template.

## Technical Context

**Language/Version**: Python 3.14+  
**Primary Dependencies**: FastAPI, Jinja2 (SSR), HTMX, Tailwind CSS (CDN), pytest  
**Storage**: N/A (geen nieuwe datapersistentie)  
**Testing**: pytest (unit), Playwright E2E (iPhone 13, 390×844)  
**Target Platform**: Web — mobiel-first (iPhone 13 viewport)  
**Project Type**: web-service  
**Performance Goals**: Standaard web-responstijd; geen speciale eisen  
**Constraints**: Mobiel-first; touch targets ≥44×44pt; geen SPA, geen inline `style` attributen  
**Scale/Scope**: Kleine feature — 1 nieuw module-bestand, 2 gewijzigde routerfuncties, 2 gewijzigde templates, uitbreiding test fixtures

## Constitution Check

*GATE: Gecontroleerd voor en na Phase 1 design.*

| Principe | Status | Toelichting |
|----------|--------|-------------|
| I. TDD | ✅ | Alle productie-code wordt voorafgegaan door een falende test |
| II. SSR | ✅ | Template-aanpassing via Jinja2; HTMX toggle-endpoint ongewijzigd |
| III. YAGNI | ✅ | Alleen enum + pure mapping-functie; geen abstractielagen |
| IV. Code Quality | ✅ | ruff check + format verplicht voor commit |
| V. Domain Modelling | ✅ | `Afdeling` is een `str`-enum; `Product` dataclass ongewijzigd |
| VI. UI/UX | ✅ | Sectieheaders tonen alleen bij gevulde secties; mobiele viewport primair |
| VII.1 AHIntegratie façade | ✅ | `AHIntegratie.haal_voorraad_producten()` ongewijzigd; router roept het via façade aan |
| VII.3 Domeinlogica in domeinmodule | ✅ | Mapping-regels in `ah/afdeling.py`, niet in router |
| VII.4 Dependency direction | ✅ | `ah/afdeling.py` is een pure utility; geen reverse dependencies |

**Post-design re-check**: ✅ Alle principes gerespecteerd — geen Complexity Tracking nodig.

## Project Structure

### Documentation (this feature)

```text
specs/005-voorraad-categorie-sortering/
├── plan.md              # Dit bestand
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (relevante bestanden)

```text
src/boodschappenagent/
    ah/
        afdeling.py          # NIEUW: Afdeling enum + categorie_naar_afdeling()
        __init__.py          # Uitbreiden exports met Afdeling, categorie_naar_afdeling
    web/
        routers/
            voorraad.py      # WIJZIGING: category doorgeven, sortering op afdeling
        templates/
            fragments/
                voorraad_content.html  # WIJZIGING: sectieheaders via groupby
            components/
                voorraaditem.html      # Ongewijzigd

tests/
    test_afdeling.py                   # NIEUW: unit tests categorie_naar_afdeling()
    web/
        conftest.py                    # WIJZIGING: TEST_VOORRAAD_PRODUCTEN multi-categorie
        test_voorraadcheck.py          # WIJZIGING: sectie-assertions toevoegen
    e2e/
        test_voorraadcheck.py          # WIJZIGING: volgorde-verificatie
```

## Implementation Approach

### Stap 1 — `ah/afdeling.py` (nieuw domeinmodule)

De mapping is gebaseerd op de AH-hoofdcategorie (exact, case-sensitief, deel vóór `/`), gevalideerd via een API-steekproef van 100 producten. Geen trefwoordheuristiek — expliciete dict-lookup.

```python
from enum import Enum

class Afdeling(str, Enum):
    KOELKAST     = "Koelkast"      # sort_key 1
    VOORRAADKAST = "Voorraadkast"  # sort_key 2
    DIEPVRIES    = "Diepvries"     # sort_key 3
    OVERIG       = "Overig"        # sort_key 4 (fallback)

AFDELING_VOLGORDE = {
    Afdeling.KOELKAST: 1,
    Afdeling.VOORRAADKAST: 2,
    Afdeling.DIEPVRIES: 3,
    Afdeling.OVERIG: 4,
}

HOOFD_CATEGORIE_NAAR_AFDELING: dict[str, Afdeling] = {
    # Koelkast
    "Zuivel, eieren":                    Afdeling.KOELKAST,
    "Vlees":                             Afdeling.KOELKAST,
    "Vleeswaren":                        Afdeling.KOELKAST,
    "Vis":                               Afdeling.KOELKAST,
    "Kaas":                              Afdeling.KOELKAST,
    "Maaltijden, salades":               Afdeling.KOELKAST,
    "Vegetarisch, vegan en plantaardig": Afdeling.KOELKAST,
    # Diepvries
    "Diepvries":                         Afdeling.DIEPVRIES,
    # Voorraadkast
    "Groente, aardappelen":              Afdeling.VOORRAADKAST,
    "Fruit, verse sappen":               Afdeling.VOORRAADKAST,
    "Pasta, rijst, wereldkeuken":        Afdeling.VOORRAADKAST,
    "Soepen, sauzen, kruiden, olie":     Afdeling.VOORRAADKAST,
    "Borrel, chips, snacks":             Afdeling.VOORRAADKAST,
    "Ontbijtgranen, beleg":              Afdeling.VOORRAADKAST,
    "Bakkerij":                          Afdeling.VOORRAADKAST,
    "Dranken":                           Afdeling.VOORRAADKAST,
    "Wijn, bier en gedestilleerd":       Afdeling.VOORRAADKAST,
    "Thee, koffie en cacao":             Afdeling.VOORRAADKAST,
    "Snoep en koek":                     Afdeling.VOORRAADKAST,
    "Baby en kind":                      Afdeling.VOORRAADKAST,
    # Overig (non-food)
    "Drogisterij en gezondheid":         Afdeling.OVERIG,
    "Huishouden":                        Afdeling.OVERIG,
    "Bloemen en planten":                Afdeling.OVERIG,
}

def categorie_naar_afdeling(category: str) -> Afdeling:
    if not category or not category.strip():
        return Afdeling.OVERIG
    hoofd = category.split("/")[0].strip()
    return HOOFD_CATEGORIE_NAAR_AFDELING.get(hoofd, Afdeling.OVERIG)
```

### Stap 2 — Router-wijzigingen (`web/routers/voorraad.py`)

**`_haal_voorraad_producten()`**: voeg `"category": p.category` toe aan de item-dict.

**`_build_voorraad_context()`**: 
1. Na het bouwen van `items`, voeg `afdeling` toe via `categorie_naar_afdeling(item["category"])`
2. Sorteer `items` op `AFDELING_VOLGORDE[item["afdeling"]]`

### Stap 3 — Template (`fragments/voorraad_content.html`)

Vervang de huidige `{% for item in voorraad_items %}` loop door een groupby-loop:

```jinja
{% for afdeling_naam, groep_items in voorraad_items | groupby('afdeling') %}
  <h3 class="...">{{ afdeling_naam }}</h3>
  {% for item in groep_items %}
    {% include "components/voorraaditem.html" %}
  {% endfor %}
{% endfor %}
```

Sectieheaders tonen alleen als er items in die groep zijn (Jinja2 `groupby` slaat lege groepen automatisch over).

### Stap 4 — Tests

**`tests/test_afdeling.py`** — parametrized unit tests (exacte AH-categorienamen):
- `"Zuivel, eieren"` → KOELKAST
- `"Vlees"` → KOELKAST
- `"Vleeswaren"` → KOELKAST
- `"Vis"` → KOELKAST
- `"Kaas"` → KOELKAST
- `"Maaltijden, salades"` → KOELKAST
- `"Vegetarisch, vegan en plantaardig"` → KOELKAST
- `"Diepvries"` → DIEPVRIES
- `"Groente, aardappelen"` → VOORRAADKAST
- `"Pasta, rijst, wereldkeuken"` → VOORRAADKAST
- `"Soepen, sauzen, kruiden, olie"` → VOORRAADKAST
- `"Borrel, chips, snacks"` → VOORRAADKAST
- `""` (lege string) → OVERIG
- `"Onbekende categorie XYZ"` → OVERIG
- Hiërarchisch formaat `"Zuivel, eieren/Halfvolle melk"` → KOELKAST (extract hoofd)
- Hiërarchisch formaat `"Diepvries/Sperziebonen (diepvries)"` → DIEPVRIES (extract hoofd)

**`tests/web/conftest.py`** — `TEST_VOORRAAD_PRODUCTEN` uitbreiden met producten in drie categorieën.

**`tests/web/test_voorraadcheck.py`** — assertions:
- Sectieheader "Koelkast" aanwezig bij koelkastproducten
- Sectieheader "Diepvries" aanwezig bij diepvriesproducten
- Koelkastproduct staat vóór diepvriesproduct in DOM

**`tests/e2e/test_voorraadcheck.py`** — Playwright verificatie van de sorteervolgorde op de pagina.
