# Period variance measures: MoM, QoQ, YoY

These numeric measures feed every style. Each returns a ratio (0.082 = +8.2%)
or `BLANK()`. A blank is what every style renders as `--`.

## The two blank rules (always both)

| Rule | Example | Result |
|---|---|---|
| 1. The period is not selected | No month and year picked in the slicers, so MoM has nothing to compare | `--` |
| 2. The prior period has no data | Jan 2021 is selected but there is no Dec 2020 (no rows, or the date table starts in 2021) | `--` |

Two extra guards follow from rule 2 and are on by default: a prior value of `0`
(the ratio is undefined) and a blank current value also return `--`.

## Model requirements

Check these with `semantic-model-authoring` / the modeling MCP before writing measures:

- A date table marked as a date table, one row per day, contiguous, covering
  every year in the fact table. `DATEADD` needs contiguous dates.
- The fact table related to it on the date key.
- A column that is unique per period, used for rule 1:

| Period | Grain column (add if missing) | Example values |
|---|---|---|
| Month | `'Date'[Year Month]` (e.g. `Year * 100 + Month`, or text "2025-08") | 202508 |
| Quarter | `'Date'[Year Quarter]` (e.g. `Year * 10 + Quarter`) | 20253 |
| Year | `'Date'[Year]` | 2025 |

If the model only has separate `Year` and `Month` columns, rule 1 for MoM
becomes `HASONEVALUE ( 'Date'[Year] ) && HASONEVALUE ( 'Date'[Month] )`.
Selecting only a month (January of every year) or only a year then shows `--`,
which is the intended behaviour.

`HASONEVALUE` is used rather than `ISFILTERED` so the measure also works when
the period comes from a matrix row or a chart axis, not only from a slicer.

## Measures

Replace `[Sales]`, `'Date'[Date]` and the grain columns with the model's names.

```dax
Sales MoM % =
IF (
    HASONEVALUE ( 'Date'[Year Month] ),                       -- rule 1
    VAR _Current = [Sales]
    VAR _Prior =
        CALCULATE ( [Sales], DATEADD ( 'Date'[Date], -1, MONTH ) )
    RETURN
        IF (
            NOT ISBLANK ( _Current ) && NOT ISBLANK ( _Prior ) && _Prior <> 0,   -- rule 2
            DIVIDE ( _Current - _Prior, ABS ( _Prior ) )
        )
)
```

```dax
Sales QoQ % =
IF (
    HASONEVALUE ( 'Date'[Year Quarter] ),
    VAR _Current = [Sales]
    VAR _Prior =
        CALCULATE ( [Sales], DATEADD ( 'Date'[Date], -1, QUARTER ) )
    RETURN
        IF (
            NOT ISBLANK ( _Current ) && NOT ISBLANK ( _Prior ) && _Prior <> 0,
            DIVIDE ( _Current - _Prior, ABS ( _Prior ) )
        )
)
```

```dax
Sales YoY % =
IF (
    HASONEVALUE ( 'Date'[Year] ),
    VAR _Current = [Sales]
    VAR _Prior =
        CALCULATE ( [Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
    RETURN
        IF (
            NOT ISBLANK ( _Current ) && NOT ISBLANK ( _Prior ) && _Prior <> 0,
            DIVIDE ( _Current - _Prior, ABS ( _Prior ) )
        )
)
```

Notes:
- `ABS ( _Prior )` keeps the sign meaningful when the base can be negative (profit).
- YoY with a single month selected compares that month with the same month last
  year; with a full year it compares years. QoQ shifts whatever is selected
  inside one quarter by three months.
- Format string for the numeric measures: `+0.0%;-0.0%;0.0%`.
- For "lower is better" metrics (cost, days, defects) keep the maths as is and
  set `_HigherIsBetter = FALSE ()` in the style measure; only the colours flip.

## Prior-period label measures

The `*-period` styles name the period being compared against ("vs Aug 2025").
The text always comes from the selected period, never typed in, and is blank
under rule 1, so the indicator collapses to `--`. Other styles use generic
labels (`vs last month`) or short tags (`vs PM`, `vs PQ`, `vs PY`).

```dax
MoM Prior Label =
IF (
    HASONEVALUE ( 'Date'[Year Month] ),
    FORMAT ( EOMONTH ( MAX ( 'Date'[Date] ), -1 ), "mmm yyyy" )        -- Aug 2025
)
```

```dax
QoQ Prior Label =
IF (
    HASONEVALUE ( 'Date'[Year Quarter] ),
    VAR _d = EOMONTH ( MAX ( 'Date'[Date] ), -3 )
    RETURN "Q" & QUARTER ( _d ) & " " & YEAR ( _d )                     -- Q2 2025
)
```

```dax
YoY Prior Label =
IF (
    HASONEVALUE ( 'Date'[Year] ),
    IF (
        HASONEVALUE ( 'Date'[Year Month] ),
        FORMAT ( EOMONTH ( MAX ( 'Date'[Date] ), -12 ), "mmm yyyy" ),  -- Sep 2024
        FORMAT ( MAX ( 'Date'[Year] ) - 1, "0" )                        -- 2024
    )
)
```

In a `*-period` style measure, `_Label` already reads
`IF ( NOT ISBLANK ( _Pct ), "vs " & [MoM Prior Label] )`; swap in the QoQ or
YoY label measure for those periods. FORMAT uses the model's culture, so month
names follow the report language.

## Test matrix

Check each case in a table visual (rows = Year Month) and in a card with slicers:

| Case | Expected |
|---|---|
| No slicer selection | `--` |
| Year only selected (MoM) | `--` |
| Month only selected, no year (MoM) | `--` |
| First month in the date table | `--` |
| Month whose prior month has no fact rows | `--` |
| Normal month, growth | `+x.x%`, up, good colour |
| Normal month, decline | `-x.x%`, down, bad colour |
| Change rounds to zero | `0.0%`, flat, neutral colour |
