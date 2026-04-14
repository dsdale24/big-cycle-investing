---
name: changelog-check
description: Use when the user asks to "check the Claude Code changelog", "see what's new in Claude Code", "look for changelog updates", "is there a fix for X yet", or wants to evaluate whether recent Claude Code releases affect this project's workflow. Also use when re-evaluating issue #33 (revisit worktree isolation once upstream is ready). Fetches the changelog, identifies entries since the last check, evaluates relevance to this project, and produces a triage report.
---

# Changelog Check

Track Claude Code releases and evaluate whether any changes affect this
project's workflow. State persists across sessions so each invocation only
surfaces what's new since the last time we looked.

## When to invoke

- User explicitly asks ("any Claude Code updates?", "check the changelog")
- Re-evaluating a workflow issue that depends on upstream fixes — most
  notably **#33** (revisit worktree isolation)
- Roughly every 1-2 weeks if nothing else has triggered a check

## Inputs

State lives in `.claude/skills/changelog-check/state.json` (committed; this
is a solo project, so the last-checked version is a shared team fact).

Schema:
```json
{
  "last_version": "2.1.105",
  "last_checked": "2026-04-14",
  "notes": "Free-form anything-to-remember. Keep it one line."
}
```

## Process

### 1. Read state
```
cat .claude/skills/changelog-check/state.json
```
Note `last_version` and `last_checked`. If the file doesn't exist, treat
the last version as unknown and report everything from the most recent
~20 entries.

### 2. Fetch the changelog
```
WebFetch https://code.claude.com/docs/en/changelog
```
Prompt it to extract every entry with version number newer than
`last_version`. Prompt should specifically ask for entries mentioning the
keywords below, PLUS any general entries after `last_version`.

### 3. Evaluate relevance

For each new entry, classify as one of:

- **Ticks #33** — directly addresses one of issue #33's open checklist
  items. These matter most; flag prominently and reference the specific
  checklist item.
- **Likely relevant** — touches an area we depend on (see keywords
  below) but doesn't tick an open checklist item.
- **Worth noting** — project could reasonably care at some point
  (testing/CI, MCP, hooks, agent tool changes).
- **Skip** — unrelated to this project's workflow (e.g., IDE extension
  fixes, unrelated bug fixes).

**Keywords that mean "pay attention":**
- `worktree`, `isolation`, `WorktreeCreate`, `.worktreeinclude`,
  `EnterWorktree`, `ExitWorktree`
- `subagent`, `sub-agent`, `Agent tool`, `isolation`
- `settings`, `permission`, `allow`, `deny`, `allowlist`
- `hook`, `PreToolUse`, `PostToolUse`, `SessionStart`, `UserPromptSubmit`
- `skill`, `slash command`, `/review-pr`
- `pytest`, `GitHub Actions`, `CI`
- `MCP`, `MCP server`, `plugin`

**Keywords that usually mean "skip":**
- VS Code / JetBrains / IDE extension stuff (we only use the CLI)
- Windows-specific fixes (we run on macOS)
- Bedrock / Vertex / Foundry cloud provider auth
- Specific language or framework integrations we don't use

### 4. Report

Produce a summary with three sections. Keep each entry to one or two
sentences citing the version number:

```
## Changelog check (last_version: X.Y.Z → Z.Y.Z, N new entries)

### Ticks #33
- 2.1.ZZ — <short entry> — ticks "<#33 checklist item>"

### Likely relevant
- 2.1.YY — <short entry> — why it might matter here

### Worth noting
- 2.1.XX — <short entry> — one-line "could be useful if …"

(Skipped N unrelated entries covering IDE/Windows/cloud-provider fixes.)
```

Then ask the user whether to:
- Tick the #33 item(s) (coordinator files a `gh issue comment`)
- Pick up any of the "Likely relevant" items as concrete work
- Just record the check and move on

### 5. Update state

Regardless of what the user decides, update `state.json` with the
newest version seen and today's date. Set `notes` to a one-line summary
of what we found (e.g., "2 #33 ticks, 1 worth noting" or "no relevant
changes").

```
Write .claude/skills/changelog-check/state.json
```

Do NOT update state if you failed to fetch the changelog — we want to
see the same entries next time.

## Scope

- Do NOT comment on or close any GitHub issues yourself. Always defer
  to the user.
- Do NOT update #33's checkboxes without the user saying "yes, tick
  them" explicitly.
- Do NOT interpret silence as confirmation. If the fetch failed or the
  output was ambiguous, report the failure and stop.

## Output example

A good report looks like:

> Changelog check (2.1.105 → 2.1.112, 7 new entries)
>
> **Ticks #33**
> - 2.1.110 — "Fixed WorktreeCreate hook payload to include worktree_path and worktree_name for subagent-triggered worktrees" — ticks #33's *payload schema* item.
>
> **Likely relevant**
> - 2.1.108 — "Added permissions.subagents section in settings.json for subagent-specific allow/deny" — may simplify our bare-Edit/Write setup if we ever re-adopt isolation.
>
> **Worth noting**
> - 2.1.107 — "Added --output-format jsonl for scheduled tasks" — possibly useful for the autoresearch loop eventually.
>
> (Skipped 4 entries covering VS Code extension and Windows path fixes.)
>
> Want me to tick #33's *payload schema* checkbox?

A bad report is one that:
- Lists every entry without triage
- Flags irrelevant entries as "relevant"
- Claims to have found something without citing a version number
- Updates `state.json` before the user sees the report
