# UI Design: Match Review Cards

**Feature**: `003-ingredient-match-review`
**Platform**: Mobile-first, iPhone 13 (390×844), `max-w-lg mx-auto`

---

## Page Layout

```
┌─────────────────────────────┐  390px
│  ← Boodschappenlijst        │  header (back link, title)
│                             │
│  Controleer de matches      │  h2
│  Kijk of de producten       │
│  kloppen voordat je de      │  subtitle
│  lijst aanmaakt bij AH.     │
│                             │
│ ┌─────────────────────────┐ │
│ │  [matched card]         │ │
│ ├─────────────────────────┤ │
│ │  [matched card]         │ │
│ ├─────────────────────────┤ │
│ │  [no-match card] ⚠️     │ │
│ ├─────────────────────────┤ │
│ │  [matched card]         │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │  Bevestig en maak       │ │  sticky bottom bar
│ │  AH-lijst aan           │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

Cards are in a single column list. The confirm button is sticky at the bottom.

---

## Card States

### State 1 — Matched (automatic or from reference)

```
┌─────────────────────────────────────────┐
│ melk                        Corrigeer › │  ← text-gray-800 font-medium + text-ah-blue
│ 1 liter                                 │  ← text-sm text-gray-400
├─────────────────────────────────────────┤
│ 🛒  AH Volle melk 1L         € 1,09     │  ← text-gray-700 + price right-aligned
│     zoekopdracht                        │  ← badge: text-xs text-gray-400
└─────────────────────────────────────────┘
```

Tailwind: `bg-white rounded-xl p-4 border border-gray-100`

---

### State 2 — Matched from saved preference (⭐ voorkeur)

```
┌─────────────────────────────────────────┐
│ oregano                     Corrigeer › │
│ 2 tl                                    │
├─────────────────────────────────────────┤
│ 🛒  AH Oregano gedroogd 15g  € 0,89     │
│     ⭐ voorkeur                          │  ← badge: text-xs text-ah-blue bg-ah-blue-light
└─────────────────────────────────────────┘
```

Source badge `voorkeur`: `bg-ah-blue-light text-ah-blue text-xs px-2 py-0.5 rounded-full`

---

### State 3 — No match found (⚠️ error)

```
┌─────────────────────────────────────────┐  ← border-amber-200 bg-amber-50
│ quinoa                    Zoek product  │  ← "Zoek product" in text-amber-700
│ 200 gram                                │
├─────────────────────────────────────────┤
│ ⚠️   Geen match gevonden                │  ← text-amber-700
└─────────────────────────────────────────┘
```

Tailwind: `bg-amber-50 rounded-xl p-4 border border-amber-200`
"Zoek product" button/link: `text-sm font-medium text-amber-700`

---

### State 4 — Correction in progress (search open)

Clicking "Corrigeer" or "Zoek product" replaces the bottom half of the card:

```
┌─────────────────────────────────────────┐
│ melk                                    │  ← no corrigeer button while searching
│ 1 liter                                 │
├─────────────────────────────────────────┤
│ 🔍  [zoek een product...        ] ✕     │  ← search input + close button
├─────────────────────────────────────────┤
│ AH Volle melk 1L           € 1,09  Kies │
│ AH Halfvolle melk 1L       € 0,99  Kies │
│ Campina Volle melk 1L      € 1,29  Kies │
│ …                                       │
└─────────────────────────────────────────┘
```

Search input: `w-full border border-gray-200 rounded-lg px-3 py-2 text-sm`
Results list: `divide-y divide-gray-100`
Each result row: `flex items-center justify-between py-2`
Product name: `text-sm text-gray-800`
Price: `text-sm text-gray-500`
"Kies" button: `text-sm font-medium text-ah-blue py-1 px-2`

HTMX: `hx-trigger="input changed delay:300ms"` on search input, `hx-target="#zoek-<uuid>"`, `hx-get="/boodschappen/zoek-product?item_id=<uuid>&q="`

---

### State 5 — Corrected by user (✓ gecorrigeerd)

```
┌─────────────────────────────────────────┐  ← border-l-4 border-l-ah-green
│ melk                        Corrigeer › │
│ 1 liter                                 │
├─────────────────────────────────────────┤
│ ✓  AH Halfvolle melk 1L     € 0,99     │  ← text-ah-green checkmark
│    ✏️ gecorrigeerd                       │  ← badge: text-xs text-gray-400
└─────────────────────────────────────────┘
```

Left accent border: `border-l-4 border-l-ah-green` (added to the card wrapper)

---

### State 6 — Preference unavailable (fallback to search)

```
┌─────────────────────────────────────────┐
│ melk                        Corrigeer › │
│ 1 liter                                 │
├─────────────────────────────────────────┤
│ 🛒  AH Volle melk 1L         € 1,09     │
│     ⚠️ voorkeur niet meer beschikbaar   │  ← text-xs text-amber-700
└─────────────────────────────────────────┘
```

---

## Confirm Button Bar (sticky bottom)

### Disabled state (1 or more items without match)

```
┌─────────────────────────────────────────┐
│  Nog 2 producten zonder match           │  ← text-sm text-gray-500, centered
│ ┌─────────────────────────────────────┐ │
│ │    Bevestig en maak AH-lijst aan    │ │  ← bg-gray-200 text-gray-400, rounded-xl
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

Button: `w-full py-3 rounded-xl bg-gray-200 text-gray-400 text-center` + `disabled` attribute

### Active state (all items matched)

```
┌─────────────────────────────────────────┐
│ ┌─────────────────────────────────────┐ │
│ │    Bevestig en maak AH-lijst aan    │ │  ← bg-ah-blue text-white, rounded-xl
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

Button: `w-full py-3 rounded-xl bg-ah-blue text-white text-center font-medium`

---

## Color & Token Summary

| Token | Usage in this feature |
|-------|----------------------|
| `bg-white border-gray-100` | Default matched card |
| `bg-amber-50 border-amber-200` | No-match card background |
| `text-amber-700` | "Geen match" text + "Zoek product" action |
| `bg-ah-blue-light text-ah-blue` | "voorkeur" source badge |
| `text-ah-green` | Checkmark on corrected items |
| `border-l-ah-green` | Left accent on corrected card |
| `bg-ah-blue text-white` | Active confirm button |
| `bg-gray-200 text-gray-400` | Disabled confirm button |
