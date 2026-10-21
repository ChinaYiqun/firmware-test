---
type: plan
project: embedeval
task_slug: hiloop-requests-response
status: planning
created: 2026-04-19
tags: [embedeval, plan, python, embedded, hiloop, interop, benchmark]
related:
  - "[[plans/PLAN-hiloop-transpile-readiness]]"
  - "[[plans/PLAN-negative-tests]]"
  - "[[plans/PLAN-subtle-negatives]]"
  - "[[docs/METHODOLOGY]]"
  - "[[/home/noel/hiloop/docs/embedeval-requests/README]]"
summary: "Map Hiloop REQ-01..REQ-06 onto existing EmbedEval workstreams; close REQ-05/REQ-06 gap; sequence execution around /negatives and Yocto TC expansion"
---

# PLAN: Response to Hiloop embedeval-requests REQ-01..REQ-06

**Project:** embedeval
**Created:** 2026-04-19
**Source:** `/home/noel/hiloop/docs/embedeval-requests/` (6 formal requests, draft status)

---

## 🎯 Executive Summary

> **TL;DR:** 4 of 6 Hiloop requests already live inside `PLAN-hiloop-transpile-readiness` as P1–P4; REQ-05 (leaderboard schema version) and REQ-06 (check_name immutability) are net-new and cheap. Keep the umbrella plan as the execution vehicle; add REQ-05/REQ-06 as a small P5 "defensive contract" slice; sequence around the already-running `/negatives` command and the upcoming Yocto/Linux TC expansion.

### Request → Workstream Mapping

| REQ | Title | Priority | Existing plan slot | Delta vs existing |
|-----|-------|----------|---------------------|-------------------|
| REQ-01 | Negatives coverage 186/186 | **P1** | [PLAN-hiloop-transpile-readiness §P1](./PLAN-hiloop-transpile-readiness.md) | **Already in motion.** `/negatives` command + `plans/negatives-progress.json` shipped (commit d057bff). 30/186 done, 156 pending. No planning change needed — just execute. |
| REQ-02 | Per-check mutation coverage (≥80%) | **P1** | §P1 (implicit) | **Gap.** Existing plan authors negatives per TC; does NOT yet enforce per-`check_name` coverage. Need new validator + CI gate. |
| REQ-03 | `strip_comments` unified in `static.py` | **P2** | §P2 | **Blocker found.** `scoped_contains` helper exists in `check_utils.py:39` but **0/185** static.py files call it. Audit script `scripts/audit_check_scope.py` ready. Pure migration work. |
| REQ-04 | Per-check failure metrics artifact | **P2** | §P3 | Aligned. Existing plan calls this "per-check failure rates in summary JSON". Hiloop's ask is a markdown file. Pick one; recommend both (JSON canonical + markdown reader-friendly). |
| REQ-05 | LEADERBOARD `SCHEMA_VERSION` comment | **P3** | — | **Net-new.** ~5 min patch to `reporter.py:62`. |
| REQ-06 | `check_name` immutability contract + migration.yaml | **P3** | — | **Net-new.** CONTRIBUTING doc + optional migration file format + optional CI validator. |

### Key Decisions

- **Decision 1:** Do NOT create a new umbrella plan. Extend PLAN-hiloop-transpile-readiness rather than forking. *Why: that plan already has Executive Summary, Review Checklist, and user-accepted decisions (P2 flip policy, Yocto relevance flag). Forking splits context.*
- **Decision 2:** Ship REQ-05 + REQ-06 as a small P5 "Contract Hardening" slice inside the existing umbrella plan — ~2h combined, zero-risk defensive additions.
- **Decision 3:** REQ-02 coverage gate lands BEFORE Yocto/Linux TC expansion. *Why: if expansion adds ~30 new cases and we bulk-author their negatives under the current per-TC regime, we'd bake in the 88% UNTESTED rate Hiloop measured in the 5-TC pilot.*
- **Decision 4:** Treat REQ-01 (authoring) and REQ-02 (coverage validator) as parallel, not serial. Validator can run on existing 30 TCs today and surface under-covered ones.
- **Decision 5:** REQ-04 output format = `results/per_check_metrics.json` (canonical, machine-readable) + optional `results/LEADERBOARD_PER_CHECK.md` (markdown, for humans/Hiloop parser). Hiloop can consume either.

### Estimated Impact (delta on top of existing plan)

- **New code paths:** 1 validator script (REQ-02), 1 reporter helper (REQ-04 JSON), 1 markdown emitter (REQ-04 MD), 1 schema-version line (REQ-05), 1 CONTRIBUTING section + sample migration (REQ-06).
- **Existing plan expansion:** Add §P5 "Contract Hardening" section. No deletions.
- **Risk:** Low. REQ-02 validator might reveal already-landed negatives that fall below 80% — allow grandfather list, not auto-failure on day 1.
- **Estimated time:** P5 (REQ-05+REQ-06) = 2h. REQ-02 validator = 3h. REQ-04 per-check emission = 3h. REQ-03 migration = 6-8h (covered by existing plan). REQ-01 = ongoing via `/negatives`.

---

## ⚠️ REVIEW CHECKLIST — Before /execute

### Critical Decisions to Verify
- [ ] **Q1 — Fork or extend?** Extending `PLAN-hiloop-transpile-readiness` vs forking into this plan. Recommendation: **extend existing plan**; use this document as a change-request summary, then merge REQ-05/REQ-06 into the umbrella §P5.
- [ ] **Q2 — REQ-02 gate strictness.** Day-1 failure for TCs below 80% check coverage vs warn-only with grandfather list vs hard-required only for newly-added TCs. Recommendation: **warn-only for existing 30 TCs, hard-required for new TCs and for any TC visited by `/negatives` going forward.**
- [ ] **Q3 — REQ-04 output format.** JSON-only, markdown-only, or both? Recommendation: **both**; JSON is canonical contract, MD is a courtesy.
- [ ] **Q4 — REQ-06 enforcement.** Doc-only (cheapest), doc+sample-migration-file template, or doc+CI validator that diffs `check_name` sets between tagged releases. Recommendation: **doc + sample template**. Skip CI validator until first actual rename happens.
- [ ] **Q5 — Yocto/Linux TC expansion ordering.** Can REQ-02 validator ship before the expansion, or does expansion ship first and backfill negatives after? Recommendation: **REQ-02 validator first**, then expansion, then `/negatives` on the new TCs under the enforced regime.
- [ ] **Q6 — Request back-channel.** Do we file each REQ as a GitHub issue per Hiloop's submission protocol, or track internally and update Hiloop's request files with `status: merged` directly. Recommendation: **file only REQ-05/REQ-06 as issues** (net-new, low-discussion); for REQ-01..REQ-04 reference the existing PLAN in a single umbrella issue.

### Code Impact to Review
- [ ] **File: `scripts/verify_negatives_oracle.py`** — extend with optional `--coverage` flag that computes per-check coverage alongside must_fail verification. REQ-02.
- [ ] **File: `.claude/commands/negatives.md` Step 6** — add coverage check into the oracle gate so `/negatives` refuses to mark a TC done when coverage < threshold. REQ-02.
- [ ] **File: `src/embedeval/reporter.py:49-85` (`generate_leaderboard`)** — prepend `<!-- SCHEMA_VERSION: 1 -->` line. REQ-05.
- [ ] **File: `src/embedeval/reporter.py`** — new `generate_per_check_metrics(reports, output)` emitting JSON + MD. REQ-04.
- [ ] **File: `src/embedeval/cli.py`** — wire new reporter into `run`/`report` subcommands. REQ-04.
- [ ] **File: `CONTRIBUTING.md`** (create if missing) — `check_name` immutability section + migration.yaml schema. REQ-06.
- [ ] **File: `docs/METHODOLOGY.md` or similar** — document per-check coverage target + exemption protocol. REQ-02.

---

## 📋 Problem Analysis

### What Hiloop is blocked on (per the 6 REQs)

- **Phase 4.3 FP/recall report** (Hiloop's TECH_SPEC §14 P0 deliverable): 88% of transpiled rules stamped UNTESTED — dominated by missing negatives (REQ-01) and per-TC-level negatives that miss individual `check_name`s (REQ-02).
- **Severity auto-assignment**: category-level failure rates collapse two rules with very different empirical impact onto the same `aggregate_failure_rate` (REQ-04).
- **Contract drift**: LEADERBOARD format changes silently break Hiloop's parser (REQ-05). `check_name` renames silently orphan landed Hiloop rules (REQ-06).
- **Transpile faithfulness**: inconsistent `strip_comments` semantics between static.py and behavior.py forces Hiloop to faithfully reproduce a brittle behavior instead of defaulting to scope-safe rules (REQ-03).

### Current EmbedEval state (audited 2026-04-19)

- **Negatives coverage**: 30/186 cases = 16.1%. Command (`/negatives`) and progress tracker (`plans/negatives-progress.json`) live; priorities set (dma, isr, threading, memory-opt first).
- **Per-check coverage**: not measured anywhere today. Oracle script (`scripts/verify_negatives_oracle.py`) verifies `must_fail` but does not compute what fraction of `run_checks` outputs are covered.
- **Scope discipline**: 185/185 static.py files use raw `in generated_code`; 0 use `scoped_contains`. Audit script `scripts/audit_check_scope.py` ready but migration never ran.
- **Per-check metrics**: `reporter.py` computes per-check stats transiently for "Most Common Failure Patterns" table; never persisted to an external-consumer-friendly artifact.
- **Schema version**: none. `LEADERBOARD.md` starts with `# EmbedEval Leaderboard\n\n`.
- **check_name contract**: undocumented. No `CONTRIBUTING.md` in repo root.

### What's coming (user flagged)

- **Yocto/Linux TC expansion**: near-term batch of new TCs. Will appear in `/negatives` as pending via auto-sync (Step 1 of the command). If REQ-02 validator ships first, the expansion is authored under the correct regime from day 1.

---

## 🏗️ Technical Design

### Mapping to PLAN-hiloop-transpile-readiness

```
PLAN-hiloop-transpile-readiness
├── P1 Negatives coverage           ← REQ-01 (already executing via /negatives)
│   └── + coverage validator         ← REQ-02 (NEW WORK ITEM)
├── P2 Scope discipline             ← REQ-03 (already planned, not executed)
├── P3 Per-check failure rates      ← REQ-04 (align format: JSON + MD)
├── P4 Shared forbidden-API data    ← (already done, commit 21e9f09)
└── P5 Contract Hardening (NEW)
    ├── REQ-05 SCHEMA_VERSION comment
    └── REQ-06 check_name immutability doc
```

### REQ-02: Per-check mutation coverage validator

Location: `scripts/verify_negatives_oracle.py` — add `--coverage` flag. Logic:

```python
def compute_coverage(case_dir: Path) -> dict:
    """Return {'case_id', 'emitted_checks', 'labeled_checks', 'coverage'}."""
    reference = _read_reference(case_dir)
    static_mod = _load_module(case_dir / "checks" / "static.py", ...)
    behavior_mod = _load_module(case_dir / "checks" / "behavior.py", ...)
    neg_mod = _load_module(case_dir / "checks" / "negatives.py", ...)

    emitted = set()
    if static_mod:   emitted |= {c.check_name for c in static_mod.run_checks(reference)}
    if behavior_mod: emitted |= {c.check_name for c in behavior_mod.run_checks(reference)}

    labeled = set()
    for n in getattr(neg_mod, "NEGATIVES", []):
        labeled |= set(n.get("must_fail", []))
        labeled |= set(n.get("should_fail", []))

    covered = labeled & emitted
    return {
        "case_id": case_dir.name,
        "emitted": sorted(emitted),
        "labeled": sorted(labeled),
        "uncovered": sorted(emitted - labeled),
        "coverage": len(covered) / len(emitted) if emitted else 1.0,
    }
```

Wire into:
- `verify_negatives_oracle.py --coverage` flag (report, don't fail, unless `--strict-coverage` passed).
- `/negatives` Step 6 pre-commit: print coverage, warn if < 0.8, ask user to add more mutations or proceed with a documented exemption in `NEGATIVES` file docstring.
- CI workflow: `--strict-coverage` on newly-added TCs only (grandfather existing 30).

### REQ-03: Static.py scope migration

Tooling already exists (`audit_check_scope.py`). Execution strategy:

1. Run audit → list of ~185 files with N raw matches each.
2. Mechanical migration: `"needle" in generated_code` → `scoped_contains(generated_code, "needle")` with default `scope="stripped"`.
3. Preserve `scope="raw"` ONLY for comment-sensitive checks (e.g., header inclusion inside a comment should still count for "includes this header" if preprocessor doesn't skip it — rare).
4. Re-run full benchmark after migration; diff pass@1 per category; any flips enumerated in a `BENCHMARK-DELTA-<date>.md`.
5. Accept flips (per existing plan's user decision 2026-04-19: "flip 허용 + 문서화").

Target: 185/185 static.py files migrated; benchmark delta documented.

### REQ-04: Per-check failure metrics

Emit `results/<run_id>/per_check_metrics.json`:

```json
{
  "schema_version": 1,
  "run_id": "2026-04-19T12:00:00Z_sonnet_n3",
  "rows": [
    {
      "case_id": "isr-concurrency-003",
      "category": "isr-concurrency",
      "check_name": "no_mutex_in_isr",
      "model": "claude-code://sonnet",
      "samples": 13,
      "passed": 3,
      "pass_rate": 0.231
    }
  ]
}
```

Also emit `results/<run_id>/LEADERBOARD_PER_CHECK.md` with the same data in markdown form, sorted by pass_rate ascending (most-failed first).

Reuse existing per-check aggregation in `reporter.py:_failure_distribution` — extract into a shared helper.

### REQ-05: LEADERBOARD schema version

`reporter.py:62`:

```python
lines: list[str] = [
    "# EmbedEval Leaderboard",
    "",
    "<!-- SCHEMA_VERSION: 1 -->",
    "",
]
```

Document bump protocol in `docs/METHODOLOGY.md` or a new `docs/LEADERBOARD_SCHEMA.md`:
- Increment on any column add/remove/rename, section header rename, or cell format change.
- No bump for new rows (new TC, new model, new category). No bump for cosmetic whitespace.

### REQ-06: check_name immutability

Create `CONTRIBUTING.md` (doesn't exist today) with section:

```markdown
## `CheckDetail.check_name` is an external contract

Once a TC is merged into a tagged release, its `check_name` values MUST NOT
be renamed or removed. External consumers (e.g., Hiloop transpile pipeline)
stamp these names into their own artifacts and cannot follow silent renames.

### If a rename is unavoidable

Emit `cases/<tc>/checks/check_name_migrations.yaml`:

    renames:
      - from: old_check_name
        to:   new_check_name
        since: "YYYY-MM-DD"    # release date or merge commit date

The file is human-maintained; there is no auto-generator. External tools
that consume `check_name` are expected to honor the migration before a new
release is tagged.
```

Ship a sample empty file at `cases/_template/checks/check_name_migrations.yaml` (if such template dir exists, else skip the template and just document).

### Sequence & Dependencies

```
REQ-05, REQ-06 (P5)  ─── 2h ───────────────→ ship standalone, parallel to everything
REQ-02 validator     ─── 3h ───────────────→ ship BEFORE yocto/linux expansion
REQ-01 (/negatives)  ─── ongoing ──────────→ drives toward 186/186, paced by user
REQ-03 scope migrate ─── 6-8h ─────────────→ ship any time; benchmark delta review gate
REQ-04 per-check MD  ─── 3h ───────────────→ ship any time
Yocto/Linux TC exp   ─── after REQ-02 ─────→ new TCs authored under coverage gate
```

---

## 📝 Implementation Plan

### Phase 1 — P5 Contract Hardening (REQ-05 + REQ-06)

1. Add `<!-- SCHEMA_VERSION: 1 -->` to `reporter.py:generate_leaderboard`.
2. Add test: `tests/test_reporter.py` asserts schema version line present.
3. Create `CONTRIBUTING.md` with check_name immutability section + migration.yaml schema.
4. Ship as one PR; file both as separate EmbedEval issues referencing Hiloop REQ-05/REQ-06.
5. Update `/home/noel/hiloop/docs/embedeval-requests/REQ-05-*.md` and `REQ-06-*.md` status to `merged` once PR lands.

### Phase 2 — REQ-02 per-check coverage validator

1. Extend `scripts/verify_negatives_oracle.py` with `compute_coverage()` + `--coverage` flag (report) + `--strict-coverage` flag (fail on < 0.8).
2. Integrate into `/negatives` Step 6: run coverage report after oracle PASS; if < 0.8 and user-approved, stash result in progress file `notes` field for later review.
3. Add CI job: `strict-coverage` runs on any TC whose `negatives.py` was modified in the PR diff (backlog 30 TCs are grandfathered via an allowlist file).
4. Emit aggregate coverage report: `scripts/verify_negatives_oracle.py --coverage --all --json plans/coverage-snapshot.json`. Commit the snapshot.
5. Update `negatives-progress.json` entries: when a case is marked done via `/negatives`, record `coverage: 0.xx` alongside `completed_at`.

### Phase 3 — REQ-04 per-check metrics emission

1. Extract `_per_check_breakdown(reports)` helper from `reporter.py:_failure_distribution`.
2. Add `generate_per_check_metrics(reports, output_json, output_md)` function.
3. Wire into `cli.py` `run` / `report` subcommands.
4. Update `scripts/sync_docs.py` if it aggregates results (check existing behavior).
5. Add `tests/test_reporter.py::test_per_check_metrics` — fixture with 3 cases × 2 models, verify row count, schema.
6. Update Hiloop REQ-04 status once merged; Hiloop will extend their `interop.leaderboard` parser in a separate coordinated PR.

### Phase 4 — REQ-03 scope migration (existing plan P2)

This phase is already planned in PLAN-hiloop-transpile-readiness §P2. No duplication here. Execute that plan when user is ready.

### Phase 5 — REQ-01 execute via `/negatives` (ongoing)

1. Continue running `/negatives` sessions, priority order as configured.
2. After REQ-02 ships, `/negatives` enforces coverage at commit time.
3. When Yocto/Linux expansion lands, new TCs auto-sync into `plans/negatives-progress.json` as pending; authored next under coverage gate.

### Phase 6 — Post-REQ-01 verification

Once `find cases -name negatives.py | wc -l` == `find cases -name static.py | wc -l`:

1. Run `uv run python scripts/verify_negatives_oracle.py --strict-coverage` — all cases pass coverage + oracle.
2. Run full benchmark n=3 on Haiku + Sonnet. Confirm L4 mutation oracle now dark on 0% of cases (was 84%).
3. Notify Hiloop; they can re-run transpile Phase 3 pilot against 186/186.

---

## 🧪 Testing Strategy

### REQ-02 validator
- Unit test: TC with full coverage → coverage = 1.0, no missed.
- Unit test: TC with partial coverage → coverage = labeled/emitted.
- Unit test: TC with labeled-but-not-emitted (typo in `must_fail`) → flagged as stale label.
- Integration: run on all 30 existing negatives, snapshot results.

### REQ-04 per-check metrics
- Unit test: fixture report with 2 cases × 2 checks × 1 model → 4 rows.
- Unit test: rows sorted by pass_rate ascending.
- Unit test: schema_version field present.
- Snapshot test: JSON output against a checked-in fixture.

### REQ-05 schema version
- Unit test: generated leaderboard contains `<!-- SCHEMA_VERSION: 1 -->`.
- Regression test: if the comment line is missing, test fails loudly.

### REQ-06 contributing doc
- Manual review only — doc change, no code path.

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| REQ-02 validator reveals many existing TCs < 80% coverage → forced rework | Medium | Grandfather the 30 existing TCs; enforce strictly only on NEW TCs (`/negatives` going forward, and Yocto/Linux expansion). |
| REQ-03 scope migration flips benchmark numbers widely | Medium | Existing plan already accepts flip-with-documentation. Re-run n=3 on both models and publish `BENCHMARK-DELTA-<date>.md`. |
| REQ-04 output format doesn't match Hiloop's parser expectations | Low | Coordinate format via short issue comment before implementing. Hiloop REQ-04 body already proposes the shape — replicate it. |
| Yocto/Linux expansion lands BEFORE REQ-02 validator | Medium | Sequence: REQ-02 ships Phase 2, expansion afterward. If scheduling forces reverse order, flag new TCs as pending but defer `/negatives` authoring until validator lands. |
| `check_name` renames happen before REQ-06 doc lands | Low | Cost is one-time audit against last tagged release. REQ-06 prevents future recurrence. |
| Hiloop's 20-TC pilot expands before REQ-01 hits the pilot TCs | Low | Priority list in `/negatives` can be overridden; if Hiloop needs specific TCs next, re-order `plans/negatives-progress.json` priorities. |

---

## ✅ Success Criteria

- [ ] REQ-05 merged: `LEADERBOARD.md` contains schema version comment.
- [ ] REQ-06 merged: `CONTRIBUTING.md` documents `check_name` contract + migration schema.
- [ ] REQ-02 merged: `scripts/verify_negatives_oracle.py --coverage` works; `/negatives` integrates coverage gate.
- [ ] REQ-04 merged: `results/<run_id>/per_check_metrics.json` + `LEADERBOARD_PER_CHECK.md` emitted on every run.
- [ ] REQ-03 merged: 185/185 static.py files use `scoped_contains`; benchmark delta documented.
- [ ] REQ-01 merged: 186/186 cases have `negatives.py`; oracle + coverage PASS on all.
- [ ] Hiloop Phase 4.3 unblocked: Hiloop's `verify_transpile.py` reports testable-rate ≥ 80% on its 20-TC pilot.
- [ ] Yocto/Linux TC expansion lands under REQ-02 enforcement (authored with ≥80% coverage from the start).

---

## 📊 Estimated Effort

| Phase | Work item | Hours |
|-------|-----------|-------|
| 1 | REQ-05 + REQ-06 (P5 Contract Hardening) | 2 |
| 2 | REQ-02 per-check coverage validator | 3 |
| 3 | REQ-04 per-check metrics emission | 3 |
| 4 | REQ-03 scope migration | 6-8 |
| 5 | REQ-01 `/negatives` execution | ongoing (~1h/TC × 156) |
| 6 | Verification + benchmark re-run | 2 |

**New code (this plan's delta):** ~10 hours (REQ-02 + REQ-04 + REQ-05 + REQ-06).
**Ongoing authoring:** covered by `/negatives` sessions, paced by user.

---

## 🔗 Cross-references

- Umbrella: [[plans/PLAN-hiloop-transpile-readiness]]
- Upstream request docs: `/home/noel/hiloop/docs/embedeval-requests/` (REQ-01 through REQ-06)
- Live tooling: `.claude/commands/negatives.md`, `scripts/verify_negatives_oracle.py`, `scripts/audit_check_scope.py`
- Progress tracker: `plans/negatives-progress.json` (30/186 done as of 2026-04-19)
