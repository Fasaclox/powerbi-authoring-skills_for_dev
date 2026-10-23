#!/usr/bin/env bash
# Refresh vendor/ui-ux-pro-max from nextlevelbuilder/ui-ux-pro-max-skill.
# Usage: scripts/sync-ui-ux-pro-max.sh [git-ref]   (default: main)
set -euo pipefail
REF="${1:-main}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/vendor/ui-ux-pro-max"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --quiet https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git "$TMP/src"
git -C "$TMP/src" checkout --quiet "$REF"
SHA="$(git -C "$TMP/src" rev-parse HEAD)"
VER="$(sed -nE 's/.*"version": *"([^"]+)".*/\1/p' "$TMP/src/.claude-plugin/plugin.json" | head -1)"

rm -rf "$DEST/.claude" "$DEST/.claude-plugin"
mkdir -p "$DEST"
cp -r "$TMP/src/.claude-plugin" "$DEST/.claude-plugin"
rm -f "$DEST/.claude-plugin/marketplace.json"
mkdir -p "$DEST/.claude"
cp -r "$TMP/src/.claude/skills" "$DEST/.claude/skills"
cp "$TMP/src/LICENSE" "$DEST/LICENSE"

sed -i.bak -E \
  -e "s#^\| Version \|.*#| Version | $VER |#" \
  -e "s#^\| Commit \|.*#| Commit | $SHA |#" \
  -e "s#^\| Copied on \|.*#| Copied on | $(date +%Y-%m-%d) |#" \
  "$DEST/UPSTREAM.md"
rm -f "$DEST/UPSTREAM.md.bak"

echo "vendor/ui-ux-pro-max now at $VER ($SHA). Review with: git diff --stat vendor/"
