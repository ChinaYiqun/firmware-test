# Hiloop Handoff — EmbedEval Producer-Side Interop Contract

**Last updated:** 2026-04-19
**Source of truth for:** schemas, file paths, stability tiers of every EmbedEval artifact consumed by downstream interop tools (primarily [Hiloop](https://github.com/Ecro/hiloop) but applicable to any third-party transpile / evidence-injection pipeline).

This document is the **producer-side mirror** of Hiloop's [`CONTRACT.md §2`](../../hiloop/CONTRACT.md) (assumes sibling checkout at `~/hiloop`). The schemas live in EmbedEval; Hiloop's CONTRACT documents the consumer-side snapshot tests that freeze each surface. **When these two docs disagree, EmbedEval wins** — change the Hiloop CONTRACT to match, then the snapshot tests will tell you which landed rules need re-transpile.

---

## §1 Surface inventory

EmbedEval exposes six interop surfaces. Every surface carries an explicit stability tier:

| # | Surface | Path | Stability tier |
|---|---------|------|----------------|
| 1 | Case metadata | `cases/<sdk>/<case-id>/metadata.yaml` | **stable** (schema is `extra="forbid"`) |
| 2 | Check modules | `cases/<sdk>/<case-id>/checks/{static,behavior}.py` | **stable** (`run_checks` signature + `check_name` immutability) |
| 3 | Mutation oracle | `cases/<sdk>/<case-id>/checks/negatives.py` | **stable** (`NEGATIVES` list-of-dict schema) |
| 4a | Per-check metrics (row shape) | `results/runs/<run-id>/per_check_metrics.json` | **additive-only** (pinned `schema_version`) |
| 4b | Per-check aggregate (in summary.json) | `results/runs/<run-id>/summary.json` → `models[*].per_check_stats` | **additive-only** (via `BenchmarkReport.version`) |
| 5 | Leaderboard | `results/LEADERBOARD.md` | **stable** (pinned `schema_version` HTML comment) |
| 6 | Forbidden APIs | `src/embedeval/data/forbidden_apis.yaml` | **additive-only** (platform buckets + entries) |

Stability-tier meaning:

- **stable** — breaking a field, renaming, or changing semantics requires a `schema_version` bump + migration artifact. Joint Hiloop/EmbedEval release.
- **additive-only** — new fields OK within the current `schema_version`; removing or renaming is a breaking change.
- **internal** — not exposed in this doc; embedeval-only, may change freely.

---

## §2 Schemas

### §2.1 `cases/<sdk>/<case-id>/metadata.yaml` → `CaseMetadata`

**Python model:** `src/embedeval/models.py:CaseMetadata`
**Loaded by:** `src/embedeval/runner.py`
**Path layout:** `cases/<sdk>/<case-id>/metadata.yaml` where `<sdk>` ∈ `{zephyr, embedded-linux, freertos, esp-idf, stm32-hal}`. Use `embedeval.runner.iter_case_dirs(cases_root)` — it walks both the SDK-bucket layout and the legacy flat layout.

**Required fields:**

| Field | Type | Hiloop use |
|-------|------|------------|
| `id` | `str` | Rule ID prefix (`EMBED-<id>-...`) |
| `category` | `CaseCategory` enum | Pack derivation (`isr` → `@embedeval/isr`) |
| `difficulty` | `easy \| medium \| hard` | Severity heuristic |
| `title` | `str` | Rule name seed |
| `description` | `str` | LLM transpile prompt context |
| `tags` | `list[str]` | Rule tag seed |
| `platform` | `EvalPlatform` enum (`native_sim`, `esp_idf`, `stm32_hal`, `yocto_build`, `docker_only`, `qemu_arm`, `qemu_freertos`, `qemu_linux`, `babblesim`) | Path-glob hint |
| `sdk` | `Sdk` enum (`zephyr`, `embedded-linux`, `freertos`, `esp-idf`, `stm32-hal`) | SDK bucket — must match parent dir |
| `estimated_tokens` | `int` | Prompt budget check |
| `sdk_version` | `str` | Informational |

**Optional fields** (present on a subset):

- `visibility: "public" | "private"` (default `public`)
- `created_date: str | None` (ISO date, e.g. `"2026-03-24"`)
- `tier: CaseTier` (default `core`; `sanity`/`core`/`challenge`)
- `reasoning_types: list[ReasoningType]`
- `build_board: str | None` (e.g. `"nrf52840dk/nrf52840"`)
- `l1_skip: bool` (default `false`)
- `l2_skip: bool` (default `false`)

**Extra fields: FORBIDDEN.** `CaseMetadata` Pydantic model uses the default `extra="ignore"` Pydantic behavior, but Hiloop's `CaseSpec` consumer uses `extra="forbid"`. **Adding a new field in EmbedEval is a Hiloop-breaking change** until Hiloop's `CaseSpec` is widened in the same release.

**Example:**

```yaml
id: "isr-concurrency-008"
category: "isr-concurrency"
difficulty: "hard"
title: "Lock-free SPSC ring queue"
description: "Single-producer single-consumer ring buffer with atomic indices and memory barriers."
tags: ["zephyr", "isr", "lock-free", "ring-buffer"]
platform: "native_sim"
sdk: "zephyr"
estimated_tokens: 400
sdk_version: "4.1.0"
tier: "challenge"
reasoning_types: ["memory-model", "concurrency"]
```

### §2.2 `cases/<sdk>/<case-id>/checks/static.py` + `checks/behavior.py`

**Consumed by:** Hiloop's transpile script reads both files as raw text for LLM prompt input. **Hiloop does NOT exec these** — the interpreter boundary is an intentional defense.

**Required contract:**

Each file defines `run_checks(generated_code: str) -> list[CheckDetail]`. The return-list must contain `CheckDetail` objects (see §2.4 `CheckDetail` shape below).

**Key invariants:**

- **`check_name` values are stable.** Renaming a `check_name` in static.py/behavior.py orphans every landed Hiloop rule using that name (via `metadata.source_check_name` on the emitted YAML). Treat `check_name` like a public API identifier — rename requires a migration entry (see §4).
- **Use `scoped_contains(code, needle, scope=...)` instead of `needle in code`.** REQ-03 policy. Default `scope='stripped'` strips comments AND string literals (safest). Use `scope='code_only'` for `#include "x.h"` style matches where the string literal must survive. Use `scope='raw'` for non-C rule files (Yocto `.bb`, udev `.rules`).
- **No unscoped substring checks.** CI enforces this via `scripts/audit_check_scope.py --strict` in `.github/workflows/validate-cases.yml` — PRs that re-introduce `"x" in generated_code` fail.

**Shared helpers** (in `src/embedeval/check_utils.py`) that Hiloop's prompt template knows about via regex-filter few-shots: `strip_comments`, `strip_string_literals`, `scoped_contains`, `extract_function_body`, `find_isr_bodies`, `check_no_cross_platform_apis`, `udev_rule_matches`, `udev_rule_assigns`, `udev_match_key_used_as_assign`. **Adding a new shared helper requires either a Hiloop prompt update or a new assertion mode in Hiloop.**

**`CheckDetail` schema (src/embedeval/models.py:164):**

```python
class CheckDetail(BaseModel):
    check_name: str         # STABLE — see REQ-06
    passed: bool
    expected: str | None
    actual: str | None
    check_type: str         # "exact_match" | "constraint" | "behavioral" | "mutation" | ...
    weight: float = 1.0     # ≥0
```

`check_type == "mutation"` is reserved for L4 synthetic checks and is **excluded** from per-check metrics (see §2.4 note). Authors MUST NOT set `check_type="mutation"` manually.

### §2.3 `cases/<sdk>/<case-id>/checks/negatives.py` → mutation oracle input

**Consumed by:** `src/embedeval/evaluator.py` (internal) + Hiloop's `interop.negatives` (external).

**Required contract:**

Module-level symbol `NEGATIVES: list[dict]`. Each dict has:

| Key | Type | Required | Meaning |
|-----|------|----------|---------|
| `name` | `str` | yes | Unique within the TC |
| `mutation` | `Callable[[str], str]` | yes | Applied to the reference source — must produce code that differs from input |
| `must_fail` | `list[str]` | one-of | `check_name` labels that MUST fail on the mutated code |
| `should_fail` | `list[str]` | one-of | Soft negative: labels the check SHOULD flag but may legitimately miss |
| `description` | `str` | no | Human-readable bug explanation |
| `bug_description` | `str` | no | Used for `should_fail` — explains why the check may miss |
| `factor_id` | `str` | no | Reference to `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` (e.g., `"F3.2"`) |

At least one of `must_fail` / `should_fail` is required.

**Security note:** Hiloop loads `negatives.py` via `importlib` (which executes top-level code). Running against untrusted TCs is a code-execution risk. See Hiloop's Request REQ-06 for proposed tightening (AST-only parse of the `NEGATIVES` list, no code execution).

**Breaking changes:**

- Renaming `mutation` → `mutate_fn` or similar top-level key.
- Removing `NEGATIVES` symbol or re-exporting under a different name.
- Changing `must_fail` / `should_fail` to dicts-of-strings or any other shape.

### §2.4 Per-check metrics — two artifacts, two shapes

Per-check data is emitted in **two separate files** with different groupings. Consumers should pick the shape that matches their analysis grain.

#### §2.4a `results/runs/<run-id>/per_check_metrics.json` — per-(TC, check, model) rows

**Produced by:** `src/embedeval/reporter.py:generate_per_check_metrics`
**CLI write site:** `src/embedeval/cli.py:537`
**Path:** `<output_dir>/runs/<run-id>/per_check_metrics.json` — NOT `<output_dir>/per_check_metrics.json`. An n=3 benchmark writes three separate files, one per run. Consumers traversing `runs/*/per_check_metrics.json` get deterministic correlation to the run archive.

```json
{
  "schema_version": 1,
  "run_id": "<uuid-or-null>",
  "generated": "2026-04-19T12:34:56Z",
  "rows": [
    {
      "case_id": "isr-concurrency-008",
      "category": "isr-concurrency",
      "check_name": "memory_barrier_present",
      "model": "claude-code://sonnet",
      "samples": 3,
      "passed": 2,
      "pass_rate": 0.6666666666666666
    }
  ]
}
```

- Rows are per `(case_id, check_name, model)` — the finest grain.
- Rows sorted by `pass_rate` ascending, then `case_id`, `check_name`, `model` — deterministic.
- `check_type == "mutation"` checks are **excluded** (L4 synthetic).

#### §2.4b `results/runs/<run-id>/summary.json` → `models[*].per_check_stats` — per-(check, category, model) aggregate

**Produced by:** `src/embedeval/scorer.py:_calculate_per_check_stats`, embedded in the `BenchmarkReport` Pydantic dump (`src/embedeval/reporter.py:generate_json`).

**Pydantic model:** `src/embedeval/models.py:PerCheckStat` (line 207). Full JSON shape via `model_dump()`:

```json
{
  "check_name": "memory_barrier_present",
  "category": "isr-concurrency",
  "total_runs": 12,
  "fail_count": 4,
  "pass_rate": 0.6666666666666666,
  "failing_tc_ids": ["isr-concurrency-003", "isr-concurrency-008"]
}
```

- Aggregated per `(check_name, category)` within a single model's results — coarser than §2.4a.
- `failing_tc_ids` is the distinct set of TC IDs where the check failed at least once — useful for triage.
- `check_type == "mutation"` checks are **excluded** (same rule as §2.4a).

**Stability: additive-only within schema_version=1 for both artifacts.** New row/field keys (e.g., `case_git_hash`) may be added without a version bump. Removing or renaming any existing key → bump to `schema_version=2`. Note: only `per_check_metrics.json` carries an explicit `schema_version` field today; `summary.json` inherits its version from the `BenchmarkReport.version` field.

### §2.5 `results/LEADERBOARD.md`

**Produced by:** `src/embedeval/reporter.py:generate_leaderboard` (writes `<!-- SCHEMA_VERSION: 1 -->` HTML comment after the top H1).

**Consumed by:** Hiloop's `interop.leaderboard.parse_leaderboard`.

**Parse contract:**

- File at `<embedeval>/results/LEADERBOARD.md`.
- HTML comment `<!-- SCHEMA_VERSION: 1 -->` near the top — consumers MUST assert and fail loudly on unknown versions. Current: `LEADERBOARD_SCHEMA_VERSION = 1`.
- Section `## Category Results` with `### <model-id>` subsections, each containing a markdown table of columns: `Category | Pass Rate | Passed | Total | Status`.
- Cell shapes: `Pass Rate` ends in `%`; `Passed`/`Total` are integers; `Status` is a short enum string.

**Breaking changes** (require `schema_version` bump):

- Removing the `## Category Results` section or its subsection structure.
- Changing column order, renaming columns, or changing cell-value semantics.
- Switching to a different file path (`LEADERBOARD.json`, etc.).

Pass rate is **category-aggregated** by construction. Hiloop stamps `evidence_scope="category"` on every parsed rate. For per-TC evidence, consumers should read `per_check_metrics.json` (§2.4) instead.

### §2.6 `src/embedeval/data/forbidden_apis.yaml`

**Produced by:** hand-authored data file (not generated).
**Consumed by:** `src/embedeval/check_utils.py:check_no_cross_platform_apis` + any downstream tool needing the same blacklist (Hiloop shared rule pack).

**Schema:**

```yaml
platforms:
  <platform-name>:
    - <api-identifier>
    - "<api-identifier(>"   # Trailing "(" makes it a raw substring match;
                            # otherwise word-boundary match via has_api_call()
```

**Current platforms** (as of 2026-04-19): `FreeRTOS`, `Arduino`, `STM32_HAL`, `POSIX`, `Linux_Userspace`. Canonical list lives in the file itself — always read it at consumer startup rather than caching a fork of the platform list.

**Stability: additive-only.**

- Adding a new platform bucket: non-breaking.
- Adding an API entry to an existing bucket: non-breaking.
- Removing a platform or entry: breaking (downstream rules referencing it orphan).
- Changing the top-level key `platforms` → anything else: breaking.

Hiloop's shared rule pack reads this file and emits equivalent YAML rules; byte-identical meaning with the old hardcoded `CROSS_PLATFORM_FORBIDDEN` dict in `check_utils.py` is a contract.

---

## §3 Run-scoped artifact layout

When `embedeval run` completes, artifacts are written under `<output_dir>/runs/<run-id>/`:

```
results/
├── LEADERBOARD.md                 # Flat — always latest (§2.5)
├── LEADERBOARD_PER_CHECK.md       # Flat — always latest
├── history.json                   # Cross-run history
└── runs/
    └── 2026-04-19_sonnet-n3/
        ├── summary.json           # Full BenchmarkReport (includes models[*].per_check_stats)
        ├── per_check_metrics.json # Per-run row shape (§2.4)
        ├── report.md              # Human-readable narrative
        └── details/               # .gitignore'd — per-TC generated_code
```

**Run-scoped artifacts MUST live under `runs/<run-id>/`.** Writing to the flat root causes an n=3 invocation to overwrite n1/n2 silently (CLAUDE.md learned correction 2026-04-19). Hiloop's `interop.leaderboard` correlates the per-check file with the run archive via this path convention.

---

## §4 Breaking-change protocol

### §4.1 Pinned `schema_version` fields

| Artifact | Symbol | Current | Location |
|----------|--------|---------|----------|
| `per_check_metrics.json` | `PER_CHECK_METRICS_SCHEMA_VERSION` | `1` | `src/embedeval/reporter.py:43` |
| `LEADERBOARD.md` | `LEADERBOARD_SCHEMA_VERSION` | `1` | `src/embedeval/reporter.py:38` |

Bumping either requires:

1. Change the Python constant.
2. Update `tests/test_per_check_stats.py` / `tests/test_reporter.py` fixtures.
3. Cross-post in Hiloop as a CONTRACT.md migration note (`~/hiloop/CONTRACT.md §4`).
4. Migration script in `scripts/` that converts v1 → v2 for archived runs — optional for pre-v1 data but required for forward compatibility.

### §4.2 `check_name` immutability (REQ-06)

Once a `check_name` appears in a released TC, treat it as a **public API identifier**:

- **Do NOT rename** a published `check_name` without a migration entry.
- **Do NOT delete** a `check_name` without removing or renaming the corresponding negatives' `must_fail`/`should_fail` labels.
- If a rename is unavoidable, emit a `check_name_migrations:` mapping in a machine-readable file (proposed — not yet standardized; coordinate with Hiloop before introducing).

`scripts/audit_check_names.py` (Hiloop-side) surfaces unmapped labels at transpile time.

### §4.3 Additive changes within schema_version=1

The following are **non-breaking** and may land without coordination:

- New TC directories (`cases/<sdk>/<new-id>/`).
- New entries in `forbidden_apis.yaml` (new platform bucket or new API).
- New optional fields in `CaseMetadata` Pydantic model, provided the YAML file stays loadable with the field absent.
- New columns in `per_check_metrics.json` rows.
- New `check_type` values, provided `"mutation"` semantics (§2.2 exclusion) stay invariant.

### §4.4 Change announcement

Breaking changes are announced via:

1. A `docs/BENCHMARK-DELTA-<date>.md` entry summarizing the change and any flipped pass@1 numbers.
2. The `schema_version` bump (where applicable).
3. A matching CONTRACT.md entry on Hiloop side once the consumer is upgraded.

---

## §5 Mirror doc cross-reference

Hiloop's [`CONTRACT.md §2`](../../hiloop/CONTRACT.md) is the consumer-side mirror of this document:

| This doc section | Hiloop CONTRACT.md section |
|------------------|----------------------------|
| §2.1 CaseMetadata | §2.1 CaseSpec pydantic model |
| §2.2 static/behavior.py | §2.2 transpile input |
| §2.3 negatives.py | §2.3 mutation oracle input |
| §2.4a/b per-check artifacts | REQ-04 (Hiloop `interop.leaderboard` per-rule `aggregate_failure_rate`) |
| §2.5 LEADERBOARD.md | §2.4 evidence injection |
| §2.6 forbidden_apis.yaml | §2.8 shared rule pack data |

Hiloop pins each surface via snapshot tests under `~/hiloop/tests/contracts/`. When this doc changes, run `uv run pytest tests/contracts/` on the Hiloop side — failing snapshots identify where consumer updates are needed.

---

## §6 REQ status (Hiloop → EmbedEval requests)

As of 2026-04-19:

| REQ | Status | Landed in |
|-----|--------|-----------|
| [REQ-01](../../hiloop/docs/embedeval-requests/REQ-01-negatives-coverage.md) negatives coverage → 100% | in progress | 77/219 authored; tracked under PLAN-hiloop-transpile-readiness Phase 4 P1 |
| [REQ-02](../../hiloop/docs/embedeval-requests/REQ-02-per-check-mutation-coverage.md) per-check mutation coverage | **merged** | `scripts/verify_negatives_oracle.py` + `plans/coverage-grandfather.txt` |
| [REQ-03](../../hiloop/docs/embedeval-requests/REQ-03-substring-scope-consistency.md) substring scope consistency | **merged** | `scoped_contains` + 1991-span migration + CI gate |
| [REQ-04](../../hiloop/docs/embedeval-requests/REQ-04-per-check-failure-metrics.md) per-check failure metrics | **merged** | `PerCheckStat` + `per_check_metrics.json` |
| [REQ-05](../../hiloop/docs/embedeval-requests/REQ-05-leaderboard-schema-version.md) LEADERBOARD schema_version | **merged** | `LEADERBOARD_SCHEMA_VERSION = 1` in HTML comment |
| [REQ-06](../../hiloop/docs/embedeval-requests/REQ-06-check-name-immutability.md) check_name immutability | **merged** | This doc §4.2 + `plans/coverage-grandfather.txt` |

---

## Maintenance

This doc is reviewed annually or whenever a `schema_version` bumps. Last review: 2026-04-19.

When adding a new interop surface: (a) add a row to §1, (b) write a §2.N subsection with path + required/optional fields + stability tier, (c) cross-post to Hiloop's CONTRACT.md with the mirror mapping in §5.
