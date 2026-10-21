---
type: review
project: embedeval
task_slug: hiloop-requests-response
status: changes_applied
created: 2026-04-19
tags: [embedeval, review, python, benchmark, hiloop]
related:
  - "[[plans/PLAN-hiloop-requests-response]]"
summary: "B review — 0 critical, 4 warnings (all fixed 2026-04-19), 4 suggestions — APPROVED"
---

> **Resolution (2026-04-19):** W1, W2, W3, W4 all fixed. Verification: `pytest` 1456 passed, `embedeval validate` 185/185, oracle PASS=31. Suggestions S1–S4 left as follow-ups.
>
> - **W1 fixed:** `per_check_metrics.json` now written to `run_dir/per_check_metrics.json` after `generate_run_archive()` runs. Markdown stays at flat root.
> - **W2 fixed:** 24 behavior.py files consolidated — `scoped_contains` folded into the existing `from embedeval.check_utils import (...)` tuple via one-shot script.
> - **W3 fixed:** `verify_negatives_oracle.py` computes `exit_code` eagerly; coverage-gate and oracle failures no longer mask each other in CI logs.
> - **W4 fixed:** `test_empty_results` now asserts file creation, schema_version == 1, empty rows array, and `generated` field presence.

# REVIEW: Hiloop REQ-01..REQ-06 Implementation

**Project:** embedeval
**Date:** 2026-04-19
**Scope:** reporter.py, cli.py, apply_scope_migration.py, verify_negatives_oracle.py, tests/test_reporter.py, tests/test_coverage_validator.py, docs/CONTRIBUTING.md, plans/coverage-grandfather.txt
**Analysis Mode:** Deep (probing all 9 stated concerns)

---

## Summary

**Grade:** B
**Critical Issues:** 0
**Warnings:** 4
**Suggestions:** 4

The implementation is generally sound. REQ-02..REQ-06 are all functionally correct. The mechanical REQ-03 migration (1982 spans) is clean — `uv run embedeval validate` confirming 185/185 is the right gate. The four warnings below are not blockers but two of them affect Hiloop's artifact consumption contract directly.

---

## Detailed Findings

### Warnings (Should Fix)

#### W1: `per_check_metrics.json` written to `output_dir/` not `output_dir/runs/<run_id>/`
**File:** `src/embedeval/cli.py:490-494`
**Category:** Correctness (API contract drift)

**Problem:**
The PLAN (line 168) and the REQ-04 checklist (line 337) both specify:
`results/<run_id>/per_check_metrics.json`. The implementation writes it to `output_dir/per_check_metrics.json` — the flat root, not under `runs/<dir>/`. Two consequences:

1. Subsequent runs overwrite the file. An n=3 run (n1, n2, n3) produces one JSON that reflects only n3's `results_by_model`.
2. Hiloop's `interop.leaderboard` can't correlate the per-check file with a specific run archive via path convention. The `run_id` field inside the JSON doesn't help if the consumer traverses `runs/*/per_check_metrics.json`.

`LEADERBOARD_PER_CHECK.md` has the same placement issue but is less machine-critical.

**Current code:**
```python
generate_per_check_metrics(
    results_by_model,
    output_json=output_dir / "per_check_metrics.json",
    output_md=output_dir / "LEADERBOARD_PER_CHECK.md",
    run_id=run_id,
)
```

**Fixed code:**
```python
# Write run-scoped artifact AFTER run_dir is known.
# run_dir is already created by generate_run_archive above.
generate_per_check_metrics(
    results_by_model,
    output_json=run_dir / "per_check_metrics.json",
    output_md=output_dir / "LEADERBOARD_PER_CHECK.md",  # keep flat MD for humans
    run_id=run_id,
)
```

This requires moving the `generate_per_check_metrics` call to after `run_dir = generate_run_archive(...)`. The `run_dir` variable is available at line 497, so the reorder is safe.

---

#### W2: Duplicate `from embedeval.check_utils import scoped_contains` in 24 files
**File:** `scripts/apply_scope_migration.py:200-211` (injector logic)
**Category:** Correctness (import deduplication gap)

**Problem:**
`_inject_import` checks for an exact single-line match (`if new_import in source`) but does not detect the case where `scoped_contains` is already present inside an existing **multi-line** import tuple. For 24 behavior.py files that had `from embedeval.check_utils import (check_no_cross_platform_apis, ...)`, the AST `_Finder` correctly sets `has_check_utils_import=True` but `has_scoped_contains_import=False` (because `scoped_contains` was not in their import list). The injector then adds a second standalone `from embedeval.check_utils import scoped_contains` line, producing:

```python
from embedeval.check_utils import (
    check_no_cross_platform_apis,
    strip_comments,
)
from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains  # <-- injected duplicate
```

Confirmed in `/home/noel/embedeval/cases/isr-concurrency-003/checks/behavior.py` (and 23 other files). Python silently accepts this — the second import is a no-op — but it:
- Violates the project's single-import-per-module convention
- Will confuse future `apply_scope_migration.py` re-runs (the `has_scoped_contains_import` flag won't prevent re-injection on a second apply since the early-exit `if new_import in source` will find it)
- Will be flagged by linting tools

**Fixed code for `_inject_import`:** The check should also parse the existing multi-line import to see if `scoped_contains` is among the names, or simply check the AST `has_scoped_contains_import` flag before entering the injector:

In `rewrite_file`:
```python
# Change from:
if finder.spans and not finder.has_scoped_contains_import:
    new_source = _inject_import(new_source, finder.has_check_utils_import)
```
The existing guard is correct — the bug is that `_Finder.visit_ImportFrom` does NOT set `has_scoped_contains_import=True` when `scoped_contains` appears in a `from embedeval.check_utils import (...)` multi-line tuple. The fix:

```python
def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
    if node.module == "embedeval.check_utils":
        self.has_check_utils_import = True
        for alias in node.names:
            if alias.name == "scoped_contains":
                self.has_scoped_contains_import = True
                break  # already correct — this IS the existing logic
    self.generic_visit(node)
```

Wait — the existing `_Finder` already checks `n.name == "scoped_contains"`. The bug is that the 24 files pre-migration did NOT have `scoped_contains` in their tuple, so the flag was legitimately False. The injector correctly added it. The current state IS the expected post-migration state. The issue is the code now has redundant imports, not a bug in the migrator logic.

**Actual fix needed:** For the 24 existing files, consolidate the redundant imports. The migrator is a one-time tool, but the resulting files should be cleaned. Example for `isr-concurrency-003/checks/behavior.py`:

```python
# Before (current state):
from embedeval.check_utils import (
    check_no_cross_platform_apis,
    check_no_isr_forbidden,
    find_isr_bodies,
    strip_comments,
)
from embedeval.check_utils import scoped_contains  # injected

# After:
from embedeval.check_utils import (
    check_no_cross_platform_apis,
    check_no_isr_forbidden,
    find_isr_bodies,
    scoped_contains,
    strip_comments,
)
```

This is a cosmetic but measurable debt across 24 files in the public repo. Since `apply_scope_migration.py` won't be re-run in normal workflow, a one-time cleanup script or manual pass is needed.

---

#### W3: Oracle failure masked by coverage failure when both occur simultaneously
**File:** `scripts/verify_negatives_oracle.py:361-371`
**Category:** Correctness (error reporting ambiguity)

**Problem:**
The exit-code logic has an ordering issue. When `--strict-coverage` is passed and BOTH oracle failures AND non-grandfathered coverage gaps exist in the same run:

```python
if args.strict_coverage:
    blocking = [r for r in coverage_below if r.case_id not in grandfather]
    if blocking:
        print("STRICT COVERAGE: ...", file=sys.stderr)
        return 1  # <-- early exit, never reaches oracle fail check

return 1 if failed > 0 else 0
```

The `STRICT COVERAGE` stderr message is printed but the FAIL case text was already printed to stdout earlier. CI will see exit 1, parse `STRICT COVERAGE` from stderr, and conclude it's a coverage gate failure — not an oracle failure. If the coverage gate passes (e.g., all low-coverage TCs are grandfathered), exit falls through to `return 1 if failed > 0 else 0` and the oracle failure surfaces correctly.

The problem isn't the exit code (both return 1) but that the distinction disappears in CI log parsing when both conditions hold.

**Fixed code:**
```python
exit_code = 1 if failed > 0 else 0

if args.strict_coverage:
    blocking = [r for r in coverage_below if r.case_id not in grandfather]
    if blocking:
        if not args.quiet:
            print(
                f"\nSTRICT COVERAGE: {len(blocking)} non-grandfathered TC(s) below threshold",
                file=sys.stderr,
            )
        exit_code = 1  # mark but don't early-return

return exit_code
```

This ensures both failure messages appear before exit when both conditions hold, and CI can grep stdout for `FAIL` and stderr for `STRICT COVERAGE` independently.

---

#### W4: `test_empty_results` does not assert file creation or JSON validity
**File:** `tests/test_reporter.py:542-546`
**Category:** Test coverage gap

**Problem:**
The test only checks the return value:
```python
def test_empty_results(self, tmp_path: Path) -> None:
    rows = generate_per_check_metrics(
        {"sonnet": []}, output_json=tmp_path / "empty.json"
    )
    assert rows == []
```

It does not verify that `empty.json` was actually created with valid JSON and the correct schema structure. If `generate_per_check_metrics` raised an exception before writing (e.g., a future `if not rows: return rows` short-circuit), this test would still pass (the exception would propagate). The file creation path is the contract Hiloop depends on.

**Fixed code:**
```python
def test_empty_results(self, tmp_path: Path) -> None:
    import json as _json
    out = tmp_path / "empty.json"
    rows = generate_per_check_metrics({"sonnet": []}, output_json=out)
    assert rows == []
    # Verify the file is created and valid even with no rows.
    assert out.exists(), "JSON file must be written even when rows is empty"
    data = _json.loads(out.read_text())
    assert data["schema_version"] == 1
    assert data["rows"] == []
    assert "generated" in data
```

---

### Suggestions (Nice to Have)

#### S1: `TestGrandfatherList.test_loads_from_plans_file` uses `>=` — won't detect removals
**File:** `tests/test_coverage_validator.py:135`

`assert len(gf) >= 30` passes if someone adds entries (fine) but also passes if entries are reduced to 30 (from 37 currently). If removing a grandfather entry is an intended workflow step (a TC graduates after getting negatives.py), silently passing the test gives false confidence. Consider pinning to the exact count at the time this gate was introduced:

```python
assert len(gf) >= 30  # current: change to:
# Grandfather list should only shrink as TCs get negatives.py authored.
# This pinned count helps catch accidental truncation of the file.
assert len(gf) >= 30, f"Grandfather list has {len(gf)} entries; expected at least 30"
```

The `>=` is fine policy-wise (removal is legitimate), but the assertion comment should document the intent.

#### S2: `_aggregate_per_check_rows` category inconsistency on same (case_id, check_name, model)
**File:** `src/embedeval/reporter.py:64-80`

The bucket `setdefault` captures `category` from the FIRST result seen for a given `(case_id, check_name, model)` key. For comprehensive_results built by `_build_comprehensive_results`, category comes from `meta.category` which is deterministic per case_id. So in practice this is not a real bug. However, the code silently drops subsequent `category` values without asserting they match — a future refactor that synthesizes EvalResults differently (e.g., two results for the same case_id with different categories due to a remapping error) would produce a silently wrong row. Logging a warning would help:

```python
if bucket["category"] != category:
    logger.warning(
        "Inconsistent category for (%s, %s, %s): %s vs %s",
        r.case_id, d.check_name, model, bucket["category"], category
    )
```

#### S3: `compute_coverage` silently skips when `run_checks(reference)` raises
**File:** `scripts/verify_negatives_oracle.py:236-238`

The `except Exception: continue` swallows errors from `run_checks(reference)`. If a TC's static.py has a bug (not the mutation, but the check code itself), coverage will be silently computed as if that module doesn't exist, yielding inflated coverage. The oracle's `verify_case` path (not the coverage path) does catch mutation-related errors, but coverage computation on the reference is independent. At minimum, log the exception:

```python
try:
    emitted |= {c.check_name for c in mod.run_checks(reference)}
except Exception as exc:
    logger.warning("run_checks failed for %s/%s: %s", case_dir.name, name, exc)
    continue
```

#### S4: `should_fail`-only negatives counted toward coverage numerator — document the design
**File:** `scripts/verify_negatives_oracle.py:241-243`

Per concern #4: `should_fail` entries DO contribute to the labeled set and thus to coverage. This is intentional (REQ-02 says "must_fail OR should_fail" counts) but is not documented in `compute_coverage`'s docstring. A reader maintaining this function could plausibly remove `should_fail` from the labeled set under the impression that only hard gates matter. Add to docstring:

```
Note: should_fail entries intentionally count toward the labeled set.
REQ-02 defines coverage = (must_fail ∪ should_fail labels) ∩ emitted / emitted.
Subtle negatives (should_fail-only) are valid mutation witnesses even though
they don't gate the oracle exit code.
```

---

## Positive Observations

1. **REQ-03 migration tooling is architecturally sound.** Using AST for position detection and text-level replacement (not AST unparsing) preserves formatting. The `end_lineno != lineno` multi-line bailout is the right conservative safety valve — better to skip than to corrupt. The reverse-order span application within a line correctly handles multiple rewrites on the same line.

2. **`compute_coverage` correctly handles the empty-emitted edge case** — returning 1.0 rather than 0.0 or raising ZeroDivisionError when no checks are emitted. The test coverage for this edge case (`test_empty_emitted_returns_perfect`) explicitly documents the convention.

3. **Per-check metrics schema versioning is properly decoupled from leaderboard schema versioning** (`LEADERBOARD_SCHEMA_VERSION` vs `PER_CHECK_METRICS_SCHEMA_VERSION`). This is the correct design — the two artifacts evolve independently.

4. **`cli.py` `results_by_model` dict building is correct**: the current model's results go in first (`{model: comprehensive_results}`), then other models are iterated from `prior_tracker`. The `if other_model == model` guard prevents double-counting. The `if not other_merged: continue` guard prevents empty-list entries from entering the dict (addressing concern #2 directly).

5. **The grandfather list + `--strict-coverage` design is pragmatic.** Allowing pre-gate TCs to report but not fail gives a migration window without breaking CI immediately. The `_load_grandfather()` returning `frozenset()` (not failing) when the file is missing means a bare run without the plans directory won't catastrophically fail.

6. **REQ-06 documentation in CONTRIBUTING.md is complete and actionable** — the check_name immutability contract, migration YAML schema, and the two-way Hiloop consumer list are all present. This is the right place (CONTRIBUTING.md vs README) for this level of contributor guidance.

---

## Project-Specific Checks

### Quality Gates
- [x] `uv run pytest` passes (1456 tests)
- [x] `uv run embedeval validate --cases cases/` passes (185/185)
- [x] `uv run python scripts/verify_negatives_oracle.py` passes (PASS=31 FAIL=0 SKIP=155)
- [x] `uv run python scripts/audit_check_scope.py` clean (0 unscoped)
- [x] New feature (per_check_metrics) has tests
- [x] New feature (coverage validator) has tests
- [ ] `per_check_metrics.json` output path matches PLAN spec (currently flat, should be run-scoped — W1)

### REQ Compliance
- [ ] REQ-01: 31/186 negatives TCs done, ongoing — expected, not a code issue
- [x] REQ-02: Coverage validator implemented, grandfather list, --strict-coverage gate
- [x] REQ-03: 1982 spans migrated, 0 unscoped remaining
- [ ] REQ-04: Per-check metrics emitted BUT path diverges from plan (W1)
- [x] REQ-05: `<!-- SCHEMA_VERSION: 1 -->` in LEADERBOARD.md
- [x] REQ-06: check_name immutability documented, migration template provided

### Test Coverage
- [x] `generate_per_check_metrics` — 6 tests
- [x] `compute_coverage` — 5 tests
- [x] `_load_grandfather` — 2 tests
- [ ] `test_empty_results` incomplete — doesn't verify file creation (W4)
- [ ] No test for `--strict-coverage` + oracle failure co-occurrence (W3 scenario)
- [ ] No test for MD output of `generate_per_check_metrics` with multi-model input

---

## Code Metrics

- **Files Reviewed:** 8 primary + 24 spot-checked cases
- **New lines:** ~800 in scripts, ~120 in reporter.py, ~90 in cli.py, ~150 in tests
- **Complexity:** Low — no new algorithmic complexity; the REQ-03 migration complexity is in the tooling, not the runtime path
- **Maintainability:** Good, with the cosmetic debt of 24 files having duplicate imports (W2)

---

## Action Items

**Must Do (Before Hiloop Integration):**
- [ ] W1: Move `per_check_metrics.json` write to `run_dir/per_check_metrics.json` so n=3 runs produce 3 artifacts

**Should Do (This Week):**
- [ ] W2: Clean up 24 files with duplicate `from embedeval.check_utils import` lines (cosmetic but visible in public repo)
- [ ] W3: Fix exit-code ordering in `verify_negatives_oracle.py` to prevent coverage message masking oracle failure
- [ ] W4: Extend `test_empty_results` to assert file creation and valid JSON

**Nice to Have (Future):**
- [ ] S1: Document grandfather removal intent in test comment
- [ ] S2: Add category consistency warning in `_aggregate_per_check_rows`
- [ ] S3: Log (don't silently swallow) `run_checks` exceptions in `compute_coverage`
- [ ] S4: Document `should_fail` in coverage docstring
- [ ] Add test for `--strict-coverage` + simultaneous oracle failure scenario

---

## Recommendation

**Status:** CHANGES_REQUESTED

W1 is the highest-priority fix because it affects Hiloop's artifact consumption contract — per-check metrics will be silently overwritten on multi-run benchmarks (n1/n2/n3). W3 is a CI diagnostic issue that will cause confusion when the coverage gate and oracle failures overlap. W2 and W4 are quality issues with no runtime impact. None of these are release blockers for internal use, but W1 should be resolved before Hiloop integration.
