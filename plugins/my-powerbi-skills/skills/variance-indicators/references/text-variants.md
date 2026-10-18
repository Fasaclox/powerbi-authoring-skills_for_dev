# Text variants: every style in a card's reference label

A card's reference label, a callout value, a visual subtitle and a tooltip only
render text, never an image, so the SVG measures in `styles/` can't go there.
Every style therefore has a text twin in `text/<style>.dax`, generated from the
same style definition:

| Measure | Returns | Bind it to |
|---|---|---|
| `[<Base> <Period> <style> Text]` | the indicator as text, e.g. `▲ +8.2% vs PM`, or `--` | the reference label's **Value** |
| `[<Base> <Period> <style> Color]` | hex colour for the state (up / down / flat / blank) | the Value's **font colour**: fx > Format style **Field value** |
| `[<Base> <Period> <style> Bg]` | soft (or solid) background colour; only styles drawn on a shape | a **background** colour fx, see below |

The two blank rules carry over unchanged: the text is `--` whenever the
variance measure is blank (no period selected, or no prior-period data), and
the colour measures return the neutral blank grey.

Preview of each text variant: `assets/text-previews/<style>.png` (also in the
[style catalog](style-catalog.md), next to the SVG preview).

## What changes compared with the SVG style

- **Icons become glyphs**: `▲ ▼` triangle, `⬆ ⬇` block arrow and circle badge,
  `↑ ↓` thin, `↗ ↘` diagonal and trend line, `∧ ∨ ›` chevron, `–` flat,
  `●` dot, `▌` accent bar, `▰▱` for the diverging bar (filled cells = size).
  Block and diagonal arrows carry U+FE0E so Windows draws the plain glyph in
  your font colour instead of a colour emoji.
- **One colour per label**: a reference label has one font colour, so the label
  text (`vs last month`) takes the status colour too. For a grey label, set
  `_Label = ""` in the Text measure and type the label into the reference
  label's **Title** (or **Detail**, where your card version has it), styled grey.
- **Shapes become a background colour**: pills, chips, soft boxes and the
  solid pill have a `Bg` measure. Apply it to the reference label's background
  fx if your Card visual offers one; otherwise to the card (or callout area)
  background, or leave it off. The text still reads correctly without it.
  `pill-solid` returns white text and a solid status-colour background.
- `stack` becomes one line (`⬆ +8.2% MoM`).

## Set-up in Power BI Desktop (new Card visual)

1. Add the period measures from [period-measures.md](period-measures.md) and
   the measures from `text/<style>.dax`. Rename `Sales`, `MoM` and the base
   measure exactly as for the SVG style; the label and `_HigherIsBetter`
   options work the same way.
2. Select the card. In the **Data** pane, drop the `Text` measure into
   **Reference labels**.
3. Format pane > **Reference labels** > **Value** > **Color** > **fx** >
   Format style **Field value** > the `Color` measure.
4. If the style has a `Bg` measure: in the same Reference labels section (or
   the card's **Background** / callout area), set the colour fx to Field value
   > the `Bg` measure.
5. Use a font with the glyphs (Segoe UI, the default, has all of them) and
   check the up, down, flat and `--` states with your period slicers.

The same Text + Color pair works in a visual's **subtitle** (Title > Subtitle >
Text fx, colour fx) and in a table/matrix cell with font colour fx.

When editing PBIR with `powerbi-report-cli`, bind the Text measure to the
card's reference label role and the Color/Bg measures as measure-driven
conditional formatting; look the role and formatting object names up with the
CLI (`catalog describe`, `formatting describe-object`) rather than guessing.
