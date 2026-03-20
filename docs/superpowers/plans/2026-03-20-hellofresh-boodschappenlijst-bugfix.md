# HelloFresh Boodschappenlijst Bugfix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the bug where hellofresh-days still generate groceries by making `stel_type_in` set `recept=None, personen=0` for hellofresh days, identical to "geen menu" days.

**Architecture:** The fix is in one handler (`stel_type_in`). Both "geen_menu" and "hellofresh" dagtypes set `DagPlanning(recept=None, personen=0)`. The `hellofresh_dagen` set remains as UI-only state for rendering. No domain model changes needed — `geplande_dagen` already filters on `recept is not None`.

**Tech Stack:** Python, FastAPI, pytest, Playwright (E2E)

**Spec:** `docs/superpowers/specs/2026-03-20-hellofresh-boodschappenlijst-bugfix-design.md`

---

### Task 1: Fix `stel_type_in` and update unit tests

This task combines the fix and all unit test updates into a single commit so the test suite never enters a broken state.

**Files:**
- Modify: `src/boodschappenagent/web/routers/menu.py:249-306`
- Modify: `tests/web/test_dag_aanpassen.py`
- Modify: `tests/web/conftest.py`

- [ ] **Step 1: Write the failing unit test**

Add to `tests/web/test_dag_aanpassen.py` in class `TestDagTypeSelector`:

```python
def test_stel_hellofresh_in_zet_recept_op_none(self, client: TestClient):
    """Bugfix: na stel hellofresh in is dag 0 recept=None, personen=0."""
    set_week_menu(client, make_full_week_menu())
    client.post("/week/dag/0/stel-type-in", data={"type": "hellofresh"})
    dag = client.app.state.week_menu.dagen[0]
    assert dag.recept is None
    assert dag.personen == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/web/test_dag_aanpassen.py::TestDagTypeSelector::test_stel_hellofresh_in_zet_recept_op_none -v`
Expected: FAIL — `dag.recept` is not None (current behavior keeps the recipe)

- [ ] **Step 3: Implement the fix**

In `src/boodschappenagent/web/routers/menu.py`, replace lines 262-298 of the `stel_type_in` handler. **Keep lines 300-306 (the template rendering) intact.** The new handler body becomes:

```python
    week_menu = _get_week_menu_or_404(request)
    hellofresh_dagen = set(getattr(request.app.state, "hellofresh_dagen", set()))

    nieuwe_dagen = []
    for d in week_menu.dagen:
        if d.dag == dag:
            if dagtype in ("geen_menu", "hellofresh"):
                nieuwe_dagen.append(DagPlanning(dag=dag, recept=None, personen=0))
            else:  # recept
                recept = d.recept
                if recept is None:
                    raise HTTPException(
                        status_code=422, detail="Geen recept beschikbaar"
                    )
                personen = d.personen if d.personen > 0 else 2
                nieuwe_dagen.append(
                    DagPlanning(dag=dag, recept=recept, personen=personen)
                )
        else:
            nieuwe_dagen.append(d)

    if dagtype == "hellofresh":
        hellofresh_dagen.add(dag)
    else:
        hellofresh_dagen.discard(dag)

    request.app.state.week_menu = WeekMenu(
        week_start=week_menu.week_start, dagen=nieuwe_dagen
    )
    request.app.state.hellofresh_dagen = hellofresh_dagen
    _save_state(request)

    # Lines 300-306 remain unchanged: render dag_context + template response
```

Note: `recept_backup` is removed entirely — no variable, no `getattr`, no `request.app.state.recept_backup`.

- [ ] **Step 4: Run the new test to verify it passes**

Run: `uv run pytest tests/web/test_dag_aanpassen.py::TestDagTypeSelector::test_stel_hellofresh_in_zet_recept_op_none -v`
Expected: PASS

- [ ] **Step 5: Add `make_week_menu_met_hellofresh` helper to conftest**

Add to `tests/web/conftest.py` after `make_week_menu_met_niet_thuis`:

```python
def make_week_menu_met_hellofresh(hellofresh_dag: int = 2) -> WeekMenu:
    """Maak een weekmenu met één hellofresh dag (recept=None, personen=0)."""
    dagen = []
    for i in range(7):
        if i == hellofresh_dag:
            dagen.append(DagPlanning(dag=i, recept=None, personen=0))
        else:
            dagen.append(DagPlanning(dag=i, recept=RECEPTEN[i], personen=2))
    return WeekMenu(week_start=WEEK_START, dagen=dagen)
```

Update the import in `tests/web/test_dag_aanpassen.py` to include `make_week_menu_met_hellofresh`.

- [ ] **Step 6: Update hellofresh tests to use correct domain state**

In `tests/web/test_dag_aanpassen.py`, replace all `set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})` calls with `set_week_menu(client, make_week_menu_met_hellofresh(), hellofresh_dagen={2})` in these tests:

- `test_hellofresh_kaart_is_tappable`
- `test_geen_vervang_dag_button_met_hellofresh`
- `test_sheet_opent_voor_hellofresh_dag`
- `test_huidig_dagtype_hellofresh_is_actief`
- `test_hellofresh_dag_geeft_422`
- `test_genereer_bewaart_hellofresh_dag`

- [ ] **Step 7: Update "terug naar recept" tests**

Replace the three `test_niet_thuis_terug_naar_recept_*` tests with a single test that verifies 422:

```python
def test_geen_menu_terug_naar_recept_zonder_backup_geeft_422(self, client: TestClient):
    """Na geen_menu → recept geeft 422 als er geen recept meer is."""
    set_week_menu(client, make_full_week_menu())
    client.post("/week/dag/0/stel-type-in", data={"type": "geen_menu"})
    response = client.post("/week/dag/0/stel-type-in", data={"type": "recept"})
    assert response.status_code == 422
```

Remove:
- `test_niet_thuis_terug_naar_recept_dagkaart_type`
- `test_niet_thuis_terug_naar_recept_app_state`
- `test_niet_thuis_terug_naar_recept_heeft_recept`

- [ ] **Step 8: Update "hellofresh uit" tests**

Replace `test_zet_hellofresh_uit_dagkaart_type` and `test_zet_hellofresh_uit_app_state` with:

```python
def test_hellofresh_terug_naar_recept_zonder_backup_geeft_422(self, client: TestClient):
    """Na hellofresh → recept geeft 422 als er geen recept meer is."""
    set_week_menu(client, make_week_menu_met_hellofresh(), hellofresh_dagen={2})
    response = client.post("/week/dag/2/stel-type-in", data={"type": "recept"})
    assert response.status_code == 422

def test_zet_hellofresh_uit_app_state_bij_422(self, client: TestClient):
    """Bij 422 (geen recept) blijft dag in hellofresh_dagen."""
    set_week_menu(client, make_week_menu_met_hellofresh(), hellofresh_dagen={2})
    client.post("/week/dag/2/stel-type-in", data={"type": "recept"})
    assert 2 in client.app.state.hellofresh_dagen
```

Note: when `stel_type_in` raises HTTPException(422) inside the loop for the "recept" case, the `hellofresh_dagen.discard(dag)` after the loop never executes. So the day correctly remains in `hellofresh_dagen` — the user needs to pick a recipe first.

- [ ] **Step 9: Run all dag_aanpassen tests**

Run: `uv run pytest tests/web/test_dag_aanpassen.py -v`
Expected: all tests PASS

- [ ] **Step 10: Commit**

```bash
git add src/boodschappenagent/web/routers/menu.py tests/web/test_dag_aanpassen.py tests/web/conftest.py
git commit -m "fix(menu): hellofresh dagen zetten recept op None in domeinmodel

Consolideert hellofresh en geen_menu in stel_type_in: beide zetten
recept=None, personen=0. Verwijdert recept_backup. Terugschakelen
naar recept zonder beschikbaar recept geeft nu 422."
```

---

### Task 2: Update E2E fixtures and tests

**Files:**
- Modify: `tests/e2e/conftest.py:215` (remove `recept_backup`)
- Modify: `tests/e2e/test_dag_aanpassen.py:220-241` (update terug-naar-recept test)

- [ ] **Step 1: Remove `recept_backup` from E2E conftest**

In `tests/e2e/conftest.py`, remove line 215:

```python
    app.state.recept_backup = {}
```

- [ ] **Step 2: Update E2E test `test_niet_thuis_terug_naar_recept`**

In `tests/e2e/test_dag_aanpassen.py`, replace the test at line 220-241 with:

```python
def test_niet_thuis_terug_naar_recept_dagtype_knoppen_blijven(self, week_page: Page):
    """E6: Niet-thuis → Recept (422) → dagkaart blijft niet-thuis, sheet toont dagtype knoppen."""
    # Zet dag 4 op niet-thuis
    week_page.locator("[data-testid='dagkaart'][data-dag='4']").click()
    week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")
    week_page.locator("[data-testid='dagtype-geen-menu']").click()
    week_page.wait_for_selector(
        "[data-testid='dagkaart'][data-dag='4'][data-type='niet-thuis']"
    )

    # Probeer terug naar recept — 422, HTMX does not swap on error
    week_page.locator("[data-testid='dagtype-recept']").click()

    # Dagkaart blijft niet-thuis (expect auto-retries tot timeout)
    expect(
        week_page.locator("[data-testid='dagkaart'][data-dag='4']")
    ).to_have_attribute("data-type", "niet-thuis")

    # Sheet toont nog steeds dagtype-selector
    expect(
        week_page.locator("#sheet [data-testid='dagtype-selector']")
    ).to_be_visible()
```

- [ ] **Step 3: Run E2E tests (dag_aanpassen only)**

Run: `uv run pytest tests/e2e/test_dag_aanpassen.py -v`
Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/conftest.py tests/e2e/test_dag_aanpassen.py
git commit -m "test(e2e): update fixtures en tests voor hellofresh bugfix"
```

---

### Task 3: E2E test — hellofresh dag genereert geen boodschappen

**Files:**
- Create: `tests/e2e/test_hellofresh_boodschappen.py`

- [ ] **Step 1: Write the E2E test**

```python
"""Playwright E2E test: HelloFresh-dag genereert geen boodschappen.

Valideert de hele keten: dagtype instellen → domeinmodel → boodschappenlijst.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestHelloFreshGeenBoodschappen:
    """Bugfix: HelloFresh-dag mag geen boodschappen genereren."""

    def test_hellofresh_dag_uitgesloten_van_boodschappenlijst(
        self, week_page: Page, live_server_url: str, app
    ):
        """Dag op hellofresh zetten → geplande_dagen telt 1 minder → boodschappenlijst OK.

        TEST_WEEK_MENU: 5 receptdagen, 1 hellofresh (dag 2), 1 niet-thuis (dag 5).
        Na dag 0 op hellofresh: 4 receptdagen, 2 hellofresh, 1 niet-thuis.
        """
        # Verifieer uitgangssituatie: 5 geplande dagen
        assert len(app.state.week_menu.geplande_dagen) == 5

        # Zet dag 0 (maandag, recept) op hellofresh via UI
        week_page.locator("[data-testid='dagkaart'][data-dag='0']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")
        week_page.locator("[data-testid='dagtype-hellofresh']").click()
        week_page.wait_for_selector(
            "[data-testid='dagkaart'][data-dag='0'][data-type='hellofresh']"
        )

        # Verifieer domeinmodel: nu 4 geplande dagen
        assert len(app.state.week_menu.geplande_dagen) == 4

        # Navigeer naar boodschappenlijst — deze moet laden zonder error
        week_page.goto(f"{live_server_url}/boodschappen")
        week_page.wait_for_load_state("networkidle")
        expect(week_page.locator("h1")).to_contain_text("Boodschappenlijst")

        # Boodschappenlijst heeft items (van de 4 receptdagen)
        expect(
            week_page.locator("[data-testid='boodschapitem']").first
        ).to_be_visible()
```

Note: the `data-testid='boodschapitem'` selector is used in the existing E2E tests in `tests/e2e/test_boodschappenlijst.py` (line 23, 41, etc.), so it is correct.

- [ ] **Step 2: Run the E2E test**

Run: `uv run pytest tests/e2e/test_hellofresh_boodschappen.py -v`
Expected: PASS (fix was applied in Task 1)

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_hellofresh_boodschappen.py
git commit -m "test(e2e): voeg hellofresh boodschappenlijst keten test toe"
```

---

### Task 4: Run full test suite and verify

- [ ] **Step 1: Run unit tests**

Run: `uv run pytest tests/ -v --ignore=tests/e2e`
Expected: all tests PASS

- [ ] **Step 2: Run E2E tests**

Run: `uv run pytest tests/e2e/ -v`
Expected: all tests PASS

- [ ] **Step 3: Run linter**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: no issues

- [ ] **Step 4: Final commit (if any lint fixes needed)**

```bash
git add -A
git commit -m "style: ruff format fixes"
```
