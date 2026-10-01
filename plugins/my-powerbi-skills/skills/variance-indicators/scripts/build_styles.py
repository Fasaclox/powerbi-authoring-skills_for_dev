#!/usr/bin/env python3
"""Build the variance-indicator style catalog from one source of truth.

Every style is an SVG template defined once in STYLES below. This script turns
each template into:

  references/styles/<name>.dax       a ready-to-paste Power BI SVG measure
  assets/previews/<name>.svg         a preview (up, down, flat, blank states)
  references/style-catalog.md        the pick-by-name gallery page
  assets/gallery.html                all previews on one page (for the PNG)

Because the DAX and the previews come from the same template, a preview shows
exactly what the measure draws (up to font metrics).

Template syntax
  {{expr}}         numeric expression, rounded to a whole pixel
                   vars: _vw value width, _lw label width, _iw icon size (0 when
                   blank), _ig gap after icon (0 when blank), _lg gap before
                   label (0 when no label), _W total width; MAX(a, b)
  {{$v}} {{$l}}    value text / label text (escaped)
  {{$c}} {{$bg}}   status colour / soft background colour
  {{$tc}}          neutral label colour
  [[ICON|x|y]]     the direction icon placed at x, y (numeric expressions)

Run:  python3 scripts/build_styles.py   (from the skill folder or anywhere)
"""

import html
import math
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent

FONT = "font-family='Segoe UI,Arial,sans-serif'"

# Status colours: (text/icon colour, soft background)
GOOD = ("#15803D", "#DCFCE7")
BAD = ("#DC2626", "#FEE2E2")
FLAT = ("#64748B", "#F1F5F9")
BLANK = ("#94A3B8", "#F1F5F9")
LABEL = "#64748B"

# Average glyph width as a share of font size, used to size pills and place
# labels. Same factor in DAX and in the previews.
VALUE_EM = 0.6
LABEL_EM = 0.55

# ---------------------------------------------------------------- icons
# Each icon is drawn pointing up in a 16x16 box; "down" is the same icon
# flipped vertically. "flat" is drawn separately.
_STROKE = "fill='none' stroke='{{$c}}' stroke-linecap='round' stroke-linejoin='round'"
DASH = "<path d='M3 8H13' " + _STROKE + " stroke-width='2.5'/>"
ICONS = {
    "block": ("<path d='M8 1L15 8H10.5V15H5.5V8H1Z' fill='{{$c}}'/>", DASH),
    "thin": ("<path d='M8 14V2M3 7L8 2L13 7' " + _STROKE + " stroke-width='2'/>", DASH),
    "diag": ("<path d='M4 12L12 4M6 4H12V10' " + _STROKE + " stroke-width='2'/>", DASH),
    "trend": ("<path d='M1 12L6 7L9 10L15 4M11 4H15V8' " + _STROKE + " stroke-width='1.8'/>", DASH),
    "triangle": ("<path d='M8 3L14.5 13H1.5Z' fill='{{$c}}'/>", DASH),
    "chevron": (
        "<path d='M2.5 11L8 5.5L13.5 11' " + _STROKE + " stroke-width='2.8'/>",
        "<path d='M5.5 2.5L11 8L5.5 13.5' " + _STROKE + " stroke-width='2.8'/>",
    ),
    "circle": (
        "<circle cx='8' cy='8' r='8' fill='{{$bg}}'/><path d='M8 12V4.5M5 7.5L8 4.5L11 7.5' "
        + _STROKE + " stroke-width='1.8'/>",
        "<circle cx='8' cy='8' r='8' fill='{{$bg}}'/><path d='M5 8H11' " + _STROKE + " stroke-width='1.8'/>",
    ),
    "none": ("", ""),
}

# ---------------------------------------------------------------- styles
# label: a string, None (no label), or a dict per direction
#        {"up", "down", "flat", "blank"}.
# Labels are generic on purpose: no hard-coded month or year.


def text(x, y, size, weight, fill, content, anchor=None):
    a = f" text-anchor='{anchor}'" if anchor else ""
    return (f"<text x='{x}' y='{y}' {FONT} font-size='{size}' font-weight='{weight}' "
            f"fill='{fill}'{a}>{content}</text>")


STYLES = [
    dict(
        name="arrow-simple", title="Simple arrow",
        desc="Bold block arrow and the percentage, nothing else.",
        source="Style sheet #1",
        icon="block", isz=16, ig=6, vfs=15, label=None, h=24,
        w="_iw+_ig+_vw",
        body="[[ICON|0|4]]" + text("{{_iw+_ig}}", 17.5, 15, 700, "{{$c}}", "{{$v}}"),
    ),
    dict(
        name="arrow-suffix", title="Arrow after value",
        desc="Percentage first, thin arrow after it. Quiet, fits next to a big KPI number.",
        source="Examples: 12.9% ↓, 80.9% ↑",
        icon="thin", isz=14, ig=3, vfs=14, label=None, h=24,
        w="_vw+_ig+_iw",
        body=text(0, 17, 14, 600, "{{$c}}", "{{$v}}") + "[[ICON|_vw+_ig|5]]",
    ),
    dict(
        name="arrow-label", title="Arrow with label",
        desc="Block arrow, percentage, then a grey comparison label.",
        source="Style sheet #3 (and #2 without the month)",
        icon="block", isz=16, ig=6, vfs=15, label="vs last month", lfs=12, lg=10, h=24,
        w="_iw+_ig+_vw+_lg+_lw",
        body="[[ICON|0|4]]" + text("{{_iw+_ig}}", 17.5, 15, 700, "{{$c}}", "{{$v}}")
        + text("{{_iw+_ig+_vw+_lg}}", 17, 12, 400, "{{$tc}}", "{{$l}}"),
    ),
    dict(
        name="trend-label", title="Trend line with label",
        desc="Small trend-line icon, coloured percentage, grey label.",
        source="Examples: ↗ 5% vs last month, ↗ 12.00% from June",
        icon="trend", isz=16, ig=5, vfs=13, label="vs last month", lfs=13, lg=6, h=24,
        w="_iw+_ig+_vw+_lg+_lw",
        body="[[ICON|0|4]]" + text("{{_iw+_ig}}", 17, 13, 600, "{{$c}}", "{{$v}}")
        + text("{{_iw+_ig+_vw+_lg}}", 17, 13, 400, "{{$tc}}", "{{$l}}"),
    ),
    dict(
        name="pill", title="Pill",
        desc="Soft coloured pill with arrow and percentage.",
        source="Style sheet #4",
        icon="block", isz=12, ig=5, vfs=13, label=None, h=24,
        w="10+_iw+_ig+_vw+10",
        body="<rect width='{{_W}}' height='24' rx='12' fill='{{$bg}}'/>[[ICON|10|6]]"
        + text("{{10+_iw+_ig}}", 16.5, 13, 600, "{{$c}}", "{{$v}}"),
    ),
    dict(
        name="pill-label", title="Pill with label",
        desc="Soft pill holding the arrow, percentage and a short label.",
        source="Style sheet #6 (and #5 without the month)",
        icon="triangle", isz=11, ig=6, vfs=13, label="vs last month", lfs=11, lg=7, h=24,
        w="12+_iw+_ig+_vw+_lg+_lw+12",
        body="<rect width='{{_W}}' height='24' rx='12' fill='{{$bg}}'/>[[ICON|12|6.5]]"
        + text("{{12+_iw+_ig}}", 16.5, 13, 700, "{{$c}}", "{{$v}}")
        + text("{{12+_iw+_ig+_vw+_lg}}", 16, 11, 400, "#334155", "{{$l}}"),
    ),
    dict(
        name="pill-outline", title="Outline pill",
        desc="White pill with a coloured border, triangle and percentage.",
        source="Style sheet #7",
        icon="triangle", isz=12, ig=6, vfs=13, label=None, h=26,
        w="13+_iw+_ig+_vw+13",
        body="<rect x='1' y='1' width='{{_W-2}}' height='24' rx='12' fill='#FFFFFF' "
        "stroke='{{$c}}' stroke-width='1.5'/>[[ICON|13|7]]"
        + text("{{13+_iw+_ig}}", 17.5, 13, 700, "{{$c}}", "{{$v}}"),
    ),
    dict(
        name="trend-pill", title="Trend pill",
        desc="Percentage then a trend-line icon, inside a soft rounded box.",
        source="Examples: 12.20% ↗, 38.64% ↗, 32.73% ↘",
        icon="trend", isz=14, ig=5, vfs=13, label=None, h=26,
        w="9+_vw+_ig+_iw+9",
        body="<rect width='{{_W}}' height='26' rx='7' fill='{{$bg}}'/>"
        + text(9, 17.5, 13, 600, "{{$c}}", "{{$v}}") + "[[ICON|9+_vw+_ig|6]]",
    ),
    dict(
        name="chip-label", title="Chip, label after",
        desc="Small chip with percentage and diagonal arrow, grey label after it.",
        source="Examples: +3.2% ↑ from last month, ↗ +6.2% vs last month",
        icon="diag", isz=11, ig=3, vfs=12, label="vs last month", lfs=12, lg=8, h=24,
        w="7+_vw+_ig+_iw+7+_lg+_lw",
        body="<rect y='2' width='{{7+_vw+_ig+_iw+7}}' height='20' rx='5' fill='{{$bg}}'/>"
        + text(7, 16, 12, 600, "{{$c}}", "{{$v}}") + "[[ICON|7+_vw+_ig|6.5]]"
        + text("{{7+_vw+_ig+_iw+7+_lg}}", 16, 12, 400, "{{$tc}}", "{{$l}}"),
    ),
    dict(
        name="label-chip", title="Label, chip after",
        desc="Grey label first, then the small chip. Good in a row of KPI cards.",
        source="Example: vs Last Week +1.3% ↗",
        icon="diag", isz=11, ig=3, vfs=12, label="vs last month", lfs=12, lg=8, h=24,
        w="_lw+_lg+7+_vw+_ig+_iw+7",
        body=text(0, 16, 12, 400, "{{$tc}}", "{{$l}}")
        + "<rect x='{{_lw+_lg}}' y='2' width='{{7+_vw+_ig+_iw+7}}' height='20' rx='5' fill='{{$bg}}'/>"
        + text("{{_lw+_lg+7}}", 16, 12, 600, "{{$c}}", "{{$v}}")
        + "[[ICON|_lw+_lg+7+_vw+_ig|6.5]]",
    ),
    dict(
        name="soft-box", title="Soft box",
        desc="Square-cornered soft box with triangle and percentage; add a tag such as MoM if you like.",
        source="Example: ▲ 12.4%; reference sheet #13 with a tag",
        icon="triangle", isz=11, ig=6, vfs=13, label="", lfs=11, lg=6, h=24,
        w="8+_iw+_ig+_vw+_lg+_lw+8",
        body="<rect width='{{_W}}' height='24' rx='4' fill='{{$bg}}'/>[[ICON|8|6.5]]"
        + text("{{8+_iw+_ig}}", 16.5, 13, 600, "{{$c}}", "{{$v}}")
        + text("{{8+_iw+_ig+_vw+_lg}}", 16, 11, 500, "{{$c}}", "{{$l}}"),
    ),
    dict(
        name="triangle-tag", title="Triangle with tag",
        desc="Triangle, bold percentage and a short period tag (MoM, QoQ, YoY).",
        source="Style sheet #8 and #9",
        icon="triangle", isz=14, ig=7, vfs=15, label="MoM", lfs=12, lg=8, h=24,
        w="_iw+_ig+_vw+_lg+_lw",
        body="[[ICON|0|4]]" + text("{{_iw+_ig}}", 17.5, 15, 700, "{{$c}}", "{{$v}}")
        + text("{{_iw+_ig+_vw+_lg}}", 17, 12, 400, "#334155", "{{$l}}"),
    ),
    dict(
        name="brackets", title="Value in brackets",
        desc="Triangle and the percentage in brackets.",
        source="Style sheet #10",
        icon="triangle", isz=14, ig=7, vfs=15, label=None, h=24,
        w="_iw+_ig+_vw+11",
        body="[[ICON|0|4]]" + text("{{_iw+_ig}}", 17.5, 15, 700, "{{$c}}", "({{$v}})"),
    ),
    dict(
        name="prefix", title="Tag prefix",
        desc="Period tag first (MoM:), then triangle and percentage.",
        source="Style sheet #11",
        icon="triangle", isz=14, ig=7, vfs=15, label="MoM:", lfs=14, lg=7, h=24,
        w="_lw+_lg+_iw+_ig+_vw",
        body=text(0, 17.5, 14, 500, "#1F2937", "{{$l}}") + "[[ICON|_lw+_lg|4]]"
        + text("{{_lw+_lg+_iw+_ig}}", 17.5, 15, 700, "{{$c}}", "{{$v}}"),
    ),
    dict(
        name="text-only", title="Coloured text only",
        desc="No icon: coloured percentage and a period tag.",
        source="Style sheet #14 and #19",
        icon="none", isz=0, ig=0, vfs=15, label="MoM", lfs=12, lg=10, h=24,
        w="_vw+_lg+_lw",
        body=text(0, 17.5, 15, 700, "{{$c}}", "{{$v}}")
        + text("{{_vw+_lg}}", 17, 12, 400, "#334155", "{{$l}}"),
    ),
    dict(
        name="circle-badge", title="Circle badge",
        desc="Arrow inside a soft circle, then the percentage.",
        source="Style sheet #15",
        icon="circle", isz=22, ig=8, vfs=15, label=None, h=26,
        w="_iw+_ig+_vw",
        body="[[ICON|0|2]]" + text("{{_iw+_ig}}", 18.5, 15, 700, "{{$c}}", "{{$v}}"),
    ),
    dict(
        name="stack", title="Vertical stack",
        desc="Big arrow on top, percentage under it, tag at the bottom. Made for narrow tiles.",
        source="Style sheet #16",
        icon="block", isz=24, ig=0, vfs=15, label="MoM", lfs=11, lg=0, h=64,
        w="MAX(MAX(_vw,_lw),28)+4",
        body="[[ICON|(_W-24)/2|2]]" + text("{{_W/2}}", 44, 15, 700, "{{$c}}", "{{$v}}", "middle")
        + text("{{_W/2}}", 59, 11, 400, "#334155", "{{$l}}", "middle"),
    ),
    dict(
        name="chevron", title="Chevron",
        desc="Thick chevron and the percentage; flat shows a right chevron.",
        source="Style sheet #17",
        icon="chevron", isz=16, ig=7, vfs=15, label=None, h=24,
        w="_iw+_ig+_vw",
        body="[[ICON|0|4]]" + text("{{_iw+_ig}}", 17.5, 15, 700, "{{$c}}", "{{$v}}"),
    ),
    dict(
        name="descriptive", title="Descriptive text",
        desc="Triangle, percentage and a plain-language sentence that changes with direction.",
        source="Style sheet #18",
        icon="triangle", isz=13, ig=7, vfs=14, lfs=12, lg=12, h=24,
        label={"up": "Higher than last month", "down": "Lower than last month",
               "flat": "No change", "blank": ""},
        w="_iw+_ig+_vw+_lg+_lw",
        body="[[ICON|0|4.5]]" + text("{{_iw+_ig}}", 17.5, 14, 700, "{{$c}}", "{{$v}}")
        + text("{{_iw+_ig+_vw+_lg}}", 17, 12, 400, "#374151", "{{$l}}"),
    ),
]

TOKEN = re.compile(r"\{\{(.+?)\}\}|\[\[ICON\|(.+?)\|(.+?)\]\]")
STRVARS = {"$v": "_ve", "$l": "_le", "$c": "_c", "$bg": "_bg", "$tc": "_tc"}


def labels_for(style):
    lab = style.get("label")
    if lab is None:
        lab = ""
    if isinstance(lab, str):
        return {"up": lab, "down": lab, "flat": lab, "blank": lab}
    return lab


def icon_variants(style):
    up, flat = ICONS[style["icon"]]
    if not up:
        return "", ""
    return up, flat


def down_of(up):
    return "<g transform='translate(0,16) scale(1,-1)'>" + up + "</g>"


# ---------------------------------------------------------------- preview (Python)
def px(x):
    return int(math.floor(x + 0.5))


def fmt_pct(p):
    if p is None:
        return "--"
    r = round(p * 1000) / 1000  # one decimal place of a percentage
    s = f"{abs(r) * 100:.1f}%"
    return ("+" if r > 0 else "-" if r < 0 else "") + s


def render(style, pct):
    blank = pct is None
    r = None if blank else round(pct * 1000) / 1000
    d = "blank" if blank else ("up" if r > 0 else "down" if r < 0 else "flat")
    c, bg = {"up": GOOD, "down": BAD, "flat": FLAT, "blank": BLANK}[d]
    v = fmt_pct(pct)
    lab = labels_for(style)[d]
    up, flat = icon_variants(style)
    icon = {"up": up, "down": down_of(up) if up else "", "flat": flat, "blank": ""}[d]
    has_icon = bool(icon)
    ctx = {
        "_vw": len(v) * style["vfs"] * VALUE_EM,
        "_lw": len(lab) * style.get("lfs", 12) * LABEL_EM,
        "_iw": style["isz"] if has_icon else 0,
        "_ig": style["ig"] if has_icon else 0,
        "_lg": style.get("lg", 0) if lab else 0,
        "MAX": max,
    }
    ctx["_W"] = px(eval(style["w"], {}, ctx))
    strs = {"$v": html.escape(v), "$l": html.escape(lab), "$c": c, "$bg": bg, "$tc": LABEL}

    def sub(tpl):
        def rep(m):
            if m.group(1) is not None:
                e = m.group(1)
                return strs[e] if e in strs else str(px(eval(e, {}, ctx)))
            x, y = (px(eval(e, {}, ctx)) for e in (m.group(2), m.group(3)))
            s = style["isz"] / 16
            return f"<g transform='translate({x},{y}) scale({s:g})'>{sub(icon)}</g>" if icon else ""
        return TOKEN.sub(rep, tpl)

    return ctx["_W"], style["h"], sub(style["body"])


def preview_svg(style):
    states = [0.082, -0.046, 0.0, None]
    names = ["up", "down", "flat", "blank"]
    rows, maxw = [], 0
    rh = style["h"] + 14
    for i, (p, n) in enumerate(zip(states, names)):
        w, h, body = render(style, p)
        maxw = max(maxw, w)
        y = 10 + i * rh
        rows.append(f"<text x='12' y='{y + h / 2 + 4:g}' {FONT} font-size='10' fill='#94A3B8'>{n}</text>"
                    f"<svg x='56' y='{y}' width='{w}' height='{h}' overflow='visible'>{body}</svg>")
    W, H = 56 + maxw + 16, 10 + len(states) * rh
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>"
            f"<rect width='{W}' height='{H}' rx='8' fill='#FFFFFF'/>" + "".join(rows) + "</svg>\n")


# ---------------------------------------------------------------- DAX
def dax_str(lit):
    return '"' + lit.replace('"', '""').replace("#", "%23") + '"'


def num(e):
    """A numeric template expression as DAX: literals inline, _W as is, else ROUND."""
    if re.fullmatch(r"[\d.]+", e):
        return dax_str(str(px(float(e))))
    return "_W" if e == "_W" else f"ROUND ( {e}, 0 )"


def dax_concat(tpl, icon_var="_Icon", isz=16):
    parts = []
    pos = 0
    for m in TOKEN.finditer(tpl):
        if m.start() > pos:
            parts.append(dax_str(tpl[pos:m.start()]))
        if m.group(1) is not None:
            e = m.group(1)
            parts.append(STRVARS[e] if e in STRVARS else num(e))
        else:
            s = isz / 16
            parts += [dax_str("<g transform='translate("), num(m.group(2)), dax_str(","),
                      num(m.group(3)), dax_str(f") scale({s:g})'>"), icon_var, dax_str("</g>")]
        pos = m.end()
    if pos < len(tpl):
        parts.append(dax_str(tpl[pos:]))
    # merge adjacent literals
    merged = []
    for p in parts:
        if merged and p.startswith('"') and merged[-1].startswith('"'):
            merged[-1] = merged[-1][:-1] + p[1:]
        else:
            merged.append(p)
    return merged or ['""']


def dax_expr(tpl, indent, isz=16):
    pieces = dax_concat(tpl, isz=isz)
    return ("\n" + indent + "& ").join(pieces)


def dax_measure(style):
    lab = labels_for(style)
    up, flat = icon_variants(style)
    ind = "        "
    if up:
        icon_block = (
            "VAR _Icon =\n    SWITCH (\n        _Dir,\n"
            f"        1, {dax_expr(up, ind + '   ')},\n"
            f"        -1, {dax_expr(down_of(up), ind + '    ')},\n"
            f"        0, {dax_expr(flat, ind + '   ')},\n"
            '        ""\n    )\n'
        )
    else:
        icon_block = 'VAR _Icon = ""\n'
    if len(set(lab.values())) == 1:
        label_block = f'VAR _Label = "{lab["up"]}"            -- "" hides the label\n'
    else:
        label_block = (
            "VAR _Label =\n    SWITCH (\n        _Dir,\n"
            f'        1, "{lab["up"]}",\n        -1, "{lab["down"]}",\n'
            f'        0, "{lab["flat"]}",\n        "{lab["blank"]}"\n    )\n'
        )
    vem = round(style["vfs"] * VALUE_EM, 2)
    lem = round(style.get("lfs", 12) * LABEL_EM, 2)
    has_icon = "NOT ISBLANK ( _Pct )" if up else "FALSE ()"
    body = dax_expr(style["body"], "    ", style["isz"])
    return f"""// Style: {style['name']}  ({style['title']})
// {style['desc']}
// Generated by scripts/build_styles.py from the variance-indicators skill. Do not edit
// the SVG by hand here; change the template in the script and rebuild.
//
// Measure properties: Data category = Image URL. Use in a table/matrix cell,
// the Image visual (image URL from a field), or a card visual's image slot.
// Replace [Sales MoM %] with your variance measure (see period-measures.md):
// it must return a ratio and BLANK() when the comparison is not valid.

[Sales MoM {style['name']}] =
VAR _Pct = [Sales MoM %]                     -- ratio, BLANK when not comparable
VAR _HigherIsBetter = TRUE ()               -- FALSE () for costs, days, defects
VAR _Decimals = 1
{label_block}VAR _Num = "0" & IF ( _Decimals > 0, "." & REPT ( "0", _Decimals ) ) & "%"
VAR _R = ROUND ( _Pct, _Decimals + 2 )
VAR _Dir = IF ( ISBLANK ( _Pct ), 2, SIGN ( _R ) )   -- 1 up, -1 down, 0 flat, 2 blank
VAR _Good = IF ( _HigherIsBetter, _Dir, - _Dir )
VAR _c =
    SWITCH ( TRUE (), _Dir = 2, "{dax_hex(BLANK[0])}", _Good = 1, "{dax_hex(GOOD[0])}", _Good = -1, "{dax_hex(BAD[0])}", "{dax_hex(FLAT[0])}" )
VAR _bg =
    SWITCH ( TRUE (), _Dir = 2, "{dax_hex(BLANK[1])}", _Good = 1, "{dax_hex(GOOD[1])}", _Good = -1, "{dax_hex(BAD[1])}", "{dax_hex(FLAT[1])}" )
VAR _tc = "{dax_hex(LABEL)}"
VAR _v = IF ( _Dir = 2, "--", FORMAT ( _R, "+" & _Num & ";-" & _Num & ";" & _Num ) )
VAR _ve = SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( _v, "&", "&amp;" ), "<", "&lt;" ), "%", "%25" ), "#", "%23" )
VAR _le = SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( _Label, "&", "&amp;" ), "<", "&lt;" ), "%", "%25" ), "#", "%23" )
VAR _HasIcon = {has_icon}
VAR _vw = LEN ( _v ) * {vem:g}
VAR _lw = LEN ( _Label ) * {lem:g}
VAR _iw = IF ( _HasIcon, {style['isz']}, 0 )
VAR _ig = IF ( _HasIcon, {style['ig']}, 0 )
VAR _lg = IF ( _Label <> "", {style.get('lg', 0)}, 0 )
VAR _W = ROUND ( {style['w']}, 0 )
{icon_block}VAR _Body =
    {body}
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='" & _W
        & "' height='{style['h']}' viewBox='0 0 " & _W & " {style['h']}'>" & _Body & "</svg>"
"""


def dax_hex(h):
    return h.replace("#", "%23")


# ---------------------------------------------------------------- catalog
def catalog_md():
    out = [
        "# Variance indicator style catalog",
        "",
        "<!-- Generated by scripts/build_styles.py. Edit the script, not this file. -->",
        "",
        "![All styles](../assets/gallery.png)",
        "",
        "Pick a style by name. Each preview shows the four states: up (+8.2%), down (-4.6%),",
        "flat (0.0%) and blank (`--`, when no period is selected or the prior period has no data).",
        "Colours flip for metrics where lower is better (`_HigherIsBetter = FALSE ()`).",
        "",
        "Labels are generic (`vs last month`, `MoM`) and never name a month or year. Set",
        "`_Label` to `\"\"` to hide it, or to `QoQ` / `vs last quarter` / `YoY` / `vs last year`",
        "for the other periods.",
        "",
        "| Style | Looks like | Notes | Measure |",
        "|---|---|---|---|",
    ]
    for s in STYLES:
        out.append(
            f"| **`{s['name']}`**<br>{s['title']} | ![{s['name']}](../assets/previews/{s['name']}.svg) "
            f"| {s['desc']}<br><sub>From: {s['source']}</sub> | [{s['name']}.dax](styles/{s['name']}.dax) |"
        )
    out.append("")
    return "\n".join(out)


def gallery_html():
    cards = []
    for s in STYLES:
        svg = (SKILL / "assets" / "previews" / f"{s['name']}.svg").read_text()
        cards.append(f"<div class='card'><div class='name'>{s['name']}</div>"
                     f"<div class='title'>{html.escape(s['title'])}</div>{svg}</div>")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Variance indicator styles</title>
<style>
body {{ margin: 0; padding: 24px; background: #F8FAFC; font-family: 'Segoe UI', Arial, sans-serif; }}
h1 {{ font-size: 20px; color: #0F172A; margin: 0 0 4px; }}
p {{ color: #64748B; font-size: 13px; margin: 0 0 20px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 14px; }}
.card {{ background: #fff; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 12px 4px; }}
.name {{ font: 600 14px ui-monospace, 'DejaVu Sans Mono', monospace; color: #0F172A; }}
.title {{ font-size: 12px; color: #64748B; margin-bottom: 4px; }}
.card > svg {{ max-width: 100%; height: auto; }}
</style></head><body>
<h1>Variance indicator styles</h1>
<p>Pick by name. Rows: up, down, flat, blank (no period selected or no prior data).</p>
<div class="grid">
{''.join(cards)}
</div></body></html>
"""


def main():
    for s in STYLES:
        (SKILL / "assets" / "previews" / f"{s['name']}.svg").write_text(preview_svg(s))
        (SKILL / "references" / "styles" / f"{s['name']}.dax").write_text(dax_measure(s))
    (SKILL / "references" / "style-catalog.md").write_text(catalog_md())
    (SKILL / "assets" / "gallery.html").write_text(gallery_html())
    print(f"built {len(STYLES)} styles")


if __name__ == "__main__":
    main()
