# How a ui-ux-pro-max row becomes Power BI decisions

All rules live in `scripts/direction.py` as ordered regex lists: the first match
wins. Change a rule there, then regenerate the catalog:

```
python3 scripts/direction.py --catalog > references/domain-catalog.md
```

## Source rows

The four CSVs in `uiux-data/` have one row per product type in the same order
(192 rows). The script refuses to run if they get out of step.

| File | Used for |
|---|---|
| `products.csv` | product type, keywords (matching), primary style (card style), dashboard style (archetype, density), key considerations |
| `colors.csv` | palette tokens, dark or light (background luminance), contrast checks |
| `ui-reasoning.csv` | colour and typography mood, anti-patterns |
| `typography.csv` | the font pairing whose mood and "best for" words overlap the product most |

## Matching a brief

Each query word scores 3 for a hit in the product type, 2 in its keywords and
1 in its dashboard style (plurals match singulars). The whole query appearing
in the product type adds 5. Rows with no dashboard style lose 0.5 so a
dashboard-shaped row wins a tie. `ALIASES` adds 6 for BI subject areas the
source has no row for:

| Words | Row |
|---|---|
| hr, people, workforce, headcount, attrition, employee | Job Board/Recruitment (HR Analytics Dashboard) |
| manufacturing, production, factory, warehouse, procurement | Inventory & Stock Management |
| supply, shipping | Logistics/Delivery |
| sales, pipeline | CRM & Client Management |
| finance, financial, accounting, budget, revenue | Financial Dashboard |
| marketing, campaign | Marketing Agency |
| helpdesk, itsm | Status Page / Incident Management |
| executive, kpi | Analytics Dashboard |

## Tone

The tone is one of upstream's catalog names
(`powerbi-report-cli/references/design/tone-catalog.md`), so its typography,
surface, gridline and signature guidance carries over. The product type name
is tested first; only if it matches nothing are its keywords and styles tested.

| Tone | Matches (word starts) |
|---|---|
| Corporate Cool | saas, b2b, crm, bank, insurance, legal, invoice, government (and the default) |
| Monospace Terminal | developer, ide, terminal, cyber, api, quantum, devops, code, hacker |
| Clinical Calm | health, medical, clinic, patient, dental, pharmac, veterinar, telemedicine, senior care, mental, therapy, sleep, wellness, meditation, spa … |
| Editorial Newsroom | news, magazine, blog, publishing, journal, podcast, editorial |
| Scholarly Calm | academic, research, universit, course, lms, education, learning, science, biotech, museum … |
| Industrial Dense (Analyst Workbench) | logistic, inventory, iot, energy, utilit, manufactur, airline, construction, fleet, warehouse, supply, status, incident … |
| Minimal Restrained | luxury, premium, fashion, architecture, interior, gallery, hotel, real estate, wedding, photography, portfolio |
| Playful Energetic | gam, kids, fitness, sport, music, food, restaurant, pet, social, event, e-commerce, retail, shop, marketplace … |
| Industrial Cockpit | overrides the above when the palette is dark **and** the row is live (real-time, monitor, operations, streaming, trading) |

## Archetype, density, card style, mode

| Decision | From | Rule |
|---|---|---|
| Archetype | dashboard style | real-time, monitor, operations, occupancy, inventory, IoT, pipeline, claims → `operational-monitor`; comparative, benchmark, leaderboard, performance → `comparative-benchmark`; drill-down, behaviour, predictive, data-dense, analytics → `analytical-canvas`; anything else or `N/A` → `executive-summary` |
| Density | dashboard style + tone | data-dense, real-time, monitor → dense; executive, luxury, minimal, editorial → spacious; else standard |
| Mode | background colour | relative luminance < 0.2 → dark |
| Card (`report-themes --card`) | primary style | dark mode, OLED, cyberpunk, HUD, 3D → `elevated`; glass, soft UI, clay, neumorphism, aurora, organic → `soft`; data-dense, bento, accessible, trust → `outlined`; else `flat` (dark rows never get `flat`) |

## Palette and contrast

The output lists the row's tokens and checks five pairs: text on background,
label on primary and muted text on card at 4.5:1, primary and accent on
background at 3:1. `color_map_seed` is primary, secondary and accent, each
lightened (dark cards) or darkened (light cards) in 5% steps until it reaches
3:1 on the card, so it is safe for measure colours in the Design Brief.

`report-themes --palette` builds the series from the raw row, so it warns on
the same colours. When it does, either put the seed into a tokens file
(`report-themes/references/design-tokens.md`) or choose another row.

## Fonts

Every font in `typography.csv` is classed and mapped to a font the Power BI
service ships:

| Class | Examples | Heading | Body |
|---|---|---|---|
| sans | Inter, Poppins, Open Sans, IBM Plex Sans, Lexend | Segoe UI Semibold | Segoe UI |
| serif | Playfair Display, Lora, Merriweather, EB Garamond, Cinzel | Georgia | Segoe UI |
| script | Caveat, Great Vibes, Kalam | Georgia | Segoe UI |
| condensed / tech display | Bebas Neue, Barlow Condensed, Orbitron, Russo One | DIN | Segoe UI |
| mono | JetBrains Mono, Fira Code, Space Mono | Consolas | Consolas only for Monospace Terminal, else Segoe UI |
| rounded | Fredoka, Nunito, Quicksand, Varela Round | Trebuchet MS | Segoe UI |

Body text never becomes a serif or script font: upstream's typography rules
keep axis labels, data labels and matrix cells in a sans. Language-specific
Noto pairings are skipped; for a right-to-left or CJK report choose fonts with
the user.

## Known limits

- The source is written for apps and websites. Anti-patterns such as
  "excessive animation" or "hidden filters" are passed through as written;
  apply the ones that have a report equivalent.
- Tone rules are keyword-based. Check the result reads right for the user's
  audience; a board pack for a gaming company may still want Minimal
  Restrained, not Playful Energetic.
- Brand guidelines always win over this skill.
