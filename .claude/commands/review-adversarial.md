---
description: Adversarial project review — looks for what the project is wrong about, what's being avoided, and where evidence is weak
---

Run an adversarial project review by spawning the `review-adversarial` subagent.

Steps:

1. Spawn the agent in the foreground (the user typically wants to see the headline before deciding whether to commit and open a PR):

   ```
   Agent(
     subagent_type="review-adversarial",
     description="Adversarial project review",
     prompt="Run an adversarial review of the big-cycle-investing project per your system prompt. Write the review to reviews/YYYY-MM-DD-adversarial.md (today's date). Follow the output structure exactly. Your final message to the coordinator should be short: filename, one-sentence headline, list of finding titles (not bodies)."
   )
   ```

2. When the agent completes, verify the review file was written:

   ```
   ls -la reviews/$(date +%Y-%m-%d)-adversarial.md
   ```

3. Update `.claude/review-state.json`:
   - Set `last_run.adversarial` to today's date (YYYY-MM-DD)
   - Leave other fields unchanged

4. Update `reviews/README.md`:
   - Add the new review to the index table (bottom of file)
   - Add a one-line entry to the meta-story section

5. Report to the user:
   - The review file path (clickable)
   - The agent's one-sentence headline
   - The finding titles
   - Ask whether to (a) commit and open a PR, or (b) let it sit uncommitted while you digest it

Do NOT commit or push without user approval. The review is already a durable artifact in the working tree; git commit is a separate decision.

If the user approves commit: create a `docs/review-adversarial-YYYYMMDD` branch, commit the review file + state update + README update, push, and open a PR with a summary of the headline + finding titles in the body. Merge decision is the user's.
