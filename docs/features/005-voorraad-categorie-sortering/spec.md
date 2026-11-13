# Feature Specification: Voorraadlijst Sortering op Categorie

**Feature Branch**: `005-voorraad-categorie-sortering`
**Created**: 2026-05-27
**Status**: Draft
**Input**: User description: "sorteer de items op de voorraadlijst per categorie, waarbij elke categorie wordt gemapt naar: 1 koelkast, 2 voorraadkast, 3 diepvries. Laat de items ook in die volgorde zien."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Items gesorteerd op winkellocatie (Priority: P1)

Een gebruiker opent de voorraadpagina en ziet de producten uit zijn AH Voorraad-lijst gegroepeerd en gesorteerd op logische winkellocatie: eerst koelkast-producten, dan voorraadkast-producten, dan diepvriesproducten. Zo kan hij de lijst van boven naar beneden aflopen in de volgorde die de winkel logisch volgt.

**Why this priority**: De kern van de feature — zonder sortering is er geen waarde. Dit is wat de gebruiker beschreef als probleeem in de issues ("staat door elkaar ipv op logische volgorde").

**Independent Test**: Open de voorraadpagina met producten uit meerdere categorieën (bijv. melk, conserven en diepvriesgroenten). Controleer dat melk bovenaan staat, conserven in het midden en diepvriesgroenten onderaan.

**Acceptance Scenarios**:

1. **Given** de Voorraad-lijst bevat producten uit meerdere AH-categorieën, **When** de gebruiker de voorraadpagina opent, **Then** ziet hij de producten gesorteerd: eerst koelkast-items, daarna voorraadkast-items, daarna diepvries-items.
2. **Given** alle producten vallen in dezelfde categorie (bijv. alleen koelkast), **When** de gebruiker de voorraadpagina opent, **Then** worden alle items als één groep getoond zonder lege secties.
3. **Given** een product heeft een onbekende of lege categorie, **When** de gebruiker de voorraadpagina opent, **Then** verschijnt het product aan het einde van de lijst (na diepvries).

---

### User Story 2 - Zichtbare categoriescheiding (Priority: P2)

De gebruiker ziet bij de gesorteerde lijst een visuele scheiding of sectieheader (bijv. "Koelkast", "Voorraadkast", "Diepvries") zodat hij in één oogopslag weet in welk deel van de winkel hij zich bevindt.

**Why this priority**: Sortering zonder labeling maakt de volgorde impliciet; sectieheaders maken de bedoeling direct duidelijk voor de gebruiker.

**Independent Test**: Open de voorraadpagina. Controleer dat er een herkenbare sectionering zichtbaar is tussen de drie groepen.

**Acceptance Scenarios**:

1. **Given** producten in meerdere categorieën, **When** de voorraadpagina geladen is, **Then** verschijnen sectielabels ("Koelkast", "Voorraadkast", "Diepvries") boven elke gevulde sectie.
2. **Given** er zijn geen producten in de diepvries-categorie, **When** de voorraadpagina geladen is, **Then** verschijnt de sectieheader "Diepvries" niet.

---

### Edge Cases

- Wat gebeurt er als een product meerdere categorieën heeft (niet van toepassing: AH geeft één category-waarde per product)?
- Wat als een product een onbekende categorie heeft? → valt onder "Overig", getoond na diepvries.
- Wat als de Voorraad-lijst leeg is? → bestaand gedrag, geen items tonen.
- Wat als de AH API geen categoriedata teruggeeft voor een product? → product valt onder "Overig".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Het systeem MOET de categorienaam van elk product ophalen uit de AH-productdata en bewaren bij het ophalen van de Voorraad-lijst.
- **FR-002**: Het systeem MOET elke AH-categorienaam mappen naar één van drie winkellocaties: koelkast, voorraadkast of diepvries.
- **FR-003**: Het systeem MOET producten op de voorraadpagina sorteren in de volgorde: koelkast (1) → voorraadkast (2) → diepvries (3).
- **FR-004**: Producten met een onbekende of lege categorie MOETEN als laatste getoond worden (na diepvries).
- **FR-005**: De voorraadpagina MOET per gevulde sectie een zichtbaar sectielabel tonen ("Koelkast", "Voorraadkast", "Diepvries").
- **FR-006**: Lege secties (geen producten in die winkellocatie) MOGEN geen sectielabel tonen.
- **FR-007**: Binnen elke sectie MOGEN producten in hun huidige volgorde blijven (volgorde van de AH-lijst).

### Categorie-mapping

De mapping is gebaseerd op de AH-hoofdcategorie: het deel vóór de `/` in de AH category-string (exact, case-sensitief). De tabel hieronder is uitputtend op basis van de bekende AH-categoriestructuur (gevalideerd via API-steekproef van 100 producten, 2026-05-27). Onbekende of lege categorieën vallen terug op Overig.

| AH hoofdcategorie | Winkellocatie |
|---|---|
| Zuivel, eieren | Koelkast |
| Vlees | Koelkast |
| Vleeswaren | Koelkast |
| Vis | Koelkast |
| Kaas | Koelkast |
| Maaltijden, salades | Koelkast |
| Vegetarisch, vegan en plantaardig | Koelkast |
| Diepvries | Diepvries |
| Groente, aardappelen | Voorraadkast |
| Fruit, verse sappen | Voorraadkast |
| Pasta, rijst, wereldkeuken | Voorraadkast |
| Soepen, sauzen, kruiden, olie | Voorraadkast |
| Borrel, chips, snacks | Voorraadkast |
| Ontbijtgranen, beleg | Voorraadkast |
| Bakkerij | Voorraadkast |
| Dranken | Voorraadkast |
| Wijn, bier en gedestilleerd | Voorraadkast |
| Thee, koffie en cacao | Voorraadkast |
| Snoep en koek | Voorraadkast |
| Baby en kind | Voorraadkast |
| Drogisterij en gezondheid | Overig |
| Huishouden | Overig |
| Bloemen en planten | Overig |
| *(onbekend of leeg)* | Overig |

**Mapping-rationale voor niet-voor-de-hand-liggende keuzes:**
- `Groente, aardappelen` → Voorraadkast: AH verkoopt verse groenten op kamertemperatuur (versafdeling zonder koeling)
- `Fruit, verse sappen` → Voorraadkast: fruit is houdbaar; vers sap (koelkast bij AH) is een klein deelcategorie
- `Maaltijden, salades` → Koelkast: omvat verse pasta, verse maaltijden en salades — allen gekoeld
- `Vegetarisch, vegan en plantaardig` → Koelkast: hummus, tofu, tempeh en vleesvervangers zijn gekoeld
- `Vis` → Koelkast: ook conserven vallen in deze AH-categorie, maar de hoofdstroom (verse/gerookte vis) is gekoeld

### Key Entities

- **VoorraadProduct**: een product uit de AH Voorraad-lijst, met naam, AH-id, AH-categorienaam, en afgesproken winkellocatie.
- **Winkellocatie**: enum van drie waarden (Koelkast, Voorraadkast, Diepvries) plus Overig, met vaste sorteervolgorde.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: De voorraadpagina toont items in de volgorde koelkast → voorraadkast → diepvries voor alle testgevallen.
- **SC-002**: Items met een onbekende categorie verschijnen altijd ná de drie benoemde secties.
- **SC-003**: Lege secties produceren geen zichtbare sectieheader.
- **SC-004**: De bestaande functionaliteit (aan/uit zetten van voorraad, navigatie naar boodschappenlijst) werkt ongewijzigd na invoering van de sortering.

## Assumptions

- De AH-categorienaam is beschikbaar als het veld `category` op een Product-object en heeft het formaat `"HoofdCategorie/SubCategorie"` of alleen `"HoofdCategorie"`. Het deel vóór de `/` is bepalend voor de mapping.
- "Koelkast" krijgt prioriteit 1 omdat dit de meest gebruikte sectie is voor verse producten.
- "Voorraadkast" is de standaard/fallback voor alles wat niet koelkast of diepvries is.
- Er wordt geen nieuwe datalaag of API-call toegevoegd: de categoriedata zit al in de bestaande productopslag bij AH-productophalingen.
- De volgorde ínnen een sectie is niet relevant voor de gebruiker; alleen de volgorde tússen secties telt.
- Mobiele weergave (iPhone 13-viewport) is de primaire weergave; de sectielabels moeten leesbaar zijn op dit formaat.
