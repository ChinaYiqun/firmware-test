# /wrapup — Finalize and commit

Final validation, docs sync, and commit. Step 5 of the embedeval 5-stage
workflow. **Reports to screen only — no WRAPUP/LEARNING document.**

## Communication

- Direct, evidence-based.
- Never commit on a red gate. Never push without explicit user confirmation.
- Report what actually happened — don't paper over a skipped step.

## Usage

```
/wrapup [task-slug]
```

Slug is optional — used in commit message if provided; inferred from the PLAN
referenced by the diff otherwise.

## Context

- Repo: `/home/noel/embedeval`
- PLAN (if slug given): `plans/PLAN-<slug>.md`
- Pre-commit hook at `.githooks/pre-commit` mirrors the ruff subset. Activate
  per clone: `git config core.hooksPath .githooks`. Never skip with
  `--no-verify`.
- Quality gates — MANDATORY, all must pass:
  - `uv run ruff format --check src/`
  - `uv run ruff check src/`
  - `uv run mypy src/`
  - `uv run pytest tests/ -v --tb=short`
- Doc auto-sync — MANDATORY when `cases/`, `src/`, or `tests/` changed:
  - `uv run python scripts/sync_docs.py`

## Steps

1. **Preflight**
   - `git status --short` — show uncommitted changes.
   - Confirm branch. Warn if on `main` directly without the agent-branch
     convention: `agent/<slug>/<YYYY-MM-DD>`.

2. **Full quality gate**
   - Run all four gates sequentially. Stop on first failure; report exact
     error and exit. Do not commit.

3. **Doc auto-sync**
   - If the diff (staged + unstaged + last commit vs HEAD~1) touches `cases/`,
     `src/`, or `tests/`:
     - Run `uv run python scripts/sync_docs.py`.
     - If `README.md` or `docs/METHODOLOGY.md` changed, stage them.
   - If the script prints "already up to date", no action.

4. **Self-review diff**
   - Print `git diff --stat` for staged + unstaged.
   - Sanity-check against CLAUDE.md "Quality Gates" #1 (API contracts,
     redundant calls, edge cases).
   - Ask user to confirm before committing.

5. **Refresh test tracker (if `cases/` changed)**
   ```bash
   if git diff --name-only HEAD~1 -- cases/ | grep -q .; then
       uv run embedeval refresh-tracker --cases cases/ --results results/
   fi
   ```

6. **Commit**
   - Stage only task-relevant files; never `git add -A`.
   - Commit message (HEREDOC to preserve formatting):
     ```
     <type>(<scope>): <summary>

     <body — focus on the *why*, not the *what*>

     Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
     ```
   - Let the pre-commit hook run. If it fails, fix the root cause and create a
     *new* commit — never `--amend` after a failed hook.

7. **Push — only if user explicitly confirms**
   - `git push origin <branch>`. Do not assume prior push authorization
     extends to this commit.

8. **CLAUDE.md corrections (optional)**
   - If this task surfaced a repeatable mistake, append to CLAUDE.md
     "Learned Corrections" → `### 2026`:
     ```
     - YYYY-MM-DD: [embedeval] <mistake> — <correct approach>
     ```

## Output (screen only)

```
/wrapup <slug>

Quality gate
  ruff format --check src/  PASS
  ruff check src/           PASS
  mypy src/                 PASS
  pytest tests/             PASS (N passed, M skipped)

Doc sync
  scripts/sync_docs.py      updated README.md + docs/METHODOLOGY.md
                          | already in sync
                          | N/A (no cases/src/tests changes)

Diff summary
  <git diff --stat output>

Commit <sha>: <subject>
Push:         pushed to origin/<branch> | pending user confirmation | skipped (user)
CLAUDE.md:    added 1 correction | none needed
```

## Error handling

- Any quality gate fails → stop; do not commit.
- `sync_docs.py` fails → stop; do not commit.
- Pre-commit hook blocks commit → fix underlying issue; **never** use
  `--no-verify`.
- User declines push → report "skipped (user)"; leave commit local.
- Accidentally staged secret (.env, credentials.json, large binaries) → unstage
  and warn. Never commit secrets.
