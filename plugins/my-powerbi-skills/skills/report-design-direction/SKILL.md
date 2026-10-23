---
name: report-design-direction
description: "Picks a Power BI report's design direction from its business domain: tone, archetype, density, dark or light, card style, contrast-checked palette and Power BI-safe fonts, from 192 industry profiles. Use for design direction, look and feel, what style suits an HR / finance / healthcare / logistics report. For the theme JSON use report-themes; for the Design Brief, charts and PBIR use powerbi-report-cli."
---

# Report design direction

Turns "it's a hospital operations report" into concrete design decisions before
any page is drawn. Upstream's design mode has 12 tones and a 9-row
domain → tone table; this skill covers 192 product and industry types from
[ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT)
and translates each into the fields upstream's `Design Brief:` and the
`report-themes` skill already use.

## When to use this skill
- "What style suits a recruitment / clinic / fintech / logistics dashboard?"
- "Pick colours and fonts for our insurance claims report", "give it a look and feel"
- The user names a domain but no tone, palette or brand: run this before
  `powerbi-report-cli` design mode fills `design_identity`

## When NOT to use it
- The user gave brand colours, a screenshot or a preset name → `report-themes`
  directly (brand wins over domain defaults)
- Chart choice, layout contract, signatures, the full brief → `powerbi-report-cli` (design mode)
- Building, registering and applying the theme file → `report-themes`, then `powerbi-report-cli` authoring

## Workflow
1. **Match the domain.**
   `python3 scripts/direction.py "<domain words from the brief>"`
   (e.g. `"hr attrition"`, `"hospital patient"`, `"warehouse inventory"`). It
   prints the best row and up to three close matches. If a close match fits
   better, rerun with `--product "<name>"`. `--list` shows all 192 rows;
   [references/domain-catalog.md](references/domain-catalog.md) shows each
   row's result in one table. Common BI subject areas the source lacks (HR,
   manufacturing, sales, finance, marketing, IT) are aliased to the nearest row.
2. **Show the direction and say it is a recommendation.** Give the user the
   tone, archetype, light or dark, card style, three palette colours and the
   Power BI fonts in a few lines, and note the matched row. When the brief is
   vague, offer it as one option, as upstream's tone catalog asks.
3. **Fix contrast before using it.** The output checks the palette (4.5:1 for
   text, 3:1 for data colours). `color_map_seed` is already adjusted to 3:1 on
   the card. A row marked `FIX` on a data colour needs either the seed colours
   in a `report-themes` tokens file or another row; don't ship it as is.
4. **Hand off.**
   - `design_identity.tone`, `archetype`, density and the `color_map` seed go
     into the `Design Brief:` (`powerbi-report-cli` design mode). The tone is
     an upstream catalog name, so its typography, gridline and signature
     guidance applies.
   - Run the printed `report-themes` command to build the theme JSON and
     preview, and show the preview before applying it.
5. **Fonts.** Use the Power BI fonts the output gives. The source pairing
   (e.g. Poppins / Open Sans) only renders where installed; if the user wants
   it anyway, use the printed fallback chain and tell them viewers without
   the font see the Power BI font.

## Done means
The user has seen and accepted the direction (or chosen another row), every
contrast pair passes or has a stated fix, and the tone, archetype and colour
seed are in the Design Brief or the theme was built from the printed command.

## How the mapping works
Rules for tone, archetype, density, card style, dark mode and fonts, and how
to change them: [references/mapping.md](references/mapping.md).

## References
- [references/mapping.md](references/mapping.md): how each ui-ux-pro-max field becomes a Power BI decision
- [references/domain-catalog.md](references/domain-catalog.md): every row's direction (regenerate with `--catalog`)
- `references/uiux-data/`: `products.csv`, `colors.csv`, `typography.csv`, `ui-reasoning.csv` copied unchanged from ui-ux-pro-max v2.15.0 (`d14efff`), with its MIT `LICENSE`
- `scripts/direction.py`: matching, mapping, contrast checks, catalog
