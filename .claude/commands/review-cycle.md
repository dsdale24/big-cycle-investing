---
description: Run the project-level reviewers whose cadence is due (parallel), then meta sequentially. Default — save outputs to reviews/, update state and README. Flags — --all runs all four reviewers regardless of cadence; --ephemeral writes to gitignored reviews/.ephemeral/ and skips state/README updates.
---

Run a full project review cycle: the four project-level reviewers in parallel, then meta sequentially after they complete.

## Default behavior (no flags)

- Reads `.claude/review-state.json` and runs **only the project-level reviewers whose cadence is due** (where `today - last_run > cadence_targets_days`, or `last_run is null`).
- Meta always runs at the end of the cycle regardless of its cadence — the cycle is where meta is most informative, because it just observed a fresh batch.
- Outputs are **saved** to `reviews/` and `reviews/meta/`.
- `.claude/review-state.json` and `reviews/README.md` are **updated** for every reviewer that ran.
- User is asked whether to commit the cycle as one PR. No commit without approval.

If the cadence-based set is empty (nothing due), tell the user all reviewers are up-to-date and ask whether to proceed with `--all` or skip.

## Flags

Parse `$ARGUMENTS` for these flags (any order; any combination):

- **`--all`** — ignore cadence; run all 4 project-level reviewers (adversarial, dalio, practitioner, data-quality) plus meta. Use for milestone review days.
- **`--ephemeral`** — write all review outputs to `reviews/.ephemeral/` (gitignored). Do NOT update `.claude/review-state.json`. Do NOT update `reviews/README.md`. Do NOT offer a commit flow. Use during rapid development for a full-cycle pulse-check without polluting the series. Combine with `--all` for "full cycle, draft mode."

## Steps

### 1. Decide which reviewers to run

Read `.claude/review-state.json`. Compute today's date (YYYY-MM-DD).

If `--all`: the set is {adversarial, dalio, practitioner, data-quality}.

Otherwise: for each of those four, compute `days_since_last_run`. If `last_run` is `null`, treat as infinitely overdue (include). If `days_since_last_run > cadence_targets_days[<type>]`, include.

If the resulting set is empty, tell the user all reviewers are up-to-date per cadence; ask whether to proceed with `--all` or skip.

### 2. Run project-level reviewers in parallel

For each reviewer in the set, spawn its agent in a **single message with multiple Agent tool calls** so they run concurrently. Use `run_in_background: true` for each.

Construct each prompt with the correct output path based on mode:
- Saved (default): `reviews/YYYY-MM-DD-<type>.md`
- Ephemeral: `reviews/.ephemeral/YYYY-MM-DD-<type>.md`

Example prompt shape (per reviewer):

```
Agent(
  subagent_type="review-<type>",
  description="<Type> review (cycle-batch [ephemeral|saved])",
  prompt="Run a <type> review per your system prompt. Write to <output_path>. Follow the output structure exactly. Final message: filename, one-sentence headline, <type-specific summary>.",
  run_in_background=true
)
```

Send all Agent calls in the same assistant message so they execute in parallel. Wait for each to complete (task-notification messages). Collect each agent's filename and headline from its return message.

### 3. Run meta-review last, sequentially

Meta always runs as part of a cycle (regardless of its own cadence-days, since a fresh batch is the highest-value moment to observe the series).

If the number of saved reviews in `reviews/*.md` is less than 3, warn the user that meta-review output will be thin. (Only saved reviews count — `reviews/.ephemeral/` does not.)

Spawn meta in the foreground (not parallel — needs the other reviewers' output files to exist):

- Saved mode: write to `reviews/meta/YYYY-MM-DD-meta.md`
- Ephemeral mode: write to `reviews/.ephemeral/meta/YYYY-MM-DD-meta.md`

In the prompt, include the headlines from the project-level reviewers that just ran so the meta reviewer knows which are from today's batch vs. historical. The meta agent's system prompt already skips `reviews/.ephemeral/` when reading the series.

### 4. State and README updates

**Saved mode only:**
- Update `.claude/review-state.json`: set `last_run.<type>` to today's date for every reviewer that ran (including meta).
- Update `reviews/README.md`: add one row to the index table per project-level review; add one line to the meta-story section summarizing the cycle (e.g., "2026-MM-DD — cycle review: <brief synthesis of the headlines>"); do NOT add an index row for the meta-review (meta lives under `reviews/meta/`).

**Ephemeral mode:** skip both updates. The ephemeral outputs are drafts only.

### 5. Report to the user

Summarize in order:
- Mode (saved or ephemeral)
- Reviewers that ran (name + filename + one-sentence headline)
- Meta-review headline and health-check summary
- Saved mode: ask whether to commit and open a single PR containing all new review files. Ephemeral mode: no commit flow — user can promote specific drafts by moving them to `reviews/` and re-running the individual command without `--ephemeral`.

**Saved mode commit flow (if approved):**
- Create branch `docs/review-cycle-YYYYMMDD`
- Commit all new review files + `.claude/review-state.json` update + `reviews/README.md` update in one commit
- Push and open a PR with a body listing each review's headline

## Design notes

- **Parallel execution** is the wall-time win. Each project-level reviewer reads similar context (specs/theses, research docs, issues) but writes distinct output. They don't interfere.
- **Meta after** is load-bearing: meta reads the files the others just wrote, so it must run sequentially. Meta in parallel with the others would miss today's batch.
- **Default = cadence-respect** makes `/review-cycle` safe to run often — it does nothing when nothing is due, rather than generating noise. `--all` is the explicit opt-in for "give me everything."
- **`--ephemeral` + `--all`** is the common rapid-development pattern: "full cycle, don't save, let me digest."
