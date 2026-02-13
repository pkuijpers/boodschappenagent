# UI Ontwerp: Albert

**Versie:** 1.1
**Datum:** 2026-02-13
**Platform:** iOS/iPadOS (mobiel-first)

### Changelog

| Versie | Wijziging |
|--------|-----------|
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
| **Seizoensgebonden** | Automatisch gefilterd op huidig seizoen |

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
│  │ MA 10 feb                    2p │   │
│  │ Ossobuco                     ↻  │   │  ← ↻ = vervang dit recept
│  │ 🥔 Aardappel · Vlees            │   │
│  │ ░░░░░░░░░░░░ 3 mnd geleden      │   │  ← Subtiele indicator: lang niet gehad
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ DI 11 feb              HelloFresh│   │  ← Oranje accent
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
│  │ Zalm teriyaki                ↻  │   │
│  │ 🍚 Rijst · Vis                  │   │
│  │ ░░░░░░░░ 2 mnd geleden          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ZA 15 feb                    4p │   │  ← Weekend: 4 personen
│  │ Kip tandoori                 ↻  │   │
│  │ 🍚 Rijst · Gevogelte            │   │
│  │ ░░░░░░ 6 wkn geleden            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ZO 16 feb                    4p │   │
│  │ Moussaka                     ↻  │   │
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

**Na handmatig vervangen van een recept:**

```
┌─────────────────────────────────────────┐
│ ◀ Week 7                    Albert   ● │
├─────────────────────────────────────────┤
│                                         │
│  Voorstel voor deze week          🔀   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ MA 10 feb                    2p │   │
│  │ Spaghetti Bolognese          ↻  │   │  ← Door jou gekozen (vervangt voorstel)
│  │ 🍝 Pasta · Vlees                │   │
│  └─────────────────────────────────┘   │
│  ...                                    │
└─────────────────────────────────────────┘
```

**Interacties:**
- **🔀 Shuffle** (rechtsboven) → Genereer volledig nieuw weekvoorstel
- **Tap ↻** op een dag → Vervang alleen dit recept (toont receptkiezer)
- **Swipe dag naar links** → Snelle vervang-actie
- **Tap op dag** → Details bekijken, porties aanpassen
- **"Verder naar boodschappen"** → Direct beschikbaar (alles is al ingevuld)

---

### 5.2 Receptkiezer (Vervangmodus)

Opent als sheet wanneer je een voorgesteld recept wilt vervangen.
Focus op snel een alternatief vinden.

```
┌─────────────────────────────────────────┐
│ ─────                                   │  ← Drag handle
│                                         │
│  Vervang recept voor maandag            │
│  Nu: Ossobuco                           │  ← Toont huidige suggestie
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │ 🔍 Zoek recept...               │   │  ← Zoekbalk
│  └─────────────────────────────────┘   │
│                                         │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐   │
│  │Alle│ │Vlees│ │Kip │ │Vis │ │Vega│   │  ← Filter chips (horizontaal scrollen)
│  └────┘ └────┘ └────┘ └────┘ └────┘   │
│                                         │
│  Lang niet gegeten                      │  ← Sectie header
│  ─────────────────────────────────────  │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Ossobuco                        │   │
│  │ Vlees · Aardappel · 45 min      │   │
│  │ 3 maanden geleden               │   │  ← Wanneer laatst gegeten
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Zalm teriyaki                   │   │
│  │ Vis · Rijst · 25 min            │   │
│  │ 2 maanden geleden               │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Moussaka                        │   │
│  │ Vlees · Aardappel · 60 min      │   │
│  │ 6 weken geleden                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Risotto champignons             │   │
│  │ Vegetarisch · Rijst · 35 min    │   │
│  │ 5 weken geleden                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ... (scrollbaar)                       │
│                                         │
└─────────────────────────────────────────┘
```

**Interacties:**
- Tap op recept → Portiescherm
- Zoeken filtert live
- Filter chips zijn toggles (meerdere selecteerbaar)
- Pull-to-dismiss om terug te gaan

---

### 5.3 Porties Kiezen

Snel tussenscherm na receptselectie.

```
┌─────────────────────────────────────────┐
│ ─────                                   │
│                                         │
│  Spaghetti Bolognese                    │
│  Maandag 10 februari                    │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Aantal personen                        │
│                                         │
│     ┌─────┐   ┌─────┐   ┌─────┐        │
│     │     │   │     │   │     │        │
│     │  2  │   │  3  │   │  4  │        │
│     │     │   │     │   │     │        │
│     └─────┘   └─────┘   └─────┘        │
│       ▲                                 │  ← 2 is default doordeweeks
│    geselecteerd                         │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │           Toevoegen             │   │  ← Primaire actie
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**Slimme defaults:**
- Ma/Vr: 2 personen (doordeweeks)
- Za/Zo: 4 personen (weekend met kinderen)

---

### 5.4 Voorraadcheck

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

### 5.5 Boodschappenlijst

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

### 5.6 AH Koppeling (Bevestiging)

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

### 5.7 Kookmodus (Dagelijks)

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
│  Week 7           🔀   │   Vervang recept                       │
│  ──────────────────    │   Nu: Zalm teriyaki                    │
│                        │   ──────────────────                   │
│  MA 10  Ossobuco    ↻  │                                        │
│  DI 11  HelloFresh     │   🔍 Zoek recept...                    │
│  WO 12  HelloFresh     │                                        │
│  DO 13  HelloFresh     │   [Alle] [Vlees] [Kip] [Vis] [Vega]   │
│  VR 14  Zalm teriy. ←↻ │                                        │
│  ZA 15  Kip tandoori↻  │   Gebakken zalmfilet                  │
│  ZO 16  Moussaka    ↻  │   Vis · Geen · 20 min                 │
│                        │   4 maanden geleden                   │
│                        │                                        │
│  ┌──────────────────┐  │   Vissticks met puree                 │
│  │  Naar            │  │   Vis · Aardappel · 25 min            │
│  │  boodschappen →  │  │   2 maanden geleden                   │
│  └──────────────────┘  │                                        │
│                        │   ...                                  │
└────────────────────────┴────────────────────────────────────────┘
```

Het rechter paneel toont de receptkiezer alleen wanneer je op ↻ tapt.
Standaard is het rechter paneel leeg of toont het receptdetails.

---

## 8. Componenten Bibliotheek

### 8.1 Dagkaart

```
┌─────────────────────────────────────────┐
│ MA 10 feb                           2p │  ← Header: dag, datum, porties
│ Ossobuco                             ↻ │  ← Receptnaam, vervang-icoon
│ 🥔 Aardappel · Vlees                   │  ← Metadata (basis, categorie)
│ ░░░░░░░░░░░░ 3 mnd geleden             │  ← Wanneer laatst gegeten
└─────────────────────────────────────────┘

States:
- Voorstel: receptnaam + metadata + "lang niet gegeten" indicator + ↻ icoon
- Handmatig gekozen: receptnaam + metadata + ↻ icoon (geen indicator)
- HelloFresh: Oranje balk, niet interactief
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
| 🔀 Shuffle | Alle kaarten roteren uit, nieuwe kaarten roteren in |
| ↻ Recept vervangen | Oude naam fade out naar links, nieuwe fade in vanaf rechts |
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
- **Seizoensfilter**: Automatisch filteren op huidig seizoen
- **Meerdere weken**: Vooruit plannen

---

## 12. Samenvatting Ontwerpkeuzes

| Keuze | Rationale |
|-------|-----------|
| **Automatisch weekvoorstel** | Minder werk: alleen aanpassen wat niet bevalt, niet alles zelf kiezen |
| **↻ Vervang i.p.v. + Kies** | Positieve framing: je hebt al iets, vervang alleen indien nodig |
| **🔀 Shuffle voor hele week** | Snelle reset als het voorstel helemaal niet past |
| Half-modal sheets | Snelle context-switches zonder navigatie te verliezen |
| Ja/Nee in plaats van checkboxes | Duidelijker dan alleen vinkjes, geen dubbelzinnigheid |
| "Lang niet gegeten" indicator | Transparantie over waarom het systeem dit recept voorstelt |
| HelloFresh als oranje blokken | Duidelijk onderscheid, geen interactie nodig |
| Kookboekverwijzing i.p.v. instructies | De fysieke bron blijft leidend |
| Standaard "Nee" bij voorraadcheck | Veilige default: liever te veel bestellen dan te weinig |

---

*Dit document vormt de basis voor de implementatie van de Albert UI. Wijzigingen worden hier gedocumenteerd.*
