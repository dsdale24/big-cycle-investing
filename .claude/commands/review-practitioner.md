---
description: Practitioner review — identifies operational gaps between strategy backtest and real-world execution
---

Run a practitioner review by spawning the `review-practitioner` subagent.

Steps:

1. Spawn the agent in the foreground:

   ```
   Agent(
     subagent_type="review-practitioner",
     description="Practitioner operational-gap review",
     prompt="Run a practitioner review of the big-cycle-investing project per your system prompt. Write the review to reviews/YYYY-MM-DD-practitioner.md (today's date). Follow the output structure exactly, including the operational-readiness matrix. Your final message should be short: filename, one-sentence headline, matrix summary (counts by label)."
   )
   ```

2. Verify the review file:

   ```
   ls -la reviews/$(date +%Y-%m-%d)-practitioner.md
   ```

3. Update `.claude/review-state.json`: set `last_run.practitioner` to today's date.

4. Update `reviews/README.md`: index table + meta-story line.

5. Report to the user:
   - File path
   - Headline
   - Operational-readiness matrix summary
   - Ask whether to commit and open a PR

Do NOT commit without approval. Practitioner reviews often surface uncomfortable findings — the user may want to sit with it before committing publicly.

If approved: `docs/review-practitioner-YYYYMMDD` branch, commit, push, PR.
