# Feature Specification: Bestel Workflow Aanpassing — Recept-ingrediëntselectie voor Voorraadcheck

**Feature Branch**: `004-bestel-workflow-aanpassing`  
**Created**: 2026-05-15  
**Status**: Draft  
**Input**: User description: "ik wil een aanpassing in de workflow van het bestellen. Na het weekmenu wil ik een scherm waarop de gebruiker per recept kan aangeven welke producten van dat recept wel en niet besteld moeten worden, en hoeveel. Het is eigenlijk het huidige 'Boodschappenlijst' scherm, maar dan een stap eerder, voor de voorraadcheck. Daarna volgt de voorraadcheck zoals die nu is. Na de voorraadcheck hoeft er niet opnieuw een boodschappenlijst gemaakt te worden, in plaats daarvan moet de product matching worden gestart."

## Clarifications

### Session 2026-05-15

- Q: Wat is de rol van de voorraadcheck in de bestelworkflow — filtert of ontvangt hij recept-ingrediënten, of is hij een onafhankelijke stap? → A: De voorraadcheck is een onafhankelijke stap van het weekmenu. In die stap worden voorraadartikelen geselecteerd (bijv. wc-papier, broodbeleg) die naast de recept-ingrediënten besteld moeten worden. De recept-ingrediënten (uit stap 1, de ingredient-selectie) plus de gekozen voorraadartikelen komen samen op de boodschappenlijst die naar product matching gaat.
- Q: Ziet de gebruiker de gecombineerde boodschappenlijst op een overzichtsscherm vóórdat product matching start, of begint matching direct na bevestiging van de voorraadcheck? → A: Matching start direct na bevestiging van de voorraadcheck — geen apart overzichtsscherm.
- Q: Worden gelijke ingrediënten uit verschillende recepten samengevoegd op de boodschappenlijst, of blijven ze als aparte regels per recept staan? → A: Gelijke ingrediënten worden samengevoegd — hoeveelheden worden opgeteld tot één regel op de boodschappenlijst.
- Q: Als de gebruiker vanuit de voorraadcheck terugnavigeert naar het ingredient-selectiescherm, blijft zijn selectie dan bewaard of begint hij opnieuw? → A: Selectie wordt bewaard — de gebruiker ziet zijn eerder gemaakte keuzes nog staan.

### Session 2026-05-16

- Q: Als het weekmenu gewijzigd is (recept toegevoegd of verwijderd) nadat de gebruiker de ingredient-selectie al gestart heeft, wat moet er dan met de eerdere selectie gebeuren? → A: Volledige reset — de ingredient-selectie start altijd opnieuw als het weekmenu gewijzigd is; alle ingrediënten staan standaard aangevinkt.
- Q: Waar navigeert de back-button op de "controleer matches" (match-review) pagina naartoe? → A: Naar de Voorraadcheck — de directe voorgaande stap in de flow.
- Q: Moet het ingredient-selectiescherm de checkbox- en hoeveelheden-selector-componenten hergebruiken van `/boodschappen`, of is visuele gelijkenis voldoende? → A: Exacte hergebruik van dezelfde Jinja2/HTMX-componenten als `/boodschappen` — geen aparte implementatie.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Selecteer ingrediënten per recept vóór voorraadcheck (Priority: P1)

Na het bekijken of samenstellen van het weekmenu gaat de gebruiker naar een nieuw scherm. Dit scherm toont alle recepten uit het weekmenu met hun ingrediënten en hoeveelheden. Per ingredient kan de gebruiker aangeven of het besteld moet worden (standaard: alle ingrediënten aangevinkt) en de hoeveelheid aanpassen. Na het afronden van deze selectie gaat de gebruiker door naar de voorraadcheck.

**Why this priority**: Dit is de kern van de feature — zonder dit nieuwe scherm bestaat de rest van de workflow-aanpassing niet. Het vervangt de huidige positie van de boodschappenlijst.

**Independent Test**: Start het bestelproces vanuit het weekmenu en controleer dat het nieuwe selectiescherm verschijnt met alle recepten en hun ingrediënten, en dat de gebruiker per ingredient kan aan- en uitvinken en hoeveelheden kan wijzigen voordat hij verder gaat naar de voorraadcheck.

**Acceptance Scenarios**:

1. **Given** een weekmenu is samengesteld, **When** de gebruiker het bestelproces start vanuit het weekmenu, **Then** verschijnt het ingredient-selectiescherm met alle recepten van de week, elk uitklapbaar of direct zichtbaar met hun ingrediënten en standaardhoeveelheden
2. **Given** het selectiescherm is geopend, **When** de gebruiker een ingredient uitvinkt, **Then** is dat ingredient niet meer geselecteerd voor bestelling en visueel duidelijk uitgegrijsd of doorgestreept
3. **Given** het selectiescherm is geopend, **When** de gebruiker de hoeveelheid van een ingredient aanpast, **Then** wordt de aangepaste hoeveelheid gebruikt in de rest van de workflow
4. **Given** de gebruiker zijn selectie heeft gemaakt, **When** hij op "Verder" of "Controleer voorraad" klikt, **Then** gaat hij door naar de voorraadcheck met de door hem geselecteerde ingrediënten en hoeveelheden
5. **Given** de gebruiker alle ingrediënten van een recept uitvinkt, **When** hij verder gaat, **Then** wordt dat recept niet meegenomen in de rest van de workflow

---

### User Story 2 - Voorraadcheck voegt voorraadartikelen toe aan de bestelling (Priority: P2)

Na de ingredient-selectie gaat de gebruiker naar de voorraadcheck. Dit is een onafhankelijke stap van het weekmenu: hier selecteert de gebruiker voorraadartikelen (bijv. wc-papier, broodbeleg) die los van de recepten besteld moeten worden. De voorraadcheck-stap zelf is ongewijzigd. Na afronding worden de geselecteerde recept-ingrediënten (stap 1) en de gekozen voorraadartikelen (stap 2) samengevoegd tot de boodschappenlijst.

**Why this priority**: De voorraadcheck is een bestaande, ongewijzigde stap. De wijziging zit alleen in wat er daarna gebeurt: in plaats van een apart boodschappenlijstscherm, start direct de product matching op de gecombineerde lijst.

**Independent Test**: Doorloop weekmenu → ingredient-selectie → voorraadcheck en controleer dat de voorraadcheck ongewijzigd werkt en dat de geselecteerde voorraadartikelen na bevestiging samen met de recept-ingrediënten beschikbaar zijn voor matching.

**Acceptance Scenarios**:

1. **Given** de gebruiker heeft de ingredient-selectie afgerond, **When** hij de voorraadcheck opent, **Then** toont de voorraadcheck zijn gebruikelijke interface voor het selecteren van voorraadartikelen — ongewijzigd ten opzichte van de huidige implementatie
2. **Given** de gebruiker heeft voorraadartikelen geselecteerd in de voorraadcheck, **When** hij de voorraadcheck bevestigt, **Then** worden de gekozen voorraadartikelen samengevoegd met de geselecteerde recept-ingrediënten uit stap 1 tot één boodschappenlijst
3. **Given** de voorraadcheck is bevestigd, **When** de samengevoegde boodschappenlijst klaar is, **Then** wordt het product-matchingproces direct gestart op de gecombineerde lijst (geen apart "boodschappenlijst genereren"-stap tussendoor)

---

### User Story 3 - Product matching start direct na voorraadcheck (Priority: P3)

Na het afronden van de voorraadcheck wordt het product-matchingproces direct gestart. Er is geen aparte stap meer om een boodschappenlijst aan te maken of te bevestigen tussen voorraadcheck en matching.

**Why this priority**: Dit stroomlijnt de workflow en voorkomt onnodige duplicatie van wat de gebruiker al gedaan heeft in stap 1.

**Independent Test**: Doorloop de volledige flow en controleer dat na de voorraadcheck direct de bestaande match-review (003-ingredient-match-review) wordt gestart zonder tussenliggende boodschappenlijststap.

**Acceptance Scenarios**:

1. **Given** de voorraadcheck is afgerond en bevestigd, **When** de boodschappenlijst wordt samengesteld, **Then** bevat die lijst zowel de geselecteerde recept-ingrediënten (uit stap 1) als de gekozen voorraadartikelen (uit de voorraadcheck), en start het product-matchingproces direct
2. **Given** de gebruiker heeft in stap 1 alle recept-ingrediënten uitgevinkt én in de voorraadcheck geen artikelen geselecteerd, **When** hij wil bevestigen, **Then** wordt een melding getoond dat de boodschappenlijst leeg is en kan hij niet verder

---

### Edge Cases

- Wat gebeurt er als de gebruiker in stap 1 alle ingrediënten uitvinkt en toch verder gaat?
- Wat als het weekmenu geen recepten bevat (bijv. een week met alleen "niet thuis"-dagen)? De gebruiker kan dan wel de voorraadcheck doen en zo toch een boodschappenlijst samenstellen.
- Wat als de gebruiker teruggaat vanuit de voorraadcheck naar het ingredient-selectiescherm? → Zijn selectie wordt bewaard; hij ziet de eerder gemaakte keuzes nog staan.
- Wat als het weekmenu gewijzigd is (recept toegevoegd of verwijderd) nadat de ingredient-selectie al gestart was? → De ingredient-selectie wordt volledig gereset: alle ingrediënten van het nieuwe weekmenu staan standaard aangevinkt. Een gewijzigd weekmenu maakt een eerder gemaakte selectie stale.
- Hoeveelheden worden per ingredient ingesteld, niet per portie — wat als de gebruiker een decimale hoeveelheid invoert voor een ingredient dat alleen in hele eenheden beschikbaar is?
- Wat als de gebruiker geen voorraadartikelen selecteert in de voorraadcheck? De boodschappenlijst bevat dan alleen de recept-ingrediënten — dit is een geldig scenario.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Het systeem MOET na het weekmenu een nieuw ingredient-selectiescherm tonen voordat de voorraadcheck wordt gestart
- **FR-002**: Het selectiescherm MOET alle recepten uit het weekmenu tonen, gegroepeerd per recept, met de naam en hoeveelheid van elk ingredient
- **FR-003**: De gebruiker MOET elk ingredient individueel kunnen aan- of uitvinken (standaard: alle ingrediënten aangevinkt)
- **FR-004**: De gebruiker MOET de hoeveelheid van elk ingredient kunnen aanpassen voordat hij verder gaat
- **FR-005**: Na de ingredient-selectie MOET het systeem de geselecteerde recept-ingrediënten (met aangepaste hoeveelheden) bewaren zodat zij later samengevoegd kunnen worden met de voorraadartikelen
- **FR-006**: Het voorraadcheck-scherm MOET ongewijzigd functioneren als zelfstandige stap voor het selecteren van voorraadartikelen (zoals wc-papier, broodbeleg) — het scherm ontvangt geen recept-ingrediënten als invoer. Het bevestig-endpoint (`POST /voorraad/bevestig`) leest de opgeslagen recept-selectie uit stap 1 en combineert deze met de gekozen voorraadartikelen
- **FR-007**: Na het bevestigen van de voorraadcheck MOET het systeem de geselecteerde recept-ingrediënten en de gekozen voorraadartikelen samenvoegen tot één boodschappenlijst en het product-matchingproces direct starten op die gecombineerde lijst — zonder een tussenliggend overzichtsscherm
- **FR-010**: Bij het samenvoegen tot de boodschappenlijst MOETEN gelijke ingrediënten uit verschillende recepten worden geaggregeerd: hoeveelheden worden opgeteld tot één regel per uniek ingredient (op basis van ingredientnaam en eenheid)
- **FR-011**: De ingredient-selectie MOET bewaard blijven zolang de gebruiker actief is binnen de bestelflow — terugnavigeren vanuit de voorraadcheck naar het selectiescherm MOET de eerder gemaakte keuzes tonen
- **FR-012**: Als het weekmenu gewijzigd is (recept toegevoegd of verwijderd) ten opzichte van de aktieve ingredient-selectie, MOET het systeem de ingredient-selectie volledig resetten: alle ingrediënten van het nieuwe weekmenu worden aangevinkt weergegeven
- **FR-013**: Het ingredient-selectiescherm MOET de checkbox-component en hoeveelheden-selector hergebruiken van de `/boodschappen`-pagina — dezelfde Jinja2/HTMX-implementatie, geen aparte component
- **FR-008**: Als de gecombineerde boodschappenlijst (recept-ingrediënten + voorraadartikelen) leeg is, MOET het systeem de gebruiker waarschuwen en niet toestaan om door te gaan
- **FR-009**: De navigatiestroom MOET zijn: Weekmenu → Ingredient-selectie → Voorraadcheck → [samenvoegen tot boodschappenlijst] → Product matching → Match-review (bestaande 003-flow). Terugnavigatie: Match-review → Voorraadcheck → Ingredient-selectie → Weekmenu. Als `week_menu` ontbreekt in `app.state`, MAG `GET /ingredient-selectie` redirecten naar `/week`

### Key Entities

- **WeekMenu**: Het samengestelde weekmenu met recepten per dag; input voor stap 1 (ingredient-selectie)
- **IngredientSelectie**: De door de gebruiker gemaakte selectie in stap 1 — per recept-ingredient: geselecteerd (ja/nee) en aangepaste hoeveelheid; wordt bewaard totdat de voorraadcheck afgerond is
- **GeselecteerdIngredient**: Een ingredient uit een recept met een vinkje en hoeveelheid, zoals ingesteld door de gebruiker in stap 1
- **Voorraadcheck**: Bestaande, ongewijzigde stap waarbij de gebruiker voorraadartikelen (los van het weekmenu, bijv. wc-papier, broodbeleg) selecteert die ook besteld moeten worden; is een onafhankelijke stap van de ingredient-selectie
- **Boodschappenlijst**: De gecombineerde lijst van geselecteerde recept-ingrediënten (geaggregeerd per uniek ingredient) en gekozen voorraadartikelen (uit Voorraadcheck); dit is de input voor het product-matchingproces

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: De gebruiker kan de volledige bestelling doorlopen (weekmenu → selectie → voorraadcheck → matching) in minder stappen dan de huidige flow
- **SC-002**: (Ontwerpdoel) Het selectiescherm is bruikbaar voor een volledig weekmenu (max. 7 recepten × ~15 ingrediënten = max. ~105 items); initialisatietijd < 100ms (in-memory operatie). Niet getest via geautomatiseerde benchmark — zie Assumptions
- **SC-003**: Alle geselecteerde ingrediënten en hoeveelheden worden foutloos doorgegeven aan de voorraadcheck en vervolgens aan de product-matching — geen ingrediënten gaan verloren of worden onbedoeld gewijzigd
- **SC-004**: Na de voorraadcheck verschijnt de match-review zonder extra tussenstap; de gebruiker hoeft niet opnieuw een actie te ondernemen om de matching te starten

## Assumptions

- De gebruiker werkt op een mobiel scherm (iPhone 13 viewport, 390×844), consistent met de bestaande UI-conventi
- Uitgevinkte ingrediënten worden niet opgeslagen of onthouden tussen sessies — de selectie begint elke keer standaard met alles aangevinkt
- De hoeveelheidsaanpassing is een vrij in te vullen getal (bijv. 2, 0.5) per ingredient; eenheid wordt niet gewijzigd
- Handmatige artikelen (vrije tekst, niet aan een recept gekoppeld) vallen buiten de scope van dit selectiescherm — zij stromen ongewijzigd door naar de voorraadcheck en matching
- De bestaande product-matching flow (003-ingredient-match-review) wordt ongewijzigd hergebruikt als laatste stap
- "Ingredient-selectiescherm" vervangt de huidige positie van de boodschappenlijst; de boodschappenlijst als apart scherm valt na deze feature buiten de normale bestelflow
