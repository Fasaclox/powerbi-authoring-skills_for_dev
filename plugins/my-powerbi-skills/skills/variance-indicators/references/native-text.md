# Text-only variant (no SVG)

When the indicator must go somewhere that cannot show an image, such as a card
callout, a reference label, a subtitle or a tooltip, use a text measure plus a
colour measure for conditional formatting. This covers the icon-and-text styles
(`arrow-simple`, `triangle-tag`, `prefix`, `text-only`, `brackets`,
`descriptive`) with Unicode glyphs; pills, chips and boxes need the SVG measure.

```dax
Sales MoM Text =
VAR _Pct = [Sales MoM %]
VAR _R = ROUND ( _Pct, 3 )
VAR _Icon = SWITCH ( SIGN ( _R ), 1, "▲ ", -1, "▼ ", "– " )   -- or ↑ ↓, ↗ ↘
VAR _Label = "vs last month"                                   -- "" to hide
RETURN
    IF (
        ISBLANK ( _Pct ),
        "--",
        _Icon & FORMAT ( _R, "+0.0%;-0.0%;0.0%" )
            & IF ( _Label <> "", " " & _Label )
    )
```

```dax
Sales MoM Color =
VAR _Pct = [Sales MoM %]
VAR _HigherIsBetter = TRUE ()
VAR _Dir = SIGN ( ROUND ( _Pct, 3 ) )
VAR _Good = IF ( _HigherIsBetter, _Dir, - _Dir )
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( _Pct ), "#94A3B8",
        _Good = 1, "#15803D",
        _Good = -1, "#DC2626",
        "#64748B"
    )
```

Bind `Sales MoM Color` through the visual's font colour **fx → Field value**.
The text measure always returns a value, so a card never shows "(Blank)".

Glyph sets that render in Segoe UI on Windows and the service:
`▲ ▼` (triangle), `↑ ↓` (thin), `↗ ↘` (diagonal), `⬆ ⬇` (block). Test the
chosen glyph in the report's font before committing to it.
