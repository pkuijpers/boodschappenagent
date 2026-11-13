# Research: Handmatig toegevoegde artikelen meesturen naar AH

**Date**: 2026-05-13  
**Feature**: Handmatig toegevoegde artikelen meesturen naar AH

## Root Cause Analyse

### Bevinding: Twee parallelle datastructuren voor boodschappenlijst

De router `boodschappen.py` beheert de boodschappenlijst via twee onafhankelijke structuren in `app.state`:

| State-attribuut | Type | Inhoud | Gebruikt door |
|-----------------|------|--------|---------------|
| `boodschappenlijst` | `list[dict]` | Alle items (menu + handmatig), mutable | UI-rendering, toggling, verwijderen |
| `boodschappenlijst_model` | `Boodschappenlijst` | Alleen menu-gegenereerde items | `verstuur_naar_ah()` → AH sync |

**`_build_boodschappenlijst_state()`** (regel 43-70) vult beide bij het laden van de pagina, maar met uitsluitend menu-gegenereerde items.

**`handmatig_toevoegen()`** (regel 179-213) voegt een dict toe aan `boodschappenlijst`, maar werkt `boodschappenlijst_model` **nooit** bij.

**`verstuur_naar_ah()`** (regel 216-261) leest uitsluitend `boodschappenlijst_model`, waardoor handmatige items altijd worden overgeslagen.

### Beslissing: Fix in `verstuur_naar_ah()` — bouw lijst af van UI-itemslijst

**Wat is gekozen**: In `verstuur_naar_ah()` de te versturen `Boodschappenlijst` opbouwen vanuit `request.app.state.boodschappenlijst` (de UI-itemslijst van dicts), in plaats van `boodschappenlijst_model`.

**Rationale**:
- De UI-itemslijst is de enige bron die altijd compleet is (zowel menu- als handmatige items).
- Minimale impact: slechts één functie (`verstuur_naar_ah`) wijzigt.
- Geen complexe state-mutatie: frozen dataclasses hoeven niet te worden gemuteerd.
- Existing checked-item filtering blijft werken (wordt al gedaan via de dict-lijst).

**Overwogen alternatieven**:

| Alternatief | Reden afgewezen |
|-------------|-----------------|
| Update `boodschappenlijst_model` in `handmatig_toevoegen()` | Vereist aanmaken van nieuw frozen object bij elke toevoeging; houdt twee structuren synchroon — meer kans op drift |
| Voeg handmatige items toe als aparte parameter aan `sync_naar_lijst()` | Wijzigt het domeininterface van `AHIntegratie`; meer invasief dan nodig |
| Vervang model door mutable state-klasse | Grote refactoring; buiten scope van dit ticket |

## Conversie: dict → BoodschappenRegel

`BoodschappenRegel.__post_init__` eist: `naam` (non-empty), `eenheid` (non-empty), `originele_namen` (non-empty frozenset).

Voor een handmatig item uit `boodschappenlijst`:
```python
BoodschappenRegel(
    naam=item["naam"],
    hoeveelheid=item["hoeveelheid"],
    eenheid=item["eenheid"],
    originele_namen=frozenset({item["naam"]}),
)
```

Menu-gegenereerde items in de dict-lijst bevatten dezelfde velden (`naam`, `hoeveelheid`, `eenheid`) en kunnen identiek worden geconverteerd. Het `recepten`-tuple en `originele_namen` zijn voor AH-zoeken niet relevant — alleen `naam` wordt gebruikt in `smart_search()`.

## Bestaande checks filtering

De bestaande code in `verstuur_naar_ah()` filtert gecheckte items via `checked_namen` (regel 234). Na de fix wordt dit vereenvoudigd: items worden gefilterd rechtstreeks uit de dicts (`item.get("checked")`), waarna de overblijvende dicts worden geconverteerd naar `BoodschappenRegel`.

## Impact op bestaande tests

Bestaande tests (`TestVerstuurNaarAHSucces`, `TestVerstuurNaarAHCheckedItems`, etc.) gebruiken `setup_boodschappenlijst` fixtures die al `boodschappenlijst_model` en `boodschappenlijst` items instellen. De tests blijven geldig — ze verifiëren extern gedrag (HTTP-status, template-output), niet de interne state-structuur.

Nieuwe tests moeten toevoegen dat `sync_naar_lijst()` wordt aangeroepen met een lijst die handmatige items bevat.

## Geen externe afhankelijkheden

Geen documentatiezoekopdrachten vereist. Root cause is volledig traceerbaar in de broncode. Geen nieuwe bibliotheken nodig.
