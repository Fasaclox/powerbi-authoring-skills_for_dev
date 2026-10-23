# Upstream snapshot

| | |
|---|---|
| Source | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| Path copied | `.claude/skills/` (all 7 skills) and `.claude-plugin/plugin.json` |
| Also copied | `LICENSE` |
| Version | 2.15.0 |
| Commit | d14efff8ed1faa4187f004f79926f428c8074ec7 |
| Copied on | 2026-10-23 |
| License | MIT, Copyright (c) 2024 Next Level Builder (see `LICENSE` in this folder). `.claude/skills/ui-styling/` carries its own Apache-2.0 `LICENSE.txt`, and its bundled fonts their own OFL files. |

Everything in this folder except this file is kept **unmodified** so it can be replaced
wholesale by `scripts/sync-ui-ux-pro-max.sh`. The layout (`.claude/skills/` under the plugin
root) is kept as-is because the skills call their scripts through
`${CLAUDE_PLUGIN_ROOT}/.claude/skills/...`.
