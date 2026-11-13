# Web layer guidance

## UI/UX Principles

- **"Systeem stelt voor, jij past aan"**: the app always opens with a fully populated weekly menu proposal — never a blank screen. The user rejects or replaces; they don't build from zero.
- **Touch-first**: all interactive targets ≥ 44×44 pt. Primary platform iOS/iPadOS (iPhone 13, 390×844).
- **HTMX out-of-band updates**: when a sheet is open and the user changes something (dagtype, persons, shuffle recipe), the background dagkaart updates in place while the sheet stays open. No full-page reloads for within-session changes. No SPA frameworks; the server returns HTML, not JSON.
- **Fixed ordering flow**: Weekoverzicht → (optioneel) Recept vervangen / Shuffle → Ingredient-selectie → Voorraadcheck → Matching → Match-review → AH Bevestiging. The system never skips a step; the user may proceed past any step directly. Kookmodus is a separate daily flow.

## Styling Conventions

All colors and visual tokens are defined **once** in the Tailwind config in `templates/base.html`. Never use inline `style` attributes or hardcoded hex color codes in templates.

- **Use Tailwind utility classes** (`bg-ah-blue`, `text-hf-text`, `bg-muted-bg`) — never inline `style="color: #..."`.
- **Add new colors to the Tailwind config** in `base.html` under `tailwind.config.theme.extend.colors` before using them in templates.
- **Use semantic color names** grouped by domain: `ah-*` (Albert Heijn brand), `hf-*` (HelloFresh), `muted-*` (inactive/disabled states).
