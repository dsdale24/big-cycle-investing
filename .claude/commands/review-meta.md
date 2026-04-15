---
description: Meta-review — reads the entire reviews/ history and reports on the evolution of the series (repeated concerns, addressed concerns, framing drift). Add --ephemeral for draft mode (gitignored).
---

Run a meta-review by spawning the `review-meta` subagent.

## Modes

- **Default (saved):** written to `reviews/meta/YYYY-MM-DD-meta.md`.
- **`--ephemeral`:** written to `reviews/.ephemeral/meta/YYYY-MM-DD-meta.md` (gitignored).

Check `$ARGUMENTS` for `--ephemeral` before starting.

## Pre-flight (both modes)

Check that enough reviews exist to produce a meaningful meta-review:

```
ls reviews/*.md 2>/dev/null | wc -l
```

If fewer than 3 reviews exist, warn the user that meta-review output will be thin and ask whether to proceed. Meta-review on a 2-review series is just a summary; the pattern-finding value requires more history.

## Steps (saved mode)

1. Spawn the agent in the foreground:

   ```
   Agent(
     subagent_type="review-meta",
     description="Meta-review of review series",
     prompt="Run a meta-review per your system prompt. Write to reviews/meta/YYYY-MM-DD-meta.md (today's date). Read only files in reviews/ (skip reviews/.ephemeral/ — those are gitignored drafts that don't count toward the series signal). Follow output structure exactly, including the series-level health check. Final message: filename, one-sentence headline, health check summary (4 dimensions, one label each)."
   )
   ```

2. Verify: `ls -la reviews/meta/$(date +%Y-%m-%d)-meta.md`

3. Update `.claude/review-state.json`: set `last_run.meta` to today's date.

4. Update `reviews/README.md`: add a line to the meta-story section; no index-table entry (meta-reviews live under reviews/meta/).

5. Report: file path, headline, health check summary. Ask about commit.

Do NOT commit without approval. Meta-reviews carry more weight because they reason across the full series; the user may want extended time to digest.

If approved: `docs/review-meta-YYYYMMDD` branch, commit, push, PR.

## Steps (ephemeral mode)

1. `mkdir -p reviews/.ephemeral/meta`

2. Spawn with ephemeral output path:

   ```
   Agent(
     subagent_type="review-meta",
     description="Meta-review (ephemeral)",
     prompt="Run a meta-review per your system prompt. Write to reviews/.ephemeral/meta/YYYY-MM-DD-meta.md (today's date). Read only files in reviews/ (skip reviews/.ephemeral/). Follow output structure exactly. Final message: filename, headline, health check summary."
   )
   ```

3. Verify: `ls -la reviews/.ephemeral/meta/$(date +%Y-%m-%d)-meta.md`

4. Do NOT update state or README.

5. Report file path (gitignored), headline, health check summary.

No commit flow in ephemeral mode.
