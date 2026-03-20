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

### Wijziging 1: `stel_type_in()` consolideren

**Bestand:** `src/boodschappenagent/web/routers/menu.py`

Geen duplicatie tussen hellofresh en geen_menu — beide zetten `recept=None, personen=0`:

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

### Wijziging 2: `recept_backup` verwijderen

De `recept_backup` logica in `stel_type_in()` en op `app.state` wordt volledig verwijderd. Bij terugschakelen naar "recept" zonder beschikbaar recept geeft de server HTTP 422. HTMX swapt niet bij 422, dus de sheet blijft staan — functioneel correct. Dit scenario komt in de praktijk nauwelijks voor.

De `recept_backup = {}` regel in `tests/e2e/conftest.py` (regel 215) moet ook verwijderd worden.

### DagPlanning-validatie: geen wijziging

De bestaande constraint `personen > 0 and recept is None → ValueError` blijft behouden als safety guard. De fix zet al `personen=0` voor hellofresh-dagen, dus de constraint wordt niet geraakt. Dit voorkomt dat per ongeluk een `DagPlanning(personen=3, recept=None)` wordt aangemaakt, wat downstream NoneType-fouten zou veroorzaken.

### Geen wijzigingen nodig

De volgende consumers werken automatisch correct doordat ze `WeekMenu.geplande_dagen` gebruiken (filtert op `recept is not None`):

- **BoodschappenlijstGenerator.genereer()** — itereert over `geplande_dagen`
- **MenuHistory.sync_week() / add_week()** — itereert over `geplande_dagen`
- **voorraad._build_voorraad_context()** — itereert over `geplande_dagen`
- **VoorraadChecker._ingredienten_uit_menu()** — itereert over `geplande_dagen`
- **MenuPlanner.vervang_recept()** — gebruikt `geplande_dagen` voor used IDs en buurdag
- **CLI menu module** — gebruikt `geplande_dagen` op meerdere plaatsen

### Serialisatie (`current_menu.json`)

Geen formatwijziging. Een hellofresh-dag wordt opgeslagen als `{"dag": 2, "recept_id": null, "personen": 0}` met het dagnummer in de `hellofresh_dagen` array. Bij laden wordt het onderscheid hersteld via `_build_dag_context()`, die `hellofresh_dagen` checkt *voordat* `personen == 0` wordt gecontroleerd.

### Edge case: `_generate_week_menu` + hellofresh

Bij "Genereer nieuw weekmenu" wordt `personen` per dag overgenomen uit het bestaande menu. Na de fix heeft een hellofresh-dag `personen=0`, dus de planner slaat die dag over. Tegelijk blijft `hellofresh_dagen` op `app.state` intact. Resultaat: hellofresh-status persisteert correct over regeneratie heen.

## E2E test

Nieuwe test `tests/e2e/test_hellofresh_boodschappen.py` die de hele keten valideert:

1. Start met standaard `TEST_WEEK_MENU` (5 receptdagen, 1 hellofresh, 1 niet-thuis)
2. **Cruciaal:** zet een extra receptdag op hellofresh via de UI (tap dagkaart, tap "HelloFresh") — dit exerciseert de bugfix in `stel_type_in`
3. Navigeer naar `/boodschappen`
4. Verifieer dat de ingrediënten van de hellofresh-gezette dag niet op de boodschappenlijst staan

Dit test de keten: UI -> `stel_type_in` -> domeinmodel -> `geplande_dagen` -> generator.

## Scope

### In scope
- `stel_type_in()` consolideren (geen_menu + hellofresh)
- `recept_backup` verwijderen (incl. E2E conftest.py)
- E2E test voor hellofresh + boodschappenlijst keten
- Bestaande unit tests aanpassen

### Uit scope
- DagPlanning validatie wijzigen (constraint blijft behouden)
- Nieuwe dagtypes toevoegen (uit eten, restjes, etc.)
- UI wijzigingen aan dagkaarten of sheet
- Wijzigingen aan serialisatieformaat
