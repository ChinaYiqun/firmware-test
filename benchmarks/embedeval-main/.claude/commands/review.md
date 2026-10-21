# /review — Code review & quality check

Deep review of task changes. Step 4 of the embedeval 5-stage workflow.
**Reports to screen only — no ANALYSIS document.**

## Communication

- Direct, evidence-based. Cite `file:line` for every finding.
- Lead with critical issues, then warnings, then nits.
- Before analyzing, reframe as: *"Does this meet the stated requirements
  without issues?"* — counters confirmation bias toward the author's intent.
- Don't fold on pushback without new evidence.

## Usage

```
/review [task-slug]       # review files relevant to PLAN-<slug>
/review                   # review uncommitted + last commit
```

## Context

- Repo: `/home/noel/embedeval`
- PLAN (if slug given): `plans/PLAN-<slug>.md`
- Standards: `CLAUDE.md` → "Quality Gates" and "Learned Corrections"
- Quality gates to verify pass before reviewing:
  - `uv run ruff format --check src/`
  - `uv run ruff check src/`
  - `uv run mypy src/`
  - `uv run pytest tests/`

## Steps

1. **Determine scope**
   - Slug provided → Read PLAN; list "Affected files" and "Success criteria".
     Review those files plus their tests.
   - No slug → `git diff HEAD~1 -- ':!plans/'` plus uncommitted working tree.

2. **Run quality gates first** — if any fail, report and stop. Don't review on
   top of a broken build.

3. **Invoke specialized reviewers in parallel** (via `Task` tool):
   - `reviewer` — general code quality and correctness (always)
   - `walkthrough-reviewer` — trace happy path, errors, edge cases through
     changed code (when logic changed)
   - `side-effect-reviewer` — blast radius of API/contract changes (when
     exports or public APIs changed)
   - `test-quality-reviewer` — do behavioral changes have matching tests?
   - `concurrency-reviewer` — threading/locking touched?
   - `resource-lifecycle-reviewer` — FD/connection/thread lifetimes touched?

4. **Consolidate** — merge reviewer outputs, dedup, rank by severity.

## Focus areas

- Correctness: API contracts, edge cases, off-by-one, None handling
- Security: input validation, secrets, injection
- Architecture: separation, coupling, cohesion
- Tests: new behavior has matching tests (CLAUDE.md "new feature = new tests")
- Embedeval-specific — cross-check against CLAUDE.md "Learned Corrections":
  - `scoped_contains` scope argument explicit (not the default `stripped`)?
  - Run-scoped artifacts written under `run_dir/`, not `output_dir/`?
  - L1/L2 skipping correctly for non-compilable cases?
  - L4 mutation lambdas avoid hardcoding reference literals?
  - Check regex accepts API variants (k_msleep/k_sleep, printf/printk/LOG_*)?
  - Pydantic v2 uses `@computed_field` for JSON-serialized derived fields?

## Output (screen only)

```
/review <slug | recent-changes>

Quality gates
  ruff format ✓   ruff check ✓   mypy ✓   pytest ✓

Scope
  files reviewed: N
  PLAN success criteria met: N/M   <list unmet>

Findings
  CRITICAL (block merge)
    1. <file:line> — <issue> — <suggested fix>
  MAJOR
    2. <file:line> — <issue>
  MINOR / NITS
    3. <file:line> — <issue>

Verdict: APPROVED | CHANGES_REQUESTED | NEEDS_WORK
```

## Verdict handling

- **APPROVED** → proceed to `/wrapup`.
- **CHANGES_REQUESTED** → user decides: fix now, run `/execute <slug>` to
  address, or defer with explicit justification.
- **NEEDS_WORK** → block `/wrapup`; return to `/execute`.
