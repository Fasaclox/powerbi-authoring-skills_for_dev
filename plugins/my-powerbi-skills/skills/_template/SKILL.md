---
name: my-skill-name
description: "<What it owns, in one clause>. Use when <the literal words a user would type: file types, commands, product names>. <When to load it before acting>. For <neighbouring job> use <sibling skill>; for <other job> use <other sibling>."
---

<!--
Template for a new skill. Copy this folder to skills/<your-skill-name>/,
rename `name` above to match the folder, and delete this comment.

Description formula (borrowed from upstream, keep it under ~450 chars):
  1. what the skill owns
  2. literal trigger tokens users actually type
  3. when to load it
  4. negative routing: which sibling skill handles the neighbouring job
     (powerbi-report-cli for visuals/pages, semantic-model-authoring for
     model/DAX, or another of your own skills)
-->

# My skill name

## When to use this skill
- ...

## When NOT to use it
- Visuals, pages, PBIR edits, publishing reports → `powerbi-report-cli`
- Tables, measures, relationships, DAX, refresh → `semantic-model-authoring`

## Workflow
1. ...
2. ...

## Done means
State the concrete deliverable that counts as finished (a file written, a
validation passing, a screenshot reviewed), not just "the command succeeded".

## References
Keep this file short and move detail into `references/*.md` (upstream keeps
each file under ~500 lines). List every reference here so it is one hop away:
- [references/example.md](references/example.md)
