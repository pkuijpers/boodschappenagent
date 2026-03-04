---
name: tdd-step
description: Implement a single TDD step from a test plan. Use this skill whenever the user references a test plan step or story number, says things like "implementeer S3", "voer stap 4 uit", "implementeer de volgende stap uit het testplan", "doe TDD stap X", or when they want to implement a specific numbered feature step following test-driven development. Always invoke this skill before starting any TDD implementation work — even if the user just says "volgende stap" or "begin met de implementatie".
---

# TDD Step Implementation

## Werkwijze

### 1. Begrijp de stap volledig
Lees het testplan (doorgaans `docs/testplan.md` of een vergelijkbaar bestand) en zoek de exacte stap op. Let specifiek op:
- De **exacte naamgeving** van routes, functies, klassen en templates — gebruik precies wat er staat, verzin niets
- De acceptatiecriteria: wat moet de test verifiëren?
- Welke bestaande code geraakt wordt

### 2. Lees de bestaande code eerst
Voordat je tests schrijft, lees de relevante bestaande bestanden. Dit voorkomt dat je dingen dupliceert of tegenstrijdig implementeert.

### 3. Schrijf de falende test(s) (Rood)
- Schrijf de test(s) die de gewenste functionaliteit beschrijven
- Gebruik de **exact** in het testplan gespecificeerde namen — geen alternatieve benamingen
- Controleer dat de tests falen met de test-reporter subagent

Draai tests via de `test-reporter` subagent (voorkeur) of direct via `uv run pytest -v` als dat niet beschikbaar is. Verifieer altijd dat de tests falen *vóór* je de implementatie schrijft — dit bewijst dat de test daadwerkelijk iets test.

### 4. Implementeer de minimale code (Groen)
- Schrijf alleen de code die nodig is om de tests te laten slagen — niet meer
- Voeg geen extra features toe die niet in de stap staan
- Houd het simpel

### 5. Verifieer dat alle tests slagen
Draai de volledige testsuite (test-reporter of `uv run pytest`). Controleer dat:
- De nieuwe tests slagen
- Geen bestaande tests zijn gebroken

### 6. Refactor (Blauw)
Nu de tests groen zijn, verbeter de code zonder gedrag te wijzigen. Kijk actief naar:
- **Duplicatie**: zelfde logica op meerdere plekken? Extraheer naar een gedeelde functie of helper
- **Code smells**: lange functies, onduidelijke namen, te diepe nesting, magic values
- **Consistentie**: sluit aan bij de stijl en patronen van de omliggende code

Draai na de refactor opnieuw de `test-reporter` subagent om te bevestigen dat alles nog groen is.

### 7. Code kwaliteit
```bash
uv run ruff check --fix .   # Fix lint-issues
uv run ruff format .        # Format code
```
Los alle ruff-meldingen op voor je klaar bent.

### 8. Rapporteer en vraag om commit
- Geef een korte samenvatting van wat je hebt geïmplementeerd
- Noem eventuele afwijkingen van het testplan (en waarom)
- Vraag of de gebruiker wil committen
