---
description: Scaffold a new stabilizing spec for a component. Invoke before creating a `stable/` branch for work touching `src/`, `tests/`, or `configs/`. Opens the `create-spec` skill, which provides the canonical sections, 8 principles, MUST-checkable rule, inheritance-framing guidance, and template skeleton. Produces a scaffolded spec file at the target path.
---

Invoke the `create-spec` skill to scaffold a new stabilizing spec.

Pass any of these as `$ARGUMENTS` if the coordinator has them at hand; the skill will ask for what's missing:

- Component name (kebab-case — e.g., `uk_data_pipeline`, `regime_classifier`)
- Target path (e.g., `specs/regime_classifier.md` or `specs/data_pipeline/uk.md`)
- Upstream exploration (branch name like `explore/phase2/regime-research`, or research-note path like `docs/research/regime_scoring_comparison.md`). If there is no upstream exploration, the skill requires explicit acknowledgment per CLAUDE.md Workflow-section delegation-time rule.
- Baseline spec for extension specs (e.g., `specs/data_pipeline/us.md` as baseline for country pipelines)
- Related issue numbers (parent issue, known follow-ups)

The skill's full procedure is in `.claude/skills/create-spec/SKILL.md`. The output is a scaffolded file at the target path with canonical sections present and `[bracket]` placeholders where coordinator judgment is required.

## After the skill finishes

1. Review the scaffolded file and edit placeholders
2. If this is a new branch: `git checkout -b stable/<phase>/<feature>`
3. Commit the spec as the first commit on the branch
4. Delegate implementation to a coding agent with the spec as the sole contract — delegation prompt must state branch rationale, cite upstream exploration (or acknowledge its absence), and require the `Co-Authored-By: Claude` trailer per CLAUDE.md

## Do NOT use `/create-spec` for

- Editing an existing spec (just edit the file)
- Writing a thesis under `specs/theses/` (different schema — see `specs/theses/README.md`)
- Writing an agent prompt under `.claude/agents/` (operational, not a component contract)

For small spec updates, edit directly. For thesis authoring, follow the thesis-file schema. For agent prompts, see existing examples in `.claude/agents/`.
