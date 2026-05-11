# Feature Specification: Menu Variety — Seasonal/Non-Seasonal Recipe Mix

**Feature Branch**: `001-menu-variety-ratio`  
**Created**: 2026-05-11  
**Status**: Draft  
**Input**: User description: "Bij het samenstellen van het weekmenu wil ik meer variatie in de gekozen recepten. Kijk niet alleen naar recepten met de seizoensgroenten, maar neem ook andere recepten mee om uit te kiezen. Hanteer een verhouding van 80% seizoens en 20% andere recepten. Voor andere recepten mag je uit alle beschikbare recepten kiezen."

## Clarifications

### Session 2026-05-11

- Q: How should the 80/20 ratio be applied — fixed slot allocation or probabilistic per day? → A: Probabilistic per day: for each day independently, there is an 80% chance of selecting from the seasonal pool and a 20% chance of selecting from the full catalogue (no season constraint). The final distribution is approximate, not exact.
- Q: How is a recipe's season determined — via the `seizoen` attribute or another mechanism? → A: The `seizoen` attribute is obsolete. Season is determined dynamically using the `groenten_seizoenskalender` from `data/reference`: a recipe is seasonal for the current month if at least one of its ingredients appears in the calendar with the current month listed in `lage_co2_maanden`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Varied Weekly Menu (Priority: P1)

When the weekly menu is generated, each day's recipe is chosen independently: with 80% probability from the current season's pool, and with 20% probability from the full recipe catalogue without any season filter. Over time this produces menus that are predominantly seasonal but include regular non-seasonal variety.

**Why this priority**: This is the core behaviour change requested. Without it, all other user stories have no foundation.

**Independent Test**: Generate a large number of weekly menus and verify that approximately 20% of individual day selections come from outside the current season's pool.

**Acceptance Scenarios**:

1. **Given** a weekly menu is requested, **When** the planner selects a recipe for a given day, **Then** it independently draws either from the seasonal pool (with 80% probability) or from the full catalogue (with 20% probability).
2. **Given** the 20% draw occurs for a day, **When** the planner selects from the full catalogue, **Then** any recipe in the database may be chosen — including recipes that happen to match the current season.
3. **Given** multiple weeks of menus are generated, **Then** approximately 20% of all daily recipe selections are drawn from the unconstrained full catalogue.

---

### User Story 2 - Variety Constraints Still Applied (Priority: P2)

Existing variety rules (no recently repeated recipes, category diversity) continue to apply regardless of which pool a recipe is drawn from on any given day.

**Why this priority**: Without this, the 20% unconstrained draw could repeatedly pick the same popular recipe, defeating the purpose of variety.

**Independent Test**: Generate menus for multiple consecutive weeks and verify no single recipe appears in back-to-back weeks regardless of which pool it was drawn from.

**Acceptance Scenarios**:

1. **Given** a recipe was used in the previous week's menu, **When** the next weekly menu is generated, **Then** that recipe is excluded from both the seasonal and unconstrained candidate pools (subject to existing history rules).
2. **Given** the unconstrained pool is drawn for a day, **When** all unconstrained candidates were recently used, **Then** the planner applies the same fallback behaviour as it does today for exhausted pools.

---

### User Story 3 - Graceful Fallback When Seasonal Pool Is Empty (Priority: P3)

If the seasonal pool is empty when an 80% draw occurs for a day (e.g., all seasonal recipes have been recently used), the planner falls back to the full catalogue for that day rather than failing.

**Why this priority**: Edge case that keeps the system functional when the seasonal pool is exhausted.

**Independent Test**: With all seasonal recipes in the history window, the planner still produces a complete menu without errors.

**Acceptance Scenarios**:

1. **Given** the seasonal pool is empty for a given day's draw, **When** the menu is generated, **Then** the planner selects from the full catalogue for that day instead of returning an error.
2. **Given** the fallback is triggered, **When** the menu is presented, **Then** no error or warning is shown to the user — the menu is simply complete.

---

### Edge Cases

- What happens when the seasonal pool is empty on an 80% draw? → Fall back to full catalogue for that day (covered in User Story 3).
- What happens if a recipe drawn from the full catalogue also matches the current season? → This is valid; the pool selection (seasonal vs. full) is what matters, not the recipe's own season attribute.
- What happens when the full recipe catalogue is entirely seasonal (all recipes match current season)? → The 20% unconstrained draw still selects from all recipes; variety is achieved via history constraints.
- Can the same recipe be both a candidate in the seasonal pool and the unconstrained pool? → Yes, but it will only be selected once for a given day; the pools overlap, the day slot does not.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: For each day in the weekly menu, the planner MUST independently apply an 80% probability of selecting a recipe from the seasonal pool and a 20% probability of selecting from the full recipe catalogue.
- **FR-002**: When the 80% draw occurs, the recipe MUST be selected from recipes that are seasonal for the current month. A recipe is seasonal for a given month if at least one of its ingredients appears in the `groenten_seizoenskalender` with that month listed in `lage_co2_maanden`.
- **FR-003**: When the 20% draw occurs, the recipe MAY be selected from any recipe in the database, without season filtering.
- **FR-004**: Existing variety constraints (history-based repetition prevention, category diversity) MUST be applied regardless of which pool is selected for a given day.
- **FR-005**: If the seasonal pool is empty when an 80% draw occurs for a day, the planner MUST fall back to the full recipe catalogue for that day.

### Key Entities

- **Recipe**: A dish with a list of ingredients. Season is not stored on the recipe itself; it is derived dynamically from the ingredient list.
- **Groenten Seizoenskalender**: A reference table (`data/reference/groenten_seizoenskalender.json`) listing vegetables and the months in which they have low CO2 footprint (`lage_co2_maanden`). This is the authoritative source for determining whether a recipe is seasonal.
- **Seasonal Recipe**: A recipe that has at least one ingredient that appears in the `groenten_seizoenskalender` with the current month in its `lage_co2_maanden`.
- **Weekly Menu**: A collection of recipe assignments across all days of a single week.
- **Seasonal Pool**: The subset of recipes that are seasonal for the current month, after applying variety constraints.
- **Full Catalogue**: All available recipes regardless of season classification, after applying variety constraints.
- **Variety History**: The record of recently used recipes used to prevent repetition.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Over 10 or more consecutively generated menus, approximately 20% of daily recipe selections come from the unconstrained full catalogue (within a ±10% tolerance).
- **SC-002**: The planner does not restrict recipe selection exclusively to the current season — at least one day per week will statistically select from the full catalogue over a series of weeks.
- **SC-003**: No single recipe appears in consecutive weekly menus (existing variety guarantee remains intact across both pools).
- **SC-004**: The planner always produces a complete menu for every requested day, even when the seasonal pool is exhausted.

## Assumptions

- The 80/20 probability is applied independently and randomly for each day — the weekly distribution is approximate, not exact.
- The existing history-based variety constraints continue to apply unchanged.
- "Full catalogue" means all available recipes after removing those excluded by history or other active constraints.
- Season classification is dynamic and based on the `groenten_seizoenskalender`; there is no `seizoen` attribute on recipes. A recipe without any vegetables in the calendar is never in the seasonal pool.
- The feature affects only the recipe selection algorithm; menu presentation and data storage are unchanged.
- Days marked as "niet-thuis" (not home) do not require recipe selection and are unaffected by this change.
