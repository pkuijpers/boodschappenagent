# Feature Specification: Handmatig toegevoegde artikelen meesturen naar AH

**Feature Branch**: `002-fix-manual-items-ah-send`  
**Created**: 2026-05-13  
**Status**: Draft  
**Input**: User description: "artikelen die ik handmatig toevoeg aan de boodschappenlijst worden niet naar AH gestuurd bij klikken op 'Verstuur naar AH'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Handmatig artikel wordt meegestuurd naar AH (Priority: P1)

Als gebruiker wil ik dat alle artikelen op mijn boodschappenlijst — inclusief de artikelen die ik zelf handmatig heb toegevoegd — worden opgenomen wanneer ik op 'Verstuur naar AH' klik, zodat ik geen artikelen hoef na te bestellen.

**Why this priority**: Dit is de kern van het gemelde bug. Handmatig toegevoegde artikelen worden momenteel genegeerd bij het versturen, wat leidt tot onvolledige bestellingen.

**Independent Test**: Kan volledig getest worden door een handmatig artikel toe te voegen, op 'Verstuur naar AH' te klikken, en te controleren of het artikel in de AH-lijst verschijnt.

**Acceptance Scenarios**:

1. **Given** de boodschappenlijst bevat één handmatig toegevoegd artikel (bijv. "Zeep"), **When** de gebruiker klikt op 'Verstuur naar AH', **Then** verschijnt het artikel "Zeep" in de AH-boodschappenlijst.
2. **Given** de boodschappenlijst bevat zowel menu-gegenereerde als handmatig toegevoegde artikelen, **When** de gebruiker klikt op 'Verstuur naar AH', **Then** worden alle artikelen — van beide typen — meegestuurd naar AH.
3. **Given** de boodschappenlijst bevat alleen handmatig toegevoegde artikelen (geen menu), **When** de gebruiker klikt op 'Verstuur naar AH', **Then** worden alle handmatig toegevoegde artikelen verstuurd en de AH-lijst bevat ze daarna.

---

### User Story 2 - Bevestiging na versturen (Priority: P2)

Als gebruiker wil ik duidelijke feedback krijgen dat alle artikelen (inclusief handmatige) succesvol zijn verstuurd naar AH, zodat ik weet dat de actie correct is uitgevoerd.

**Why this priority**: Zonder bevestiging weet de gebruiker niet of de bug is opgelost of de actie is geslaagd.

**Independent Test**: Kan getest worden door te controleren of de bevestigingsmelding het correcte aantal versturde artikelen weergeeft inclusief handmatig toegevoegde.

**Acceptance Scenarios**:

1. **Given** er zijn 3 menu-artikelen en 2 handmatig toegevoegde artikelen, **When** de gebruiker klikt op 'Verstuur naar AH', **Then** toont de bevestigingsmelding dat 5 artikelen zijn verstuurd.
2. **Given** het versturen mislukt (bijv. geen verbinding met AH), **When** de gebruiker klikt op 'Verstuur naar AH', **Then** krijgt de gebruiker een foutmelding en blijven alle artikelen onveranderd op de lijst.

---

### Edge Cases

- Wat gebeurt er als een handmatig artikel dezelfde naam heeft als een al bestaand artikel in de AH-lijst?
- Wat als het handmatige artikel een naam heeft die AH niet herkent? (Geen blokkade — artikel wordt toch verstuurd als vrije tekst of geschikt alternatief)
- Wat als de boodschappenlijst leeg is? (Knop 'Verstuur naar AH' toont een melding dat er niets te versturen is)
- Wat als er alleen handmatige artikelen zijn zonder menuplanning?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Het systeem MOET bij het versturen naar AH alle artikelen op de boodschappenlijst meenemen, ongeacht of ze door het menu zijn gegenereerd of handmatig zijn toegevoegd.
- **FR-002**: Het systeem MOET handmatig toegevoegde artikelen op identieke wijze behandelen als menu-gegenereerde artikelen bij de AH-verstuuractie.
- **FR-003**: Gebruikers MOETEN na het klikken op 'Verstuur naar AH' feedback ontvangen over hoeveel artikelen zijn verstuurd.
- **FR-004**: Het systeem MOET een foutmelding tonen als het versturen naar AH mislukt, zonder artikelen van de lijst te verwijderen.
- **FR-005**: Het systeem MOET de boodschappenlijst volledig bewaren (inclusief handmatige artikelen) totdat de gebruiker expliciet artikelen verwijdert of de lijst wist.

### Key Entities

- **Boodschappenlijstartikel**: Een artikel op de boodschappenlijst, met een naam, hoeveelheid en herkomst (menu-gegenereerd of handmatig toegevoegd).
- **AH-verzendopdracht**: De verzameling van alle artikelen op de lijst die in één actie naar AH wordt gestuurd.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% van de handmatig toegevoegde artikelen verschijnt in de AH-boodschappenlijst na klikken op 'Verstuur naar AH'.
- **SC-002**: De gebruiker ontvangt binnen 3 seconden visuele bevestiging nadat op 'Verstuur naar AH' is geklikt.
- **SC-003**: Geen enkel handmatig artikel gaat verloren of wordt overgeslagen bij het versturen, ook niet bij gemengde lijsten (menu + handmatig).
- **SC-004**: Bij een mislukte verzending blijft de boodschappenlijst intact en wordt de gebruiker geïnformeerd.

## Assumptions

- De gebruiker is reeds ingelogd bij AH en heeft de nodige rechten om een boodschappenlijst bij te werken.
- "Handmatig toegevoegd" betekent: artikelen die de gebruiker zelf heeft ingetypt via de UI, niet via de menuplanner.
- De AH-integratie (API/verbinding) is functioneel; dit spec richt zich op de correcte selectie en doorzending van artikelen, niet op het oplossen van AH API-problemen.
- Handmatig toegevoegde artikelen hebben minimaal een naam; hoeveelheid is optioneel.
- De boodschappenlijst onderscheidt intern wel handmatige van menu-gegenereerde artikelen (voor weergave/sortering), maar beide worden zonder onderscheid verstuurd naar AH.
