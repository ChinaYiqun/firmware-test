# Benchmark Delta — 2026-04-19 (REQ-03 scope migration)

Hiloop REQ-03 asked EmbedEval to unify `strip_comments` semantics across `static.py` and `behavior.py`. This delta documents the resulting check-logic changes per the user-accepted 2026-04-19 flip policy (PLAN-hiloop-transpile-readiness §P2).

## What changed

All `"<needle>" in generated_code` substring checks were rewritten to `scoped_contains(generated_code, "<needle>", scope=...)` via `scripts/apply_scope_migration.py`. The scope argument is set per-file:

| Scope | Applied to | Behavior |
|-------|------------|----------|
| `code_only` | C / RTOS / Kconfig / device-tree / ESP-IDF / STM32 / Linux-driver refs (most TCs) | Strip `/* */` and `//` comments, keep string literals. Matches behavior.py's `strip_comments` idiom — REQ-03's intent. |
| `raw` | Yocto `.bb` refs (10 TCs) | No stripping. Bitbake uses `#` comments (not C-style), and `strip_comments` mis-strips `file://` and `git://` URLs as C line comments. |
| `raw` (explicit per-check override) | `memory-opt-004` checks that deliberately inspect a prj.conf-style comment block embedded in the reference | Per-check opt-out where the check author intentionally wanted to match inside `/* */`. |

Scope was chosen to match each check's existing semantic intent — NOT to tighten or loosen check precision.

## Files touched

- `cases/*/checks/static.py`: mechanical rewrite to `scoped_contains` on 1982 call sites across 185 files.
- `cases/*/checks/behavior.py`: same.
- `cases/memory-opt-004/checks/static.py`: 1 check manually overridden to `scope='raw'` (CONFIG comment block lookup).
- `cases/memory-opt-004/checks/behavior.py`: 2 checks manually overridden to `scope='raw'` (same reason).

## Reference validation (post-migration)

```
uv run embedeval validate --cases cases/
Validation: 185 passed, 0 failed
```

No reference solutions regressed.

## Oracle + negatives (post-migration)

```
uv run python scripts/verify_negatives_oracle.py
Total: 186 | PASS=31 FAIL=0 SKIP=155
```

Oracle PASS count rose from 30 → 31 on one previously-borderline case where the tighter `code_only` scope correctly detects a mutation the old raw-substring logic missed (precision improvement).

## Test suite

```
uv run pytest -q
1456 passed
```

All tests green. No behavioral regressions in the Python check modules themselves.

## Benchmark (Haiku / Sonnet) re-run

**Not run as part of this delta.** A paired n=3 re-run on Haiku 4.5 and Sonnet 4.6 is pending. The scope migration SHOULD produce pass@1 numbers statistically indistinguishable from the 2026-04-12/13 baseline because:

1. `code_only` is weakly more strict than the prior raw substring (doesn't match content inside comments).
2. Reference solutions pass 185/185, confirming the checks haven't drifted.
3. LLM-generated code is unlikely to rely on comment-embedded API references; if anything, some false-positive L0 pass rates may drop slightly on generations that previously matched `// TODO: use X` style comments.

Any measured delta against baseline will be recorded in a follow-up `BENCHMARK-DELTA-<date>.md` after the re-run.

## Tooling produced

- `scripts/apply_scope_migration.py` — AST-based rewrite tool with per-case scope selection and scoped_contains import injection. Idempotent; safe to re-run.

## Rollback

If a benchmark re-run surfaces unacceptable drift:

```bash
git revert <this-commit>
# OR selectively re-edit offending check files to scope='raw'.
```

## Follow-up — `linux-userspace-005` (2026-04-19, PLAN-hiloop-handoff-finalize)

Nine unscoped substring sites in `cases/embedded-linux/linux-userspace-005/checks/behavior.py` were authored in Phase B (commit `8423040`) *after* the main REQ-03 migration landed. They were migrated to `scoped_contains(..., scope='raw')` via `scripts/apply_scope_migration.py` with `_scope_for_case` extended to recognize udev rule TCs. `raw` scope matches the Yocto `.bb` precedent — udev `.rules` format uses `#` comments (not C-style) and the references embed quoted tokens like `ATTRS{idVendor}=="1d6b"` that the default `stripped` scope would empty out.

**Post-fix verification:**

```
uv run python scripts/audit_check_scope.py --strict
Total unscoped substring checks: 0 across 0 files

uv run embedeval validate --cases cases/
Validation: 219 passed, 0 failed

uv run embedeval validate --cases ../embedeval-private/cases/
Validation: 48 passed, 0 failed

uv run python scripts/verify_negatives_oracle.py
Total: 219 | PASS=77 FAIL=0 SKIP=142
```

**Verdict flips:** 0. `scope='raw'` is semantically identical to `"needle" in code`; the only change is the call-site form, which is why no reference regressed and no oracle count shifted.

**CI gate:** `.github/workflows/validate-cases.yml` now runs `audit_check_scope.py --strict` after `embedeval validate`, so the "0 unscoped sites" invariant is frozen — future TCs that regress will fail CI.
