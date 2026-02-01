# Boodschappen Automatisering

## High-Level Ontwerp

---

## 1. Inleiding

Dit document beschrijft het ontwerp van een systeem om het wekelijkse boodschappenproces te automatiseren. Het huidige proces bestaat uit vier stappen: weekmenu plannen, recepten vertalen naar ingrediënten, voorraad checken, en bestellen bij Albert Heijn.

---

## 2. Systeemoverzicht

Het systeem bestaat uit vijf hoofdcomponenten die op elkaar voortbouwen:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Recepten-      │────▶│  Menuweek-      │────▶│  Boodschappen-  │
│  database       │     │  planner        │     │  lijst          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Voorraad-      │     │  AH             │
                        │  beheer         │────▶│  integratie     │
                        └─────────────────┘     └─────────────────┘
```

1. **Receptendatabase** — Centrale opslag van alle recepten met ingrediënten
2. **Menuplanner** — Automatische suggesties op basis van seizoen en variatie
3. **Voorraadbeheer** — Bijhouden wat op voorraad is met slimme suggesties
4. **Boodschappenlijst-generator** — Aggregeert en optimaliseert de benodigde producten
5. **AH-integratie** — Koppeling met Albert Heijn voor het plaatsen van bestellingen

---

## 3. Receptendatabase

De receptendatabase vormt de fundering van het systeem. De bestaande papieren receptenverzameling wordt gedigitaliseerd naar een gestructureerd formaat.

### Datamodel per recept

- Naam en categorie (pasta, ovenschotel, soep, etc.)
- Seizoen(en) waarin het recept past
- Basisporties (standaard voor 2 personen)
- Ingrediënten met hoeveelheden, schaalbaar naar porties
- Tags voor variatie (kip, vegetarisch, vis, etc.)
- Bereidingstijd en complexiteit

### Digitaliseren

Dit is eenmalig werk. Foto's van papieren recepten kunnen gestructureerd worden omgezet naar het juiste dataformaat.

---

## 4. Menuplanner

### Input per week

- Per dag: aantal personen (1-4), of "niet thuis"
- Eventuele voorkeuren ("zin in iets met vis", "snelle maaltijd")

### Planningslogica

- Filter recepten op huidig seizoen
- Variatie afdwingen: niet 2x dezelfde hoofdcategorie achter elkaar
- Automatische portieberekening op basis van aantal personen
- Houdt bij wat recent is gegeten (geen herhaling binnen X weken)

### Output

Een voorgesteld weekmenu dat handmatig aangepast kan worden.

---

## 5. Voorraadbeheer

### Twee typen producten

**Houdbare voorraad** (pasta, rijst, blikken, kruiden)
- Markeren wanneer iets op is
- Systeem suggereert: "Je hebt 3 weken geleden spaghetti gekookt, heb je nog pasta?"

**Verse basisproducten** (melk, eieren, boter, kaas)
- Standaard wekelijks op de lijst, tenzij aangegeven "nog genoeg"

### Slimme suggesties

- Na X recepten met ingrediënt Y → "Check of je nog Y hebt"
- Seizoensgebonden: "Herfst begint, heb je nog pompoensoep-ingrediënten?"

---

## 6. Boodschappenlijst-generator

### Aggregeert

- Ingrediënten uit het weekmenu (geschaald naar porties)
- Standaard verse producten
- Handmatige toevoegingen

### Slimme stappen

- Combineert hoeveelheden ("2x 200g gehakt" → "400g gehakt")
- Rondt af naar logische verpakkingen
- Filtert wat op voorraad is

---

## 7. AH-integratie

Voor de AH-integratie worden twee opties onderzocht via een Proof of Concept.

### POC Optie B: Mijn Lijstje

**Wat te valideren:**
- Kun je producten geautomatiseerd aan een lijstje toevoegen?
- Hoe goed kun je ingrediënten matchen aan AH-producten?
- Hoe soepel is de flow van lijstje → winkelmandje?

**Aanpak:**
1. Onderzoek hoe AH lijstjes werken (URL-structuur, cookies, API-calls via browser dev tools)
2. Probeer handmatig een lijstje te maken en kijk of import mogelijk is
3. Test met 5-10 producten of betrouwbare mapping mogelijk is

**Risico's:**
- AH heeft mogelijk geen handige import-functie
- Productmatching kan lastig zijn (welke melk? welk merk?)

### POC Optie C: Browser Automation

**Wat te valideren:**
- Kun je stabiel inloggen en zoeken via Playwright?
- Hoe ga je om met productkeuzes (meerdere zoekresultaten)?
- Hoe fragiel is het als AH hun site aanpast?

**Aanpak:**
1. Playwright opzetten, handmatig inloggen en sessie opslaan
2. Script schrijven dat één product zoekt en aan mandje toevoegt
3. Uitbreiden naar een lijstje van 5-10 producten
4. Afhandeling van "product niet gevonden" of meerdere opties

**Risico's:**
- AH kan bot-detectie hebben
- Site-wijzigingen breken het script
- Inloggen kan lastig zijn (2FA, captcha)

### Evaluatiecriteria

| Criterium | Optie B (Mijn Lijstje) | Optie C (Browser Automation) |
|-----------|------------------------|------------------------------|
| Betrouwbaarheid | ? | ? |
| Onderhoudbaarheid | ? | ? |
| Gebruiksgemak | ? | ? |
| Bouwtijd | ? | ? |

De keuze tussen optie B en C wordt gemaakt na afronding van beide POCs.

---

## 8. Technische Implementatie

### Voorgestelde tech stack

- **Database:** SQLite of JSON-bestanden
- **Backend:** Python voor de logica
- **Frontend:** Eenvoudige web UI of CLI
- **Mobiel:** PWA (Progressive Web App) voor toegang via telefoon

### Fasering

1. Recepten digitaliseren en database opzetten
2. Menuplanner bouwen met portieberekening
3. Boodschappenlijst-generator
4. Voorraadbeheer toevoegen
5. AH-integratie (na POC-keuze)

---

## 9. Volgende stappen

1. **POC AH-integratie starten** — Beide opties onderzoeken
2. **Recepten digitaliseren** — Papieren recepten omzetten naar gestructureerd formaat
3. **Datamodel finaliseren** — Exacte velden en relaties vastleggen
4. **Eerste prototype** — Minimale versie van menuplanner + boodschappenlijst
