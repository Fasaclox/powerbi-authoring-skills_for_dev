---
name: variance-indicators
description: "Builds MoM, QoQ and YoY variance indicators for Power BI cards and tables: DAX % measures that show -- when no period is selected or the prior period has no data, plus 19 named arrow/pill/badge styles as SVG image measures. Use for month over month, quarter over quarter, year over year, variance arrow, KPI trend badge, % change pill. For the base model use semantic-model-authoring; for placing visuals use powerbi-report-cli."
---

# Variance indicators

Period-over-period change (MoM, QoQ, YoY) shown as a small styled indicator:
an arrow or badge plus the percentage, picked from a catalog by name.

## When to use this skill
- "Add MoM / QoQ / YoY to this card", "show % change vs last month with an arrow"
- "Make the variance look like a green pill", "use the `trend-pill` style"
- Fixing variance measures that show wrong numbers when no period is selected

## When NOT to use it
- Building the date table, relationships or base measures → `semantic-model-authoring`
- Laying out pages, cards and tables, PBIR edits, publishing → `powerbi-report-cli`

## The two blank rules
Every variance this skill produces shows `--` when:
1. the period is not selected (e.g. no month **and** year for MoM), and
2. the prior period has no data (Jan 2021 selected but no Dec 2020).

Both are enforced in the numeric measure, so every style inherits them.
Details and the test matrix: [references/period-measures.md](references/period-measures.md).

## Workflow
1. **Inspect the model.** Find the base measure, the date table and a column
   unique per month / quarter / year. If the date table is missing or not
   contiguous, hand that part to `semantic-model-authoring` first.
2. **Write the numeric measures** `<Base> MoM %`, `<Base> QoQ %`, `<Base> YoY %`
   from [period-measures.md](references/period-measures.md), with both blank rules.
   Only the periods the user asked for.
3. **Pick the style.** Use the name the user gave. If they gave none, show the
   catalog ([references/style-catalog.md](references/style-catalog.md) or
   `assets/gallery.png`) and ask them to pick by name; suggest `pill` for cards
   and `arrow-simple` for tables.
4. **Write the style measure** by copying `references/styles/<style>.dax`:
   - point `_Pct` at the variance measure from step 2;
   - set `_Label` for the period (`vs last quarter`, `QoQ`, `vs last year`, `YoY`),
     or `""` to hide it. Never hard-code a month or year in a label; a dynamic
     label is opt-in (see period-measures.md);
   - set `_HigherIsBetter = FALSE ()` for cost-type metrics;
   - name it `<Base> <Period> <style>` and set **Data category = Image URL**
     (TMDL: `dataCategory: ImageUrl`).
5. **Place it** (with `powerbi-report-cli` when editing PBIR): a table/matrix
   column (set image height to the style's height), the Image visual bound to
   the measure, or a card's image slot. Where an image can't go (card callout,
   subtitle, tooltip), use the text + colour measures in
   [references/native-text.md](references/native-text.md).
6. **Verify** with the test matrix in period-measures.md: no selection, first
   period, a period with no prior data, growth, decline, zero change.

## Done means
The numeric variance measures and the chosen style measure exist in the model,
the style measure has the Image URL data category, and every row of the test
matrix shows the expected output (`--` for both blank rules) in a rendered
report or a DAX query.

## Adding or changing a style
Styles are generated. Edit `STYLES` in `scripts/build_styles.py`, run
`python3 scripts/build_styles.py`, and commit the regenerated `.dax`, previews
and catalog. Re-render `assets/gallery.png` from `assets/gallery.html` with any
headless browser.

## References
- [references/period-measures.md](references/period-measures.md): MoM/QoQ/YoY DAX, blank rules, model requirements, test matrix
- [references/style-catalog.md](references/style-catalog.md): all 19 styles with previews
- [references/styles/](references/styles/): one ready-to-paste SVG measure per style
- [references/native-text.md](references/native-text.md): text + colour measures for places that can't show an image
- `assets/gallery.png`, `assets/gallery.html`: every style on one page
- `scripts/build_styles.py`: the single source for styles, measures and previews
