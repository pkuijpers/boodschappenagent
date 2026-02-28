# UI Ontwerp: Albert

**Versie:** 1.2
**Datum:** 2026-02-27
**Platform:** iOS/iPadOS (mobiel-first)

### Changelog

| Versie | Wijziging |
|--------|-----------|
| 1.2 | Dag aanpassen: tap op dagkaart opent gecombineerde sheet (personen, dagtype, random recept). Zoekfunctie verwijderd. |
| 1.1 | Automatisch weekvoorstel: app start met gevuld menu i.p.v. lege dagen |
| 1.0 | Initieel ontwerp |

---

## 1. Ontwerpprincipes

| Principe | Toelichting |
|----------|-------------|
| **Systeem stelt voor, jij past aan** | Je begint met een automatisch weekmenu, niet met een leeg scherm |
| **Eén sessie, één flow** | De hele weekplanning + bestelling in één ononderbroken flow |
| **Minimalistisch** | Geen afleiding, alleen wat nodig is voor de huidige stap |
| **Touch-first** | Grote taptargets, swipe-interacties, geen precisiewerk |
| **Snel** | Eén tap om een recept te vervangen, niet vier taps om er een te kiezen |
| **Foutpreventie** | Systeem voorkomt vergeten ingrediënten, niet de gebruiker |

---

## 2. Kleurenpalet

Geïnspireerd op Albert Heijn, maar subtieler voor dagelijks gebruik.

| Naam | Hex | Gebruik |
|------|-----|---------|
| **AH Blauw** | `#00A0E2` | Primaire acties, headers, navigatie |
| **AH Blauw Donker** | `#0077B3` | Pressed states, accenten |
| **Lichtblauw** | `#E6F4FA` | Achtergrond geselecteerde items |
| **Wit** | `#FFFFFF` | Achtergrond schermen |
| **Grijs 100** | `#F5F5F5` | Kaartachtergrond, secties |
| **Grijs 400** | `#9E9E9E` | Secundaire tekst, iconen |
| **Grijs 800** | `#424242` | Primaire tekst |
| **Oranje** | `#FF6B00` | HelloFresh dagen (hun merkkleur) |
| **Groen** | `#4CAF50` | Bevestigingen, "klaar" states |

---

## 3. Typografie

| Element | Stijl |
|---------|-------|
| Headers | SF Pro Display Semibold, 20-24pt |
| Body | SF Pro Text Regular, 16pt |
| Secundair | SF Pro Text Regular, 14pt, Grijs 400 |
| Buttons | SF Pro Text Semibold, 16pt |

---

## 4. User Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           WEKELIJKSE FLOW                               │
│                         (woensdagavond)                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      1. WEEKOVERZICHT         │
                    │   Automatisch voorstel van    │
                    │   MenuPlanner, direct gevuld  │
                    │   HelloFresh dagen zichtbaar  │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
              Tevreden?                      Niet tevreden?
                    │                               │
                    │                               ▼
                    │               ┌───────────────────────────────┐
                    │               │      2a. VERVANG RECEPT       │
                    │               │   Swipe/tap op dag →          │
                    │               │   Kies alternatief            │
                    │               └───────────────────────────────┘
                    │                               │
                    │               ┌───────────────────────────────┐
                    │               │      2b. SHUFFLE ALLES        │
                    │               │   🔀 Nieuw voorstel genereren │
                    │               └───────────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      3. VOORRAADCHECK         │
                    │   "Heb je nog...?" Ja/Nee     │
                    │   Houdbare + standaard lijst  │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │     4. BOODSCHAPPENLIJST      │
                    │   Overzicht wat je gaat       │
                    │   bestellen, laatste check    │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      5. NAAR AH MANDJE        │
                    │   Producten in AH app/site    │
                    │   Jij rondt af en betaalt     │
                    └───────────────────────────────┘


                    ┌───────────────────────────────┐
                    │      6. KOOKMODUS             │
                    │   (los van de wekelijkse      │
                    │    flow, dagelijks gebruik)   │
                    │   Welk recept is vandaag?     │
                    │   Verwijzing naar kookboek    │
                    └───────────────────────────────┘
```

### Voordelen van "Systeem stelt voor"

| Aspect | Voordeel |
|--------|----------|
| **Sneller** | In het beste geval: 0 wijzigingen nodig, direct door naar boodschappen |
| **Minder keuzestress** | Niet zelf 4 recepten bedenken, alleen afwijzen wat niet past |
| **Slimme variatie** | MenuPlanner zorgt automatisch voor afwisseling (categorie, basis) |
| **Lang niet gegeten** | Systeem kiest recepten die jullie lang niet hebben gehad |
| **Lage CO2** | Automatisch gefilterd op groenten met lage CO2-voetafdruk voor de huidige maand |

---

## 5. Schermontwerpen

### 5.1 Weekoverzicht (Hoofdscherm)

Het startpunt. **Direct gevuld met een automatisch voorstel** van de MenuPlanner.
Geen lege dagen meer — je begint met een compleet weekmenu en past aan waar nodig.

```
┌─────────────────────────────────────────┐
│ ◀ Week 7                    Albert   ● │  ← Header met weeknummer
├─────────────────────────────────────────┤
│                                         │
│  Voorstel voor deze week          🔀   │  ← Shuffle: genereer nieuw voorstel
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ MA 10 feb                    2p │   │  ← Hele kaart is tappable
│  │ Ossobuco                        │   │
│  │ 🥔 Aardappel · Vlees            │   │
│  │ ░░░░░░░░░░░░ 3 mnd geleden      │   │  ← Subtiele indicator: lang niet gehad
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ DI 11 feb              HelloFresh│   │  ← Oranje accent, ook tappable
│  │ ████████████████████████████████│   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ WO 12 feb              HelloFresh│   │
│  │ ████████████████████████████████│   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ DO 13 feb              HelloFresh│   │
│  │ ████████████████████████████████│   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ VR 14 feb                    2p │   │
│  │ Zalm teriyaki                   │   │
│  │ 🍚 Rijst · Vis                  │   │
│  │ ░░░░░░░░ 2 mnd geleden          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ZA 15 feb                    4p │   │  ← Weekend: 4 personen
│  │ Kip tandoori                    │   │
│  │ 🍚 Rijst · Gevogelte            │   │
│  │ ░░░░░░ 6 wkn geleden            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ZO 16 feb                    4p │   │
│  │ Moussaka                        │   │
│  │ 🥔 Aardappel · Vlees            │   │
│  │ ░░░░░ 5 wkn geleden             │   │
│  └─────────────────────────────────┘   │
│                                         │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │     Verder naar boodschappen →  │   │  ← Direct beschikbaar
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Interacties:**
- **🔀 Shuffle** (rechtsboven) → Genereer volledig nieuw weekvoorstel
- **Tap op dagkaart** → Dag aanpassen (toont gecombineerde sheet voor dagtype, porties en recept)
- **"Verder naar boodschappen"** → Direct beschikbaar (alles is al ingevuld)

---

### 5.2 Dag aanpassen

Opent als sheet wanneer je op een dagkaart tapt.
Combineert dagtype, porties en receptkeuze in één scherm — geen aparte stappen.

```
┌─────────────────────────────────────────┐
│ ─────                                   │  ← Drag handle
│                                         │
│  Maandag 10 feb                         │
│  Ossobuco · 2 personen                  │  ← Huidige staat
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │Geen menu │ │ • Recept │ │HelloFresh ││  ← Dagtype selector
│  └──────────┘ └──────────┘ └──────────┘│
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Aantal personen                        │
│                                         │
│  ┌────┐   ┌────┐   ┌────┐              │
│  │ 2  │   │ 3  │   │ 4  │             │
│  └────┘   └────┘   └────┘             │
│    ▲ geselecteerd                       │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  🔀  Ander recept               │   │  ← Variety-aware random selectie
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**States van het sheet:**

*Dagtype = Geen menu:*
```
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │• Geen    │ │  Recept  │ │HelloFresh ││
│  └──────────┘ └──────────┘ └──────────┘│
│                                         │
│  (personen-selector en "Ander recept"   │
│   zijn verborgen)                       │
```
Dagkaart wordt niet-thuis (grijs).

*Dagtype = HelloFresh:*
```
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │Geen menu │ │  Recept  │ │•HelloFresh││
│  └──────────┘ └──────────┘ └──────────┘│
│                                         │
│  (personen-selector en "Ander recept"   │
│   zijn verborgen)                       │
```
Dagkaart wordt HelloFresh (oranje).

**"🔀 Ander recept" knop:**
- Selecteert een nieuw recept via dezelfde logica als de MenuPlanner
- Houdt rekening met de andere dagen: geen 2x kip achter elkaar, variatie in categorie en basis
- Receptnaam in de sheet-header update direct
- Dagkaart in de achtergrond update ook direct (HTMX out-of-band)
- Meerdere keren drukken geeft steeds een ander voorstel

**Interacties:**
- Tap dagtype knop → Dagkaart update direct (HTMX), sheet blijft open
- Tap personen knop → Portie update direct (HTMX), sheet blijft open
- Tap "🔀 Ander recept" → Nieuw variety-aware recept, sheet + kaart update direct
- Pull-to-dismiss om terug te gaan (wijzigingen zijn al opgeslagen)

---

### 5.3 Voorraadcheck

Na het afronden van de weekplanning. Checklist-stijl.

```
┌─────────────────────────────────────────┐
│ ◀ Terug                      Albert  ● │
├─────────────────────────────────────────┤
│                                         │
│  Voorraadcheck                          │
│  Wat heb je nog in huis?                │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Houdbare producten                     │
│  ─────────────────────────────────────  │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Spaghetti              Ja   Nee │   │
│  │ (voor Spaghetti Bolognese)      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Rijst                  Ja   Nee │   │
│  │ (voor Kip tandoori)             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Passata                Ja   Nee │   │
│  │ (voor Spaghetti Bolognese)      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Standaard boodschappen                 │
│  ─────────────────────────────────────  │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Melk                   Ja   Nee │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Eieren                 Ja   Nee │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Kaas                   Ja   Nee │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Boter                  Ja   Nee │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ... (scrollbaar)                       │
│                                         │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │     Naar boodschappenlijst →    │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Interacties:**
- Tap "Ja" → Product wordt niet besteld (je hebt het nog)
- Tap "Nee" → Product komt op de boodschappenlijst
- Standaard staat op "Nee" (veilige default: liever te veel dan te weinig)

---

### 5.4 Boodschappenlijst

Overzicht van alles wat besteld gaat worden. Laatste controle.

```
┌─────────────────────────────────────────┐
│ ◀ Terug                      Albert  ● │
├─────────────────────────────────────────┤
│                                         │
│  Boodschappenlijst                      │
│  Week 7 · 23 producten                  │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Vlees & vis                            │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │ ☐ Rundergehakt          500 g   │   │
│  │ ☐ Zalmfilet             400 g   │   │
│  │ ☐ Kipfilet              600 g   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Zuivel                                 │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │ ☐ Melk                    1 L   │   │
│  │ ☐ Eieren               10 st   │   │
│  │ ☐ Parmezaanse kaas      100 g   │   │
│  │ ☐ Crème fraîche         200 ml  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Groente & fruit                        │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │ ☐ Uien                   4 st   │   │
│  │ ☐ Knoflook              1 bol   │   │
│  │ ☐ Paprika rood           3 st   │   │
│  │ ☐ Spinazie             400 g   │   │
│  │ ☐ Champignons          250 g   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ... (scrollbaar, meer categorieën)     │
│                                         │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐   │
│    + Voeg product toe                   │  ← Handmatige toevoeging
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘   │
│                                         │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │      Verstuur naar AH →         │   │  ← Primaire actie
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Interacties:**
- Tap checkbox → Verwijder van lijst (al in huis)
- Swipe naar links → Verwijder product
- Tap product → Hoeveelheid aanpassen
- "+ Voeg product toe" → Handmatig toevoegen

---

### 5.5 AH Koppeling (Bevestiging)

Na "Verstuur naar AH" - bevestigingsscherm.

```
┌─────────────────────────────────────────┐
│                                         │
│                                         │
│                                         │
│              ┌───────┐                  │
│              │  ✓    │                  │  ← Groen vinkje, animatie
│              └───────┘                  │
│                                         │
│         Toegevoegd aan AH               │
│                                         │
│      23 producten in je mandje          │
│                                         │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │       Open Albert Heijn →       │   │  ← Opent AH app
│  └─────────────────────────────────┘   │
│                                         │
│           of rond later af              │  ← Secundaire tekst
│                                         │
│                                         │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │         Terug naar home         │   │  ← Terug naar weekoverzicht
│  └─────────────────────────────────┘   │
│                                         │
│                                         │
└─────────────────────────────────────────┘
```

---

### 5.6 Kookmodus (Dagelijks)

Apart toegankelijk, los van de wekelijkse planning.

```
┌─────────────────────────────────────────┐
│                             Albert   ● │
├─────────────────────────────────────────┤
│                                         │
│  Vandaag                                │
│  Vrijdag 14 februari                    │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │       Zalm met spinazie         │   │
│  │                                 │   │
│  │       2 personen                │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│                                         │
│  Ingrediënten                           │
│  ─────────────────────────────────────  │
│  · 300 g zalmfilet                      │
│  · 400 g spinazie                       │
│  · 1 citroen                            │
│  · 2 teentjes knoflook                  │
│  · 2 el olijfolie                       │
│  · Peper en zout                        │
│                                         │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  📖  Recept: Kookboek p. 47     │   │  ← Verwijzing naar fysiek boek
│  └─────────────────────────────────┘   │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  ◀ Gisteren          Morgen ▶          │  ← Navigeer tussen dagen
│                                         │
└─────────────────────────────────────────┘
```

**Interacties:**
- Swipe links/rechts → Navigeer door de week
- Tap op kookboekverwijzing → Toont eventueel grotere weergave van bron

---

## 6. Navigatiestructuur

```
┌─────────────────────────────────────────┐
│              Tab Bar                    │
├─────────────┬─────────────┬─────────────┤
│             │             │             │
│   📅        │    📖       │    ⚙️       │
│   Week      │  Vandaag    │  Instellingen│
│             │             │             │
└─────────────┴─────────────┴─────────────┘
```

| Tab | Functie |
|-----|---------|
| **Week** | Weekoverzicht, planning, boodschappen |
| **Vandaag** | Kookmodus - wat eten we vandaag? |
| **Instellingen** | Account, HelloFresh dagen, standaard producten |

---

## 7. iPad Aanpassingen

Op iPad wordt een split-view gebruikt:

```
┌────────────────────────┬────────────────────────────────────────┐
│                        │                                        │
│  Week 7           🔀   │   Vrijdag aanpassen                    │
│  ──────────────────    │   Zalm teriyaki · 2 personen           │
│                        │   ──────────────────                   │
│  MA 10  Ossobuco       │                                        │
│  DI 11  HelloFresh     │  [Geen menu] [• Recept] [HelloFresh]  │
│  WO 12  HelloFresh     │                                        │
│  DO 13  HelloFresh     │   Aantal personen                      │
│  VR 14  Zalm teriy. ←  │   [2•]  [3]  [4]                      │
│  ZA 15  Kip tandoori   │                                        │
│  ZO 16  Moussaka       │  ┌────────────────────────────────┐   │
│                        │  │  🔀  Ander recept              │   │
│  ┌──────────────────┐  │  └────────────────────────────────┘   │
│  │  Naar            │  │                                        │
│  │  boodschappen →  │  │                                        │
│  └──────────────────┘  │                                        │
│                        │                                        │
└────────────────────────┴────────────────────────────────────────┘
```

Het rechter paneel toont de dag-aanpassen sheet wanneer je op een dagkaart tapt.
Standaard is het rechter paneel leeg.

---

## 8. Componenten Bibliotheek

### 8.1 Dagkaart

```
┌─────────────────────────────────────────┐
│ MA 10 feb                           2p │  ← Header: dag, datum, porties
│ Ossobuco                               │  ← Receptnaam
│ 🥔 Aardappel · Vlees                   │  ← Metadata (basis, categorie)
│ ░░░░░░░░░░░░ 3 mnd geleden             │  ← Wanneer laatst gegeten
└─────────────────────────────────────────┘
▲ Hele kaart is tappable → opent dag-aanpassen sheet

States:
- Recept: receptnaam + metadata + "lang niet gegeten" indicator (hele kaart tappable)
- HelloFresh: Oranje balk (hele kaart tappable → kan HelloFresh uitzetten)
- Geen menu: Grijze balk (hele kaart tappable → kan dagtype wijzigen)
```

### 8.2 Receptrij

```
┌─────────────────────────────────────────┐
│ Ossobuco                               │  ← Naam
│ Vlees · Aardappel · 45 min             │  ← Categorie · Basis · Tijd
│ 3 maanden geleden                      │  ← Laatste keer gegeten
└─────────────────────────────────────────┘
```

### 8.3 Voorraaditem

```
┌─────────────────────────────────────────┐
│ Spaghetti                    [Ja] [Nee]│
│ (voor Spaghetti Bolognese)             │  ← Context: welk recept
└─────────────────────────────────────────┘
```

### 8.4 Boodschapitem

```
┌─────────────────────────────────────────┐
│ ☐ Rundergehakt                  500 g  │
└─────────────────────────────────────────┘

States:
- Unchecked: op de lijst
- Checked: doorgestreept, vervaagt
```

### 8.5 Primaire Button

```
┌─────────────────────────────────────────┐
│         Verstuur naar AH →             │
└─────────────────────────────────────────┘

- Achtergrond: AH Blauw (#00A0E2)
- Tekst: Wit, semibold
- Hoogte: 50pt
- Border radius: 12pt
```

---

## 9. Micro-interacties

| Actie | Animatie |
|-------|----------|
| Weekvoorstel laden | Kaarten verschijnen met staggered fade-in (0.1s delay per dag) |
| 🔀 Shuffle (hele week) | Alle kaarten roteren uit, nieuwe kaarten roteren in |
| 🔀 Ander recept (dag) | Receptnaam in sheet fade out → in; dagkaart update in achtergrond |
| Dagtype wisselen | Dagkaart update met crossfade; sheet past inhoud aan |
| Voorraad Ja/Nee | Button highlight, snelle fade |
| Naar AH verzonden | Vinkje schaalt in, confetti-hint |
| Dag wisselen (kookmodus) | Crossfade met slide |
| Sheet openen | Spring-animatie vanaf onderkant |

---

## 10. Toegankelijkheid

- Alle touch targets minimaal 44x44pt
- Kleurcontrast voldoet aan WCAG AA
- VoiceOver labels voor alle interactieve elementen
- Dynamic Type ondersteuning (tekst schaalt mee)
- Haptic feedback bij belangrijke acties

---

## 11. Toekomstige Uitbreidingen

Buiten scope van v1, maar rekening mee houden in architectuur:

- **Delen met Ieke**: Weekmenu delen via link/widget
- **Receptfoto's**: Visuele preview in receptkiezer
- **Slimme suggesties**: "Je hebt al 2x pasta deze week"
- **~~Seizoensfilter~~**: Vervangen door CO2-seizoenskalender (al geïmplementeerd in de menuplanner)
- **Meerdere weken**: Vooruit plannen

---

## 12. Samenvatting Ontwerpkeuzes

| Keuze | Rationale |
|-------|-----------|
| **Automatisch weekvoorstel** | Minder werk: alleen aanpassen wat niet bevalt, niet alles zelf kiezen |
| **Tap op dagkaart → gecombineerde sheet** | Één tap geeft toegang tot alle aanpassingen voor die dag |
| **Geen zoekfunctie** | Bladeren door recepten is traag en leidt tot keuzestress; systeem stelt voor |
| **"🔀 Ander recept" i.p.v. zoekbalk** | Eén tap, variety-aware alternatief — sneller dan zoeken |
| **🔀 Shuffle voor hele week** | Snelle reset als het voorstel helemaal niet past |
| **Dagtype als 3-knops selector** | Eén handeling voor geen menu / recept / HelloFresh, geen apart scherm |
| **Directe HTMX updates** | Sheet blijft open, dagkaart update in achtergrond — geen navigatieonderbreking |
| Half-modal sheets | Snelle context-switches zonder navigatie te verliezen |
| Ja/Nee in plaats van checkboxes | Duidelijker dan alleen vinkjes, geen dubbelzinnigheid |
| "Lang niet gegeten" indicator | Transparantie over waarom het systeem dit recept voorstelt |
| HelloFresh als oranje blokken | Duidelijk onderscheid; ook tappable om dagtype te wijzigen |
| Kookboekverwijzing i.p.v. instructies | De fysieke bron blijft leidend |
| Standaard "Nee" bij voorraadcheck | Veilige default: liever te veel bestellen dan te weinig |

---

*Dit document vormt de basis voor de implementatie van de Albert UI. Wijzigingen worden hier gedocumenteerd.*
