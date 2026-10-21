# /myplan — Create implementation plan

Analyze, design, and write a PLAN document. Step 2 of the embedeval 5-stage
workflow. **The PLAN file is the only persistent artifact in this workflow** —
`/execute`, `/review`, and `/wrapup` all report to screen only.

## Communication

- Direct, evidence-based, no preamble.
- Push back on unclear requirements *before* planning.
- Lead with concerns; explain *why* you agree, not just "looks good."

## Usage

```
/myplan <task-slug>
```

`<task-slug>` — short kebab-case identifier, e.g. `context-quality-mode`,
`fix-ci`, `negative-tests`. Matches the filename `plans/PLAN-<slug>.md`.

## Context

- Repo: `/home/noel/embedeval`
- PLAN destination: `plans/PLAN-<slug>.md`
- Existing plans: `plans/PLAN-*.md` — browse first, avoid duplicating prior work
- Embedeval quality gates (reference these in the PLAN's testing strategy):
  - `uv run ruff format --check src/`
  - `uv run ruff check src/`
  - `uv run mypy src/`
  - `uv run pytest tests/`
- Doc auto-sync: `uv run python scripts/sync_docs.py` (mandatory before commit
  when `cases/`, `src/`, or `tests/` changed)

## Steps

1. **Clarify scope** — confirm with user what's in and out of scope. If
   ambiguous, ask; don't guess.

2. **Prior work** — grep `plans/PLAN-*.md` and CLAUDE.md "Learned Corrections"
   for related work. Read hits; note what to reuse or avoid repeating.

3. **Code review** — Read affected modules under `src/embedeval/` and existing
   tests. Understand current implementation before designing changes.

4. **Design** — for non-trivial work, identify 2–3 approaches. Pick one with
   explicit rationale and rejected alternatives.

5. **Write the PLAN file** — `plans/PLAN-<slug>.md`, using the template below.

## PLAN template

```markdown
---
type: plan
task_slug: <slug>
status: planning
created: YYYY-MM-DD
tags: [embedeval, plan, <topic>, <tech>]
---

# PLAN: <Title>

**Task:** <one-line description>
**Created:** <YYYY-MM-DD>

## Executive summary

**TL;DR:** <one sentence>.

### What
<2–3 sentences: the core change>

### Why
<1–2 sentences: motivation>

### Key decisions
- **<Decision>:** <what> — because <reason>

### Impact
- Complexity: Low | Medium | High
- Risk: Low | Medium | High
- Files changed: ~N
- Estimated effort: X hours

## Prior work

<Related PLAN-*.md, CLAUDE.md corrections, existing patterns — with file paths.>

## Problem analysis

### Current state
<What the code does today, with file:line references.>

### Success criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

## Design

### Approach
<Chosen approach and rationale.>

### Alternatives considered
- **<Alt 1>:** <why rejected>

### Affected files
- `<path>` — <what changes>

## Implementation phases

### Phase 1: <name>
- [ ] <step>

### Phase 2: <name>
- [ ] <step>

## Testing strategy

- Unit tests: <what to add under tests/>
- Integration: <any end-to-end runs needed>
- Quality gates: `ruff format --check src/`, `ruff check src/`, `mypy src/`, `pytest tests/`
- Doc sync: run `scripts/sync_docs.py` if `cases/`/`src/`/`tests/` changed

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| <risk> | High/Med/Low | <how> |

## Review checklist (verify before /execute)

- [ ] Scope correct — nothing missing or unnecessary
- [ ] Design sound — no obvious flaws
- [ ] Affected-files list complete
- [ ] Tests cover every success criterion
- [ ] Risks identified with mitigations
```

## Output summary (screen)

After writing the PLAN:

```
Plan saved: plans/PLAN-<slug>.md
  TL;DR:      <one-liner>
  Complexity: <level>
  Risk:       <level>
  Files:      ~N
  Est effort: X hours

Review the "Review checklist" section in the PLAN before /execute <slug>.
```

## Error handling

- `plans/PLAN-<slug>.md` already exists → ask: overwrite, append, or pick a
  different slug.
- Task scope ambiguous → stop and ask; don't guess.
