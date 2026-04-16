---
description: Meta-review of the project's AI-assisted spec-driven development workflow. Audits `CLAUDE.md` + `.claude/` (the distributed workflow spec) on three layers — spec quality, implementation fidelity, and effectiveness. Writes to `reviews/YYYY-MM-DD-ai-workflow.md`. Add `--ephemeral` for draft mode (gitignored, doesn't count toward cadence or series signal).
---

Run the `review-ai-workflow` reviewer.

## Parse `$ARGUMENTS`

- `--ephemeral` — write output to `reviews/.ephemeral/YYYY-MM-DD-ai-workflow.md` (gitignored), skip `.claude/review-state.json` update, skip `reviews/README.md` update, no commit flow. Use for pulse-checks during rapid workflow evolution (e.g., right after a governance-change PR lands) without polluting the series signal.

If no flag: saved mode (default) — output to `reviews/YYYY-MM-DD-ai-workflow.md`, update cadence state, update `reviews/README.md` index + meta-story, ask user whether to commit as a PR.

## Steps

### 1. Spawn the review-ai-workflow agent

Foreground, since the coordinator needs the output before deciding whether to commit or act on findings.

Construct the output path based on mode and pass to the agent via prompt:
- Saved: `reviews/YYYY-MM-DD-ai-workflow.md`
- Ephemeral: `reviews/.ephemeral/YYYY-MM-DD-ai-workflow.md`

Agent reads CLAUDE.md + `.claude/` (the distributed workflow spec) and evidence from recent PRs and reviews; writes a dated review applying the three-layer structure (spec quality / implementation fidelity / effectiveness).

### 2. Receive the agent's final message

The agent ends with: filename, one-sentence headline, list of finding titles. Preserve that verbatim — the coordinator presents it to the user along with a read of the full review file.

### 3. State and README updates (saved mode only)

- Update `.claude/review-state.json`: set `last_run.ai-workflow` to today's date.
- Update `reviews/README.md`: add one row to the index table for the new review; add one line to the meta-story section summarizing the headline.

Ephemeral mode skips both.

### 4. Commit flow (saved mode)

Ask the user whether to commit the review as a PR (following the pattern of other periodic reviewers). If approved:
- Branch `docs/review-ai-workflow-YYYYMMDD`
- Commit the review file + state update + README update
- Push + open PR with body listing the headline and finding titles

Ephemeral mode has no commit flow; user digests the draft and optionally promotes later by moving the file and re-running without `--ephemeral`.

## Design notes

- This reviewer runs **less frequently** than project-level reviewers (adversarial, dalio). Default cadence is quarterly plus after material governance changes. The rationale: the workflow evolves more slowly than the project's substantive work; over-running this reviewer produces noise.
- Unlike `review-meta`, this reviewer audits the workflow-producing-artifacts (CLAUDE.md, `.claude/`, review-state), not the workflow-as-a-series-of-reviews. Distinct lens.
- The three-layer structure (spec quality / implementation fidelity / effectiveness) is the load-bearing discipline. A review that returns findings only in one layer is likely missing angles — push the reviewer to span all three.
