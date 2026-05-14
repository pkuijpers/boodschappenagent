# Feature Specification: Ingredient Match Review & Correction

**Feature Branch**: `003-ingredient-match-review`  
**Created**: 2026-05-14  
**Status**: Draft  
**Input**: User description: "Niet altijd worden juiste producten gematcht met recepten. Geef na versturen naar AH per item weer wat gematcht is, met mogelijkheid om te corrigeren. Bewaar gematchte artikel IDs bij ingredient."

## Clarifications

### Session 2026-05-14

- Q: Wat is de volgorde van de flow — wordt de AH-lijst aangemaakt vóór of ná de match-review? → A: Eerst alle ingrediënten matchen, dan review en correcties, dan pas de AH-lijst aanmaken. De lijst wordt dus niet aangemaakt vóór de review.
- Q: Kan de gebruiker de AH-lijst aanmaken als één of meer ingrediënten geen match hebben? → A: Nee — alle ingrediënten moeten een match hebben (of handmatig gekoppeld zijn) voordat de lijst aangemaakt kan worden.
- Q: Op welk niveau wordt een gecorrigeerde match opgeslagen? → A: Per ingredientnaam globaal — dezelfde voorkeur geldt voor hetzelfde ingredient in alle recepten.
- Q: Hoe start de gebruiker het match-en-verstuur-proces? → A: De bestaande "verstuur naar AH"-knop triggert nu eerst het matchproces, daarna de review, daarna pas aanmaken bij AH.
- Q: Verschijnen handmatige artikelen ook in het matchoverzicht? → A: Ja, en zij gaan ook door het matchproces. Handmatige artikelen zijn vrije tekstbeschrijvingen (bijv. "oregano", "ibuprofen") zonder gestructureerde product-data — zij worden net als recept-ingrediënten gematcht aan een AH-product en kunnen een opgeslagen voorkeur hebben.
- Q: Waar belandt de gebruiker na het bevestigen en aanmaken van de AH-lijst? → A: Bestaande flow behouden — bevestigingsscherm met een knop om naar de AH-website te gaan om de bestelling af te ronden.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bekijk matchresultaten vóór aanmaken AH-lijst (Priority: P1)

De gebruiker start het proces vanuit de boodschappenlijst. Het systeem matcht automatisch alle items — zowel recept-ingrediënten als handmatige artikelen (vrije tekstbeschrijvingen zoals "oregano" of "ibuprofen") — aan AH-producten en toont een overzicht, nog voordat de lijst bij AH aangemaakt wordt. De gebruiker kan beoordelen of alle koppelingen kloppen en pas daarna de lijst bevestigen.

**Why this priority**: Zonder inzicht in de matches vóór het aanmaken kan de gebruiker niet voorkomen dat verkeerde producten besteld worden. Dit is de basis van de hele feature.

**Independent Test**: Start het match-proces vanuit de boodschappenlijst en controleer dat de matchoverzichtpagina verschijnt met alle ingrediënten en hun gekoppelde producten, zonder dat er al een lijst bij AH aangemaakt is.

**Acceptance Scenarios**:

1. **Given** een boodschappenlijst is klaar, **When** de gebruiker het match-en-verstuur-proces start, **Then** matcht het systeem alle items (recept-ingrediënten én handmatige artikelen) aan AH-producten en toont een overzicht per item (naam, hoeveelheid indien beschikbaar, gekoppeld productnaam, prijs) — de AH-lijst is nog niet aangemaakt
2. **Given** een ingredient waarvoor geen match gevonden kon worden, **When** de gebruiker het matchoverzicht bekijkt, **Then** ziet hij dat ingredient gemarkeerd als "geen match gevonden"
3. **Given** het matchoverzicht wordt getoond, **When** de gebruiker de pagina bekijkt, **Then** zijn alle ingrediënten uit de boodschappenlijst aanwezig in het overzicht

---

### User Story 2 - Corrigeer een onjuiste match (Priority: P2)

De gebruiker kan een onjuist gematcht product vervangen door een alternatief te zoeken en te selecteren vanuit het matchoverzicht.

**Why this priority**: Incorrecte matches zijn het kernprobleem. Zonder correctiemogelijkheid heeft het inzicht weinig waarde.

**Independent Test**: Selecteer een ingredient in het matchoverzicht, zoek een alternatief product, selecteer het, en controleer dat het ingredient nu gekoppeld is aan het nieuwe product.

**Acceptance Scenarios**:

1. **Given** een ingredient met een onjuiste match, **When** de gebruiker op "corrigeren" klikt, **Then** verschijnt een zoekinterface voor AH-producten
2. **Given** de zoekinterface is open, **When** de gebruiker een zoekterm invoert, **Then** ziet hij relevante AH-producten als resultaten
3. **Given** de gebruiker een alternatief product selecteert, **When** de selectie bevestigd wordt, **Then** is het ingredient nu gekoppeld aan het gekozen product en wordt de matchoverzicht bijgewerkt
4. **Given** een ingredient zonder match, **When** de gebruiker een product selecteert, **Then** wordt het ingredient alsnog gekoppeld

---

### User Story 3 - Bewaar voorkeurs-match per ingredient (Priority: P3)

Gecorrigeerde of bevestigde article IDs worden opgeslagen bij het ingredient, zodat toekomstige boodschappenlijsten automatisch het juiste product gebruiken.

**Why this priority**: Opgeslagen voorkeuren voorkomen dat de gebruiker dezelfde correctie elke week opnieuw moet doen.

**Independent Test**: Corrigeer een match, start daarna opnieuw het match-proces met hetzelfde ingredient, en controleer dat de opgeslagen voorkeur automatisch gebruikt wordt zodat de gebruiker geen correctie meer hoeft te doen.

**Acceptance Scenarios**:

1. **Given** een gebruiker heeft een match gecorrigeerd, **When** het match-proces opnieuw gestart wordt met hetzelfde ingredient, **Then** wordt automatisch het eerder opgeslagen article ID gebruikt
2. **Given** een ingredient met opgeslagen voorkeur, **When** dat product niet meer beschikbaar is bij AH, **Then** valt het systeem terug op automatische matching en markeert het ingredient als "voorkeur niet beschikbaar"
3. **Given** een ingredient heeft een opgeslagen voorkeur, **When** de gebruiker een nieuwe correctie doorvoert, **Then** wordt de opgeslagen voorkeur overschreven met het nieuwe article ID

---

### Edge Cases

- Wat gebeurt er als AH geen zoekresultaten retourneert voor een ingredient?
- Wat als een opgeslagen article ID niet meer bestaat bij AH?
- Wat als een ingredient structureel niet te matchen is — kan de gebruiker het handmatig overslaan of blijft de bevestigingsknop dan altijd geblokkeerd?
- Wat als twee recepten hetzelfde ingredient bevatten maar met andere hoeveelheden — de voorkeur wordt per ingredientnaam opgeslagen (niet per recept), dus de gebruiker krijgt altijd hetzelfde product aangeboden.
- Wat als de verbinding met AH wegvalt tijdens het corrigeren?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wanneer de gebruiker het verstuurproces start, MOET het systeem eerst alle items matchen aan AH-producten — zowel recept-ingrediënten als handmatige artikelen — en een matchoverzicht tonen vóórdat de AH-lijst aangemaakt wordt
- **FR-002**: Het matchoverzicht MOET per ingredient minimaal tonen: ingredientnaam, gevraagde hoeveelheid, gekoppeld productnaam, en productprijs
- **FR-003**: Gebruiker MOET voor elk ingredient een correctieactie kunnen starten vanuit het matchoverzicht
- **FR-004**: Systeem MOET bij correctie een zoekfunctie bieden die AH-producten doorzoekt op naam
- **FR-005**: Gebruiker MOET een zoekresultaat kunnen selecteren als vervangende match voor een ingredient
- **FR-006**: Systeem MOET na bevestiging het article ID van het geselecteerde product opslaan bij het betreffende ingredient
- **FR-007**: Systeem MOET bij een volgend matchproces met hetzelfde ingredient het opgeslagen article ID gebruiken in plaats van opnieuw te matchen
- **FR-008**: Systeem MOET ingrediënten zonder gevonden match duidelijk markeren in het overzicht
- **FR-009**: Gebruiker MOET vanuit het matchoverzicht de AH-lijst kunnen aanmaken zodra alle ingrediënten een match hebben
- **FR-010**: De AH-lijst mag pas aangemaakt worden nadat de gebruiker het matchoverzicht heeft bevestigd en alle ingrediënten een match hebben
- **FR-011**: De bevestigingsknop voor aanmaken van de AH-lijst MOET uitgeschakeld (niet klikbaar) zijn zolang er één of meer ingrediënten zonder match zijn

### Key Entities

- **Recept-ingredient**: Afkomstig uit een recept — heeft naam, eenheid, hoeveelheid, en optioneel een opgeslagen `preferred_article_id`
- **Handmatig artikel**: Vrije tekstbeschrijving toegevoegd door de gebruiker (bijv. "oregano", "ibuprofen") — heeft alleen een naam en optioneel een opgeslagen `preferred_article_id`; beide typen gaan door hetzelfde matchproces
- **Match Result**: Koppeling tussen een item (recept-ingredient of handmatig artikel) en een AH-product voor een specifieke boodschappenlijst (article ID, productnaam, prijs, beschikbaarheid)
- **AH Product**: Article ID, naam, prijs, eenheid, beschikbaarheid (zoekresultaat van AH)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Na het starten van het match-proces ziet de gebruiker het volledige matchoverzicht binnen één schermwissel, vóórdat de AH-lijst aangemaakt wordt
- **SC-002**: Een incorrecte match corrigeren kost de gebruiker maximaal 3 interacties (klik corrigeren → zoeken → selecteren)
- **SC-003**: Bij een herhaalde boodschappenlijst met eerder gecorrigeerde ingrediënten worden alle opgeslagen voorkeuren automatisch toegepast zonder gebruikersactie
- **SC-004**: Ingrediënten zonder match zijn direct herkenbaar in het overzicht zonder additionele uitleg te hoeven lezen

## Assumptions

- De AH-integratie (aanmaken van een lijst bij AH) is al operationeel; deze feature voegt een match-en-review stap toe vóór het aanmaken van de lijst — de volgorde wordt: match alle ingrediënten → review en corrigeer → maak pas dan de AH-lijst aan
- Het opslaan van `preferred_article_id` gebeurt op niveau van de ingredient-naam (niet per recept), zodat dezelfde voorkeur geldt voor hetzelfde ingredient in alle recepten
- De web UI (FastAPI + HTMX) is het primaire interface voor deze feature; geen native app
- Ingrediënten worden geïdentificeerd op naam voor het opslaan van voorkeuren; homoniemen (bijv. "ui" als groente vs. merk) vallen buiten scope
- Handmatige artikelen zijn vrije tekstbeschrijvingen zonder gestructureerde product-data; zij gaan door hetzelfde matchproces als recept-ingrediënten en kunnen eveneens een opgeslagen `preferred_article_id` hebben
- Het matchoverzicht toont alleen de huidige boodschappenlijst, geen historische vergelijking
- Correcties worden direct opgeslagen na bevestiging, zonder aparte "opslaan"-knop
- De bestaande "verstuur naar AH"-knop wordt de ingang voor de nieuwe flow: klik → match alle ingrediënten → review → bevestig → maak AH-lijst aan
- Na het aanmaken van de AH-lijst wordt de bestaande bevestigingsflow getoond: bevestigingsscherm met een knop om naar de AH-website te gaan om de bestelling af te ronden
