# Design tokens

A theme is built from one small token set. The idea (semantic tokens such as
primary, background, card, muted, border, checked for contrast, instead of raw
hex scattered over visuals) comes from
[ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
(MIT, © 2024 Next Level Builder); its palette table is vendored as
`uiux-palettes.csv`.

## Token file

`--tokens brand.json` takes the same keys as a preset in `scripts/build_theme.py`:

```json
{
  "label": "Contoso HR",
  "mode": "light",
  "card": "soft",
  "radius": 14,
  "heading": "Segoe UI Semibold",
  "body": "Segoe UI",
  "page": "#FFFFFF",
  "outspace": "#F4F0FB",
  "surface": "#F7F3FD",
  "tile": "#F7F3FD",
  "border": null,
  "text": "#1F1A2E",
  "muted": "#6B5F8A",
  "grid": "#E6DEF5",
  "header": "#FFFFFF",
  "data": ["#5B2C83", "#A88BDB", "#7E57C2", "#C7B5EC", "#3B1A5A", "#D58BC0", "#8E7CB8", "#E3D8F6"],
  "good": "#1E8E54",
  "bad": "#C93B53",
  "neutral": "#B7791F"
}
```

`tile` and `header` default to `surface`; `border` defaults to `grid` for
outlined cards. Start from the closest preset and change only what differs.

## Matching a screenshot

| Look in the design | Token |
|---|---|
| Area behind the cards | `page` |
| Frame or sidebar around the page | `outspace` |
| Card / visual background | `surface` |
| KPI tile background (inside a multi-value card) | `tile` |
| Card outline (none, hairline) | `border`, `card` |
| Corner rounding, in px at 1920 wide | `radius` |
| Darkest text: values, titles | `text` |
| Labels, axis text, legend | `muted` (must stay ≥ 4.5:1 on `surface` and `tile`) |
| First and second chart series | `data[0]`, `data[1]` |
| Green and red pill text | `good`, `bad` (pill fill is derived: 15 % of the colour over `tile`) |

Sample colours from the image, then darken `muted` until the check passes.
Designs often use pale lavender or grey labels that fail contrast at 9–10 pt.

## How tokens map to the theme

| Token | Theme keys |
|---|---|
| `data` | `dataColors`; `data[0]` also `tableAccent`, gradient `maximum`, filter-pane checkbox |
| `text` | `firstLevelElements`, `textClasses.*.color`, titles, values, table values |
| `muted` | `secondLevelElements`, `fourthLevelElements`, axis/legend `labelColor`, card labels, table headers |
| `grid` | `thirdLevelElements`, gridlines (dotted), table rules, filter card borders |
| `surface` | `background`, `visualStyles.*.*.background`, slicer item background, tooltip (dark mode) |
| `tile` | `secondaryBackground`, `cardVisual.cardCalloutArea.backgroundFillColor`, `fillCustom`, applied filter cards |
| `page`, `outspace` | `visualStyles.page.*.background` / `.outspace` (also set per page, see visual-styling.md) |
| `header` | table and matrix `columnHeaders.backColor`, totals |
| `border`, `radius` | `visualStyles.*.*.border`, `cardVisual.border`; `radius - 4` for KPI tiles |
| `heading` | `textClasses.callout/title/largeTitle/header.fontFace`, visual titles, card values |
| `body` | `textClasses.label.fontFace`, axes, legends, tables, slicers |
| `good`, `bad`, `neutral` | sentiment keys; card reference label colour |

The rest is fixed and comes from upstream's `base.json` safeguards: textbox
zero padding and no background, card zero padding, table grow-to-fit headers,
bar charts with labels and no value axis, smooth line charts.

## Card styles

| `card` | Visual container | Use when |
|---|---|---|
| `soft` | tinted fill, no border, no shadow | pastel dashboards; canvas white, cards tinted |
| `outlined` | white fill, 1 px `border` | grey canvas, formal reports |
| `elevated` | white fill, soft drop shadow | warm or tinted canvas; few visuals per page |
| `flat` | no border, square corners | Swiss/minimal, dense analytical pages |

Shadows cost legibility on dense pages; keep `elevated` for pages with ≤ 8 visuals.

## Fonts

Fonts the Power BI service renders for every viewer: Segoe UI, Segoe UI
Semibold, Segoe UI Bold, Segoe UI Light, DIN, Arial, Arial Black, Calibri,
Cambria, Candara, Consolas, Constantia, Corbel, Courier New, Georgia, Lucida
Sans Unicode, Tahoma, Times New Roman, Trebuchet MS, Verdana.

Any other font is written as `Font, Segoe UI, sans-serif` and only shows on
machines that have it installed; viewers in the service see Segoe UI. Closest
safe stand-ins for common design fonts:

| Design font | Use |
|---|---|
| Poppins, Montserrat, Inter, DM Sans | Segoe UI Semibold headings, Segoe UI body |
| Roboto, Open Sans, Lato | Segoe UI |
| Playfair, Lora, Merriweather (headings) | Georgia headings, Segoe UI body |
| Barlow, Oswald, condensed numerics | DIN |

Keep serif fonts out of axes, tables and data labels.

## Contrast rules

`build_theme.py` checks every build (WCAG 2.2):

| Pair | Minimum | On failure |
|---|---|---|
| `text` on `surface` and `page` | 4.5:1 | FAIL, exit 1 |
| `muted` on `surface`, `tile`, `header` | 4.5:1 | FAIL, exit 1 |
| `good`, `bad` on `tile` | 3:1 | warn |
| `data[0]`, `data[1]` on `surface` | 3:1 (graphics) | warn |

A pastel second series (`lavender-soft`, `rose-soft`) warns by design. Keep
data labels or a legend on those charts, and never let the pastel series be
the only carrier of meaning.

## Palettes from ui-ux-pro-max

`--palette "<Product Type>"` reads a row of `uiux-palettes.csv` and maps:
Primary/Secondary/Accent → `data[0..2]` (plus tints and shades for the rest),
Foreground → `text`, Muted Foreground → `muted`, Border → `grid`,
Muted → `header`, Destructive → `bad`, Background → `outspace`, and a 5 %
tint of Primary → `surface` and `tile` (soft cards on a white canvas).
`--list-palettes` lists all 192.
