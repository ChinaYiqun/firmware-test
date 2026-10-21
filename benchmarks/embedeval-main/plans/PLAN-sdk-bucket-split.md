---
type: plan
task_slug: sdk-bucket-split
status: executed
created: 2026-04-19
tags: [embedeval, plan, restructure, metadata, cli, zephyr, freertos, embedded-linux, esp-idf, stm32-hal]
---

# PLAN: SDK Bucket Split — Separate TCs by Platform Family

**Task:** Physically separate all test cases into 5 SDK buckets (`zephyr/`, `embedded-linux/`, `freertos/`, `esp-idf/`, `stm32-hal/`) and add an `sdk` metadata field so reporting, filtering, and case organization are SDK-aware.
**Created:** 2026-04-19

## Executive summary

**TL;DR:** Move every TC under `cases/` into a per-SDK subdirectory, add a required `sdk:` field to `metadata.yaml`, make case discovery recursive, and surface SDK as a first-class filter/report dimension. Classify only — no new TCs are authored in this plan.

### What
- Restructure `cases/*/` → `cases/<sdk>/*/` with 5 buckets: `zephyr`, `embedded-linux`, `freertos`, `esp-idf`, `stm32-hal`.
- Add `sdk: <bucket>` to all 186 `metadata.yaml` files (new required Pydantic field).
- Make `discover_cases()` walk 2 levels (`cases/<sdk>/<case-id>/metadata.yaml`).
- Split `boot` category: the one U-Boot TC (`boot-002`) is renamed to `boot-uboot-001` and moved to `embedded-linux/`; the remaining 7 `boot-*` TCs are MCUboot and move to `zephyr/`.
- Add `--sdk` CLI filter on `run`, `list`, `validate`, and the other cases-iterating subcommands.
- Reporter emits a per-SDK pass@1 breakdown.

### Why
Current layout has no first-class SDK dimension: the `platform:` field conflates runtime (native_sim, qemu_arm, yocto_build, …) with SDK identity; tags carry the SDK hint inconsistently; `boot` and `ota` categories mix U-Boot and MCUboot TCs in the same namespace. A flat `cases/` directory makes it impossible at a glance to see how many TCs cover Zephyr vs FreeRTOS vs Embedded Linux, and reports cannot break out pass@1 by SDK without fragile tag-sniffing heuristics.

### Key decisions
- **5 buckets, not 3** (user-confirmed): `zephyr`, `embedded-linux`, `freertos`, `esp-idf`, `stm32-hal`. `esp-idf` and `stm32-hal` stay separate from `freertos` even though they're all non-Zephyr RTOS/bare-metal — the SDK toolchain is what matters for prompts and checks.
- **Physical split** (user-confirmed) over metadata-only tagging, because the flat layout is the primary pain point.
- **`sdk:` field keyed by enum**, not free-form string — prevents typo drift.
- **`platform:` field preserved** for runtime (native_sim, qemu_arm, …). Renaming it out to `runtime:` is out of scope; adding a separate `sdk:` is sufficient and minimizes churn.
- **Classify only** (user-confirmed): no new FreeRTOS TCs authored in this plan. `freertos/` bucket starts with 1 TC (`stm32-freertos-001` moved over).
- **Only one ID rename**: `boot-002` → `boot-uboot-001`. All other `boot-*` and every `ota-*` TC is Zephyr/MCUboot — they move into `zephyr/` with unchanged IDs.
- **`stm32-freertos-001` goes to `freertos/`** (not `stm32-hal/`) — the RTOS is the primary identity; the TC is FreeRTOS-on-STM32, not a bare-metal HAL demo.
- **Results continuity**: `test_tracker.json` keys by `case_id`, so moving TCs under new dirs does not break tracker lookups. Only `boot-002` → `boot-uboot-001` needs a one-time key migration.

### Impact
- Complexity: **High** (touches 186 TC dirs, 10+ Python modules, CI, tracker, docs).
- Risk: **Medium** — mostly mechanical moves, but any hardcoded `cases/<flat-id>/` path left unchanged will silently fail discovery.
- Files changed: ~**200** (186 metadata.yaml edits + ~15 source/test/script edits + docs).
- Estimated effort: **8–10 hours** (bulk is the metadata migration script and verifying every consumer).

## Prior work

- `plans/PLAN-tc-restructure.md` — added `tier:` and `reasoning_types:` metadata fields. Same migration pattern (extend Pydantic model, batch-edit all metadata.yaml, update scorer/reporter) reused here for `sdk:`.
- `plans/PLAN-expand-categories.md` — category namespace evolution (`zephyr-kconfig` → `kconfig`). Demonstrates ID renames + tracker keepalive.
- `CLAUDE.md` (2026-03-29): "Content hashing must use file bytes, not st_mtime." Confirms `case_git_hash` is content-based, so `git mv` preserves hash identity — tracker stays valid after a move.
- `CLAUDE.md` (2026-02-15): "WSL2/NTFS Edit tool can corrupt files — use Write tool for full-file rewrites." Bulk metadata.yaml rewrites will use Write, not Edit.
- `src/embedeval/runner.py:67` — `discover_cases()` currently iterates one level (`cases_dir.iterdir()`), needs to become 2-level.
- `src/embedeval/models.py:73-88` — `EvalPlatform` enum already groups values by SDK in comments (`# Zephyr`, `# FreeRTOS`, `# STM32 HAL`, `# Linux`) — those comments become the basis of the `Sdk` enum.

## Problem analysis

### Current state

TC count and current flat layout (evidence from `cases/*/metadata.yaml`):

| Current category | Count | Target bucket | Notes |
|------------------|-------|---------------|-------|
| gpio-basic, dma, threading, kconfig, device-tree, ble, adc, uart, spi-i2c, pwm, isr-concurrency, networking, sensor-driver, memory-opt, power-mgmt, security, storage, timer, watchdog | ~150 | `zephyr/` | All tagged `[zephyr, …]`, platform `native_sim` or `qemu_arm`. |
| `boot-001`, `boot-003..008` | 7 | `zephyr/` | MCUboot on Zephyr. |
| `boot-002` | 1 | `embedded-linux/` | Actual U-Boot. **Rename** to `boot-uboot-001`. |
| `ota-001..011` | 9 | `zephyr/` | All Zephyr MCUboot/DFU. No renames. |
| `linux-driver-001..008` | 8 | `embedded-linux/` | Linux kernel modules, `docker_only` runtime. |
| `yocto-001..008` | 8 | `embedded-linux/` | BitBake recipes, `yocto_build` runtime. |
| `esp-gpio-001`, `esp-i2c-001`, `esp-spi-001`, `esp-timer-001`, `esp-wifi-001` | 5 | `esp-idf/` | ESP-IDF framework. |
| `stm32-gpio-001`, `stm32-i2c-001`, `stm32-spi-001`, `stm32-uart-001` | 4 | `stm32-hal/` | Bare-metal STM32 HAL. |
| `stm32-freertos-001` | 1 | `freertos/` | FreeRTOS-on-STM32. |
| **Total** | **~183** | 5 buckets | Exact count verified during migration. |

Target distribution: `zephyr` ≈ 159, `embedded-linux` = 17, `freertos` = 1, `esp-idf` = 5, `stm32-hal` = 4.

Problem surface:
- `src/embedeval/models.py:99` — no `sdk` field on `CaseMetadata`.
- `src/embedeval/runner.py:81` — `for case_dir in sorted(cases_dir.iterdir())` is 1-level; misses `cases/<sdk>/<case-id>/` layout.
- `src/embedeval/cli.py:145, 780, 833, 964, 1006, 1152, 1208, 1245` — all 8 subcommands default `cases_dir=Path("cases")`; none expose an SDK filter.
- `src/embedeval/reporter.py` — no per-SDK aggregation.
- `tests/test_tracker.py:155` — hardcoded `Path("cases/case-001")`. Not a real case, but migration script must not try to move non-existent dirs.
- External: `../embedeval-private/cases/` (48 held-out TCs) — same schema must be applied; bucket layout mirrored. Migration runs via CLI with explicit `--private-cases` path, so the same migration script is reused externally.

### Success criteria

- [ ] All public `cases/` TCs live under exactly one of `cases/{zephyr,embedded-linux,freertos,esp-idf,stm32-hal}/`.
- [ ] Every `metadata.yaml` has an `sdk:` field matching its parent bucket directory; Pydantic rejects mismatches.
- [ ] `uv run embedeval list --cases cases/` returns the same TC count as before the move (modulo the 1 renamed TC).
- [ ] `uv run embedeval list --cases cases/ --sdk zephyr` returns only Zephyr TCs; same for the other 4 buckets.
- [ ] `uv run embedeval validate --cases cases/` exits 0.
- [ ] `uv run pytest tests/` passes.
- [ ] `uv run embedeval run ...` for a single case produces the same pass/fail result as before the move (content hash identical).
- [ ] Report JSON contains a `per_sdk` block with pass@1 per bucket.
- [ ] `test_tracker.json` contains one migrated key (`boot-002` → `boot-uboot-001`) and retains all other keys.
- [ ] `scripts/sync_docs.py` outputs updated per-SDK counts in `README.md` and `docs/METHODOLOGY.md`.
- [ ] Private cases repo migrated with the same script and passes `embedeval validate --cases ../embedeval-private/cases/`.

## Design

### Approach

**Tool-driven migration with a single source of truth.**

Introduce a `cases/SDK_LAYOUT.yaml` manifest listing `<case-id> → <sdk>` for all 186 public TCs. A new `scripts/migrate_sdk_buckets.py` script reads the manifest and:
1. `git mv cases/<id>/ cases/<sdk>/<id>/` for every entry.
2. Rewrites each `metadata.yaml` to add `sdk: <bucket>` (using `Write`, not `Edit`, per WSL2 guidance).
3. For the single ID rename, `git mv cases/boot-002 cases/embedded-linux/boot-uboot-001/` and updates `id:` inside `metadata.yaml`.
4. Updates `test_tracker.json` with the one key rename.

The manifest gets checked in so the mapping is auditable and reproducible.

### Alternatives considered

- **Metadata-only, no dir move** — rejected: user explicitly asked for physical split; flat layout is the primary complaint.
- **3 buckets** (linux / rtos / bare-metal) — rejected: loses SDK-level discrimination that prompts and checks already depend on. Zephyr prompts differ structurally from ESP-IDF prompts even though both are "rtos."
- **Auto-classify from tags at runtime** — rejected: silent misclassification risk; tags are not validated. Explicit `sdk:` field + Pydantic enum catches errors at load.
- **Rename every `boot-*` to `boot-mcuboot-*` and every `ota-*` to `ota-mcuboot-*`** — rejected: creates noisy tracker-key churn for 16 TCs with no actual naming collision (no `ota-uboot-*` exists). Only the single ambiguous case (`boot-002`) gets renamed.

### Affected files

**Source (Python):**
- `src/embedeval/models.py` — add `Sdk` enum (5 values), add `sdk: Sdk` to `CaseMetadata`. Extend `Filters` dataclass with `sdks: list[Sdk]`.
- `src/embedeval/runner.py` — rewrite `discover_cases()` to walk 2 levels; update `filter_cases()` to honor `filters.sdks`.
- `src/embedeval/cli.py` — add `--sdk` option (repeatable or comma-separated) to 8 subcommands that take `--cases`.
- `src/embedeval/reporter.py` — aggregate pass@1 per `sdk`; emit `per_sdk` block in JSON + a Markdown table.
- `src/embedeval/scorer.py` — add `per_sdk_scores()` helper analogous to `per_category_scores()`.

**Scripts:**
- `scripts/migrate_sdk_buckets.py` (new) — the migration driver.
- `cases/SDK_LAYOUT.yaml` (new) — authoritative ID → SDK map.
- `scripts/sync_docs.py` — read new `per_sdk` data, emit per-SDK counts in README/METHODOLOGY.
- `scripts/verify_negatives_oracle.py`, `scripts/apply_scope_migration.py`, `scripts/audit_check_scope.py`, `scripts/sync_negatives_progress.py`, `scripts/verify_references_build.py`, `scripts/generate_expected_output.py` — switch from `iterdir()` to a shared `discover_cases(cases_root)` helper (import from `embedeval.runner`).

**Tests:**
- `tests/test_e2e.py`, `tests/test_bugfix.py`, `tests/test_negatives.py`, `tests/test_context_quality_mode_e2e.py`, `tests/test_expected_output.py`, `tests/test_tc_restructure.py`, `tests/test_esp_idf_support.py` — unchanged if they use `CASES_DIR` + `discover_cases`. Spot-verify each.
- `tests/test_tracker.py:155` — update `Path("cases/case-001")` fixture path (test uses a made-up ID; swap to `Path("cases/zephyr/case-001")`).
- `tests/test_sdk_buckets.py` (new) — verify every `metadata.yaml`'s `sdk:` equals its parent dir; verify `discover_cases` returns same count pre/post move; verify `--sdk` filter.

**Data / CI / docs:**
- `results/test_tracker.json` — single key rename `boot-002` → `boot-uboot-001`.
- `.github/workflows/*.yml` — grep for hardcoded `cases/<id>/` references; update if any. (Expected: none, since workflows call CLI.)
- `README.md` — replace the flat TC count table with per-SDK counts; regenerated by `sync_docs.py`.
- `docs/METHODOLOGY.md` — same; add a short paragraph on the SDK taxonomy.
- `CLAUDE.md` — add a "Learned Corrections" entry noting that `discover_cases` is now recursive.
- `cases/` — physical reorganization (186 `git mv` operations).

## Implementation phases

### Phase 1: Schema + discovery

- [x] Add `Sdk` enum to `src/embedeval/models.py` (5 values: `ZEPHYR`, `EMBEDDED_LINUX`, `FREERTOS`, `ESP_IDF`, `STM32_HAL`).
- [x] Add `sdk: Sdk` field to `CaseMetadata` (**required**, no default — forces migration to complete).
- [x] Add `sdks: list[Sdk] = field(default_factory=list)` to `Filters` in `runner.py`.
- [x] Rewrite `discover_cases()` to walk 2 levels: iterate `cases_dir.iterdir()`, for each entry that is a dir AND matches a known SDK name, descend one level; skip unrelated dirs silently. Log a warning if a `metadata.yaml` is found at the old 1-level location (transitional safety net).
- [x] Update `filter_cases()` to filter on `filters.sdks`.
- [x] Unit test: `tests/test_sdk_buckets.py::test_discover_is_recursive`.

Phase 1 ships the code skeleton; no case data is touched yet. After Phase 1, `pytest` still passes on the unchanged flat layout because `discover_cases` falls back when it sees case dirs at the top level.

### Phase 2: Manifest + migration script

- [x] Hand-author `cases/SDK_LAYOUT.yaml` listing every TC ID → SDK bucket. Derive from current tags and manual review; double-check `boot-*`, `ota-*`, `stm32-freertos-001`.
- [x] Write `scripts/migrate_sdk_buckets.py`:
  - Read manifest.
  - For each entry: `git mv <old-path> <new-path>`, rewrite `metadata.yaml` with new `sdk:` field (use Write tool semantics — full rewrite preserving existing keys).
  - Special-case `boot-002`: rename dir to `boot-uboot-001`, update `id:` in metadata.
  - Update `results/test_tracker.json` for the one renamed ID (rename key across all model sub-dicts).
  - Dry-run mode (`--dry-run`) prints the plan without touching files.
- [x] Run `--dry-run`, eyeball output, then execute.
- [x] Verify with `git status`: exactly 186 renamed files plus the metadata edits.

### Phase 3: CLI + reporter

- [x] Add `--sdk` option to `run`, `list`, `validate`, `agent` (main user-facing subcommands). **Deferred** for admin commands (`validate-metadata`, `list_categories`, `sensitivity`, `refresh-tracker`) — they operate on the whole corpus, where --sdk isn't load-bearing.
- [x] `scorer.py`: add `_calculate_sdk_scores(results) -> list[SdkScore]`.
- [x] `reporter.py`: emit a `## SDK Breakdown` section via `_sdk_breakdown()`; `BenchmarkReport.sdk_scores` carries the data to JSON.
- [x] `models.py`: extend `BenchmarkReport` with `sdk_scores: list[SdkScore]`; add `sdk: Sdk | None` to `EvalResult`.

### Phase 4: Scripts + tests

- [x] Refactor 7 consumer scripts (`sync_docs.py`, `verify_negatives_oracle.py`, `sync_negatives_progress.py`, `apply_scope_migration.py`, `audit_check_scope.py`, `classify_tiers.py`, `tag_reasoning_types.py`, `verify_references_build.py`, `generate_expected_output.py`) to use `iter_case_dirs` from `embedeval.runner` (added as a new helper alongside `discover_cases`).
- [x] `tests/test_tracker.py:155` untouched — test uses a tmp_path fixture, not the real cases layout.
- [x] Write `tests/test_sdk_buckets.py`:
  - Every loaded case's `metadata.sdk` matches its parent dir name.
  - `discover_cases(cases_root)` returns count matching `SDK_LAYOUT.yaml`.
  - `filter_cases(..., Filters(sdks=[Sdk]))` returns only that bucket.
  - `boot-uboot-001` present, `boot-002` absent.
- [x] Fix test fixtures: added `sdk=Sdk.ZEPHYR` / `"sdk": "zephyr"` to `test_bugfix`, `test_checkpoint`, `test_cli_merge`, `test_new_features`, `test_runner`, `test_evaluator`, `test_esp_idf_support`.
- [x] Update `tests/test_e2e.py` and `tests/test_tc_restructure.py` to walk via `iter_case_dirs` instead of `CASES_DIR.iterdir()`.
- [x] Run full gate: `ruff format --check src/` ✓, `ruff check src/` ✓, `mypy src/` ✓, `pytest tests/` 1131 passed / 4 skipped.

### Phase 5: Private cases + docs

- [ ] Run `scripts/migrate_sdk_buckets.py --cases ../embedeval-private/cases/ --manifest <private-manifest>` on the private repo. **Deferred** — separate commit/branch in the private repo; needs its own SDK_LAYOUT.yaml.
- [x] Update `scripts/sync_docs.py` to collect `sdks` Counter; `README.md` regenerated.
- [ ] Manually edit `docs/METHODOLOGY.md` to add a short "SDK taxonomy" subsection. **Deferred** — to be added in /wrapup.
- [x] Append a `CLAUDE.md` Learned Corrections entry documenting `iter_case_dirs` + the `sdk:` field contract.
- [x] `.claude-verify.sh` updated — pilot case paths now live under `cases/zephyr/`.

## Testing strategy

- **Unit tests:** 
  - `tests/test_sdk_buckets.py` — new file covering discovery, filter, metadata-vs-dir consistency, and CLI `--sdk` filter.
  - Extend `tests/test_tc_restructure.py` — verify `sdk` field is present on every loaded metadata, bucket counts match manifest.
- **Integration:** 
  - Pre/post snapshot test: run `embedeval run --cases cases/ --cases-filter kconfig-001 --model mock` before and after the move; `case_git_hash` and pass/fail result must be identical (proves content-hash invariance under `git mv`).
  - Per-SDK filtering: run the benchmark with `--sdk freertos` and confirm exactly 1 TC is evaluated.
- **Quality gates (mandatory before commit):**
  - `uv run ruff format --check src/ tests/`
  - `uv run ruff check src/ tests/`
  - `uv run mypy src/`
  - `uv run pytest tests/`
- **Doc sync:** `uv run python scripts/sync_docs.py` — must run because `cases/` changed. Commit the regenerated docs in the same commit as the migration.
- **Smoke test:** `uv run embedeval list --cases cases/` and `uv run embedeval validate --cases cases/` after migration — both must succeed.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| A hardcoded `cases/<flat-id>/` path in a script or test is missed, silently breaking after move. | Medium | Grep for `cases/[a-z]` regex across the repo before Phase 2; add a transitional warning log in `discover_cases` if a metadata.yaml is found at the old 1-level location (catches stragglers at runtime). |
| Misclassification in `SDK_LAYOUT.yaml` (e.g., a disguised MCUboot TC moved to embedded-linux). | Medium | Hand-review each `boot-*`, `ota-*`, and any TC whose tags contain both `zephyr` and `uboot`/`linux`. Pydantic `sdk:` field mismatch-vs-parent-dir triggers a test failure. |
| Content hash changes unexpectedly (tracker keys go stale). | High if it happens | `case_git_hash` is byte-content–based, not path-based (per CLAUDE.md 2026-03-29) — `git mv` preserves bytes, but the `sdk:` field edit to `metadata.yaml` **will** change the hash. Expected and acceptable: tracker already handles hash drift via the existing content-hash mechanism. Verify via the pre/post snapshot integration test. |
| Renaming `boot-002` → `boot-uboot-001` loses historical benchmark results for that TC. | Low | One-time key rename inside `migrate_sdk_buckets.py`. Annotate the tracker entry with a migration comment. |
| Private cases repo drifts out of sync with public schema. | Medium | Same migration script runs on both repos via `--cases` argument; Pydantic `sdk:` required field forces compliance at load time. |
| Regex-based case-ID matching in `.github/workflows/*.yml` breaks. | Low | Grep workflows for `cases/` paths in Phase 0; expected to find nothing because workflows invoke the CLI. If any are found, either fix or convert to CLI invocation. |
| ESP-IDF and STM32-HAL buckets are too thin (4–5 TCs) to produce meaningful per-SDK pass@1 in the reporter. | Low | Reporter still emits the block; add a `n_cases` field and a CLI-visible caveat when `n < 8`. Future plan (out of scope) can expand these buckets. |

## Review checklist (verify before /execute)

- [ ] Scope correct — 5 buckets, physical split, classify-only, boot/ota disambiguation handled as `boot-002` rename only.
- [ ] Design sound — recursive discovery falls back to 1-level during transition; Pydantic required field forces complete migration.
- [ ] Affected-files list complete — models, runner, cli, scorer, reporter, 6 scripts, 7 tests, 1 new test file, 1 manifest, 1 migration script, README, METHODOLOGY, CLAUDE.md, tracker JSON, workflow grep.
- [ ] Tests cover every success criterion — discovery, filter, CLI, per-SDK reporting, content-hash invariance under move, tracker key migration.
- [ ] Risks identified with mitigations — 7 risks, each with a concrete mitigation.
- [ ] Private-cases migration strategy explicit — same script, invoked with `--cases ../embedeval-private/cases/`.
- [ ] Doc-sync invoked (mandatory per CLAUDE.md because `cases/`, `src/`, `tests/` all change).
