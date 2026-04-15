---
description: Meta-review — reads the entire reviews/ history and reports on the evolution of the series (repeated concerns, addressed concerns, framing drift)
---

Run a meta-review by spawning the `review-meta` subagent.

Steps:

1. First check that enough reviews exist to produce a meaningful meta-review:

   ```
   ls reviews/*.md 2>/dev/null | wc -l
   ```

   If fewer than 3 reviews exist, warn the user that meta-review output will be thin and ask whether to proceed. Meta-review on a 2-review series is just a summary; the pattern-finding value requires more history.

2. Spawn the agent in the foreground:

   ```
   Agent(
     subagent_type="review-meta",
     description="Meta-review of review series",
     prompt="Run a meta-review of the big-cycle-investing reviews series per your system prompt. Write the review to reviews/meta/YYYY-MM-DD-meta.md (today's date). Follow the output structure exactly, including the series-level health check. Your final message: filename, one-sentence headline, health check summary (4 dimensions, one label each)."
   )
   ```

3. Verify:

   ```
   ls -la reviews/meta/$(date +%Y-%m-%d)-meta.md
   ```

4. Update `.claude/review-state.json`: set `last_run.meta` to today's date.

5. Update `reviews/README.md`: add a line to the meta-story section referring to the meta-review; no index-table entry needed (meta-reviews live under reviews/meta/, not the main chronology).

6. Report to the user:
   - File path
   - Headline
   - Health check summary
   - Ask whether to commit and open a PR

Do NOT commit without approval. Meta-reviews carry more weight because they reason across the full series; the user may want extended time to digest.

If approved: `docs/review-meta-YYYYMMDD` branch, commit, push, PR.
