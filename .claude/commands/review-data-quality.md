---
description: Data-quality review — audits measurement soundness, unaudited approximations, silent look-ahead leakage. Add --ephemeral for draft mode (gitignored).
---

Run a data-quality review by spawning the `review-data-quality` subagent.

## Modes

- **Default (saved):** written to `reviews/YYYY-MM-DD-data-quality.md`.
- **`--ephemeral`:** written to `reviews/.ephemeral/YYYY-MM-DD-data-quality.md` (gitignored).

Check `$ARGUMENTS` for `--ephemeral` before starting.

## Steps (saved mode)

1. Spawn the agent in the foreground:

   ```
   Agent(
     subagent_type="review-data-quality",
     description="Data-quality audit review",
     prompt="Run a data-quality review per your system prompt. Write to reviews/YYYY-MM-DD-data-quality.md (today's date). Follow output structure exactly, including the data-period confidence matrix. Final message: filename, one-sentence headline, confidence matrix summary (counts by label)."
   )
   ```

2. Verify: `ls -la reviews/$(date +%Y-%m-%d)-data-quality.md`

3. Update `.claude/review-state.json`: set `last_run.data-quality` to today's date.

4. Update `reviews/README.md`: index + meta-story.

5. Report: file path, headline, matrix summary. Ask about commit.

Do NOT commit without approval.

If approved: `docs/review-data-quality-YYYYMMDD` branch, commit, push, PR.

## Steps (ephemeral mode)

1. `mkdir -p reviews/.ephemeral`

2. Spawn with ephemeral output path:

   ```
   Agent(
     subagent_type="review-data-quality",
     description="Data-quality review (ephemeral)",
     prompt="Run a data-quality review per your system prompt. Write to reviews/.ephemeral/YYYY-MM-DD-data-quality.md (today's date). Follow output structure exactly. Final message: filename, headline, matrix summary."
   )
   ```

3. Verify: `ls -la reviews/.ephemeral/$(date +%Y-%m-%d)-data-quality.md`

4. Do NOT update state or README.

5. Report file path (gitignored), headline, matrix summary.

No commit flow in ephemeral mode.
