# Plan: Recepten Digitaliseren

Dit document beschrijft het gedetailleerde plan voor fase 1 van het boodschappenagent project: het digitaliseren van de receptendatabase.

---

## 1. Datamodel Ontwerp

Volgens het globale plan heeft een recept de volgende attributen:

```python
@dataclass
class Ingredient:
    naam: str                    # "ui", "knoflook", "gehakt"
    hoeveelheid: float           # 200, 2, 0.5
    eenheid: str                 # "gram", "stuks", "eetlepel", "teen"
    opmerking: str | None        # "fijngesneden", "vers"

@dataclass
class Recipe:
    id: str                      # UUID of slug
    naam: str                    # "Spaghetti Bolognese"
    categorie: str               # "pasta", "ovenschotel", "soep", "stamppot"
    seizoenen: list[str]         # ["herfst", "winter"] of ["alle"]
    basis_porties: int           # Standaard 2
    ingredienten: list[Ingredient]
    tags: list[str]              # ["vlees", "italiaans", "budget"]
    bereidingstijd_min: int      # 30 (minuten)
    bereidingswijze: str | None  # Optionele instructies
    bron: str | None             # "oma's kookboek", "AH Allerhande"
```

---

## 2. Opslagformaat Keuze

**Aanbeveling: JSON-bestanden**

| Aspect | JSON | SQLite |
|--------|------|--------|
| Leesbaarheid | Direct te bewerken | Tooling nodig |
| Versiebeheer | Git-friendly | Binair bestand |
| Eenvoud | Geen schema migraties | Migraties nodig |
| Query's | In-memory filtering | SQL queries |
| Schaalbaarheid | ~200 recepten prima | Duizenden recepten |

Voor ~200 recepten is JSON nog steeds werkbaar. Laden van 200 JSON-bestanden in memory is snel genoeg. Kan later naar SQLite migreren indien performance een probleem wordt.

---

## 3. Projectstructuur Uitbreiding

```
src/boodschappenagent/
├── __init__.py
├── ah_client.py              # Bestaand
├── models/
│   ├── __init__.py
│   ├── recipe.py             # Recipe, Ingredient dataclasses
│   └── enums.py              # Seizoen, Categorie, Complexiteit
├── repository/
│   ├── __init__.py
│   └── recipe_repository.py  # CRUD operaties
└── utils/
    └── portion_calculator.py # Portie schaling

data/
└── recipes/
    ├── pasta/
    │   ├── spaghetti-bolognese.json
    │   └── carbonara.json
    └── ovenschotel/
        └── lasagne.json
```

---

## 4. Implementatie Stappen (TDD)

Alle code wordt geschreven volgens Test-Driven Development: eerst een falende test, dan de minimale code om de test te laten slagen, daarna refactoren.

| Stap | Beschrijving | Test bestand |
|------|--------------|--------------|
| 4.1 | `Ingredient` dataclass met validatie | `test_ingredient.py` |
| 4.2 | `Recipe` dataclass met validatie | `test_recipe.py` |
| 4.3 | Enums: `Seizoen`, `Categorie` | `test_enums.py` |
| 4.4 | `RecipeRepository`: laden/opslaan JSON | `test_recipe_repository.py` |
| 4.5 | Portieberekening (ingrediënten schalen) | `test_portion_calculator.py` |
| 4.6 | Zoeken/filteren op tags, seizoen, categorie | `test_recipe_search.py` |

### 4.1 Ingredient Dataclass

- Velden: `naam`, `hoeveelheid`, `eenheid`, `opmerking`
- Validatie: hoeveelheid > 0, naam niet leeg
- Methode: `scale(factor: float)` voor portieberekening

### 4.2 Recipe Dataclass

- Alle velden uit het datamodel
- Validatie: verplichte velden, geldige waardes
- Methode: `scale_to_portions(aantal: int)`

### 4.3 Enums

```python
class Seizoen(Enum):
    LENTE = "lente"
    ZOMER = "zomer"
    HERFST = "herfst"
    WINTER = "winter"
    ALLE = "alle"

class Categorie(Enum):
    PASTA = "pasta"
    OVENSCHOTEL = "ovenschotel"
    SOEP = "soep"
    STAMPPOT = "stamppot"
    ROERBAK = "roerbak"
    SALADE = "salade"
    OVERIG = "overig"
```

### 4.4 RecipeRepository

- `load(path: Path) -> Recipe` - Laad één recept uit JSON
- `load_all(directory: Path) -> list[Recipe]` - Laad alle recepten
- `save(recipe: Recipe, path: Path)` - Sla recept op als JSON
- `delete(path: Path)` - Verwijder recept

### 4.5 Portieberekening

- Input: recept + gewenst aantal porties
- Output: recept met geschaalde ingrediënten
- Afrondingslogica voor praktische hoeveelheden

### 4.6 Zoeken en Filteren

- Filter op seizoen (huidig of specifiek)
- Filter op categorie
- Filter op tags (AND/OR)
- Zoeken op naam (fuzzy matching)

---

## 5. Recepten Digitaliseren via Foto's

De bestaande receptenbibliotheek (~200 recepten) wordt gedigitaliseerd door foto's te maken en deze met AI om te zetten naar het doelformaat.

### Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Foto maken     │────▶│  AI extractie   │────▶│  Review &       │
│  van recept     │     │  (Claude/GPT)   │     │  correctie      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  Opslaan als    │
                                                │  JSON           │
                                                └─────────────────┘
```

### Fase 5a: Pilot (eerste 10 recepten)

1. Fotografeer 10 recepten uit de bibliotheek
2. Test AI-extractie met verschillende promptstrategieën
3. Valideer of het datamodel alle recepttypes aankan
4. Bepaal gemiddelde tijd per recept (foto + review)

### Fase 5b: Bulk digitalisatie (~200 recepten)

**Fotograferen:**
- Batch-gewijs foto's maken (bijv. 20 per sessie)
- Goede belichting, leesbare tekst
- Opslaan met duidelijke naamgeving

**AI-extractie tool:**
```bash
uv run python -m boodschappenagent.cli recipe digitize foto.jpg
```

- Stuurt foto naar AI (Claude API)
- Ontvangt gestructureerde JSON
- Slaat op in `data/recipes/draft/` voor review

**Review interface:**
- Toon originele foto naast geëxtraheerde data
- Mogelijkheid tot correcties
- Verplaats naar definitieve locatie na goedkeuring

### Fase 5c: Handmatige invoer (fallback)

Voor recepten die niet goed digitaliseren:

```bash
uv run python -m boodschappenagent.cli recipe add
```

### AI Prompt Strategie

De AI krijgt:
1. De foto van het recept
2. Het doelformaat (JSON schema)
3. Instructies voor standaardisatie (eenheden, categorieën)

**Voorbeeld prompt:**
```
Analyseer deze foto van een recept en extraheer de informatie naar JSON.

Gebruik dit formaat:
- eenheden: gram, ml, stuks, eetlepel, theelepel, teen, snuf, naar smaak
- seizoenen: lente, zomer, herfst, winter, alle
- categorie: pasta, ovenschotel, soep, stamppot, roerbak, salade, overig

Genereer een slug-id gebaseerd op de receptnaam.
```

### Voorbeeld Output JSON

```json
{
  "id": "spaghetti-bolognese",
  "naam": "Spaghetti Bolognese",
  "categorie": "pasta",
  "seizoenen": ["alle"],
  "basis_porties": 2,
  "ingredienten": [
    {"naam": "spaghetti", "hoeveelheid": 200, "eenheid": "gram", "opmerking": null},
    {"naam": "rundergehakt", "hoeveelheid": 250, "eenheid": "gram", "opmerking": null},
    {"naam": "ui", "hoeveelheid": 1, "eenheid": "stuks", "opmerking": "fijngesneden"},
    {"naam": "knoflook", "hoeveelheid": 2, "eenheid": "teen", "opmerking": "geperst"},
    {"naam": "passata", "hoeveelheid": 400, "eenheid": "gram", "opmerking": null},
    {"naam": "tomatenpuree", "hoeveelheid": 2, "eenheid": "eetlepel", "opmerking": null},
    {"naam": "Parmezaanse kaas", "hoeveelheid": 50, "eenheid": "gram", "opmerking": "geraspt"}
  ],
  "tags": ["vlees", "italiaans", "budget", "kindvriendelijk"],
  "bereidingstijd_min": 35,
  "bereidingswijze": "1. Kook de spaghetti...",
  "bron": "receptenbibliotheek"
}
```

---

## 6. Validatie & Constraints

| Veld | Constraint |
|------|------------|
| `id` | Uniek, lowercase, geen spaties (slug) |
| `naam` | Niet leeg, max 100 karakters |
| `hoeveelheid` | > 0 |
| `basis_porties` | >= 1 |
| `seizoenen` | Uit: lente, zomer, herfst, winter, alle |
| `categorie` | Uit voorgedefinieerde enum |
| `bereidingstijd_min` | > 0 |

---

## 7. Acceptatiecriteria

Fase 1 is compleet wanneer:

- [ ] Datamodel geïmplementeerd en getest
- [ ] RecipeRepository werkt met JSON bestanden
- [ ] Portieberekening functioneert correct
- [ ] AI-digitalisatie tool werkend (foto → JSON)
- [ ] Minimaal 10 recepten gedigitaliseerd via foto's (pilot)
- [ ] Zoeken/filteren op seizoen en categorie werkt
- [ ] Alle tests slagen
- [ ] Code voldoet aan ruff linting

Fase 1b (bulk digitalisatie):

- [ ] ~200 recepten gedigitaliseerd en gereviewd
- [ ] Review workflow getest en geoptimaliseerd

---

## 8. Volgende Acties

1. **Models implementeren** - Recipe en Ingredient dataclasses (TDD)
2. **Repository implementeren** - JSON lezen/schrijven (TDD)
3. **Digitalisatie tool bouwen** - Foto → AI → JSON pipeline
4. **Pilot met 10 recepten** - Foto's maken en digitaliseren
5. **Review interface** - Voor correcties na AI-extractie
6. **Bulk digitalisatie** - Resterende ~190 recepten

---

## 9. Relatie met Andere Fases

Na voltooiing van fase 1 kan fase 2 (Menuplanner) starten, die afhankelijk is van:

- Recepten filteren op seizoen
- Recepten filteren op categorie/tags
- Portieberekening per recept

De `RecipeRepository` en `Recipe.scale_to_portions()` vormen de interface voor de menuplanner.
