# Flaky Test Analysis (2026-03-20)

## Flaky Test Identified

**Test**: `tests/e2e/test_dag_aanpassen.py::TestDagTypeWijzigenUI::test_ander_recept_via_sheet[chromium]`

**Description**: Tests the "Ander recept" (shuffle recipe) feature on the week overview page.

### Failure Pattern

Test fails intermittently when the recipe shuffle doesn't actually change the recipe. Error message:
```
AssertionError: Dagkaart dag 0 heeft dezelfde tekst na shuffle: '[recipe_text]'
assert '[recipe_text]' != '[recipe_text]'
```

All 3 test runs failed with this test, but with different recipes selected (indicating the randomness is working, but the shuffle isn't actually changing the recipe).

### Root Cause

Located in `/home/pieter/projects/albert/agent-backend/src/boodschappenagent/planner/menu_planner.py`, method `vervang_recept()` (lines 85-130):

The method's fallback logic at line 191 allows returning the entire `seasonal` list when no non-used recipes are available:

```python
# Laatste redmiddel: sta duplicaten toe
return seasonal
```

**Test data has only 5 recipes**, and the E2E test setup uses all 5:
- Day 0: Spaghetti Bolognese (TARGET FOR SHUFFLE)
- Day 1: Kip Curry
- Day 2: None (HelloFresh)
- Day 3: Zalm Teriyaki
- Day 4: Groente Risotto
- Day 5: None (niet thuis)
- Day 6: Biefstuk met Friet

When shuffling day 0, the used_ids set contains all 5 recipes (other 4 + current), leaving 0 candidates. The fallback then returns the full seasonal list, which includes the original recipe, and `random.choice()` can select it again.

### Solution

The `vervang_recept()` method should explicitly exclude the original recipe from the final fallback, or ensure selection of a different recipe. Options:
1. Add logic to ensure selected recipe != original recipe (retry or explicit filtering)
2. Provide more test recipes in E2E fixture to avoid exhaustion
3. Document that menu shuffling requires sufficient recipe variety

### Files Affected

- `/home/pieter/projects/albert/agent-backend/src/boodschappenagent/planner/menu_planner.py` (lines 85-131)
- `/home/pieter/projects/albert/agent-backend/tests/e2e/conftest.py` (TEST_RECIPES fixture, lines 62-93)
- `/home/pieter/projects/albert/agent-backend/tests/e2e/test_dag_aanpassen.py` (test_ander_recept_via_sheet, lines 294-322)
