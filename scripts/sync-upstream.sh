#!/usr/bin/env bash
# Refresh upstream/ from microsoft/skills-for-fabric.
# Usage: scripts/sync-upstream.sh [git-ref]   (default: main)
set -euo pipefail
REF="${1:-main}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --quiet https://github.com/microsoft/skills-for-fabric.git "$TMP/src"
git -C "$TMP/src" checkout --quiet "$REF"
SHA="$(git -C "$TMP/src" rev-parse HEAD)"
TAG="$(git -C "$TMP/src" describe --tags --always)"

rm -rf "$ROOT/upstream/powerbi-authoring"
cp -r "$TMP/src/plugins/powerbi-authoring" "$ROOT/upstream/powerbi-authoring"
cp "$TMP/src/LICENSE" "$ROOT/upstream/LICENSE"
cp "$TMP/src/mcp-setup/mcp-config-template.json" "$ROOT/upstream/mcp-config-template.json"

sed -i.bak -E \
  -e "s#^\| Release \|.*#| Release | $TAG |#" \
  -e "s#^\| Commit \|.*#| Commit | $SHA |#" \
  -e "s#^\| Copied on \|.*#| Copied on | $(date +%Y-%m-%d) |#" \
  "$ROOT/upstream/UPSTREAM.md"
rm -f "$ROOT/upstream/UPSTREAM.md.bak"

echo "upstream/ now at $TAG ($SHA). Review with: git diff --stat upstream/"
