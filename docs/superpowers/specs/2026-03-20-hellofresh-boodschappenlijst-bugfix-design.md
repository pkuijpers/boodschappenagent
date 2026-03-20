# Bugfix: HelloFresh-dagen genereren onterecht boodschappen

**Datum:** 2026-03-20
**Status:** Ontwerp

## Probleem

Wanneer een dag in het weekmenu als "hellofresh" wordt gemarkeerd:

1. Het recept en personen-aantal blijven ongewijzigd in het domeinmodel (`DagPlanning`)
2. De boodschappenlijst-generator, history-sync en voorraadcheck behandelen de dag als een normale receptdag
3. Er worden dus onterecht boodschappen gegenereerd voor hellofresh-dagen

### Root cause

In `stel_type_in()` (menu.py:273-274) wordt bij dagtype "hellofresh" de `DagPlanning` ongewijzigd overgenomen:

```python
elif dagtype == "hellofresh":
    nieuwe_dagen.append(d)  # recept + personen blijven staan
```

Het feit dat het hellofresh is, wordt alleen bijgehouden in een losse `hellofresh_dagen` set op `app.state`. Het domeinmodel (`WeekMenu.geplande_dagen`) weet er niets van, en alle consumers (generator, history, voorraad) itereren over `geplande_dagen` die filtert op `recept is not None`.

## Ontwerp

### Beslissing: reden is UI-concern, domeinmodel kent alleen "geen boodschappen"

Het domeinmodel hoeft niet te weten *waarom* er geen boodschappen nodig zijn (hellofresh, uit eten, restjes). Het hoeft alleen te weten dat een dag geen recept heeft. De specifieke reden (hellofresh label, emoji, kleur) is puur UI-state en blijft in `hellofresh_dagen`.

### Wijziging 1: DagPlanning-validatie versoepelen

**Bestand:** `src/boodschappenagent/planner/models.py`

Verwijder de constraint:

```python
if self.personen > 0 and self.recept is None:
    msg = "recept is verplicht als personen > 0 is"
    raise ValueError(msg)
```

Dit maakt `DagPlanning(dag=X, recept=None, personen=0)` de universele representatie voor elke dag zonder boodschappen.

### Wijziging 2: `stel_type_in()` consolideren

**Bestand:** `src/boodschappenagent/web/routers/menu.py`

Geen duplicatie tussen hellofresh en geen_menu:

```python
if dagtype in ("geen_menu", "hellofresh"):
    nieuwe_dagen.append(DagPlanning(dag=dag, recept=None, personen=0))
else:  # recept
    recept = d.recept
    if recept is None:
        raise HTTPException(status_code=422, detail="Geen recept beschikbaar")
    personen = d.personen if d.personen > 0 else 2
    nieuwe_dagen.append(DagPlanning(dag=dag, recept=recept, personen=personen))
```

De `recept_backup` logica wordt volledig verwijderd. Bij terugschakelen naar "recept" zonder beschikbaar recept geeft de server HTTP 422 en moet de UI de receptkiezer openen.

### Geen wijzigingen nodig

De volgende componenten werken automatisch correct doordat ze `WeekMenu.geplande_dagen` gebruiken (filtert op `recept is not None`):

- **BoodschappenlijstGenerator.genereer()** — itereert over `geplande_dagen`
- **MenuHistory.sync_week() / add_week()** — itereert over `geplande_dagen`
- **voorraad._build_voorraad_context()** — itereert over `geplande_dagen`

### Serialisatie (`current_menu.json`)

Geen formatwijziging. Een hellofresh-dag wordt opgeslagen als `{"dag": 2, "recept_id": null, "personen": 0}` met het dagnummer in de `hellofresh_dagen` array. Bij laden wordt het onderscheid hersteld.

## E2E test

Nieuwe test `tests/e2e/test_hellofresh_boodschappen.py` die de hele keten valideert:

1. Start met standaard `TEST_WEEK_MENU` (5 receptdagen, 1 hellofresh, 1 niet-thuis)
2. Zet een extra dag op hellofresh via UI (tap dagkaart, tap "HelloFresh")
3. Navigeer naar `/boodschappen`
4. Verifieer dat het aantal boodschapitems correspondeert met het aantal receptdagen (hellofresh-dag uitgesloten)

Dit test de keten: UI -> `stel_type_in` -> domeinmodel -> `geplande_dagen` -> generator.

## Scope

### In scope
- DagPlanning validatie versoepelen
- `stel_type_in()` consolideren (geen_menu + hellofresh)
- `recept_backup` verwijderen
- E2E test voor hellofresh + boodschappenlijst keten
- Bestaande unit tests aanpassen

### Uit scope
- Nieuwe dagtypes toevoegen (uit eten, restjes, etc.)
- UI wijzigingen aan dagkaarten of sheet
- Wijzigingen aan serialisatieformaat
