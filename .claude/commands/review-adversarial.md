---
description: Adversarial project review — looks for what the project is wrong about, what's being avoided, and where evidence is weak. Add --ephemeral for draft mode (gitignored, doesn't count toward cadence or series signal).
---

Run an adversarial project review by spawning the `review-adversarial` subagent.

## Modes

- **Default (saved):** review is written to `reviews/YYYY-MM-DD-adversarial.md`, committed to the historical record, counts toward the meta-review series, updates cadence state.
- **`--ephemeral`:** review is written to `reviews/.ephemeral/YYYY-MM-DD-adversarial.md` (gitignored). Does NOT update state, does NOT update README, does NOT offer a commit flow. Use during rapid development when you want a pulse-check without polluting the series. User can promote to saved later by moving the file to `reviews/` and running the state/README update manually.

Check `$ARGUMENTS` for `--ephemeral` before starting.

## Steps (saved mode)

1. Spawn the agent in the foreground:

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

## Steps (ephemeral mode)

1. Ensure `reviews/.ephemeral/` exists: `mkdir -p reviews/.ephemeral` (the directory is gitignored).

2. Spawn the agent in the foreground with an ephemeral output path:

   ```
   Agent(
     subagent_type="review-adversarial",
     description="Adversarial project review (ephemeral)",
     prompt="Run an adversarial review of the big-cycle-investing project per your system prompt. Write the review to reviews/.ephemeral/YYYY-MM-DD-adversarial.md (today's date). Follow the output structure exactly. Your final message: filename, one-sentence headline, finding titles."
   )
   ```

3. Verify the file exists: `ls -la reviews/.ephemeral/$(date +%Y-%m-%d)-adversarial.md`

4. Do NOT update `.claude/review-state.json`. Ephemeral runs don't count against cadence.

5. Do NOT update `reviews/README.md`. Ephemeral reviews are not part of the series.

6. Report to the user:
   - The file path (in `reviews/.ephemeral/`, gitignored, not visible to the meta reviewer)
   - The headline
   - The finding titles
   - Note: to promote this to a saved review, move it to `reviews/` and run the state/README update manually (or re-run without `--ephemeral`).

Do NOT offer a commit flow in ephemeral mode. The file is gitignored on purpose.
