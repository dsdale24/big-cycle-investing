---
description: Dalio-framework alignment review — checks faithful application of the big-cycle framework and what's missing from it. Add --ephemeral for draft mode (gitignored).
---

Run a Dalio-framework alignment review by spawning the `review-dalio` subagent.

## Modes

- **Default (saved):** written to `reviews/YYYY-MM-DD-dalio.md`, committed, counts toward the series.
- **`--ephemeral`:** written to `reviews/.ephemeral/YYYY-MM-DD-dalio.md` (gitignored). No state update, no README update, no commit flow.

Check `$ARGUMENTS` for `--ephemeral` before starting.

## Steps (saved mode)

1. Spawn the agent in the foreground:

   ```
   Agent(
     subagent_type="review-dalio",
     description="Dalio-framework alignment review",
     prompt="Run a Dalio-framework review of the big-cycle-investing project per your system prompt. Write the review to reviews/YYYY-MM-DD-dalio.md (today's date). Follow the output structure exactly, including the framework-element coverage matrix. Your final message should be short: filename, one-sentence headline, matrix row summary (VERIFIED / PARTIAL / MISSING counts)."
   )
   ```

2. Verify: `ls -la reviews/$(date +%Y-%m-%d)-dalio.md`

3. Update `.claude/review-state.json`: set `last_run.dalio` to today's date.

4. Update `reviews/README.md`: add the review to the index table and a line to the meta-story.

5. Report to the user: file path, headline, matrix summary. Ask about commit.

Do NOT commit without approval.

If approved: create `docs/review-dalio-YYYYMMDD` branch, commit the review + state + README, push, open PR.

## Steps (ephemeral mode)

1. `mkdir -p reviews/.ephemeral`

2. Spawn the agent with ephemeral output path:

   ```
   Agent(
     subagent_type="review-dalio",
     description="Dalio-framework review (ephemeral)",
     prompt="Run a Dalio-framework review per your system prompt. Write to reviews/.ephemeral/YYYY-MM-DD-dalio.md (today's date). Follow output structure exactly. Final message: filename, one-sentence headline, matrix row summary."
   )
   ```

3. Verify: `ls -la reviews/.ephemeral/$(date +%Y-%m-%d)-dalio.md`

4. Do NOT update `.claude/review-state.json` or `reviews/README.md`.

5. Report file path (gitignored), headline, matrix summary. Note: to promote, move to `reviews/` and update state/README manually.

No commit flow in ephemeral mode.
