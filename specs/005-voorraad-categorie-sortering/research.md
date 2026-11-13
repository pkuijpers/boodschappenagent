# Research: Voorraadlijst Sortering op Categorie

**Feature**: 005-voorraad-categorie-sortering
**Date**: 2026-05-27

## Beslissing 1: Waar leeft de mapping-logica?

**Beslissing**: Nieuw bestand `ah/afdeling.py` met `Afdeling` enum en `categorie_naar_afdeling(category: str) -> Afdeling`.

**Rationale**: Per constitution Principle VII.3 mag domeinlogica (de vraag "in welke afdeling hoort dit product?") niet in de HTTP-laag staan. Het is AH-specifieke kennis → behoort in de `ah`-module. De router roept de pure mapping-functie aan als onderdeel van template-marshalling.

**Alternatieven overwogen**:
- Mapping in router (`_build_voorraad_context`) → verworpen: schending Principle VII.3
- Mapping als property op `Product` → verworpen: koppelt AH-categorielogica aan het datamodel; `Product` is een generiek dataclass
- Mapping als methode op `AHIntegratie` → niet nodig: `categorie_naar_afdeling()` is een pure functie zonder I/O; vergt geen façade-indirectie

---

## Beslissing 2: Hoe de template de groepsindeling ontvangt

**Beslissing**: De router sorteert `voorraad_items` op afdeling-prioriteit en voegt een `afdeling` veld toe aan elk item-dict. De template gebruikt Jinja2's `groupby('afdeling')` filter om sectieheaders te renderen.

**Rationale**: Jinja2's `groupby` werkt correct op gesorteerde lijsten (identiek aan Python's `itertools.groupby`). Dit vermijdt een aparte geneste context-structuur en houd de template eenvoudig. Sortering door de router is marshalling, niet domeinlogica.

**Alternatieven overwogen**:
- Pre-grouped structuur `[{naam, items}]` in context → vermijdt groupby in template maar voegt complexiteit toe aan router
- Sortering/grouping via `AHIntegratie.haal_voorraad_producten()` retourneert gesorteerde producten → `AHIntegratie` heeft dan geen zicht op template-context; de sorteervolgorde is presentatie-logica, niet integratie-logica

---

## Beslissing 3: AH category-formaat en mapping-regels

**Bevinding uit codebase**: `Product.category` heeft het formaat `"HoofdCategorie/SubCategorie"` of alleen `"HoofdCategorie"`. Het deel vóór de `/` is de hoofdcategorie.

**Mapping-strategie**: substring-match (case-insensitief) op de hoofdcategorie:

| Trefwoorden in hoofdcategorie (bevat-match) | Afdeling |
|---------------------------------------------|----------|
| `zuivel`, `eieren`, `vlees`, `kip`, `vis`, `kaas`, `vleeswaren`, `deli`, `charcuterie`, `boter`, `margarine`, `vet`, `crème fraîche`, `kwark`, `yoghurt` | KOELKAST |
| `diepvries` | DIEPVRIES |
| alles overige (incl. conserven, pasta, rijst, sauzen, dranken, brood, snacks, huishouden, verzorging) | VOORRAADKAST |
| lege of geen categorie | OVERIG |

**Sorteervolgorde**: KOELKAST (1) → VOORRAADKAST (2) → DIEPVRIES (3) → OVERIG (4)

---

## Beslissing 4: Bestaande HTMX toggle-endpoint

**Bevinding**: `voorraad_toggle` (`POST /voorraad/{product_id}/status`) retourneert een enkelvoudig `voorraaditem.html` fragment en hoeft niet op de hoogte te zijn van afdeling. De `afdeling` op het item-dict is alleen relevant voor de list-rendering, niet voor de toggle-update.

**Beslissing**: `voorraad_toggle` wordt niet aangepast.

---

## Beslissing 5: Tests conftest aanpassen

**Bevinding**: `TEST_VOORRAAD_PRODUCTEN` in `tests/web/conftest.py` bevat alleen producten met `category="Zuivel"`. Voor sorteringstests zijn producten uit meerdere categorieën nodig.

**Beslissing**: `TEST_VOORRAAD_PRODUCTEN` uitbreiden met producten uit VOORRAADKAST- en DIEPVRIES-categorieën. Bestaande tests die alleen op aanwezigheid/toggle testen worden niet geraakt door deze uitbreiding.
