# Power BI Skills Lab

Agent skills for authoring Power BI reports and semantic models: Microsoft's
upstream skills kept as-is, plus my own skills that build on them.

## Layout

```
.
├── .claude-plugin/marketplace.json   # installs both plugins below
├── upstream/                         # DO NOT EDIT: verbatim copy of Microsoft's plugin
│   ├── powerbi-authoring/
│   │   ├── skills/
│   │   │   ├── powerbi-report-cli/         # plan, design, author, preview, publish reports (PBIR/PBIP)
│   │   │   └── semantic-model-authoring/   # tables, measures, DAX, TMDL, Direct Lake, refresh, deploy
│   │   ├── common/                   # COMMON-CORE, COMMON-CLI, ITEM-DEFINITIONS-CORE (shared by both skills)
│   │   ├── .mcp.json                 # powerbi-modeling-mcp (stdio, via npx)
│   │   ├── .claude-plugin/plugin.json
│   │   └── .github/plugin/plugin.json
│   ├── mcp-config-template.json      # upstream's MCP config template for other clients
│   ├── LICENSE                       # Microsoft's MIT license
│   └── UPSTREAM.md                   # exact release + commit copied
├── plugins/my-powerbi-skills/        # my own skills live here
│   ├── .claude-plugin/plugin.json
│   └── skills/_template/             # copy this to start a new skill
├── vendor/ui-ux-pro-max/             # DO NOT EDIT: verbatim copy of the UI/UX Pro Max plugin
│   ├── .claude/skills/               # ui-ux-pro-max, design-system, ui-styling, design, brand, slides, banner-design
│   ├── .claude-plugin/plugin.json
│   ├── LICENSE                       # Next Level Builder's MIT license
│   └── UPSTREAM.md                   # exact version + commit copied
├── scripts/sync-upstream.sh          # pull a newer upstream release
└── scripts/sync-ui-ux-pro-max.sh     # pull a newer UI/UX Pro Max release
```

## Provenance

`upstream/powerbi-authoring/` is copied unchanged from
[`plugins/powerbi-authoring`](https://github.com/microsoft/skills-for-fabric/tree/main/plugins/powerbi-authoring)
in microsoft/skills-for-fabric (MIT, © Microsoft Corporation). The release and
commit are recorded in [`upstream/UPSTREAM.md`](upstream/UPSTREAM.md). See
[`NOTICE.md`](NOTICE.md).

`vendor/ui-ux-pro-max/` is copied unchanged from
[nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
(MIT, © Next Level Builder; `ui-styling` is Apache-2.0). Version and commit are in
[`vendor/ui-ux-pro-max/UPSTREAM.md`](vendor/ui-ux-pro-max/UPSTREAM.md).

Keeping both untouched means updates are a clean replace instead of a merge.

## Third-party design skills

The `ui-ux-pro-max` plugin adds general UI/UX design knowledge that is useful next to the
Power BI skills: searchable styles, colour palettes, font pairings, chart-type guidance and UX
rules (`ui-ux-pro-max`), design tokens (`design-system`), plus `ui-styling`, `design`, `brand`,
`slides` and `banner-design`. Its search script needs Python 3; some `design` and `brand`
scripts need Node.js or an image-generation API key (see each `SKILL.md`).

## My skills

| Skill | What it does |
|---|---|
| [`variance-indicators`](plugins/my-powerbi-skills/skills/variance-indicators/SKILL.md) | MoM / QoQ / YoY % measures that show `--` when no period is selected or the prior period has no data, plus 31 named arrow, pill, badge and mini-bar styles (SVG, plus a text version for card reference labels), including ones that name the prior period (vs Aug 2025) or use PM/PY tags ([gallery](plugins/my-powerbi-skills/skills/variance-indicators/references/style-catalog.md)) |
| [`report-themes`](plugins/my-powerbi-skills/skills/report-themes/SKILL.md) | Power BI theme JSON from design tokens: palette, soft rounded / outlined / elevated / flat cards, fonts, canvas, tables, slicers and charts, with WCAG contrast checks and PBIR snippets for what themes can't set. 9 named presets with previews ([gallery](plugins/my-powerbi-skills/skills/report-themes/references/preset-catalog.md)), 192 product palettes from ui-ux-pro-max, or your own brand tokens |
| [`report-design-direction`](plugins/my-powerbi-skills/skills/report-design-direction/SKILL.md) | Design direction from the report's business domain (192 industry profiles from ui-ux-pro-max): upstream tone and archetype, density, dark or light, card style, a contrast-checked palette and Power BI-safe fonts, plus the `report-themes` command that builds the theme ([catalog](plugins/my-powerbi-skills/skills/report-design-direction/references/domain-catalog.md)) |

## Install

### 1. Get access to the repo

The marketplace is this GitHub repo, so Claude Code has to be able to clone it.

- **Public repo**: anyone can install, nothing else to do.
- **Private repo**: the repo owner adds you as a collaborator (GitHub → Settings →
  Collaborators → Add people). Accept the invite, and make sure the git on your machine
  is signed in to that GitHub account (`gh auth login`, or Git Credential Manager on
  Windows) so the clone doesn't fail with "repository not found".

### 2. Install the plugins (Claude Code)

Run these in Claude Code:

```
/plugin marketplace add Fasaclox/powerbi-authoring-skills_for_dev
/plugin install powerbi-authoring@powerbi-skills-lab
/plugin install my-powerbi-skills@powerbi-skills-lab
/plugin install ui-ux-pro-max@powerbi-skills-lab      # optional design skills
```

The marketplace is called `powerbi-skills-lab` (from `.claude-plugin/marketplace.json`), so
plugin names always end in `@powerbi-skills-lab`. Restart Claude Code afterwards, then run
`/plugin` to check all three are installed and enabled.

**`powerbi-authoring` is required.** `my-powerbi-skills` builds on Microsoft's
`powerbi-report-cli` and `semantic-model-authoring` skills and hands work off to them. Install it
from this marketplace (pinned copy, see [`upstream/UPSTREAM.md`](upstream/UPSTREAM.md)) as above,
or from Microsoft's own marketplace if you want their latest release:

```
/plugin marketplace add microsoft/skills-for-fabric
/plugin install powerbi-authoring@fabric-collection
```

Install it from one marketplace only; two copies give you duplicate skills and two
`powerbi-modeling-mcp` servers.

### 3. Prerequisites for the upstream skills

Node.js (for `npx @microsoft/powerbi-modeling-mcp`),
`npm install -g @microsoft/powerbi-report-authoring-cli`, Azure CLI (`az login`)
for Fabric calls, and Power BI Desktop on Windows for local preview.

### Other agents

Point your tool at `upstream/powerbi-authoring/skills/*` and
`plugins/my-powerbi-skills/skills/*` (and optionally `vendor/ui-ux-pro-max/.claude/skills/*`), and add the MCP server from
`upstream/powerbi-authoring/.mcp.json` (or `upstream/mcp-config-template.json`).

### Troubleshooting (mostly Windows)

**`marketplace add` times out while cloning.** The repo is large (it carries the upstream and
vendored copies), so the clone can take longer than Claude Code's default git timeout. Raise it
to 10 minutes, then start Claude Code again from the same terminal:

```powershell
# PowerShell, current session
$env:CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS = "600000"

# PowerShell, permanent (open a new terminal afterwards)
setx CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS 600000
```

```bash
# macOS / Linux
export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=600000
```

**`EBUSY` or `EPERM` errors (resource busy, operation not permitted).** Another process is holding
the marketplace folder, usually a second Claude Code window or VS Code with the Claude extension.

1. Close every other Claude Code session and VS Code window.
2. Delete what the failed attempt left behind in `~/.claude/plugins/marketplaces`
   (`%USERPROFILE%\.claude\plugins\marketplaces` on Windows): any folder ending in `...clone`
   and any `powerbi-skills-lab` folder.

   ```powershell
   Get-ChildItem "$env:USERPROFILE\.claude\plugins\marketplaces" |
     Where-Object { $_.Name -like '*clone*' -or $_.Name -eq 'powerbi-skills-lab' } |
     Remove-Item -Recurse -Force
   ```

3. Run `/plugin marketplace add` again.

**Clone hangs with no progress.** Your git may be trying SSH and waiting on a key or host
prompt that never shows. Add the marketplace by its HTTPS URL instead:

```
/plugin marketplace add https://github.com/Fasaclox/powerbi-authoring-skills_for_dev.git
```

## Adding a skill

1. `cp -r plugins/my-powerbi-skills/skills/_template plugins/my-powerbi-skills/skills/<skill-name>`
2. Set `name:` in its `SKILL.md` to `<skill-name>` and write the description with the
   four-part formula in the template (owns / trigger words / when / which sibling handles the rest).
3. Add `"./skills/<skill-name>"` to `skills` in `plugins/my-powerbi-skills/.claude-plugin/plugin.json`.
4. Keep `SKILL.md` short; put detail in `references/` and link every file from `SKILL.md`.
5. Make each skill self-contained. A plugin is installed on its own, so don't link into
   `upstream/` by relative path; copy what you need into your skill's `references/`
   and credit it.

### Improving an upstream skill

Don't edit files in `upstream/`. Either:

- **Add a companion skill** that covers the gap and routes to the upstream skill for the rest
  (preferred; both keep working and upstream updates stay clean), or
- **Fork it**: copy the skill folder into `plugins/my-powerbi-skills/skills/<new-name>/`, rename it
  (so it doesn't collide with the upstream name), note the source commit at the top of its
  `SKILL.md`, then change it. Install only one of the two if their triggers overlap.

## Updating upstream

```
scripts/sync-upstream.sh            # latest main
scripts/sync-upstream.sh v0.3.19    # a specific tag
git diff --stat upstream/           # review, then commit
```

Check upstream's CHANGELOG for renamed or merged skills, and whether any of your forks need the fix too.

The UI/UX Pro Max copy updates the same way:

```
scripts/sync-ui-ux-pro-max.sh           # latest main
scripts/sync-ui-ux-pro-max.sh v2.16.0   # a specific tag
git diff --stat vendor/                 # review, then commit
```

## License

My own files: MIT (see [`LICENSE`](LICENSE)). Files under `upstream/`: MIT, © Microsoft Corporation
(see [`upstream/LICENSE`](upstream/LICENSE)). Files under `vendor/ui-ux-pro-max/`: MIT, © Next Level Builder
(see [`vendor/ui-ux-pro-max/LICENSE`](vendor/ui-ux-pro-max/LICENSE)), except `ui-styling` (Apache-2.0) and its fonts (OFL).
