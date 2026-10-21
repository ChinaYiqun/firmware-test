# /execute — Implement the PLAN

Implement the PLAN with continuous verification. Step 3 of the embedeval
5-stage workflow. **Reports to screen only — no SESSION document.**

## Communication

- Direct, evidence-based, no preamble.
- Never fabricate progress. Say when a step fails.
- Lead with blockers before claiming success.

## Usage

```
/execute <task-slug>
```

Requires `plans/PLAN-<slug>.md` produced by `/myplan`.

## Context

- Repo: `/home/noel/embedeval`
- PLAN source: `plans/PLAN-<slug>.md`
- Quality gates (run between phases and before handoff):
  - `uv run ruff format --check src/`
  - `uv run ruff check src/`
  - `uv run mypy src/`
  - `uv run pytest tests/`
- Doc auto-sync (mandatory if `cases/`/`src/`/`tests/` changed before commit):
  `uv run python scripts/sync_docs.py`
- Pre-commit hook at `.githooks/pre-commit` runs the ruff subset; never bypass
  with `--no-verify`.

## Steps

1. **Load PLAN** — Read `plans/PLAN-<slug>.md`. If missing, error: user must
   run `/myplan <slug>` first.

2. **Confirm scope** — echo TL;DR and success criteria. Stop if anything is
   still ambiguous — ask, don't guess.

3. **Phase-by-phase implementation** — for each phase in the PLAN:
   a. State the phase goal in one line.
   b. Apply code changes with Edit/Write — never blind-append. Read before edit.
   c. Run the relevant quality-gate subset (minimum: `ruff check src/` and the
      affected `pytest tests/<module>`).
   d. Report outcome: files changed, tests added, gate result.
   e. If blocked ≥ 2 attempts: stop and escalate (ask user, or delegate to a
      specialized agent). Do **not** push around a block with `--no-verify`,
      weakened tests, or skipped steps.

4. **Full quality gate before handoff** — run all four gates and `sync_docs.py`
   if applicable. Fail fast; don't hide a red gate behind a summary.

5. **Update PLAN checkboxes** — tick implementation-phase items that are now
   done. (This is the only file modification `/execute` makes outside `src/`,
   `tests/`, and `cases/`.)

## Agent delegation

Delegate when useful (parallel where independent):
- `coder` — multi-file refactors
- `tester` — author or verify tests
- `walkthrough-reviewer` — trace new logic scenarios
- `stuck` — blocked ≥ 2 attempts

## Output (screen only)

```
/execute <slug> — summary

Phases
  1. <name>             done | skipped | blocked
     files: <list>
     gate: ruff ✓  mypy ✓  pytest ✓ (N tests)
  2. <name>             done
     ...

Full quality gate
  ruff format --check src/  : PASS | FAIL
  ruff check src/           : PASS | FAIL
  mypy src/                 : PASS | FAIL
  pytest tests/             : PASS (N passed, M skipped) | FAIL
  sync_docs.py              : updated | in sync | N/A

Success criteria
  <N>/<M> met — <list unmet>

Blockers: <none | list>

Ready for /review <slug>.
```

## Error handling

- Quality gate fails → stop, report exact error, propose a fix. Do not skip or
  mute the gate.
- Test added but fails → do **not** weaken the test; investigate root cause.
- PLAN contradicts reality → stop and reconcile with user before proceeding.
