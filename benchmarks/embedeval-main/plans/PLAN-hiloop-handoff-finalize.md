---
type: plan
task_slug: hiloop-handoff-finalize
status: implemented
created: 2026-04-19
tags: [embedeval, plan, hiloop, interop, docs, ci, python]
related:
  - "[[plans/PLAN-hiloop-transpile-readiness]]"
  - "[[plans/PLAN-hiloop-requests-response]]"
  - "[[plans/WRAPUP-hiloop-transpile-readiness-phase-0-3]]"
  - "[[plans/REVIEW-hiloop-requests-response-2026-04-19]]"
  - "[[docs/BENCHMARK-DELTA-2026-04-19]]"
summary: "Close the two open tails of hiloop-transpile-readiness: migrate the 9 P2 scope stragglers + add CI gate, then write docs/HILOOP-HANDOFF.md as the single source of truth for Hiloop consumers."
---

# PLAN: Hiloop Handoff Finalize

**Task:** Close P2 scope-migration tail + publish `docs/HILOOP-HANDOFF.md` as the canonical contract doc for Hiloop consumers.
**Created:** 2026-04-19

---

## Executive summary

**TL;DR:** Fix the 9 unscoped-substring stragglers in `linux-userspace-005`, wire `audit_check_scope.py --strict` into CI so future TCs can't regress, then write `docs/HILOOP-HANDOFF.md` as a mirror of hiloop's `CONTRACT.md §2` — pinned schemas + file paths + breaking-change protocol.

### What
- **Phase 1 (P2 tail + gate):** Migrate the 9 remaining raw `"needle" in generated_code` sites in `cases/embedded-linux/linux-userspace-005/checks/behavior.py` to `scoped_contains(..., scope='raw')` (udev `.rules` format uses `#` comments, not C-style — same precedent as Yocto `.bb` in `_scope_for_case`). Add a CI job that runs `uv run python scripts/audit_check_scope.py --strict` so Phase C / future TC additions can't re-introduce unscoped substring checks silently.
- **Phase 2 (HILOOP-HANDOFF doc):** Author `docs/HILOOP-HANDOFF.md` — enumerate the 6 interop surfaces (metadata.yaml, static.py/behavior.py, negatives.py, summary.json `per_check_stats`, `LEADERBOARD.md` schema_version, `data/forbidden_apis.yaml`), pin each schema, document the breaking-change protocol (REQ-05 version bump + REQ-06 `check_name` immutability). Link from `README.md` and `docs/CONTRIBUTING.md`.

### Why
- The 9 stragglers leak substring matching into udev comment/quote regions, which can silently match comment-documented forbidden patterns. Tiny fix; bigger value is the **CI gate** that freezes the 0-unscoped-sites invariant.
- Today, Hiloop consumers have to grep across `embedeval` to discover what they can rely on (CaseSpec fields, `per_check_stats` shape, `forbidden_apis.yaml` path). A single handoff doc in the embedeval repo is the durable fix — Hiloop's `CONTRACT.md` mirrors it, but the source of truth for schemas belongs where the schemas live.

### Key decisions
- **Single PLAN, two phases:** P2 tail is 1-2h of code, HANDOFF is 1-2h of docs — bundling them avoids churn in the PLAN index and both serve the same "finalize Hiloop contract" goal. Separate commits/PRs inside the PLAN.
- **Use `scope='raw'` for udev rules file** — udev rule syntax uses `#` for comments (not C `//`), and `strip_comments` is C-specific. Same precedent as Yocto `.bb` in `apply_scope_migration.py:_scope_for_case`. Applies to this TC and any future `linux-userspace-udev-*` cases.
- **CI gate is `--strict` on `audit_check_scope.py`** — already exists, zero new tooling. Hook into `.github/workflows/validate-cases.yml`.
- **HANDOFF.md lives at `docs/HILOOP-HANDOFF.md`** — not `docs/hiloop/`. Flat docs dir matches existing convention (`docs/METHODOLOGY.md`, `docs/LLM-EMBEDDED-*`).
- **No new BENCHMARK-DELTA doc** — the existing `docs/BENCHMARK-DELTA-2026-04-19.md` already covers the semantic migration; 9 late-authored spans are the same semantic change, not a new baseline event. One sentence appended to that doc is enough.

### Impact
- Complexity: **Low**
- Risk: **Low** (Phase 1 touches one check file with known-green reference; Phase 2 is pure docs)
- Files changed: **~6** (1 check file, 1 CI YAML, 1 CONTRIBUTING.md append, 1 new HANDOFF doc, 1 README link, 1 BENCHMARK-DELTA append)
- Estimated effort: **2-3 hours**

---

## Prior work

- **`plans/PLAN-hiloop-transpile-readiness.md` §P2** — specifies scope discipline. Phase 0-3 landed the `scoped_contains` helper + audit tool + 1982-span migration (see `plans/WRAPUP-hiloop-transpile-readiness-phase-0-3.md`). This PLAN is the documented Phase-5 tail.
- **`plans/PLAN-hiloop-requests-response.md` + `plans/REVIEW-hiloop-requests-response-2026-04-19.md`** — REQ-03 mechanical migration landed 2026-04-19 with grade B (0 critical, 4 warnings all fixed). `verify_negatives_oracle` PASS rose 30→31 post-migration (precision gain). Established the "flip-allow + BENCHMARK-DELTA.md" re-baseline policy. This PLAN extends that policy with a CI gate so it isn't a one-time thing.
- **`~/hiloop/CONTRACT.md §2`** — Hiloop's side of the mirror. 6 surfaces enumerated, snapshot tests pinned in `~/hiloop/tests/contracts/`. HILOOP-HANDOFF.md mirrors this list from EmbedEval's side; the two docs must stay in sync via linked cross-references.
- **`~/hiloop/docs/embedeval-requests/`** — 6 REQ files. REQ-01 (negatives coverage, P1 in hiloop-transpile-readiness) is **out of scope** for this PLAN — it's a mass-authoring job tracked separately.
- **CLAUDE.md corrections (2026-04-19):**
  - `strip_comments is C-specific and mis-treats file:// URLs` — justifies `scope='raw'` for udev/Yocto non-C rule files.
  - `Run-scoped artifacts MUST go under run_dir/` — HANDOFF.md must document `run_dir/per_check_metrics.json` path, not flat root.
  - `scoped_contains default scope is stripped` — HANDOFF.md must flag this to consumers reading source (default ≠ what migration picked).

---

## Problem analysis

### Current state

**P2 migration tail:**
- `uv run python scripts/audit_check_scope.py` reports **9 findings in 1 file** as of 2026-04-19:
  - `cases/embedded-linux/linux-userspace-005/checks/behavior.py` lines 41, 42, 43, 57, 58, 88 (duplicate form), 114 (2 needles)
  - Needles: `'1d6b'`, `'ATTRS{idVendor}=="1d6b"'`, `'ATTRS{idProduct}=="0002"'`, `'ENV{SYSTEMD_WANTS}=...'`, `'RUN'`, `'systemctl'`
- Root cause: TC authored in Phase B (commit `8423040`) *after* the REQ-03 migration landed, and the author used the legacy `"needle" in code` idiom by habit.
- Migration script `scripts/apply_scope_migration.py` already handles this file — but its `_scope_for_case` only recognizes `yocto-*` for `scope='raw'`. udev rules (`.rules` files) have the same property and are not yet routed to `raw`.

**CI gate gap:**
- `.github/workflows/validate-cases.yml` does **not** run the scope audit. `scripts/audit_check_scope.py --strict` exit-codes on findings (`sys.exit(1 if findings else 0)`) but is never invoked in CI.
- A new TC author can re-introduce unscoped substrings without CI failing; only a manual run of the audit would catch it.

**HANDOFF doc gap:**
- `docs/` contains `METHODOLOGY.md`, `LLM-EMBEDDED-*`, `BENCHMARK-*`, `CONTEXT-QUALITY-MODE.md` — no Hiloop-facing interop doc.
- Hiloop's `~/hiloop/CONTRACT.md §2` enumerates 6 data surfaces but it's *consumer-side*. The embedeval side has no paired producer-side doc, so any Hiloop consumer (or future third-party transpile) has to reverse-engineer schemas from source.
- `docs/CONTRIBUTING.md` doesn't tell TC authors "these fields are interop-stable, changing them is a breaking change."

### Success criteria

**Phase 1 (P2 tail + gate):**
- [ ] `uv run python scripts/audit_check_scope.py --strict` exits 0 (0 findings).
- [ ] `scripts/apply_scope_migration.py:_scope_for_case` returns `'raw'` for `linux-userspace-*-udev*` or any case whose `checks/behavior.py` imports `udev_*` helpers (decision: first route — simpler, reads from case name, future-proof for `linux-userspace-005` + siblings).
- [ ] `cases/embedded-linux/linux-userspace-005/checks/behavior.py` uses `scoped_contains(..., scope='raw')` for all 9 findings. Reference still validates.
- [ ] `uv run embedeval validate --cases cases/ --private-cases ../embedeval-private/cases/ --include-private` passes 233/233.
- [ ] `uv run python scripts/verify_negatives_oracle.py` PASS count unchanged (31 or higher — regression is a hard fail, improvement is documented).
- [ ] `.github/workflows/validate-cases.yml` runs `audit_check_scope.py --strict` and fails the job on nonzero exit.
- [ ] CI green on the branch.

**Phase 2 (HANDOFF doc):**
- [ ] `docs/HILOOP-HANDOFF.md` exists and enumerates all 6 interop surfaces with file paths, schemas, and field-stability classification (required / optional / consumer-should-ignore-unknown).
- [ ] The doc documents the breaking-change protocol: (a) schema_version bump for `LEADERBOARD.md`, (b) `check_name` immutability + migration file, (c) additive-only policy for `per_check_stats` keys, (d) `extra="forbid"` boundary on `CaseSpec`.
- [ ] `docs/CONTRIBUTING.md` gains a "Interop-stable surfaces" pointer to HANDOFF.md.
- [ ] `README.md` "Documentation" section links HANDOFF.md.
- [ ] `docs/BENCHMARK-DELTA-2026-04-19.md` gets a one-paragraph append noting the linux-userspace-005 follow-up migration (no verdict flips expected; if any, enumerate).

---

## Design

### Phase 1 — Approach

Two sub-changes, one commit each for reviewability:

**1a. Route udev cases to `scope='raw'` in the migration script.** The cleanest signal is the import list in `behavior.py` — if it imports any `udev_*` helper from `check_utils`, treat as non-C. But that requires reading the file during migration, which couples two concerns. Simpler: check the case-id prefix. `linux-userspace-005` and future `linux-userspace-*-udev*` cases would be caught. Since there's currently only one case and the migration script is a tool (not runtime code), the prefix approach is cheap and explicit.

**Chosen:** extend `_scope_for_case` with a second rule: `case_id.startswith(('yocto-', 'linux-userspace-005'))` for now, with a comment explaining the udev `.rules` format has `#` comments. When more udev TCs land, promote to a category-based lookup (deferred until needed — premature abstraction otherwise).

**1b. Run the migration + wire CI.** `uv run python scripts/apply_scope_migration.py --apply --category linux-userspace-005` (if `--category` supports case IDs; else a direct-file flag). Verify the rewrite compiles, validate passes, oracle count holds. Then add a step to `validate-cases.yml`:

```yaml
- name: Audit check scope (REQ-03)
  run: uv run python scripts/audit_check_scope.py --strict
```

Must run *after* `embedeval validate` in the same job so that a validation failure surfaces first — the audit is the secondary gate.

### Phase 1 — Alternatives considered

- **Edit `behavior.py` by hand instead of using the migration script.** Rejected: the script is the documented path per `BENCHMARK-DELTA-2026-04-19.md`, and running it here exercises the same tool future migrations will use. A hand-edit would also lose the `_scope_for_case` routing fix that prevents the next udev TC from repeating the mistake.
- **Add a pre-commit hook instead of CI gate.** Rejected: pre-commit hooks require per-clone activation (CLAUDE.md notes `core.hooksPath` is not inherited). CI is enforced for all contributors unconditionally.
- **Loosen the scope check by converting the naked `"RUN" in generated_code` to a regex that looks for `^RUN` (line-start) before migrating.** Rejected: out of scope — that's a check-precision issue, not a scope-discipline issue. The audit flags raw-substring usage; fixing check precision is a separate question the audit doesn't claim to solve.

### Phase 2 — Approach

Write `docs/HILOOP-HANDOFF.md` as a structured enumeration mirroring Hiloop's `CONTRACT.md §2`. Six subsections (one per surface), each with:

1. **File path (glob)** — e.g. `cases/<sdk>/<case-id>/metadata.yaml`.
2. **Shape** — Pydantic model name + file reference, or JSON schema snippet with required/optional fields.
3. **Stability tier** — `stable` (breaking change requires version bump), `additive-only` (new fields OK, removing/renaming breaks), `internal` (embedeval-only, may change freely).
4. **Breaking-change protocol** — what version bump / migration file is needed. Cross-link to `~/hiloop/CONTRACT.md §4` for consumer-side obligations.
5. **Example** — one inline code block showing a real case.

Then three cross-cutting sections:
- **A. Per-check metrics** — `run_dir/per_check_metrics.json` path convention, `failing_tc_ids` guarantee, `check_type == "mutation"` exclusion from model-behavior stats.
- **B. forbidden_apis.yaml** — file path (`src/embedeval/data/forbidden_apis.yaml`), YAML schema, the contract that `check_utils.check_no_cross_platform_apis` reads from this file.
- **C. Check name immutability** — REQ-06 protocol. Link to `scripts/check_name_map.yaml` (Hiloop side) or embedeval-side equivalent if we decide to add one.

### Phase 2 — Alternatives considered

- **Point at `~/hiloop/CONTRACT.md` instead of writing a new doc.** Rejected: external-repo references break when hiloop reorganizes its docs, and the schemas live in *embedeval* — the canonical producer-side doc belongs here. Hiloop's CONTRACT stays as the consumer-side mirror.
- **Generate HANDOFF.md from code (e.g. pydantic JSON-schema export).** Rejected: auto-gen adds a scripts/docs sync burden (like `sync_docs.py`) for marginal benefit — the interop surfaces change ~1/year, not per-commit. Hand-authored with annual review is simpler.
- **Split into multiple docs (one per surface).** Rejected: consumers want one file they can bookmark. 6 sections in one doc is readable at ~400 lines.

### Affected files

| File | Phase | Change |
|---|---|---|
| `scripts/apply_scope_migration.py` | 1a | Extend `_scope_for_case` to return `'raw'` for `linux-userspace-005` (with comment explaining udev `.rules` format) |
| `cases/embedded-linux/linux-userspace-005/checks/behavior.py` | 1b | Mechanical rewrite via migration script: 9 spans → `scoped_contains(..., scope='raw')`; adds `from embedeval.check_utils import scoped_contains` |
| `.github/workflows/validate-cases.yml` | 1b | Append `audit_check_scope.py --strict` step |
| `docs/HILOOP-HANDOFF.md` | 2 | **NEW** — single-source interop doc |
| `docs/CONTRIBUTING.md` | 2 | Append "Interop-stable surfaces" section pointer |
| `README.md` | 2 | Add HANDOFF.md link under Documentation |
| `docs/BENCHMARK-DELTA-2026-04-19.md` | 1b | Append one paragraph noting the linux-userspace-005 follow-up |

---

## Implementation phases

### Phase 1: P2 tail migration + CI gate

**1a. Migration script fix**
- [x] Read `scripts/apply_scope_migration.py:_scope_for_case` to confirm current state
- [x] Extend prefix check: `case_id.startswith(("yocto-", "linux-userspace-005"))` — add comment block explaining udev `.rules` file format and pointing to the migration history
- [x] Local test: `uv run python scripts/apply_scope_migration.py --category linux-userspace-005` (dry-run) shows 9 rewrites with `scope='raw'`

**1b. Apply migration + verify + CI**
- [x] `uv run python scripts/apply_scope_migration.py --apply` (or per-file flag if available)
- [x] Verify `uv run python scripts/audit_check_scope.py --strict` exits 0
- [x] Verify validate — public 219/219 + private 48/48 (validate CLI has no `--private-cases` flag; ran separately)
- [x] Verify `uv run python scripts/verify_negatives_oracle.py` PASS count ≥ 31 (actual: 77 PASS, 0 FAIL — baseline advanced since PLAN drafted)
- [x] Verify `uv run ruff check src/` + `mypy src/` clean (pytest run deferred to full quality gate)
- [x] Add audit step to `.github/workflows/validate-cases.yml` after the `embedeval validate` step
- [x] Append paragraph to `docs/BENCHMARK-DELTA-2026-04-19.md` — 0 verdict flips (`scope='raw'` is semantically identical to raw substring)
- [ ] Commit: `feat(hiloop-ready): migrate linux-userspace-005 to scoped_contains + add CI gate` — deferred to `/wrapup`

### Phase 2: HILOOP-HANDOFF.md

- [x] Draft `docs/HILOOP-HANDOFF.md` outline — 6 surface sections + cross-cutting
- [x] Section 2.1 (metadata.yaml): enumerate required/optional fields from `src/embedeval/models.py` Pydantic model (`extra="forbid"` binding decision documented)
- [x] Section 2.2 (static.py/behavior.py): `run_checks(code: str) -> list[CheckDetail]` contract + `check_name` immutability + `CheckDetail` schema
- [x] Section 2.3 (negatives.py): `NEGATIVES` list-of-dict schema (name/mutation/must_fail/should_fail/factor_id)
- [x] Section 2.4 (per_check_metrics.json): row schema + `check_type == "mutation"` exclusion + run_dir path convention
- [x] Section 2.5 (LEADERBOARD.md): `LEADERBOARD_SCHEMA_VERSION = 1` HTML comment + Category Results table shape
- [x] Section 2.6 (forbidden_apis.yaml): `src/embedeval/data/forbidden_apis.yaml` shape + additive-only tier
- [x] §3 Run-scoped artifact layout — run_dir/ path convention (CLAUDE.md 2026-04-19 correction)
- [x] §4 Breaking-change protocol — schema_version bump + check_name immutability + announcement via BENCHMARK-DELTA
- [x] §5 Mirror doc cross-reference to Hiloop `CONTRACT.md §2`
- [x] §6 REQ status table (REQ-01..REQ-06)
- [x] Link from `docs/CONTRIBUTING.md` (top-level "Interop-stable surfaces" section)
- [x] Link from `README.md` (under Contributing section)
- [x] Run `uv run python scripts/sync_docs.py` — already up to date
- [ ] Commit: `docs(hiloop): add HILOOP-HANDOFF.md as single source of truth` — deferred to `/wrapup`

---

## Testing strategy

### Unit tests
- No new Python unit tests. Phase 1 is exercised by existing `test_apply_scope_migration.py` (if it exists — confirm during execute) and the audit script's own `--strict` gate. Phase 2 is pure docs.
- If `test_apply_scope_migration.py` does not exist, add a minimal test that feeds a synthetic `linux-userspace-005`-shaped file to `_scope_for_case` and asserts `scope='raw'`.

### Integration
- `uv run embedeval validate --cases cases/ --private-cases ../embedeval-private/cases/ --include-private` — 233/233 green.
- `uv run python scripts/verify_negatives_oracle.py` — PASS ≥ 31, FAIL = 0. Note if new precision improvement appears.
- CI dry-run via `act` or a draft PR to confirm the new audit step fires.

### Quality gates
- `uv run ruff format --check src/ tests/`
- `uv run ruff check src/ tests/`
- `uv run mypy src/`
- `uv run pytest tests/` — all 1456 tests pass
- `uv run python scripts/sync_docs.py` — run before commit if `cases/`/`src/`/`tests/` changed (Phase 1 touches `cases/`, so mandatory)

### Doc sync
- `docs/METHODOLOGY.md` and `README.md` counts should be unchanged (we're not adding/removing TCs, categories, or checks). If `sync_docs.py` reports changes, investigate before accepting.

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| `scope='raw'` migration of the 9 spans flips a verdict on this TC's benchmark result because the current raw check accidentally matches a comment that the new `scoped_contains(..., scope='raw')` *also* matches (no-op semantically) | Low (verdict | `scope='raw'` is semantically identical to `"needle" in code` for matching behavior; the only difference is the call-site form. Expected 0 flips. Document any observed flips in the BENCHMARK-DELTA append. |
| CI gate rejects existing `main` because audit finds residual sites we missed | Medium (blocks PRs) | Run audit before pushing; verify 0 findings locally first. The gate is only added once the count is 0. |
| HANDOFF.md drifts from `~/hiloop/CONTRACT.md §2` over time | Medium (long-term) | Both docs carry a mutual cross-link with "mirror doc; keep in sync" annotation. Annual review line in HANDOFF.md. Not perfect but better than no mention. |
| HANDOFF.md becomes stale after `per_check_stats` schema evolves (REQ-04 follow-ups) | Low | Stability-tier classification makes it explicit which fields are additive-only. Schema additions don't invalidate the doc; removals require updating the tier table. |
| Phase 1 and Phase 2 ship together as one PR and a Phase-2-only revision can't land without re-running Phase-1 CI cost | Low | Two commits, two PRs per plan step ordering. Phase 2 doesn't depend on Phase 1 landing first. |

---

## Review checklist (verify before /execute)

- [ ] Scope correct — Phase 1 is exactly 9 spans + CI step, Phase 2 is exactly the 6-section HANDOFF doc
- [ ] Design sound — `scope='raw'` for udev matches the Yocto `.bb` precedent exactly; CI gate uses existing `--strict` flag
- [ ] Affected-files list complete (~6 files confirmed against Phase 1 + Phase 2 list above)
- [ ] Tests cover every success criterion — audit script exits 0 is the binary gate; oracle count + validate count are regression signals
- [ ] Risks identified with mitigations — 4 risks, all Low or Medium with explicit mitigation
- [ ] Two-commit sequencing preserves reviewability — Phase 1 is a migration commit, Phase 2 is a docs commit, independent PRs if wanted
- [ ] No new dependencies
- [ ] No change to benchmark numbers expected (flip policy documented even for the 0-flip case)
- [ ] Cross-links to `~/hiloop/CONTRACT.md` stay two-way (verify Hiloop side adds back-reference when HANDOFF.md lands — out of scope for this PLAN but noted)

---

## Out of scope (explicit NON-GOALS)

- **REQ-01 negatives.py coverage (77/219 → 219/219).** Separate PLAN — mass authoring job, not Hiloop-contract.
- **Auto-generation of HANDOFF.md from pydantic schemas.** Deferred until interop surface changes become frequent enough to justify the tooling burden.
- **Changes to Hiloop repo.** Hiloop-side updates (back-link in `CONTRACT.md`, `docs/embedeval-requests/` status updates to `merged`) are tracked by the Hiloop maintainer after this PLAN lands.
- **Fixing the imprecise `"RUN" in generated_code` check** in linux-userspace-005 (should be line-anchored). Separate precision concern; audit doesn't flag it and it's not REQ-03's problem.
- **Adding `docs/hiloop/` subdir.** Flat `docs/` maintained.
