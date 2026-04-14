---
description: Pre-merge review agent — verifies a PR against its specs before you merge
---

Run a pre-merge review of PR #$ARGUMENTS using the canonical prompt at
`docs/review_agent_prompt.md`.

Steps to take:

1. Read `docs/review_agent_prompt.md` so you know the current prompt
   (it may have been tuned since the last review).

2. Identify the relevant specs by running `gh pr view $ARGUMENTS` and
   checking:
   - Which files the PR touches (diff)
   - Whether the PR body mentions specific specs
   - For each modified file in `src/` or `tests/`, which `docs/specs/*.md`
     governs it (see the "Current spec status" table in CLAUDE.md)

3. Spawn a foreground general-purpose agent with the prompt from
   `docs/review_agent_prompt.md`, filling in:
   - `<PR_NUMBER>` = $ARGUMENTS
   - `<RELEVANT_SPECS>` = the specs identified in step 2

4. When the agent returns its verdict:
   - PASS → ask the user if they want to merge
   - PASS-WITH-NITS → summarize the nits and ask the user if they want to
     merge or fix first
   - CHANGES-REQUIRED → summarize the blocking issues; do NOT offer to
     merge; delegate a coding agent to fix or ask the user to redirect
   - BLOCKED → report what's blocked and ask the user how to proceed

Do NOT merge the PR yourself based on the verdict alone. The human makes
the merge decision; your job is to surface the review findings.
