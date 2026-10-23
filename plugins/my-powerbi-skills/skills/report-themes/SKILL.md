---
name: report-themes
description: "Builds Power BI report themes from design tokens: colour palette, soft rounded or outlined cards, fonts, page canvas, tables, slicers and charts, as a schema-valid theme JSON plus the per-visual formatting a theme cannot set. 9 presets with previews, 192 product palettes or brand colours. Use for report theme, theme JSON, colour palette, rounded cards, match this dashboard design, dark mode, brand colours. To register it or edit PBIR use powerbi-report-cli."
---

# Report themes

Turns a look (a screenshot, a brand, "purple, soft rounded cards") into a
Power BI theme: one token set produces the theme JSON, a preview image and the
PBIR snippets for what themes don't cascade.

## When to use this skill
- "Make the report look like this design", "use a purple palette with soft rounded cards"
- "Create a theme JSON", "apply the `lavender-soft` theme", "dark mode theme", "use our brand colours"
- Picking fonts, card style, canvas and series colours for a new report

## When NOT to use it
- Registering the theme file, page/visual edits, validation, preview → `powerbi-report-cli` (authoring mode)
- Choosing archetypes, chart types and layout → `powerbi-report-cli` (design mode); this skill supplies its Step 5 theme
- Variance arrows and % pills on cards → `variance-indicators` (use this theme's good/bad colours)

## Workflow
1. **Pick the source of the tokens.**
   - A named preset: use it. No name, but a design or screenshot to match →
     compare it with the catalog and pick the closest preset (purple soft
     cards → `lavender-soft`), then override what differs. Nothing to go on →
     **`ocean-calm`**.
   - A product type ("fintech", "analytics dashboard") → `--palette` with a
     row from `references/uiux-palettes.csv` (`--list-palettes`).
   - Brand colours or a design to copy exactly → write a tokens JSON
     ([references/design-tokens.md](references/design-tokens.md)) and use `--tokens`.
2. **Show it first.** Before writing anything into the report, show the
   preset's preview `assets/previews/<preset>.png` (or render one with
   `--preview out.svg` for palettes and tokens), and say which preset or
   palette it is. For choosing, point to `assets/gallery.png` or
   [references/preset-catalog.md](references/preset-catalog.md).
3. **Build the theme.**
   `python3 scripts/build_theme.py --preset <name> --out <ThemeName>-<guid>.json`
   (add `--card soft|outlined|elevated|flat`, `--radius`, `--font-heading`,
   `--font-body` to adjust). It prints the contrast checks and exits 1 if a
   text pair is below 4.5:1; fix the token, don't ship the failure. A `warn` on
   series 2 (light pastels below 3:1) is acceptable only when bars carry
   labels or a legend.
4. **Register it** with `powerbi-report-cli` authoring (`theming.md`): file in
   `StaticResources/RegisteredResources/`, `report.json` `customTheme` +
   `resourcePackages` with the same `<Name>-<guid>.json`, which must also be
   the `name` inside the file (`--name` sets it). Then run
   `powerbi-report-author validate`.
5. **Apply what doesn't cascade.** `python3 scripts/build_theme.py --preset
   <name> --snippets` prints PBIR objects in the theme's colours: page
   background on every `page.json`, card `fillCustom` / value / label colours,
   slicer dropdown colours, `stylePreset: None` on tables. Where each goes:
   [references/visual-styling.md](references/visual-styling.md).
6. **Check it rendered.** Preview or screenshot the page and compare it with
   the preset preview (or the user's design): canvas colour, card fill and
   corners, fonts, series order.

## Done means
The theme file is registered and `validate` passes, the contrast checks show
no `FAIL`, every page has the theme's canvas colour, cards and tables carry
the non-cascading snippets, and a screenshot of the report matches the
preview the user approved.

## Fonts
Only fonts the Power BI service ships render for every viewer (Segoe UI
family, DIN, Georgia, Trebuchet MS, Verdana, …; list in
[design-tokens.md](references/design-tokens.md#fonts)). A design font such as
Poppins or Inter goes in as a fallback chain (`Poppins, Segoe UI, sans-serif`)
and only shows where it is installed; the build warns about it. Say so when
matching a design that uses one.

## Adding or changing a preset
Edit `PRESETS` in `scripts/build_theme.py`, run
`python3 scripts/build_theme.py --build-assets` (themes, SVG previews,
catalog, gallery), then `node scripts/render_previews.js` (Playwright) for the
PNGs. Validate the themes against Microsoft's schema (`$schema` URL in each
file) before committing.

## References
- [references/preset-catalog.md](references/preset-catalog.md): the 9 presets with previews, tokens and contrast
- [references/design-tokens.md](references/design-tokens.md): token schema, how each token maps to theme keys, card styles, fonts, contrast rules
- [references/visual-styling.md](references/visual-styling.md): what themes can't set, and the PBIR snippets for it
- [references/uiux-palettes.csv](references/uiux-palettes.csv): 192 product palettes from ui-ux-pro-max (MIT)
- `assets/themes/<Preset>.json`: ready theme per preset (rename to `<Name>-<guid>.json` when registering)
- `assets/previews/<preset>.png` (and `.svg`), `assets/gallery.png`, `assets/gallery.html`
- `scripts/build_theme.py`: presets, token → theme, contrast checks, previews, snippets
- `scripts/render_previews.js`: renders the PNG previews and gallery
