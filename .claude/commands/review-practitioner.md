---
description: Practitioner review — identifies operational gaps between strategy backtest and real-world execution. Add --ephemeral for draft mode (gitignored).
---

Run a practitioner review by spawning the `review-practitioner` subagent.

## Modes

- **Default (saved):** written to `reviews/YYYY-MM-DD-practitioner.md`.
- **`--ephemeral`:** written to `reviews/.ephemeral/YYYY-MM-DD-practitioner.md` (gitignored).

Check `$ARGUMENTS` for `--ephemeral` before starting.

## Steps (saved mode)

1. Spawn the agent in the foreground:

   ```
   Agent(
     subagent_type="review-practitioner",
     description="Practitioner operational-gap review",
     prompt="Run a practitioner review per your system prompt. Write to reviews/YYYY-MM-DD-practitioner.md (today's date). Follow output structure exactly, including the operational-readiness matrix. Final message: filename, one-sentence headline, matrix summary (counts by label)."
   )
   ```

2. Verify: `ls -la reviews/$(date +%Y-%m-%d)-practitioner.md`

3. Update `.claude/review-state.json`: set `last_run.practitioner` to today's date.

4. Update `reviews/README.md`: index table + meta-story line.

5. Report: file path, headline, matrix summary. Ask about commit.

Do NOT commit without approval. Practitioner reviews often surface uncomfortable findings — the user may want to sit with it before committing publicly.

If approved: `docs/review-practitioner-YYYYMMDD` branch, commit, push, PR.

## Steps (ephemeral mode)

1. `mkdir -p reviews/.ephemeral`

2. Spawn with ephemeral output path:

   ```
   Agent(
     subagent_type="review-practitioner",
     description="Practitioner review (ephemeral)",
     prompt="Run a practitioner review per your system prompt. Write to reviews/.ephemeral/YYYY-MM-DD-practitioner.md (today's date). Follow output structure exactly. Final message: filename, headline, matrix summary."
   )
   ```

3. Verify: `ls -la reviews/.ephemeral/$(date +%Y-%m-%d)-practitioner.md`

4. Do NOT update state or README.

5. Report file path (gitignored), headline, matrix summary.

No commit flow in ephemeral mode.
