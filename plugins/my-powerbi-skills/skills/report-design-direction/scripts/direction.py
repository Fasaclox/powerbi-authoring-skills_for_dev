#!/usr/bin/env python3
"""Design direction for a Power BI report from its domain.

Matches a brief ("hr recruitment dashboard", "hospital bed occupancy") to one of
the 192 product types in ui-ux-pro-max (references/uiux-data, MIT) and turns that
row into Power BI decisions: an upstream tone and archetype, density, card style,
palette with contrast checks, a font pairing mapped to fonts the Power BI service
renders, domain anti-patterns, and the report-themes command that builds the theme.

  python3 direction.py "hr recruitment dashboard"
  python3 direction.py --product "Healthcare App"        # exact row
  python3 direction.py "fintech" --json                  # for agents
  python3 direction.py --list                            # all product types
  python3 direction.py --catalog > ../references/domain-catalog.md
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "references" / "uiux-data"

# Fonts the Power BI service renders for every viewer (same list as report-themes).
SAFE_FONTS = {
    "Segoe UI", "Segoe UI Semibold", "Segoe UI Bold", "Segoe UI Light", "DIN",
    "Arial", "Arial Black", "Calibri", "Cambria", "Candara", "Consolas",
    "Constantia", "Corbel", "Courier New", "Georgia", "Lucida Sans Unicode",
    "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana",
}

# Every font used in typography.csv, by the Power BI font that carries the same
# feel. sans -> Segoe UI, serif/script/decorative serif -> Georgia,
# condensed/tech display -> DIN, mono -> Consolas, rounded -> Trebuchet MS.
FONT_CLASS = {
    "serif": ["Abril Fatface", "Bodoni Moda", "Calistoga", "Cinzel", "Cormorant",
              "Cormorant Garamond", "Cormorant Infant", "Crimson Pro", "Crimson Text",
              "EB Garamond", "Libre Baskerville", "Libre Bodoni", "Lora", "Merriweather",
              "Newsreader", "Noto Naskh Arabic", "Noto Serif JP", "Noto Serif TC",
              "Playfair Display", "Playfair Display SC", "Poiret One", "Source Serif 4"],
    "script": ["Amatic SC", "Caveat", "Great Vibes", "Kalam", "Patrick Hand"],
    "condensed": ["Anton", "Barlow Condensed", "Bebas Neue", "Chakra Petch", "Exo", "Exo 2",
                  "Orbitron", "Russo One", "Syncopate", "Lexend Mega"],
    "mono": ["Fira Code", "JetBrains Mono", "Press Start 2P", "Roboto Mono", "Share Tech Mono",
             "Space Mono", "VT323"],
    "rounded": ["Baloo 2", "Comic Neue", "Fredoka", "Nunito", "Quicksand", "Righteous",
                "Varela Round"],
}
CLASS_OF = {f: c for c, fs in FONT_CLASS.items() for f in fs}  # anything else is sans
PBI_HEADING = {"sans": "Segoe UI Semibold", "serif": "Georgia", "script": "Georgia",
               "condensed": "DIN", "mono": "Consolas", "rounded": "Trebuchet MS"}
PBI_BODY = {"sans": "Segoe UI", "serif": "Segoe UI", "script": "Segoe UI",
            "condensed": "Segoe UI", "mono": "Consolas", "rounded": "Segoe UI"}

# Upstream tone catalog (powerbi-report-cli references/design/tone-catalog.md).
# First rule whose words appear in the product type, keywords or style wins.
TONE_RULES = [  # \b on the left only, so "logistic" also matches "logistics"
    ("Corporate Cool", r"\b(saas|b2b|crm|bank|insurance|legal|invoice|government)"),
    ("Monospace Terminal", r"\b(developer|ide\b|terminal|cyber|api\b|quantum|devops|code\b|hacker)"),
    ("Clinical Calm", r"\b(health|medical|clinic|patient|dental|pharmac|veterinar|telemedicine|"
                      r"senior care|mental|therapy|sleep|calorie|medication|biohack|spa\b|"
                      r"wellness|meditation|mindful)"),
    ("Editorial Newsroom", r"\b(news|magazine|blog|publishing|journal|podcast|editorial)"),
    ("Scholarly Calm", r"\b(academic|research|universit|scholar|course|e-learning|lms\b|"
                       r"bootcamp|education|learning|flashcard|study|science|biotech|museum)"),
    ("Industrial Dense (Analyst Workbench)",
     r"\b(logistic|inventory|iot\b|energy|utilit|manufactur|airline|construction|agricultur|"
     r"drone|transit|parking|delivery|ride hailing|fleet|warehouse|supply|automation|rpa\b|"
     r"status|incident|ev/charging|climate)"),
    ("Minimal Restrained", r"\b(luxury|premium|fashion|architecture|interior|gallery|hotel|"
                           r"real estate|wedding|photography|portfolio|jewel)"),
    ("Playful Energetic", r"\b(gam|kids|child|fitness|gym|sport|music|food|restaurant|"
                          r"bakery|cafe|pet\b|social|dating|creator|event|e-commerce|ecommerce|"
                          r"retail|shop|florist|subscription box|marketplace|meme|habit)"),
    ("Corporate Cool", r"."),
]
DARK_TONE = "Industrial Cockpit"
LIVE = r"real-time|monitor|operations|streaming|trading"

# Upstream archetypes (references/design/archetypes/*.md) by dashboard style.
ARCHETYPE_RULES = [
    ("operational-monitor", r"real-time|monitor|operations|occupancy|inventory|iot|sensor|"
                            r"route|pipeline|status|case management|claims"),
    ("comparative-benchmark", r"comparative|benchmark|leaderboard|performance"),
    ("analytical-canvas", r"drill-down|behavior|predictive|data-dense|analytics|ai/ml|3d|spatial"),
    ("executive-summary", r"."),
]

DENSITY_RULES = [("dense", r"data-dense|real-time|monitor|terminal|hud"),
                 ("spacious", r"executive|luxury|minimal|premium|editorial")]

CARD_RULES = [  # report-themes --card
    ("elevated", r"dark mode|oled|cyberpunk|hud|sci-fi|3d|hyperreal|liquid glass"),
    ("soft", r"glass|soft ui|clay|neumorph|aurora|organic|biophilic"),
    ("outlined", r"data-dense|bento|accessible|trust|enterprise"),
    ("flat", r"."),
]

# Common BI subject areas that ui-ux-pro-max has no row for, and the row that
# fits them best. A query word here boosts that row.
ALIASES = {
    "hr": "Job Board/Recruitment", "people": "Job Board/Recruitment",
    "workforce": "Job Board/Recruitment", "headcount": "Job Board/Recruitment",
    "attrition": "Job Board/Recruitment", "employee": "Job Board/Recruitment",
    "manufacturing": "Inventory & Stock Management", "production": "Inventory & Stock Management",
    "factory": "Inventory & Stock Management", "warehouse": "Inventory & Stock Management",
    "procurement": "Inventory & Stock Management", "supply": "Logistics/Delivery",
    "shipping": "Logistics/Delivery", "sales": "CRM & Client Management",
    "pipeline": "CRM & Client Management", "revenue": "Financial Dashboard",
    "finance": "Financial Dashboard", "financial": "Financial Dashboard",
    "accounting": "Financial Dashboard", "budget": "Financial Dashboard",
    "marketing": "Marketing Agency", "campaign": "Marketing Agency",
    "helpdesk": "Status Page / Incident Management", "itsm": "Status Page / Incident Management",
    "executive": "Analytics Dashboard", "kpi": "Analytics Dashboard",
}

STOP = set("a an and the for of to in on with by dashboard report reports power bi powerbi page "
           "pages app platform tool service".split())


def load(name):
    return list(csv.DictReader((DATA / name).open(encoding="utf-8")))


def words(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP]


def first(rules, text):
    return next((name for name, rx in rules if re.search(rx, text, re.I)), None)


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    return "#" + "".join(f"{round(int(a[i:i+2], 16) * (1 - t) + int(b[i:i+2], 16) * t):02X}" for i in (0, 2, 4))


def data_colors(c):
    """Primary, secondary, accent as series colours, each readable (3:1) on the card."""
    out = []
    for k in ("Primary", "Secondary", "Accent"):
        col, toward = c[k], ("#FFFFFF" if luminance(c["Card"]) < 0.2 else "#000000")
        t = 0.0
        while contrast(col, c["Card"]) < 3 and t < 1:
            t += 0.05
            col = mix(c[k], toward, t)
        out.append(col)
    return out


def pick_fonts(typo, text):
    """Best typography.csv pairing for this domain; language pairings only when asked."""
    q = set(words(text))
    best, score = None, -1
    for r in typo:
        if "multilingual" in r["Mood/Style Keywords"] and not q & set(words(r["Font Pairing Name"])):
            continue
        hay = set(words(r["Mood/Style Keywords"] + " " + r["Best For"] + " " + r["Font Pairing Name"]))
        s = len(q & hay)
        if s > score:
            best, score = r, s
    return best


def direction(i, products, colors, reasoning, typo):
    p, c, u = products[i], colors[i], reasoning[i]
    text = " ".join([p["Product Type"], p["Keywords"], p["Primary Style Recommendation"],
                     p["Dashboard Style (if applicable)"]])
    dark = luminance(c["Background"]) < 0.2
    # The product type name decides first; keywords only when the name says nothing.
    tone = first(TONE_RULES[:-1], p["Product Type"]) or first(TONE_RULES, text)
    if dark and re.search(LIVE, text, re.I):
        tone = DARK_TONE
    dash = p["Dashboard Style (if applicable)"]
    no_dash = dash.startswith("N/A")
    typo_row = pick_fonts(typo, " ".join([p["Product Type"], p["Keywords"], u["Typography_Mood"],
                                         tone]))
    hd, bd = typo_row["Heading Font"], typo_row["Body Font"]
    hc, bc = CLASS_OF.get(hd, "sans"), CLASS_OF.get(bd, "sans")
    # A mono body only suits the terminal tone; everywhere else numbers read better in Segoe UI.
    body = PBI_BODY[bc] if (bc != "mono" or tone == "Monospace Terminal") else "Segoe UI"
    heading = PBI_HEADING[hc]
    card = first(CARD_RULES, p["Primary Style Recommendation"] + " " + dash)
    if dark and card == "flat":
        card = "elevated"
    pal = {k: c[k] for k in ("Primary", "Secondary", "Accent", "Background", "Foreground", "Card",
                             "Muted Foreground", "Border", "Destructive")}
    checks = {
        "text on background": contrast(c["Foreground"], c["Background"]),
        "label on primary": contrast(c["On Primary"], c["Primary"]),
        "primary on background": contrast(c["Primary"], c["Background"]),
        "accent on background": contrast(c["Accent"], c["Background"]),
        "muted text on card": contrast(c["Muted Foreground"], c["Card"]),
    }
    return {
        "product_type": p["Product Type"],
        "tone": tone,
        "archetype": "executive-summary" if no_dash else first(ARCHETYPE_RULES, dash),
        "archetype_from": "default (source has no dashboard style)" if no_dash else dash,
        "density": next((n for n, rx in DENSITY_RULES if re.search(rx, dash + " " + tone, re.I)),
                        "standard"),
        "mode": "dark" if dark else "light",
        "card": card,
        "style_source": p["Primary Style Recommendation"],
        "palette": pal,
        "palette_note": c["Notes"],
        "contrast": checks,
        "color_map_seed": data_colors(c),
        "fonts": {
            "pairing": typo_row["Font Pairing Name"],
            "design": {"heading": hd, "body": bd},
            "powerbi": {"heading": heading, "body": body},
            "fallback_chain": {"heading": f"{hd}, {heading}, sans-serif",
                               "body": f"{bd}, {body}, sans-serif"},
        },
        "color_mood": u["Color_Mood"],
        "typography_mood": u["Typography_Mood"],
        "considerations": p["Key Considerations"],
        "anti_patterns": [a.strip() for a in u["Anti_Patterns"].split("+") if a.strip()],
        "theme_command": (f'python3 ../report-themes/scripts/build_theme.py --palette "{p["Product Type"]}" '
                          f'--card {card} --font-heading "{heading}" --font-body "{body}" '
                          f'--preview <Name>.svg --out <Name>-<guid>.json'),
    }


def score_rows(query, products):
    q = words(query)
    phrase = query.lower().strip()
    out = []
    for i, p in enumerate(products):
        name = p["Product Type"].lower()
        nw, kw, dw = set(words(name)), set(words(p["Keywords"])), set(words(p["Dashboard Style (if applicable)"]))
        s = 0.0
        for w in q:
            stem = w.rstrip("s")
            hit = lambda ws: any(x == w or x.rstrip("s") == stem for x in ws)
            s += 3 * hit(nw) + 2 * hit(kw) + 1 * hit(dw)
        if phrase and phrase in name:
            s += 5
        s += 6 * sum(ALIASES.get(w, ALIASES.get(w.rstrip("s"))) == p["Product Type"] for w in q)
        if p["Dashboard Style (if applicable)"].startswith("N/A"):
            s -= 0.5  # prefer rows that describe a dashboard
        out.append((s, i))
    return sorted((x for x in out if x[0] > 0), key=lambda x: (-x[0], x[1]))


def fmt_md(d, alts):
    pal, f = d["palette"], d["fonts"]
    L = [f"## Design direction: {d['product_type']}", ""]
    if alts:
        L += ["Other close matches: " + ", ".join(f"`{a}`" for a in alts)
              + " (rerun with `--product \"<name>\"`).", ""]
    L += [
        "```yaml",
        "design_identity:",
        f"  tone: {d['tone']}  # {d['color_mood']}; {d['typography_mood']}",
        "  signature: <pick from signatures.md to suit the tone>",
        f"archetype: {d['archetype']}  # from: {d['archetype_from']}",
        f"density: {d['density']}",
        f"theme: {{mode: {d['mode']}, card: {d['card']}, palette: \"{d['product_type']}\"}}",
        f"fonts: {{heading: \"{f['powerbi']['heading']}\", body: \"{f['powerbi']['body']}\"}}",
        "color_map_seed: [" + ", ".join(f'"{x}"' for x in d["color_map_seed"]) + "]"
        + ("  # adjusted to 3:1 on the card" if d["color_map_seed"] != [pal[k] for k in ("Primary", "Secondary", "Accent")] else ""),
        "```",
        "",
        "| Token | Hex |", "|---|---|",
    ]
    L += [f"| {k} | `{v}` |" for k, v in pal.items()]
    L += ["", f"Palette note: {d['palette_note']}", "", "| Contrast pair | Ratio | Min | |", "|---|---|---|---|"]
    for k, v in d["contrast"].items():
        need = 4.5 if k in ("text on background", "label on primary", "muted text on card") else 3.0
        L.append(f"| {k} | {v}:1 | {need}:1 | {'ok' if v >= need else 'FIX'} |")
    if any(v < 3 for k, v in d["contrast"].items() if k.endswith("on background")):
        L += ["", "A palette colour is too close to the canvas to use as a data colour. Use "
              "`color_map_seed` (already adjusted) for measures; report-themes will warn on the "
              "same series, so set series 1 from the seed in a tokens file, or pick another row."]
    L += [
        "",
        f"Fonts: source pairing **{f['pairing']}** ({f['design']['heading']} / {f['design']['body']}) "
        f"→ Power BI **{f['powerbi']['heading']} / {f['powerbi']['body']}**. To keep the design fonts "
        f"where installed, use the fallback chain `{f['fallback_chain']['heading']}`.",
        "",
        f"Style source: {d['style_source']} → card `{d['card']}`.",
        "",
        f"Consider: {d['considerations']}",
        "",
        "Avoid: " + "; ".join(d["anti_patterns"]),
        "",
        "Build the theme:",
        "```",
        d["theme_command"],
        "```",
    ]
    return "\n".join(L)


def catalog(rows):
    L = ["# Domain catalog", "",
         "Generated by `scripts/direction.py --catalog` from ui-ux-pro-max (MIT). "
         "One row per product type: the direction `direction.py --product \"<type>\"` gives.", "",
         "| Product type | Tone | Archetype | Mode | Card | Primary | Accent | PBI fonts |",
         "|---|---|---|---|---|---|---|---|"]
    for d in rows:
        f = d["fonts"]["powerbi"]
        L.append(f"| {d['product_type']} | {d['tone']} | {d['archetype']} | {d['mode']} | {d['card']} | "
                 f"`{d['palette']['Primary']}` | `{d['palette']['Accent']}` | {f['heading']} / {f['body']} |")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?", help="report domain or brief, e.g. 'hr recruitment'")
    ap.add_argument("--product", help="exact product type (see --list)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    ap.add_argument("--list", action="store_true", help="list product types")
    ap.add_argument("--catalog", action="store_true", help="print the markdown catalog of every row")
    a = ap.parse_args()

    products, colors = load("products.csv"), load("colors.csv")
    reasoning, typo = load("ui-reasoning.csv"), load("typography.csv")
    if not (len(products) == len(colors) == len(reasoning)):
        sys.exit("uiux-data CSVs are out of step; re-copy them from the same ui-ux-pro-max release")

    if a.list:
        for p in products:
            print(f"{p['Product Type']}  [{p['Dashboard Style (if applicable)']}]")
        return
    if a.catalog:
        sys.stdout.write(catalog([direction(i, products, colors, reasoning, typo)
                                  for i in range(len(products))]))
        return

    alts = []
    if a.product:
        idx = [i for i, p in enumerate(products) if p["Product Type"].lower() == a.product.lower()]
        if not idx:
            sys.exit(f"No product type '{a.product}'. Try --list.")
        i = idx[0]
    elif a.query:
        ranked = score_rows(a.query, products)
        if not ranked:
            sys.exit(f"No product type matches '{a.query}'. Try broader words or --list.")
        i = ranked[0][1]
        alts = [products[j]["Product Type"] for _, j in ranked[1:4]]
    else:
        ap.error("give a query, --product, --list or --catalog")

    d = direction(i, products, colors, reasoning, typo)
    if a.json:
        d["other_matches"] = alts
        print(json.dumps(d, indent=2))
    else:
        print(fmt_md(d, alts))


if __name__ == "__main__":
    main()
