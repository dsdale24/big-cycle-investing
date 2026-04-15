---
description: Data-quality review — audits measurement soundness, unaudited approximations, silent look-ahead leakage
---

Run a data-quality review by spawning the `review-data-quality` subagent.

Steps:

1. Spawn the agent in the foreground:

   ```
   Agent(
     subagent_type="review-data-quality",
     description="Data-quality audit review",
     prompt="Run a data-quality review of the big-cycle-investing project per your system prompt. Write the review to reviews/YYYY-MM-DD-data-quality.md (today's date). Follow the output structure exactly, including the data-period confidence matrix. Your final message: filename, one-sentence headline, confidence matrix summary (counts by label)."
   )
   ```

2. Verify:

   ```
   ls -la reviews/$(date +%Y-%m-%d)-data-quality.md
   ```

3. Update `.claude/review-state.json`: set `last_run.data-quality` to today's date.

4. Update `reviews/README.md`: index + meta-story.

5. Report to the user:
   - File path
   - Headline
   - Confidence matrix summary
   - Ask whether to commit and open a PR

Do NOT commit without approval.

If approved: `docs/review-data-quality-YYYYMMDD` branch, commit, push, PR.
