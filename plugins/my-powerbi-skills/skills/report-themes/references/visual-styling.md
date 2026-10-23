# What a theme can't set

Power BI applies per-visual and per-page formatting above the theme, and a few
properties never cascade from it. `build_theme.py --snippets` prints each of
these as PBIR objects already filled with the theme's colours; this page says
where each one goes. File mechanics (selectors, VCO vs `objects`, validation)
are in `powerbi-report-cli` authoring: `page-formatting.md`, `card*.md`,
`slicers*.md`, `table.md`.

| Snippet | Goes in | Why |
|---|---|---|
| `page.json objects` | `objects` of **every** `page.json` | The canvas colour does not reliably follow the theme; pages without it render white |
| `cardVisual objects` | `visual.objects` of each card, with `selector: { "id": "default" }` | Card value/label colours and the inner fill are not reliably inherited; without the selector they silently fail |
| `cardVisual accent bar` | same, optional | `accentBar` never cascades; use `data[0]` or one colour per card |
| `slicer objects` | `visual.objects` of dropdown slicers | Dropdown list background is hard-coded white otherwise (breaks dark themes) |
| `tableEx / pivotTable objects` | `visual.objects` of every table and matrix | A table style preset overrides the theme's header and row colours |
| `variance pill colours` | the `variance-indicators` style measure | Keeps arrows and pills in the theme's good/bad colours |

## Recipes for the soft-card look

**KPI tiles (2×2 of rounded tiles).** One multi-value `cardVisual` with the
four measures. The theme already sets `cardCalloutArea` fill (`tile`) and
corner radius (`radius - 4`), so each callout renders as a rounded tile. Set
the card's own `background` to the page colour if you want the tiles to float
on the canvas instead of sitting in a container.

**Separate tile per KPI.** Four single cards; each gets the `cardVisual
objects` snippet. Give them equal sizes on the 8 px grid with 16 px gaps.

**Table with a white header strip on a tinted card.** The theme sets
`columnHeaders.backColor` to `header` (white in the soft presets) and turns
off vertical gridlines. Add `stylePreset: None` or the preset wins.

**Donut with a total in the middle.** The theme sets `innerRadiusRatio` to 72
and a slice border in the card colour. Put the total in the donut's centre label
where your Desktop version has one; otherwise place a card with a transparent
background over the hole (theme schema 2.153 has no centre-label property).

**Variance pill on a card.** Build it with `variance-indicators` (`trend-pill`
or `pill`), passing the theme's `good` and `bad` colours from the snippet.

**Dark presets.** `midnight-dark` needs every snippet above; also set Azure
map style to `grayscale_dark` and check text colours on shapes and textboxes
(`re-theming*.md` in `powerbi-report-cli`).

## Not possible in Power BI

- Rounded ends on individual bars or columns.
- Icons inside cards from the theme (use the card's image slot or an SVG measure).
- Custom web fonts for service viewers (see design-tokens.md § Fonts).
- A search box over a table; use a text or dropdown slicer.
