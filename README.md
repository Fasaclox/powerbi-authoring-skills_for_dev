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
└── scripts/sync-upstream.sh          # pull a newer upstream release
```

## Provenance

`upstream/powerbi-authoring/` is copied unchanged from
[`plugins/powerbi-authoring`](https://github.com/microsoft/skills-for-fabric/tree/main/plugins/powerbi-authoring)
in microsoft/skills-for-fabric (MIT, © Microsoft Corporation). The release and
commit are recorded in [`upstream/UPSTREAM.md`](upstream/UPSTREAM.md). See
[`NOTICE.md`](NOTICE.md).

Keeping it untouched means updates are a clean replace instead of a merge.

## My skills

| Skill | What it does |
|---|---|
| [`variance-indicators`](plugins/my-powerbi-skills/skills/variance-indicators/SKILL.md) | MoM / QoQ / YoY % measures that show `--` when no period is selected or the prior period has no data, plus 25 named arrow, pill and badge styles, including ones that name the prior period (vs Aug 2025) or use PM/PY tags ([gallery](plugins/my-powerbi-skills/skills/variance-indicators/references/style-catalog.md)) |

## Install

**Claude Code**

```
/plugin marketplace add <owner>/<this-repo>
/plugin install powerbi-authoring@powerbi-skills-lab
/plugin install my-powerbi-skills@powerbi-skills-lab
```

**Other agents**: point your tool at `upstream/powerbi-authoring/skills/*` and
`plugins/my-powerbi-skills/skills/*`, and add the MCP server from
`upstream/powerbi-authoring/.mcp.json` (or `upstream/mcp-config-template.json`).

Prerequisites from upstream: Node.js (for `npx @microsoft/powerbi-modeling-mcp`),
`npm install -g @microsoft/powerbi-report-authoring-cli`, Azure CLI (`az login`)
for Fabric calls, and Power BI Desktop on Windows for local preview.

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

## License

My own files: MIT (see [`LICENSE`](LICENSE)). Files under `upstream/`: MIT, © Microsoft Corporation
(see [`upstream/LICENSE`](upstream/LICENSE)).
