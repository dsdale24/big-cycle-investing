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

3. The agent's report ends with an **embedded review block** (a markdown section starting with `## Pre-merge review`). Extract that block verbatim — you'll use it twice in the next steps. Do NOT paraphrase or edit it; the agent's wording is the durable record.

4. **Post the embedded block as a PR comment immediately**, regardless of verdict, so the review is visible in the PR thread before the merge decision:

   ```
   gh pr comment $ARGUMENTS --body "<embedded block contents>"
   ```

   Use a heredoc to preserve markdown formatting:

   ```
   gh pr comment $ARGUMENTS --body "$(cat <<'EOF'
   ## Pre-merge review
   ...
   EOF
   )"
   ```

   Posting before the merge decision means CHANGES-REQUIRED and BLOCKED reviews are also captured on the PR thread for the author / future readers.

5. Decide based on verdict:
   - **PASS** → ask the user if they want to merge
   - **PASS-WITH-NITS** → summarize the nits and ask the user whether to merge or fix first
   - **CHANGES-REQUIRED** → do NOT offer to merge; either delegate a coding agent to fix or ask the user to redirect. The PR comment is now visible to the author.
   - **BLOCKED** → report what is blocked and ask the user how to proceed

6. **On user's merge approval**, include the same embedded block in the merge commit body so the review is preserved in git history (PR comments live on GitHub; merge commit bodies live in the repo forever):

   ```
   gh pr merge $ARGUMENTS --merge --body "$(cat <<'EOF'
   ## Pre-merge review
   ...
   EOF
   )"
   ```

   Same block, same formatting. Two places, one source of truth.

Do NOT merge the PR yourself based on the verdict alone. The human makes the merge decision; your job is to surface the review findings and propagate the verdict to the durable artifacts (PR comment + merge commit) once they decide.
