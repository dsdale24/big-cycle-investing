---
description: Pre-merge review agent — verifies a PR against its specs before you merge
---

Run a pre-merge review of PR #$ARGUMENTS by delegating to the `review-pr` subagent (defined at `.claude/agents/review-pr.md`).

Steps:

1. Identify the relevant specs by running `gh pr view $ARGUMENTS` and checking:
   - Which files the PR touches (diff)
   - Whether the PR body mentions specific specs
   - For each modified file in `src/`, `tests/`, or `scripts/`, which spec under `specs/` governs it (see the "Current spec status" table in CLAUDE.md)

2. Spawn the `review-pr` subagent in the **foreground** (you need the verdict before deciding whether to merge):

   ```
   Agent(
     subagent_type="review-pr",
     description="Pre-merge review for PR #$ARGUMENTS",
     prompt=<<message containing PR number and the list of relevant specs>>
   )
   ```

   The agent's body has the full review prompt. Your job here is just to hand it the inputs (PR number, relevant specs) and any optional context (e.g., a commit range if the PR is multi-commit and worth reviewing commit-by-commit).

3. When the agent returns its verdict:
   - **PASS** → ask the user if they want to merge
   - **PASS-WITH-NITS** → summarize the nits and ask the user whether to merge or fix first
   - **CHANGES-REQUIRED** → summarize the blocking issues; do NOT offer to merge; either delegate a coding agent to fix or ask the user to redirect
   - **BLOCKED** → report what is blocked and ask the user how to proceed

Do NOT merge the PR yourself based on the verdict alone. The human makes the merge decision; your job is to surface the review findings.
