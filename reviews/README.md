# Reviews

This directory captures periodic project reviews from different analytical lenses. Each review is a dated snapshot committed to git; the series is the signal.

## Why reviews live here

Individual reviews are snapshots. The *series* tells you whether concerns are accumulating or being addressed, which perspectives keep surfacing the same issue, and how the project's framing is drifting over time. That signal doesn't exist without durable records — so reviews are kept in the repo rather than posted as one-off artifacts.

A review is not a living document. Once written, it's frozen. Aging reveals whether concerns proved right or wrong, which is itself information. If a review needs revision, add a new one rather than editing the old.

## Reviewer types

| Reviewer | Lens | Cadence target | Agent |
|---|---|---|---|
| external | Outside perspective, no defined lens | Ad-hoc | — (human-invoked, e.g., a different Claude session) |
| adversarial | "What is this project wrong about? What evidence is weak? What's being avoided?" | Quarterly | `.claude/agents/review-adversarial.md` |
| dalio | Big-cycle framework alignment; what's missing from Dalio's taxonomy | Quarterly | `.claude/agents/review-dalio.md` |
| practitioner | "If I put money in this today, what would actually happen?" | Before strategy → `settled` | `.claude/agents/review-practitioner.md` |
| data-quality | Measurement soundness, unaudited approximations | After significant splicing / indicator work | `.claude/agents/review-data-quality.md` |
| meta | Evolution across prior reviews; repeated concerns vs. addressed | Annually, or after 3+ reviews | `.claude/agents/review-meta.md` |

Slash commands invoke each agent: `/review-adversarial`, `/review-dalio`, `/review-practitioner`, `/review-data-quality`, `/review-meta`.

Cadence is not enforced by automation. It's tracked in `.claude/review-state.json`; a session-start check may surface a reminder if a category is overdue. A review done because cron fired it has no teeth; the reminder is the automation lever.

## File naming

`YYYY-MM-DD-<type>.md` — e.g., `2026-04-15-external.md`, `2026-07-20-adversarial.md`.

If multiple reviews of the same type land on the same day (rare), suffix with `-N`: `2026-07-20-adversarial-2.md`.

Meta-reviews live under `reviews/meta/` to keep the top-level chronology clean.

## Review output structure (shared across types)

Every review follows the same section ordering, so the series is comparable over time:

1. **Headline** — one-sentence takeaway
2. **What's working** — 2-4 bullets; lens-specific strengths
3. **Findings** — numbered; each finding names what was found, where, and why it matters
4. **The central question / tension / fork** — the big thing this lens reveals (may be absent if the review is clean)
5. **Recommendations** — optional; concrete next steps the reviewer suggests
6. **Questions worth sitting with** — optional; open questions the reviewer can't resolve

Each reviewer type may emphasize different sections based on its lens but keeps the ordering.

## Meta-story (update when new reviews land)

_A running narrative of what the review series is telling us about project evolution. Update after each new review lands; keep it to 1-2 sentences per review._

- **2026-04-15 — external (human-invoked Claude session):** Identified central tension between transition-scale thesis and cyclical-scale operationalization. Surfaced the need for multi-perspective review infrastructure (this directory). Five concrete findings filed as issues #60–#64; resulting architecture design question tracked as #65.

## Index of reviews

| Date | Type | Reviewer | File |
|---|---|---|---|
| 2026-04-15 | external | Outside Claude session | [2026-04-15.md](2026-04-15.md) |
