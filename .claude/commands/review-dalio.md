---
description: Dalio-framework alignment review — checks faithful application of the big-cycle framework and what's missing from it
---

Run a Dalio-framework alignment review by spawning the `review-dalio` subagent.

Steps:

1. Spawn the agent in the foreground:

   ```
   Agent(
     subagent_type="review-dalio",
     description="Dalio-framework alignment review",
     prompt="Run a Dalio-framework review of the big-cycle-investing project per your system prompt. Write the review to reviews/YYYY-MM-DD-dalio.md (today's date). Follow the output structure exactly, including the framework-element coverage matrix. Your final message should be short: filename, one-sentence headline, matrix row summary (VERIFIED / PARTIAL / MISSING counts)."
   )
   ```

2. Verify the review file:

   ```
   ls -la reviews/$(date +%Y-%m-%d)-dalio.md
   ```

3. Update `.claude/review-state.json`: set `last_run.dalio` to today's date.

4. Update `reviews/README.md`: add the review to the index table and a line to the meta-story.

5. Report to the user:
   - Review file path (clickable)
   - Headline
   - Coverage matrix summary
   - Ask whether to commit and open a PR, or let it sit uncommitted

Do NOT commit without approval.

If approved: create `docs/review-dalio-YYYYMMDD` branch, commit the review + state + README, push, open PR with headline + matrix summary in the body.
