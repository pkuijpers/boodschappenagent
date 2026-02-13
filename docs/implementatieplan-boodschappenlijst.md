# Implementatieplan: Boodschappenlijst Generator

## Context

Fase 3 van het boodschappen-automatiseringsplan: een module die een `WeekMenu` omzet naar een geaggregeerde boodschappenlijst. Ingredienten uit meerdere recepten worden geschaald, genormaliseerd en samengevoegd. De gebruiker wil slim samenvoegen met zichtbaarheid van originele namen voor controle.

**Scope**: Alleen WeekMenu → boodschappenlijst. Standaard verse producten, handmatige toevoegingen en voorraadbeheer komen in latere fases.

---

## Module structuur

```
src/boodschappenagent/boodschappenlijst/
    __init__.py       # Exports
    models.py         # BoodschappenRegel, Boodschappenlijst
    normalizer.py     # IngredientNormalizer
    generator.py      # BoodschappenlijstGenerator

tests/
    test_boodschappenlijst_models.py
    test_ingredient_normalizer.py
    test_boodschappenlijst_generator.py
```

---

## Data models (`models.py`)

### BoodschappenRegel (frozen dataclass)

| Veld | Type | Beschrijving |
|------|------|-------------|
| `naam` | `str` | Genormaliseerde ingredientnaam |
| `hoeveelheid` | `float` | Totale afgeronde hoeveelheid |
| `eenheid` | `str` | Eenheid |
| `originele_namen` | `frozenset[str]` | Alle originele namen (voor verificatie) |
| `opmerkingen` | `list[str]` | Unieke opmerkingen uit bronnen |

- Property `display_naam`: toont `"ui (ook: uien)"` als er aliassen zijn
- `to_dict()` / `from_dict()` (originele_namen als gesorteerde list in JSON)
- Validatie: naam, eenheid niet leeg; originele_namen niet leeg

### Boodschappenlijst (frozen dataclass)

| Veld | Type | Beschrijving |
|------|------|-------------|
| `week_start` | `str` | ISO date YYYY-MM-DD |
| `regels` | `list[BoodschappenRegel]` | Alfabetisch gesorteerd |

---

## Normalizer (`normalizer.py`)

### IngredientNormalizer

**Naam-normalisatie** via synoniemenwoordenboek (case-insensitive):

```python
_NAAM_SYNONIEMEN = {
    "uien": "ui",
    "biologische ui": "ui",
    "biologische rode ui": "rode ui",
    "knoflookteen": "knoflook",       # + unit stuks→teen
    "passata di pomodoro": "passata",
    "platte peterselie": "peterselie",
    "vers bladerdeeg": "bladerdeeg",
    "biologische tuinkers": "tuinkers",
    "sjalotten": "sjalot",
}
```

**Eenheid-normalisatie**: afkortingen naar volledig (`el`→`eetlepel`, `tl`→`theelepel`, `g`→`gram`, `l`→`liter`), `snuf`→`naar smaak`.

**Niet-aggregeerbare eenheden**: `naar smaak`, `snuf`, `mespunt` → hoeveelheid wordt altijd 1.

**API**:
- `normaliseer(naam, eenheid) -> (str, str)` — geeft genormaliseerde naam+eenheid
- `is_niet_aggregeerbaar(eenheid) -> bool`
- Constructor accepteert `extra_synoniemen` voor uitbreidbaarheid

Geen automatische prefix-stripping (te risicovol). Geen gram↔ml conversie (dichtheidsafhankelijk).

---

## Generator (`generator.py`)

### BoodschappenlijstGenerator

**Dependencies** (constructor injection): `IngredientNormalizer`, `PortionCalculator`

**Algoritme `genereer(week_menu: WeekMenu) -> Boodschappenlijst`**:

1. Loop door `week_menu.geplande_dagen`
2. Per dag: `recept.scale_to_portions(personen)` → **ruwe** geschaalde waarden (niet PortionCalculator, want die rondt te vroeg af)
3. Per ingrediënt: normaliseer `(naam, eenheid)`, accumuleer in dict met key `(norm_naam, norm_eenheid)`
4. Per groep: tel hoeveelheden op (of hoeveelheid=1 voor niet-aggregeerbaar), rond af via `PortionCalculator.round_quantity()`, verzamel originele namen + opmerkingen
5. Sorteer alfabetisch op naam
6. Return `Boodschappenlijst(week_start=week_menu.week_start, regels=...)`

**Kernbeslissing**: afronding NA aggregatie (nauwkeuriger: `round(123+123+123) = 370` vs `125+125+125 = 375`).

---

## TDD volgorde

### Fase 1: Models (tests eerst, dan implementatie)
- `TestBoodschappenRegel`: create, frozen, validatie, display_naam, to_dict/from_dict roundtrip
- `TestBoodschappenlijst`: create, frozen, lege lijst, validatie, to_dict/from_dict roundtrip

### Fase 2: Normalizer
- `TestNormaliseerNaam`: identiek, case-insensitive, synoniemen (ui/uien, knoflookteen, passata), onbekend doorlaten, extra_synoniemen
- `TestNormaliseerEenheid`: snuf→naar smaak, el→eetlepel, tl→theelepel, g→gram
- `TestIsNietAggregeerbaar`: naar smaak/snuf/mespunt ja, gram/stuks nee

### Fase 3: Generator
- `TestGenereerLeegMenu`: leeg weekmenu, alleen niet-thuis dagen
- `TestGenereerEnkelRecept`: ongeschaald, geschaald, naar-smaak items
- `TestGenereerMeerdereRecepten`: geen overlap, zelfde ingrediënt aggregeert, zelfde naam andere eenheid apart, synoniemen samengevoegd
- `TestAfrondingNaAggregatie`: sum-then-round correctheid
- `TestOpmerkingen`: verzamelen, None filteren, deduplicatie
- `TestOrigineleNamen`: bij synoniemen alle varianten, bij identiek één naam
- `TestSortering`: regels alfabetisch

### Fase 4: Package exports + ruff + pytest --cov

---

## Relevante bestaande bestanden

| Bestand | Hergebruik |
|---------|-----------|
| `src/boodschappenagent/models/ingredient.py` | Ingredient dataclass, scale() |
| `src/boodschappenagent/planner/models.py` | WeekMenu, DagPlanning, geplande_dagen, to_dict/from_dict patroon |
| `src/boodschappenagent/utils/portion_calculator.py` | PortionCalculator.round_quantity() voor finale afronding |
| `src/boodschappenagent/models/recipe.py` | Recipe.scale_to_portions() voor ruwe schaling |
| `tests/test_planner_models.py` | Test patronen: _make_recipe(), class-based, frozen assertions |

---

## Edge cases

| Case | Gedrag |
|------|--------|
| Leeg WeekMenu (geen dagen) | Lege regels lijst |
| Alle dagen niet-thuis (personen=0) | Lege regels lijst |
| Zelfde ingrediënt, andere eenheid | Twee aparte regels (NIET samenvoegen) |
| "knoflookteen" stuks + "knoflook" teen | Normalizer mapt naar knoflook/teen, aggregeert |
| Meerdere "naar smaak" entries | Eén regel met hoeveelheid=1 |
| "peper" naar smaak + "peper" snuf | snuf→naar smaak, één regel |
| Zelfde recept op meerdere dagen | Correct geschaald per dag, dan opgeteld |

---

## Verificatie

```bash
uv run pytest tests/test_boodschappenlijst_models.py tests/test_ingredient_normalizer.py tests/test_boodschappenlijst_generator.py -v
uv run pytest --cov=boodschappenagent.boodschappenlijst
uv run ruff check src/boodschappenagent/boodschappenlijst/
uv run ruff format --check src/boodschappenagent/boodschappenlijst/
```
