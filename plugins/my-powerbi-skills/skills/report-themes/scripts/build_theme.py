#!/usr/bin/env python3
"""Power BI report themes from design tokens.

One token set (palette, surfaces, card style, fonts) becomes:
  * a complete custom theme JSON (keeps the safeguards of upstream's base.json),
  * a preview SVG of a small dashboard in that theme,
  * PBIR snippets for the formatting a theme cannot cascade.

Usage
  python3 build_theme.py --list
  python3 build_theme.py --preset lavender-soft --out MyTheme.json
  python3 build_theme.py --palette "Financial Dashboard" --card soft --out Fin.json
  python3 build_theme.py --tokens brand.json --out Brand.json
  python3 build_theme.py --preset lavender-soft --snippets
  python3 build_theme.py --build-assets      # regenerate assets/ and the catalog

Options --card, --radius, --font-heading, --font-body and --mode override any
source. Every build runs the contrast checks and exits 1 if a text pair fails.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCHEMA_URL = ("https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/"
              "Report%20Theme%20JSON%20Schema/reportThemeSchema-2.153.json")
PALETTES_CSV = SKILL / "references" / "uiux-palettes.csv"

# Fonts the Power BI service renders for every viewer. Anything else needs a
# fallback chain and only shows where the font is installed.
SAFE_FONTS = {
    "Segoe UI", "Segoe UI Semibold", "Segoe UI Bold", "Segoe UI Light", "DIN",
    "Arial", "Arial Black", "Calibri", "Cambria", "Candara", "Consolas",
    "Constantia", "Corbel", "Courier New", "Georgia", "Lucida Sans Unicode",
    "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana",
}

CARD_STYLES = ("soft", "outlined", "elevated", "flat")

# --------------------------------------------------------------------------
# Presets. Keys:
#   mode        light | dark
#   card        soft (tinted fill, no border) | outlined (1px border)
#               | elevated (shadow) | flat (square, no border)
#   radius      visual corner radius, px
#   heading/body  Power BI font names (keep to SAFE_FONTS)
#   page        canvas colour      outspace  wallpaper around the canvas
#   surface     visual background  tile      fill of KPI tiles inside a card
#   border      visual border (None = no border)
#   text        primary text       muted     labels, axes, captions
#   grid        gridlines, table rules       header  table header fill
#   data        8 series colours, in order
#   good / bad / neutral   sentiment
# --------------------------------------------------------------------------
PRESETS = {
    "lavender-soft": dict(
        label="Lavender soft",
        blurb="Deep purple with lavender tiles on a white canvas; rounded, borderless, airy. HR and people dashboards.",
        mode="light", card="soft", radius=14,
        heading="Segoe UI Semibold", body="Segoe UI",
        page="#FFFFFF", outspace="#F4F0FB", surface="#F7F3FD", tile="#F7F3FD", border=None,
        text="#1F1A2E", muted="#6B5F8A", grid="#E6DEF5", header="#FFFFFF",
        data=["#5B2C83", "#A88BDB", "#7E57C2", "#C7B5EC", "#3B1A5A", "#D58BC0", "#8E7CB8", "#E3D8F6"],
        good="#1E8E54", bad="#C93B53", neutral="#B7791F",
    ),
    "ocean-calm": dict(
        label="Ocean calm",
        blurb="Confident blue on pale blue tiles; the safe default for finance, sales and ops reports.",
        mode="light", card="soft", radius=12,
        heading="Segoe UI Semibold", body="Segoe UI",
        page="#FFFFFF", outspace="#EEF4FB", surface="#F3F7FD", tile="#F3F7FD", border=None,
        text="#13233A", muted="#4E6280", grid="#DCE6F3", header="#FFFFFF",
        data=["#1D4ED8", "#60A5FA", "#0E7490", "#93C5FD", "#1E3A8A", "#F59E0B", "#64748B", "#BFDBFE"],
        good="#15803D", bad="#C2410C", neutral="#A16207",
    ),
    "mint-fresh": dict(
        label="Mint fresh",
        blurb="Teal and mint with soft green tiles; health, sustainability, operations.",
        mode="light", card="soft", radius=12,
        heading="Segoe UI Semibold", body="Segoe UI",
        page="#FFFFFF", outspace="#ECF7F4", surface="#F1F9F7", tile="#F1F9F7", border=None,
        text="#10302B", muted="#466A63", grid="#D5EBE5", header="#FFFFFF",
        data=["#0F766E", "#5EC4B6", "#155E75", "#A7E3D9", "#134E4A", "#F2994A", "#6B8F88", "#CDEFE8"],
        good="#15803D", bad="#C2410C", neutral="#A16207",
    ),
    "sunset-warm": dict(
        label="Sunset warm",
        blurb="Coral and amber on a warm off-white canvas with lifted white cards; retail, hospitality, marketing.",
        mode="light", card="elevated", radius=12,
        heading="Segoe UI Semibold", body="Segoe UI",
        page="#FFF8F3", outspace="#FBEDE3", surface="#FFFFFF", tile="#FFF3EA", border=None,
        text="#2B1B12", muted="#6E5446", grid="#F2E2D6", header="#FFF3EA",
        data=["#D9480F", "#F59F00", "#C2255C", "#FFC078", "#862E9C", "#5C940D", "#A07862", "#FFD8A8"],
        good="#2B8A3E", bad="#C92A2A", neutral="#A86B00",
    ),
    "slate-corporate": dict(
        label="Slate corporate",
        blurb="Navy and steel on a grey canvas with crisp outlined white cards; board and finance packs.",
        mode="light", card="outlined", radius=6,
        heading="Segoe UI Semibold", body="Segoe UI",
        page="#F3F5F8", outspace="#E6EAF0", surface="#FFFFFF", tile="#F6F8FB", border="#D9DFE7",
        text="#1B2533", muted="#516074", grid="#E6EAF0", header="#EEF2F6",
        data=["#1E3A5F", "#4F7CAC", "#C8963E", "#9DB4CF", "#2E5E4E", "#B5523B", "#7A8798", "#D6E0EB"],
        good="#2F7D4F", bad="#B23B3B", neutral="#9A6B12",
    ),
    "midnight-dark": dict(
        label="Midnight dark",
        blurb="Dark navy canvas, violet and cyan series, soft raised tiles; wallboards and night-mode reports.",
        mode="dark", card="soft", radius=14,
        heading="Segoe UI Semibold", body="Segoe UI",
        page="#0E1222", outspace="#080B16", surface="#181D33", tile="#20263F", border=None,
        text="#ECEEF8", muted="#A5ACC8", grid="#2A3150", header="#20263F",
        data=["#8B7CF6", "#22D3EE", "#F472B6", "#FBBF24", "#34D399", "#60A5FA", "#C4B5FD", "#94A3B8"],
        good="#34D399", bad="#F87171", neutral="#FBBF24",
    ),
    "rose-soft": dict(
        label="Rose soft",
        blurb="Raspberry and blush tiles on white; beauty, wellness, community and customer reports.",
        mode="light", card="soft", radius=16,
        heading="Segoe UI Semibold", body="Segoe UI",
        page="#FFFFFF", outspace="#FBF0F4", surface="#FDF4F7", tile="#FDF4F7", border=None,
        text="#2A1420", muted="#7A4D62", grid="#F3DCE6", header="#FFFFFF",
        data=["#BE185D", "#F49AC1", "#7C3AED", "#F9C6DA", "#831843", "#0EA5A4", "#A07088", "#FCE1EC"],
        good="#15803D", bad="#B91C1C", neutral="#A16207",
    ),
    "mono-minimal": dict(
        label="Mono minimal",
        blurb="Swiss-style black, greys and one blue accent; square corners, no chrome, maximum data-ink.",
        mode="light", card="flat", radius=0,
        heading="Segoe UI Bold", body="Segoe UI",
        page="#FFFFFF", outspace="#F2F2F2", surface="#FFFFFF", tile="#F5F5F5", border=None,
        text="#111111", muted="#555555", grid="#E5E5E5", header="#F5F5F5",
        data=["#111111", "#2563EB", "#7A7A7A", "#B8B8B8", "#1E40AF", "#D4D4D4", "#4B4B4B", "#93C5FD"],
        good="#15803D", bad="#B91C1C", neutral="#8A6D00",
    ),
    "sand-editorial": dict(
        label="Sand editorial",
        blurb="Serif headings, warm sand canvas, ink and terracotta series; narrative and board-story pages.",
        mode="light", card="outlined", radius=4,
        heading="Georgia", body="Segoe UI",
        page="#F7F3EC", outspace="#EDE6DA", surface="#FFFDF9", tile="#F7F1E7", border="#E3D9C8",
        text="#26211B", muted="#5F564A", grid="#ECE4D6", header="#F3ECE0",
        data=["#2F3E46", "#B5653B", "#7C8C5A", "#D9A877", "#5B4B8A", "#8FA9B5", "#9A8C78", "#E8D5BC"],
        good="#3F7D3A", bad="#A8322D", neutral="#9A6B12",
    ),
}
DEFAULT_PRESET = "ocean-calm"


# ------------------------------------------------------------------ colour
def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def mix(a, b, t):
    """t=0 gives a, t=1 gives b."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def luminance(h):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ------------------------------------------------------------------ tokens
def tokens_from_palette(product):
    """Turn a ui-ux-pro-max palette row (references/uiux-palettes.csv) into tokens."""
    rows = list(csv.DictReader(PALETTES_CSV.open(encoding="utf-8")))
    hit = [r for r in rows if r["Product Type"].lower() == product.lower()]
    if not hit:
        hit = [r for r in rows if product.lower() in r["Product Type"].lower()]
    if not hit:
        sys.exit(f"No palette matches '{product}'. Try --list-palettes.")
    r = hit[0]
    p, s, a = r["Primary"], r["Secondary"], r["Accent"]
    bg, fg = r["Background"], r["Foreground"]
    dark = luminance(bg) < 0.2
    white = "#FFFFFF"
    return dict(
        label=r["Product Type"], blurb=f"From the ui-ux-pro-max palette '{r['Product Type']}'. {r['Notes']}",
        mode="dark" if dark else "light", card="soft", radius=12,
        heading="Segoe UI Semibold", body="Segoe UI",
        page=white if not dark else bg, outspace=bg if not dark else mix(bg, "#000000", 0.3),
        surface=mix(p, white, 0.95) if not dark else r["Card"], tile=mix(p, white, 0.95) if not dark else mix(r["Card"], white, 0.06),
        border=None, text=fg, muted=r["Muted Foreground"], grid=r["Border"], header=r["Muted"],
        data=[p, s, a, mix(p, "#000000", 0.35), mix(p, white, 0.45), mix(a, white, 0.4), r["Muted Foreground"], mix(s, white, 0.6)],
        good="#15803D" if not dark else "#34D399", bad=r["Destructive"], neutral="#A16207" if not dark else "#FBBF24",
    )


REQUIRED = ("mode", "card", "radius", "heading", "body", "page", "outspace", "surface", "tile",
            "border", "text", "muted", "grid", "header", "data", "good", "bad", "neutral")


def normalise(t):
    t = dict(t)
    t.setdefault("label", "Custom")
    t.setdefault("blurb", "")
    t.setdefault("tile", t.get("surface"))
    t.setdefault("header", t.get("surface"))
    t.setdefault("border", None)
    missing = [k for k in REQUIRED if k not in t]
    if missing:
        sys.exit(f"Tokens missing: {', '.join(missing)}")
    if t["card"] not in CARD_STYLES:
        sys.exit(f"card must be one of {CARD_STYLES}")
    if t["card"] == "outlined" and not t["border"]:
        t["border"] = t["grid"]
    if t["card"] == "flat":
        t["radius"] = 0
    if len(t["data"]) < 2:
        sys.exit("data needs at least 2 colours")
    return t


def check(t):
    """WCAG checks. Text pairs must reach 4.5:1; series and sentiment colours 3:1 (graphics)."""
    rows = []
    for name, fg, bg, need in [
        ("text on visual", t["text"], t["surface"], 4.5),
        ("text on canvas", t["text"], t["page"], 4.5),
        ("muted labels on visual", t["muted"], t["surface"], 4.5),
        ("muted labels on KPI tile", t["muted"], t["tile"], 4.5),
        ("table header text", t["muted"], t["header"], 4.5),
        ("good on tile", t["good"], t["tile"], 3.0),
        ("bad on tile", t["bad"], t["tile"], 3.0),
        ("series 1 on visual", t["data"][0], t["surface"], 3.0),
        ("series 2 on visual", t["data"][1], t["surface"], 3.0),
    ]:
        r = contrast(fg, bg)
        hard = need == 4.5
        rows.append((name, fg, bg, r, need, "pass" if r >= need else ("FAIL" if hard else "warn")))
    for f in (t["heading"], t["body"]):
        if f not in SAFE_FONTS:
            rows.append((f"font '{f}'", "", "", 0, 0, "warn"))
    return rows


def print_checks(rows, out=sys.stderr):
    for name, fg, bg, r, need, status in rows:
        if fg:
            print(f"  {status:4}  {name:26} {fg} on {bg}  {r:4.1f}:1 (need {need}:1)", file=out)
        else:
            print(f"  {status:4}  {name}: not a Power BI service font; it falls back to Segoe UI for viewers without it", file=out)
    return not any(r[5] == "FAIL" for r in rows)


# ------------------------------------------------------------------ theme
def solid(c):
    return {"solid": {"color": c}}


def font_chain(f):
    return f if f in SAFE_FONTS else f"{f}, Segoe UI, sans-serif"


def build_theme(t, name):
    hf, bf = font_chain(t["heading"]), font_chain(t["body"])
    dark = t["mode"] == "dark"
    border = t["border"]
    shadow = t["card"] == "elevated"
    radius = t["radius"]
    good_tint = mix(t["good"], t["tile"], 0.85)
    axis = {"show": True, "fontSize": 10, "fontFamily": bf, "labelColor": solid(t["muted"]),
            "showAxisTitle": False, "gridlineShow": False}
    val_axis = {"show": False, "gridlineShow": False, "showAxisTitle": False}
    bar_defaults = {
        "labels": [{"show": True, "fontSize": 9, "fontFamily": bf, "color": solid(t["text"])}],
        "valueAxis": [val_axis],
        "categoryAxis": [dict(axis, innerPadding=20)],
        "dataPoint": [{"borderShow": False}],
        "legend": [{"show": False}],
    }
    multi_bar = dict(bar_defaults, legend=[{"show": True, "position": "Top", "fontSize": 9, "fontFamily": bf,
                                            "labelColor": solid(t["muted"])}],
                     valueAxis=[{"show": True, "fontSize": 9, "labelColor": solid(t["muted"]), "showAxisTitle": False,
                                 "gridlineShow": True, "gridlineStyle": "dotted", "gridlineColor": solid(t["grid"])}],
                     labels=[{"show": False}])
    slicer_text = {
        "header": [{"fontFamily": t["heading"] if t["heading"] in SAFE_FONTS else "Segoe UI Semibold", "textSize": 10,
                    "fontColor": solid(t["text"]), "background": solid(t["surface"]), "outlineStyle": 0}],
        "items": [{"fontFamily": bf, "textSize": 10, "fontColor": solid(t["text"]),
                   "background": solid(t["surface"]), "outlineStyle": 0, "padding": 4}],
    }
    table = {
        "*": {
            "columnHeaders": [{"autoSizeColumnWidth": True, "columnAdjustment": "growToFit",
                               "backColor": solid(t["header"]), "fontColor": solid(t["muted"]),
                               "fontFamily": bf, "fontSize": 10, "bold": False, "outlineStyle": 0}],
            "values": [{"backColorPrimary": solid(t["surface"]),
                        "backColorSecondary": solid(t["surface"] if t["card"] == "soft" else t["tile"]),
                        "fontColorPrimary": solid(t["text"]), "fontColorSecondary": solid(t["text"]),
                        "fontFamily": bf, "fontSize": 10, "outlineStyle": 0}],
            "grid": [{"gridVertical": False, "gridHorizontal": True, "gridHorizontalColor": solid(t["grid"]),
                      "gridHorizontalWeight": 1, "outlineColor": solid(t["grid"]), "rowPadding": 6}],
            "total": [{"backColor": solid(t["header"]), "fontColor": solid(t["text"]), "bold": True}],
        }
    }
    matrix = json.loads(json.dumps(table))
    matrix["*"]["rowHeaders"] = [{"backColor": solid(t["surface"]), "fontColor": solid(t["text"]), "fontFamily": bf, "fontSize": 10}]
    matrix["*"]["subTotals"] = [{"backColor": solid(t["header"]), "fontColor": solid(t["text"])}]
    matrix["*"]["grandTotal"] = [{"backColor": solid(t["header"]), "fontColor": solid(t["text"])}]
    del matrix["*"]["total"]

    container = {
        "background": [{"show": True, "color": solid(t["surface"]), "transparency": 0}],
        "border": [{"show": bool(border), "color": solid(border or t["surface"]), "radius": radius, "width": 1}],
        "dropShadow": [{"show": shadow, "color": solid("#000000" if not dark else "#000000"), "position": "Outer",
                        "preset": "Custom", "angle": 90, "shadowDistance": 2, "shadowBlur": 10, "shadowSpread": 0,
                        "transparency": 88}],
        "padding": [{"top": 12, "bottom": 12, "left": 14, "right": 14}],
        "title": [{"show": True, "fontFamily": hf, "fontSize": 12, "bold": False, "fontColor": solid(t["text"]),
                   "alignment": "left"}],
        "subTitle": [{"fontFamily": bf, "fontSize": 9, "fontColor": solid(t["muted"])}],
        "visualTooltip": [{"background": solid(t["surface"] if dark else "#FFFFFF"),
                           "titleFontColor": solid(t["muted"]), "valueFontColor": solid(t["text"]),
                           "fontFamily": bf, "fontSize": 10}],
        "visualHeader": [{"background": solid(t["surface"]), "foreground": solid(t["muted"]),
                          "border": solid(t["surface"]), "transparency": 0}],
        "categoryAxis": [{"gridlineStyle": "dotted", "gridlineColor": solid(t["grid"])}],
        "valueAxis": [{"gridlineStyle": "dotted", "gridlineColor": solid(t["grid"])}],
        "outspacePane": [{"backgroundColor": solid(t["surface"]), "foregroundColor": solid(t["text"]),
                          "borderColor": solid(t["grid"]), "border": True,
                          "checkboxAndApplyColor": solid(t["data"][0]), "inputBoxColor": solid(t["page"]),
                          "fontFamily": bf, "titleSize": 12}],
        "filterCard": [
            {"$id": "Applied", "backgroundColor": solid(t["tile"]), "foregroundColor": solid(t["text"]),
             "borderColor": solid(t["grid"]), "border": True, "inputBoxColor": solid(t["page"]), "fontFamily": bf},
            {"$id": "Available", "backgroundColor": solid(t["surface"]), "foregroundColor": solid(t["text"]),
             "borderColor": solid(t["grid"]), "border": True, "inputBoxColor": solid(t["page"]), "fontFamily": bf},
        ],
    }
    theme = {
        "$schema": SCHEMA_URL,
        "name": name,
        "dataColors": t["data"],
        "good": t["good"], "neutral": t["neutral"], "bad": t["bad"],
        "maximum": t["data"][0], "center": mix(t["data"][0], t["surface"], 0.5),
        "minimum": mix(t["data"][0], t["surface"], 0.88), "null": t["muted"],
        "firstLevelElements": t["text"],
        "secondLevelElements": t["muted"],
        "thirdLevelElements": t["grid"],
        "fourthLevelElements": t["muted"],
        "background": t["surface"],
        "secondaryBackground": t["tile"],
        "tableAccent": t["data"][0],
        "hyperlink": t["data"][0] if contrast(t["data"][0], t["surface"]) >= 4.5 else t["text"],
        "textClasses": {
            "callout": {"fontSize": 26, "fontFace": hf, "color": t["text"]},
            "title": {"fontSize": 12, "fontFace": hf, "color": t["text"]},
            "largeTitle": {"fontSize": 14, "fontFace": hf, "color": t["text"]},
            "header": {"fontSize": 12, "fontFace": hf, "color": t["text"]},
            "label": {"fontSize": 10, "fontFace": bf, "color": t["text"]},
        },
        "visualStyles": {
            "*": {"*": container},
            "page": {"*": {
                "background": [{"color": solid(t["page"]), "transparency": 0}],
                "outspace": [{"color": solid(t["outspace"]), "transparency": 0}],
            }},
            "textbox": {"*": {
                "padding": [{"top": 0, "bottom": 0, "left": 0, "right": 0}],
                "background": [{"show": False}],
                "border": [{"show": False}],
                "dropShadow": [{"show": False}],
            }},
            "cardVisual": {"*": {
                "value": [{"$id": "default", "bold": True, "fontFamily": hf, "fontSize": 24,
                           "fontColor": solid(t["text"])}],
                "label": [{"$id": "default", "show": True, "fontFamily": bf, "fontSize": 10,
                           "fontColor": solid(t["muted"])}],
                "cardCalloutArea": [{"paddingUniform": 12, "rectangleRoundedCurve": max(radius - 4, 0),
                                     "backgroundFillColor": solid(t["tile"]),
                                     "backgroundTransparency": 0 if t["card"] != "soft" else 0}],
                "fillCustom": [{"$id": "default", "show": True, "fillColor": solid(t["tile"]), "transparency": 0}],
                "outline": [{"$id": "default", "show": False}],
                "referenceLabelValue": [{"$id": "default", "valueFontColor": solid(t["good"]),
                                         "valueFontFamily": bf, "valueFontSize": 9}],
                "referenceLabel": [{"backgroundColor": solid(good_tint), "backgroundShow": True,
                                    "rectangleRoundedCurve": 6, "paddingUniform": 2}],
                "border": [{"show": bool(border), "color": solid(border or t["surface"]), "radius": radius}],
                "title": [{"show": False}],
                "spacing": [{"$id": "default", "customizeSpacing": True, "verticalSpacing": 2}],
                "padding": [{"top": 0, "bottom": 0, "left": 0, "right": 0}],
            }},
            "tableEx": table,
            "pivotTable": matrix,
            "barChart": {"*": bar_defaults},
            "columnChart": {"*": bar_defaults},
            "clusteredBarChart": {"*": multi_bar},
            "clusteredColumnChart": {"*": multi_bar},
            "lineChart": {"*": {
                "lineStyles": [{"strokeWidth": 2.5, "lineChartType": "smooth", "areaShow": True,
                                "areaMatchStrokeColor": True}],
                "labels": [{"show": False}],
                "categoryAxis": [axis],
                "valueAxis": [{"show": True, "fontSize": 9, "labelColor": solid(t["muted"]), "showAxisTitle": False,
                               "gridlineStyle": "dotted", "gridlineColor": solid(t["grid"])}],
                "legend": [{"show": True, "position": "Top", "fontSize": 9, "labelColor": solid(t["muted"])}],
            }},
            "donutChart": {"*": {
                "slices": [{"innerRadiusRatio": 72}],
                "dataPoint": [{"borderShow": True, "borderColor": solid(t["surface"]), "borderSize": 3}],
                "labels": [{"show": False}],
                "legend": [{"show": True, "position": "Bottom", "fontSize": 9, "labelColor": solid(t["muted"])}],
            }},
            "pieChart": {"*": {
                "dataPoint": [{"borderShow": True, "borderColor": solid(t["surface"]), "borderSize": 2}],
                "legend": [{"show": True, "position": "Bottom", "fontSize": 9, "labelColor": solid(t["muted"])}],
            }},
            "slicer": {"*": slicer_text},
            "listSlicer": {"*": {"padding": [{"top": 8, "bottom": 8, "left": 10, "right": 10}]}},
            "textSlicer": {"*": {"padding": [{"top": 8, "bottom": 8, "left": 10, "right": 10}]}},
            "advancedSlicerVisual": {"*": {
                "fillCustom": [{"show": True, "fillColor": solid(t["tile"]), "transparency": 0}],
                "label": [{"$id": "default", "fontFamily": bf, "fontSize": 10, "fontColor": solid(t["text"])}],
            }},
            "shape": {"*": {"dropShadow": [{"show": False}]}},
            "image": {"*": {"background": [{"show": False}], "border": [{"show": False}],
                            "dropShadow": [{"show": False}]}},
        },
    }
    return theme


# ------------------------------------------------------------------ PBIR snippets
def lit_color(c):
    return {"solid": {"color": {"expr": {"Literal": {"Value": f"'{c}'"}}}}}


def lit(v):
    if isinstance(v, bool):
        return {"expr": {"Literal": {"Value": "true" if v else "false"}}}
    if isinstance(v, int):
        return {"expr": {"Literal": {"Value": f"{v}D"}}}
    return {"expr": {"Literal": {"Value": f"'{v}'"}}}


def snippets(t):
    """Formatting that does not cascade from the theme, as PBIR objects with this theme's colours."""
    pill_good = mix(t["good"], t["tile"], 0.85)
    pill_bad = mix(t["bad"], t["tile"], 0.85)
    return {
        "page.json objects (every page)": {
            "background": [{"properties": {"color": lit_color(t["page"]), "transparency": lit(0)}}],
            "outspace": [{"properties": {"color": lit_color(t["outspace"]), "transparency": lit(0)}}],
        },
        "cardVisual objects (each card)": {
            "fillCustom": [{"properties": {"show": lit(True), "fillColor": lit_color(t["tile"]), "transparency": lit(0)},
                            "selector": {"id": "default"}}],
            "value": [{"properties": {"fontColor": lit_color(t["text"])}, "selector": {"id": "default"}}],
            "label": [{"properties": {"fontColor": lit_color(t["muted"])}, "selector": {"id": "default"}}],
            "outline": [{"properties": {"show": lit(False)}, "selector": {"id": "default"}}],
        },
        "cardVisual accent bar (optional)": {
            "accentBar": [{"properties": {"show": lit(True), "position": lit("Left"), "width": lit(4),
                                          "color": lit_color(t["data"][0])}, "selector": {"id": "default"}}],
        },
        "slicer objects (dropdown list colours)": {
            "items": [{"properties": {"background": lit_color(t["surface"]), "fontColor": lit_color(t["text"])}}],
            "header": [{"properties": {"background": lit_color(t["surface"]), "fontColor": lit_color(t["text"])}}],
        },
        "tableEx / pivotTable objects (keep theme colours)": {
            "stylePreset": [{"properties": {"name": lit("None")}}],
        },
        "variance pill colours (for variance-indicators)": {
            "good": {"text": t["good"], "background": pill_good},
            "bad": {"text": t["bad"], "background": pill_bad},
        },
    }


# ------------------------------------------------------------------ preview
CSS_FONTS = {
    "Segoe UI": "'Segoe UI', Inter, sans-serif",
    "Segoe UI Semibold": "'Segoe UI Semibold', 'Segoe UI', Inter, sans-serif",
    "Segoe UI Bold": "'Segoe UI', Inter, sans-serif",
    "Georgia": "Georgia, 'DejaVu Serif', serif",
}


def css_font(f):
    return CSS_FONTS.get(f, f"'{f}', Inter, sans-serif")


def heading_weight(f):
    return 700 if "Bold" in f else (600 if "Semibold" in f else 600)


def preview_svg(t, title):
    W, H = 640, 412
    hf, bf = css_font(t["heading"]), css_font(t["body"])
    hw = heading_weight(t["heading"])
    r = t["radius"]
    br = t["border"]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    out.append('<defs><filter id="sh" x="-10%" y="-10%" width="120%" height="130%">'
               '<feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000" flood-opacity="0.10"/></filter></defs>')
    out.append(f'<rect width="{W}" height="{H}" fill="{t["outspace"]}"/>')
    out.append(f'<rect x="8" y="8" width="{W - 16}" height="{H - 16}" rx="10" fill="{t["page"]}"/>')

    def card(x, y, w, h):
        stroke = f' stroke="{br}" stroke-width="1"' if br else ""
        flt = ' filter="url(#sh)"' if t["card"] == "elevated" else ""
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{t["surface"]}"{stroke}{flt}/>')

    def text(x, y, s, size, color, weight=400, font=None, anchor="start"):
        out.append(f'<text x="{x}" y="{y}" font-family="{font or bf}" font-size="{size}" font-weight="{weight}" '
                   f'fill="{color}" text-anchor="{anchor}">{s}</text>')

    text(24, 40, "Workforce overview", 18, t["text"], hw, hf)
    text(24, 57, "Headcount and hiring, last 5 months", 10, t["muted"])

    # KPI tiles: one multi-value card, four rounded tiles
    card(24, 70, 236, 162)
    kpis = [("4,510", "Total employees", "+25.5%", True), ("1,450", "Job applicants", "-12.5%", False),
            ("312", "New members", "-15.5%", False), ("96", "Resigned", "+2.5%", True)]
    for i, (v, lab, pct, up) in enumerate(kpis):
        x = 32 + (i % 2) * 114
        y = 78 + (i // 2) * 74
        out.append(f'<rect x="{x}" y="{y}" width="106" height="66" rx="{max(r - 4, 0)}" fill="{t["tile"]}"/>')
        col = t["good"] if up else t["bad"]
        out.append(f'<rect x="{x + 58}" y="{y + 8}" width="42" height="15" rx="7.5" fill="{mix(col, t["tile"], 0.85)}"/>')
        text(x + 79, y + 19, pct, 8.5, col, 600, anchor="middle")
        text(x + 9, y + 44, v, 17, t["text"], 700, hf)
        text(x + 9, y + 58, lab, 8.5, t["muted"])

    # Clustered column chart
    cx, cy, cw, ch = 268, 70, 348, 162
    card(cx, cy, cw, ch)
    text(cx + 14, cy + 22, "Team performance", 12, t["text"], hw, hf)
    for j, lab in enumerate(("Project team", "Product team")):
        lx = cx + 14 + j * 86
        out.append(f'<circle cx="{lx + 4}" cy="{cy + 37}" r="3.5" fill="{t["data"][j]}"/>')
        text(lx + 12, cy + 40, lab, 8.5, t["muted"])
    base = cy + ch - 24
    for k in range(4):
        gy = base - k * 24
        out.append(f'<line x1="{cx + 30}" y1="{gy}" x2="{cx + cw - 12}" y2="{gy}" stroke="{t["grid"]}" stroke-dasharray="2 3"/>')
        text(cx + 24, gy + 3, f"{k * 20}K", 7.5, t["muted"], anchor="end")
    vals = [(52, 92), (64, 96), (22, 64), (92, 74), (90, 72)]
    months = ["Jan", "Feb", "Mar", "Apr", "May"]
    for m, (a, b) in enumerate(vals):
        gx = cx + 44 + m * 60
        for s, v in enumerate((a, b)):
            hh = v * 0.8
            out.append(f'<rect x="{gx + s * 14}" y="{base - hh}" width="10" height="{hh}" rx="{min(3, r / 3):.1f}" fill="{t["data"][s]}"/>')
        text(gx + 12, base + 14, months[m], 8, t["muted"], anchor="middle")

    # Table
    tx, ty, tw, th = 24, 240, 380, 128
    card(tx, ty, tw, th)
    text(tx + 14, ty + 22, "Employees", 12, t["text"], hw, hf)
    out.append(f'<rect x="{tx + 10}" y="{ty + 32}" width="{tw - 20}" height="20" rx="{min(r, 6)}" fill="{t["header"]}"/>')
    cols = [0, 110, 200, 290]
    for c, h in zip(cols, ("Name", "Job title", "Department", "Office")):
        text(tx + 18 + c, ty + 46, h, 8.5, t["muted"])
    rows = [("Brenda Branam", "Web dev", "Product", "5 days"), ("Mark Lopez", "UI designer", "Project", "20 days"),
            ("Doris Bartlett", "Web dev", "Product", "15 days")]
    for i, row in enumerate(rows):
        y = ty + 70 + i * 20
        for c, v in zip(cols, row):
            text(tx + 18 + c, y, v, 9, t["text"])
        if i < 2:
            out.append(f'<line x1="{tx + 14}" y1="{y + 7}" x2="{tx + tw - 14}" y2="{y + 7}" stroke="{t["grid"]}"/>')

    # Donut
    dx, dy, dw, dh = 412, 240, 204, 128
    card(dx, dy, dw, dh)
    text(dx + 14, dy + 22, "Total employees", 12, t["text"], hw, hf)
    import math
    ccx, ccy, rr = dx + 62, dy + 76, 36
    shares = [0.5, 0.3, 0.2]
    start = -math.pi / 2
    for i, s in enumerate(shares):
        end = start + s * 2 * math.pi
        x1, y1 = ccx + rr * math.cos(start), ccy + rr * math.sin(start)
        x2, y2 = ccx + rr * math.cos(end), ccy + rr * math.sin(end)
        large = 1 if s > 0.5 else 0
        out.append(f'<path d="M{x1:.1f},{y1:.1f} A{rr},{rr} 0 {large} 1 {x2:.1f},{y2:.1f}" fill="none" '
                   f'stroke="{t["data"][i]}" stroke-width="11"/>')
        out.append(f'<path d="M{x2:.1f},{y2:.1f} L{ccx + (rr + 7) * math.cos(end):.1f},{ccy + (rr + 7) * math.sin(end):.1f}" '
                   f'stroke="{t["surface"]}" stroke-width="2.5"/>')
        start = end
    text(ccx, ccy + 3, "145", 15, t["text"], 700, hf, "middle")
    text(ccx, ccy + 15, "Total", 7.5, t["muted"], anchor="middle")
    for i, lab in enumerate(("Developers", "Designers", "Marketing")):
        ly = dy + 58 + i * 17
        out.append(f'<circle cx="{dx + 122}" cy="{ly - 3}" r="3.5" fill="{t["data"][i]}"/>')
        text(dx + 130, ly, lab, 8.5, t["muted"])

    # Palette strip
    py = H - 34
    text(24, py + 13, f"{title}", 10, t["text"], 600, bf)
    for i, c in enumerate(t["data"][:8]):
        out.append(f'<rect x="{196 + i * 26}" y="{py}" width="20" height="18" rx="4" fill="{c}" stroke="{t["grid"]}"/>')
    font_note = t["heading"] if t["heading"] == t["body"] else f'{t["heading"]} / {t["body"]}'
    text(W - 24, py + 13, f'{t["card"]} cards · r{t["radius"]} · {font_note}', 8.5, t["muted"], anchor="end")
    out.append("</svg>")
    return "\n".join(out)


# ------------------------------------------------------------------ assets
def theme_name(preset):
    return "".join(p.capitalize() for p in preset.split("-")) + ".json"


def build_assets():
    themes = SKILL / "assets" / "themes"
    previews = SKILL / "assets" / "previews"
    themes.mkdir(parents=True, exist_ok=True)
    previews.mkdir(parents=True, exist_ok=True)
    ok = True
    catalog = [
        "# Theme preset catalog",
        "",
        "<!-- Generated by scripts/build_theme.py --build-assets. Edit PRESETS there, not this file. -->",
        "",
        f"{len(PRESETS)} presets. Default when the user names none and has no brand or design to match: "
        f"**`{DEFAULT_PRESET}`**. Each preview is a mock page rendered from the preset's tokens "
        "(Inter stands in for Segoe UI in the images). Ready-to-register theme files are in `assets/themes/`.",
        "",
        "![All presets](../assets/gallery.png)",
        "",
        "| Preset | Mode | Cards | Radius | Fonts | Use for |",
        "|---|---|---|---|---|---|",
    ]
    detail = []
    cards_html = []
    for key, raw in PRESETS.items():
        t = normalise(raw)
        rows = check(t)
        print(f"{key}:", file=sys.stderr)
        ok &= print_checks(rows)
        name = theme_name(key)
        (themes / name).write_text(json.dumps(build_theme(t, name), indent=2) + "\n", encoding="utf-8")
        svg = preview_svg(t, t["label"])
        (previews / f"{key}.svg").write_text(svg + "\n", encoding="utf-8")
        fonts = t["heading"] if t["heading"] == t["body"] else f'{t["heading"]} / {t["body"]}'
        catalog.append(f'| [`{key}`](#{key}) | {t["mode"]} | {t["card"]} | {t["radius"]} | {fonts} | {t["blurb"]} |')
        worst = min(r[3] for r in rows if r[1] and r[4] == 4.5)
        warns = [r[0] for r in rows if r[5] == "warn"]
        detail += [
            f"## {key}",
            "",
            f"![{key}](../assets/previews/{key}.png)",
            "",
            t["blurb"],
            "",
            f"- Theme file: `assets/themes/{name}`",
            f"- Canvas `{t['page']}`, visuals `{t['surface']}`, KPI tiles `{t['tile']}`, "
            f"border {('`' + t['border'] + '`') if t['border'] else 'none'}, text `{t['text']}`, labels `{t['muted']}`",
            f"- Series: {' '.join('`' + c + '`' for c in t['data'])}",
            f"- Lowest text contrast {worst:.1f}:1"
            + (f"; below 3:1 for graphics: {', '.join(warns)}" if warns else ""),
            "",
        ]
        cards_html.append(f'<figure><img src="previews/{key}.svg" alt="{key}"><figcaption><b>{key}</b> · '
                          f'{t["blurb"]}</figcaption></figure>')
    (SKILL / "references" / "preset-catalog.md").write_text("\n".join(catalog + [""] + detail), encoding="utf-8")
    gallery = ("<!doctype html><meta charset='utf-8'><title>Theme presets</title><style>"
               "body{margin:0;padding:24px;background:#fff;font-family:Inter,sans-serif;color:#222}"
               "h1{font-size:20px;margin:0 0 16px}main{display:grid;grid-template-columns:repeat(3,640px);gap:20px}"
               "figure{margin:0}img{display:block;width:640px;height:412px}"
               "figcaption{font-size:12px;line-height:1.4;margin-top:6px;color:#444;max-width:640px}</style>"
               f"<h1>Power BI theme presets ({len(PRESETS)})</h1><main>" + "".join(cards_html) + "</main>")
    (SKILL / "assets" / "gallery.html").write_text(gallery + "\n", encoding="utf-8")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--preset", help="named preset (see --list)")
    src.add_argument("--palette", help="ui-ux-pro-max product palette, e.g. 'Analytics Dashboard'")
    src.add_argument("--tokens", help="JSON file with tokens (keys as in PRESETS)")
    ap.add_argument("--card", choices=CARD_STYLES)
    ap.add_argument("--radius", type=int)
    ap.add_argument("--font-heading")
    ap.add_argument("--font-body")
    ap.add_argument("--mode", choices=("light", "dark"))
    ap.add_argument("--name", help="theme name inside the JSON (default: from the output filename)")
    ap.add_argument("--out", help="write the theme JSON here (default: stdout)")
    ap.add_argument("--preview", help="also write a preview SVG here")
    ap.add_argument("--snippets", action="store_true", help="print PBIR snippets for non-cascading formatting")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--list-palettes", action="store_true")
    ap.add_argument("--build-assets", action="store_true")
    a = ap.parse_args()

    if a.list:
        for k, v in PRESETS.items():
            print(f"{k:16} {v['mode']:5} {v['card']:9} {v['blurb']}")
        return 0
    if a.list_palettes:
        for r in csv.DictReader(PALETTES_CSV.open(encoding="utf-8")):
            print(f"{r['Product Type']:45} {r['Primary']} {r['Secondary']} {r['Accent']}  {r['Notes']}")
        return 0
    if a.build_assets:
        return 0 if build_assets() else 1

    if a.palette:
        t = tokens_from_palette(a.palette)
    elif a.tokens:
        t = json.loads(Path(a.tokens).read_text(encoding="utf-8"))
    else:
        key = a.preset or DEFAULT_PRESET
        if key not in PRESETS:
            sys.exit(f"Unknown preset '{key}'. Use --list.")
        t = PRESETS[key]
    t = dict(t)
    for opt, k in (("card", "card"), ("radius", "radius"), ("font_heading", "heading"), ("font_body", "body"), ("mode", "mode")):
        if getattr(a, opt) is not None:
            t[k] = getattr(a, opt)
    if a.card == "outlined" and not t.get("border"):
        t["border"] = t.get("grid")
    if a.card in ("soft", "elevated", "flat"):
        t["border"] = None
    t = normalise(t)
    ok = print_checks(check(t))

    if a.snippets:
        print(json.dumps(snippets(t), indent=2))
        return 0 if ok else 1
    name = a.name or (Path(a.out).name if a.out else "CustomTheme.json")
    if not name.endswith(".json"):
        name += ".json"
    text = json.dumps(build_theme(t, name), indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    if a.preview:
        Path(a.preview).write_text(preview_svg(t, t["label"]) + "\n", encoding="utf-8")
        print(f"wrote {a.preview}", file=sys.stderr)
    if not ok:
        print("Contrast FAIL: fix the failing pair before using this theme.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
