---
type: plan
task_slug: linux-tc-expansion-phase-a
status: planning
created: 2026-04-19
tags: [embedeval, plan, linux-driver, yocto, u-boot, tc-authoring]
---

# PLAN: Linux TC Expansion — Phase A (kernel depth + yocto advanced + u-boot breadth)

**Task:** Add 15 Linux test cases — 8 linux-driver + 4 yocto + 3 boot-uboot — to target the 42-factor gaps that current 17 Linux TCs leave uncovered, while preserving the 35%p implicit-prompt discipline and n=3 flaky-case methodology. **Pinned to the user's real BSP:** Yocto 4.0 kirkstone + linux-imx 5.15 LTS + u-boot-imx 2022.04 on NXP i.MX8M Plus (reference environment at `~/EDGE/sources`).
**Created:** 2026-04-19

## Executive summary

**TL;DR:** Add 15 new Linux TCs (**kernel 5.15 LTS + Yocto kirkstone 4.0 + u-boot-imx 2022.04**) covering RCU-safe context, workqueues, threaded IRQ, `devm_*` cleanup, `IS_ERR`/`PTR_ERR`, regmap, meta-layers, `.bbappend` overrides, kernel-config fragments, `PACKAGECONFIG`, FIT images, extlinux/distro_boot, and verified boot — all implicit prompts, all with 12-mutation oracles, all `docker_only`/`yocto_build`.

### What

Author 15 new test cases split across three existing categories and one SDK bucket (`embedded-linux`):

- **8 `linux-driver`** — `linux-driver-009..016`: kernel concurrency, work deferral, managed resources, error-idiom propagation, regmap adoption
- **4 `yocto`** — `yocto-009..012`: layer infrastructure, override syntax, kernel-config fragment, feature flags
- **3 `boot`** — `boot-uboot-002..004`: FIT, distro_boot, verified boot

Each TC ships with the standard shape observed in `linux-driver-007/` et al: `metadata.yaml`, `prompt.md`, `reference/main.c` (or `.bb` / `.its`), `src/main.c` placeholder, `checks/{static,behavior,negatives}.py`, empty `context/`. Every TC carries a ≥12-entry mutation oracle as per the recent `yocto-005..007` convention.

### Why

Current 17 Linux TCs leave these failure-factor cells empty:
- **D4/D5/D6/D8** for Linux (spinlock IRQ-save, RCU, completion, lockdep) — only Zephyr-side coverage exists
- **E1/E3** for `devm_*` managed resources (matches CVE-2026-23068 class)
- **E2/E6** for `IS_ERR`/`PTR_ERR` error idiom (kernel-specific)
- **F2/F4** for regmap + i2c_driver v6.6 API (modern vs legacy)
- **F6** for Yocto layer infra, override syntax, kernel fragments, PACKAGECONFIG
- **E4/F6** for U-Boot FIT/distro_boot/verified boot

Benchmark data: `linux-driver 70%/70%` (Haiku/Sonnet) is the most discriminating category — depth investment here returns the highest per-TC signal. Academic LLM+Linux benchmarks (Live-kBench arXiv 2602.02690) focus on *crash repair*, not generative drivers; EmbedEval's generative-driver angle differentiates. Yocto LLM benchmarks: academic search returned zero results — any Yocto depth is uniquely positioned.

### Key decisions

- **Scope fixed to Phase A only.** linux-userspace (libgpiod v2, systemd/udev/D-Bus/eBPF) is explicitly Phase B, documented in "Future work" and not implemented here. Reason: enum expansion (`CaseCategory.LINUX_USERSPACE`) has O(repo) blast radius (reporter, scorer, SDK_LAYOUT, per_check_metrics, docs); keep Phase A mechanical and unblocking.
- **Kernel pinned to 5.15 LTS (linux-imx 5.15).** Matches the user's real BSP at `~/EDGE/sources/meta-freescale/recipes-kernel/linux/linux-imx_5.15.bb` and `~/EDGE/sources/meta-qcells-bsp-emsplus/recipes-kernel/linux/linux-imx_%.bbappend`. API facts for 5.15: `class_create(THIS_MODULE, name)` is 2-arg (6.4+ dropped THIS_MODULE); `proc_ops` replaces `file_operations` for procfs (stable since 5.6); regmap/devm/request_threaded_irq/kthread/workqueue APIs all stable; i2c `probe_new` signature modern form. Reason: realism against user's working environment; existing `linux-driver-001..008` use `sdk_version: '6.6'` but we **do not retrofit them** (would re-hash 8 TCs) — only new TCs target 5.15.
- **All new prompts are implicit.** Never say "use `devm_kzalloc`" or "use `request_threaded_irq`"; state behavior + context (e.g. "this probe may be called on a CPU also servicing IRQs for this driver"). Reason: 35%p explicit/implicit gap (M3); current `linux-driver-007` over-specifies (`CRITICAL: Use dma_alloc_coherent — NEVER use kmalloc`). New TCs steer the middle.
- **No new `Sdk` / `CaseCategory` enum entries.** All 15 TCs reuse existing categories (`linux-driver`, `yocto`, `boot`). Reason: avoids scorer/reporter/SDK_LAYOUT churn; Phase A remains additive-only.
- **Every TC gets a 12-entry mutation oracle.** Matches `yocto-005..007` convention established in commits 55bf..7be5..6742 (Apr 17-19, 2026). Reason: mutation coverage is the negative-robustness signal; under 10 creates blind spots.
- **New shared check helpers in `src/embedeval/check_utils.py`.** Add `has_devm_alloc_without_manual_free`, `has_is_err_guard`, `has_regmap_api`, `in_init_scope_only`, `has_sleepable_in_atomic_ctx` — reused across ≥3 new TCs each. Reason: per CLAUDE.md "Check regexes must accept API variants" + "Use find('func(') not find('func')" — shared utilities prevent per-TC regex drift.
- **Benchmark re-run scope: Phase A delta only.** Existing 233 TC `case_git_hash` values are unchanged (additive); re-run the new 15 TCs only against Haiku + Sonnet n=3. Reason: CLAUDE.md 2026-04-19 warns migrations force full re-run; additive does not.

### Impact

- Complexity: **Medium**
- Risk: **Low** (additive; no enum changes; no re-hashing of existing TCs)
- Files changed: **~95** (15 TCs × 6 files + check_utils + SDK_LAYOUT + 2 docs)
- Estimated effort: **9–12 hours** implementation + 2–3 hours baseline benchmark

## Prior work

- [plans/PLAN-expand-categories.md](PLAN-expand-categories.md) — established `linux-driver` + `yocto` categories (Mar 23). Confirms enum expansion is a last resort; Phase A honors that.
- [plans/PLAN-create-all-test-cases.md](PLAN-create-all-test-cases.md) — TC-authoring template. CMakeLists template does not apply to Linux cases (non-compilable by west build); `platform: docker_only` skips L1/L2 per CLAUDE.md 2026-03-30.
- [plans/PLAN-implicit-prompts.md](PLAN-implicit-prompts.md) — 35%p gap rationale. Applied to every new prompt: functionality + context only, never API names.
- [plans/PLAN-strengthen-tc-checks.md](PLAN-strengthen-tc-checks.md) + [plans/PLAN-deep-embedded-checks.md](PLAN-deep-embedded-checks.md) — checks must accept API variants (use `has_any_api_call`) and resolve `#define` macros. New helpers follow suit.
- [plans/PLAN-remaining-blindspots.md](PLAN-remaining-blindspots.md) — `linux-001`'s `init_error_path_cleanup` was bypassed because the same call existed in `__exit`. New helpers (`in_init_scope_only`) codify the `__init`-scope-only pattern so every new linux-driver TC avoids that blind spot by construction.
- [plans/PLAN-sdk-bucket-split.md](PLAN-sdk-bucket-split.md) — confirms content-hash is byte-stable; additive TC entries do not alter existing hashes.
- [plans/PLAN-negative-tests.md](PLAN-negative-tests.md) + [plans/PLAN-subtle-negatives.md](PLAN-subtle-negatives.md) — oracle targeting `must_fail` check-names + `factor_id`. Reuse format verbatim.

**CLAUDE.md 2026-04-19 corrections directly applied:**
- `scoped_contains` default strips string literals — use `scope='code_only'` for `#include "linux/..."` matching.
- Yocto `.bb` files use `#` line comments; `strip_comments` is C-specific and mishandles `file://`/`git://` URIs — use `scope='raw'` for Yocto recipe checks.
- Every new `metadata.yaml` carries the required `sdk:` field.

## Problem analysis

### Current state

17 Linux TCs as of 2026-04-19:

| Category | TCs | Covered factors | Gaps |
|----------|-----|----------------|------|
| `linux-driver` (8) | 001 chardev, 002 platform+DT, 003 IIO, 004 IRQ+waitqueue, 005 sysfs DEVICE_ATTR, 006 ioctl uaccess, 007 dma_alloc_coherent, 008 procfs seq_file | A7, C5, D5 (narrow), E1 (one TC), E2 (narrow), F1, F3, F5 | D4 IRQ-safe locks, D6 RCU, D8 lockdep, C3 GFP context, E1 devm vs manual, E2 `IS_ERR`, F2 i2c_driver v6.6, F4 regmap, workqueue/kthread/threaded-IRQ entire |
| `yocto` (8) | 001 hello.bb, 002 cmake.bbclass, 003 systemd.bbclass, 004 DEPENDS/RDEPENDS, 005 out-of-tree module, 006 SRC_URI patch, 007 image recipe, 008 SPDX | F6 basic recipe | F6 layer infra, `.bbappend` override, kernel config fragment, PACKAGECONFIG, FILES split, CVE_CHECK, populate_sdk |
| `boot` uboot (1) | boot-uboot-001 defconfig | F6 defconfig | FIT, distro_boot, verified boot, env mgmt, SPL |

Structural facts:
- Every TC: `metadata.yaml`, `prompt.md`, `src/main.c`, `reference/main.c`, `checks/{static,behavior,negatives}.py`, empty `context/` — see `cases/embedded-linux/linux-driver-007/` (canonical).
- `discover_cases()` at `src/embedeval/runner.py:97` walks 2-level SDK-bucket layout and accepts any dir with `metadata.yaml` under `cases/embedded-linux/`.
- `CaseCategory` enum at `src/embedeval/models.py:8` — LINUX_DRIVER, YOCTO, BOOT all present.
- `CheckDetail` schema at `src/embedeval/models.py:163` — each check emits `{check_name, passed, expected, actual, check_type, weight}`.
- Shared helpers at `src/embedeval/check_utils.py` (421 lines) — `scoped_contains`, `extract_function_body`, `check_cleanup_reverse_order`, `has_any_api_call`, `has_error_check`. New helpers must fit this module's style.
- `scripts/sync_docs.py` updates TC count in `docs/METHODOLOGY.md` and `README.md`.
- `scripts/verify_references_build.py` + `scripts/verify_negatives_oracle.py` are the two repo-wide validators that must pass for every new TC.

### Success criteria

- [ ] 15 new TCs exist under `cases/embedded-linux/` with complete 6-file layout.
- [ ] Each `metadata.yaml` validates against `CaseMetadata` pydantic model, carries `sdk: embedded-linux`, `platform: docker_only` (linux-driver) or `yocto_build` (yocto) or `native_sim` (boot), and a `sdk_version` — **kernel `5.15`, Yocto `kirkstone` (4.0.4), U-Boot `2022.04`**.
- [ ] Each reference/`main.c` (or `.bb` / `.its`) passes all of its own `static.py` + `behavior.py` checks (100% on the reference).
- [ ] Each `negatives.py` has ≥12 mutations; each mutation causes the targeted `must_fail` check-names to fail when applied to the reference; `scripts/verify_negatives_oracle.py` passes.
- [ ] New check helpers added to `check_utils.py` have unit tests under `tests/test_check_utils_linux.py` covering happy path + each false-positive trap documented in CLAUDE.md.
- [ ] `SDK_LAYOUT.yaml` lists all 15 new case IDs with `sdk: embedded-linux`.
- [ ] `uv run python scripts/sync_docs.py` updates TC count 233 → 248 in `docs/METHODOLOGY.md` and `README.md`.
- [ ] Every prompt passes the implicit-prompt grep test (no direct API names: `devm_kzalloc`, `IS_ERR`, `request_threaded_irq`, `regmap_init_i2c`, `INIT_WORK`, `FIT_*`, `CONFIG_*` kernel options — absent from `prompt.md`).
- [ ] Quality gates: `uv run ruff format --check src/ tests/ cases/embedded-linux/linux-driver-009..016/`, `uv run ruff check`, `uv run mypy src/`, `uv run pytest tests/`.
- [ ] Baseline n=1 benchmark on Haiku and Sonnet against the new 15 TCs completes and produces a delta report (`docs/BENCHMARK-linux-tc-expansion-phase-a.md`) showing per-TC pass/fail and factor-coverage table.

## Design

### Approach — Option A from research

Additive TC expansion in 4 mechanical phases, then validate + benchmark:

1. **Shared helpers first** so per-TC check code is thin and uniform.
2. **Author in factor-coverage order** (most-uncovered factor first) so early-commit review catches template drift early.
3. **Oracle-before-checks** within each TC: write the 12 mutations, then write the checks so every mutation has an actual `must_fail` target.
4. **Verify + benchmark as a single final step** so the re-run cost (Haiku + Sonnet, n=1 baseline) happens once.

### Per-TC shopping list

#### `linux-driver-009` — GFP flag selection under atomic context
- **Scenario:** a platform driver allocates a work item + data buffer; the allocation happens in `probe()` (sleepable) but the same helper is also called from an IRQ handler (atomic).
- **Implicit signal:** "this helper may be called from IRQ context — pick the right allocation flag".
- **Factor:** C3 (RAM budget), D5 (ISR context restrictions), C5 (dynamic allocation in constrained ctx).
- **Key checks:** `gfp_atomic_in_irq_path`, `gfp_kernel_in_probe_path`, `no_gfp_kernel_in_irq_handler`, `alloc_failure_returns_enomem`, `balanced_alloc_free`.
- **Negatives (12):** swap GFP_ATOMIC ↔ GFP_KERNEL, add gfp_wait, drop ENOMEM, use vmalloc in IRQ, etc.
- **Difficulty:** hard. **Tier:** challenge.

#### `linux-driver-010` — `spin_lock_irqsave` protecting IRQ-shared state
- **Scenario:** a ring-buffer index shared between top-half IRQ handler and a chardev `read()` syscall.
- **Implicit signal:** "reader must be protected against the producer that runs in interrupt context".
- **Factor:** D4, D5, D6.
- **Key checks:** `irqsave_form_used`, `flags_variable_typed_unsigned_long`, `restore_on_all_paths`, `no_plain_spin_lock_on_shared_state`, `lock_scope_does_not_contain_copy_to_user`.
- **Difficulty:** hard. **Tier:** challenge.

#### `linux-driver-011` — Deferred work via workqueue on IRQ trigger
- **Scenario:** IRQ signals a sensor event; heavy-weight post-processing (regmap I/O, `copy_to_user`-bound data prep) must happen in a kernel thread/workqueue, not the handler.
- **Implicit signal:** "this work cannot run in IRQ context because it issues bus I/O".
- **Factor:** D5, B4, E3.
- **Key checks:** `work_struct_declared`, `init_work_called`, `schedule_work_from_irq_handler`, `no_blocking_api_in_handler`, `flush_or_cancel_on_remove`.
- **Difficulty:** hard. **Tier:** challenge.

#### `linux-driver-012` — `request_threaded_irq` primary/thread split
- **Scenario:** GPIO-backed button needs debounce (sleepable) + timestamp (non-sleepable); classic primary-hardirq + threaded-softirq split.
- **Implicit signal:** "handler must both timestamp precisely and debounce via sleeping regmap read".
- **Factor:** D5, B4, E2.
- **Key checks:** `request_threaded_irq_used`, `primary_returns_irq_wake_thread`, `thread_fn_present`, `no_mdelay_in_primary`, `free_irq_on_remove`.
- **Difficulty:** hard. **Tier:** challenge.

#### `linux-driver-013` — `devm_*` managed resources, no manual free
- **Scenario:** probe acquires regmap + clk + gpio + irq via `devm_*`; must not also call manual `clk_put` / `gpiod_put` on error.
- **Implicit signal:** "probe must not leak on failure, and must not double-free on later device removal". (Mirrors CVE-2026-23068.)
- **Factor:** E1, E3, C5.
- **Key checks:** `devm_used_for_all_resources`, `no_manual_free_for_devm_resource`, `no_goto_cleanup_when_all_devm`, `probe_returns_error_without_manual_unwind`, `remove_does_not_double_free`.
- **Negative highlight:** insert `clk_put(clk)` after `devm_clk_get` → must fail `no_manual_free_for_devm_resource`.
- **Difficulty:** hard. **Tier:** challenge.

#### `linux-driver-014` — Kernel thread with `kthread_should_stop`
- **Scenario:** a long-lived kernel thread polls a sensor and updates a cached reading; lifecycle tied to module load/unload.
- **Implicit signal:** "thread must exit promptly on module unload".
- **Factor:** B4, D5, E3.
- **Key checks:** `kthread_create_or_run_used`, `loop_checks_should_stop`, `kthread_stop_on_remove`, `wakeup_before_stop`, `no_schedule_infinite_in_loop`.
- **Difficulty:** hard. **Tier:** challenge.

#### `linux-driver-015` — Regmap adoption for I2C client
- **Scenario:** I2C sensor driver reading config registers; LLM bias is to use `i2c_smbus_read_byte_data` directly.
- **Implicit signal:** "driver must support both I2C and SPI transports in a future revision" (→ forces regmap abstraction).
- **Factor:** F2, F4, F5.
- **Key checks:** `regmap_i2c_init_used`, `regmap_read_or_write_used`, `no_legacy_smbus_api`, `regmap_config_has_reg_bits`, `i2c_client_probe_v66_signature`.
- **Difficulty:** medium. **Tier:** core.

#### `linux-driver-016` — `IS_ERR`/`PTR_ERR` error propagation
- **Scenario:** chain of `clk_get_optional`, `devm_platform_ioremap_resource`, `devm_gpiod_get` — each returns `ERR_PTR`, not NULL.
- **Implicit signal:** "a NULL check is not enough for these APIs".
- **Factor:** E2, E6.
- **Key checks:** `is_err_used_after_clk_get`, `ptr_err_propagates_error_code`, `no_plain_null_check_for_err_ptr`, `dev_err_on_failure`, `err_code_returned_not_eio`.
- **Difficulty:** medium. **Tier:** core.

#### `yocto-009` — meta-layer skeleton
- **Scenario:** new `meta-sensors` layer with `conf/layer.conf` + `bblayers.conf.sample` delta.
- **Implicit signal:** "the Yocto build must be able to discover this layer when added to `bblayers.conf`".
- **Factor:** F6.
- **Key checks:** `layer_conf_has_bbfile_collections`, `bbfile_pattern_defined`, `bbfile_priority_defined`, `layerseries_compat_set`, `layer_conf_not_trailing_slash`.
- **Difficulty:** medium. **Tier:** core.

#### `yocto-010` — `.bbappend` with `:append` / `FILESEXTRAPATHS:prepend` overrides
- **Scenario:** extend an upstream recipe with an extra config file + extra RDEPENDS.
- **Implicit signal:** "use the canonical Yocto override syntax — the colon form — for an extension that must parse on kirkstone 4.0 and forward".
- **Factor:** F4, F6.
- **Key checks:** `bbappend_filename_matches_recipe`, `filesextrapaths_prepend_colon_form`, `src_uri_append_colon_form`, `rdepends_append_pn_scoped`, `no_legacy_underscore_override`.
- **Difficulty:** hard. **Tier:** challenge.

#### `yocto-011` — Linux kernel config fragment via `kernel-yocto.bbclass`
- **Scenario:** `.cfg` file added to `SRC_URI` turns on `CONFIG_DEBUG_FS=y` and `CONFIG_DYNAMIC_DEBUG=y` for a BSP kernel recipe.
- **Implicit signal:** "the enhancement must persist across kernel config regeneration".
- **Factor:** F3, F6.
- **Key checks:** `cfg_in_src_uri`, `kconf_non_hardware_mode`, `kernel_features_queue`, `no_direct_defconfig_edit`, `filesextrapaths_set`.
- **Difficulty:** hard. **Tier:** challenge.

#### `yocto-012` — `PACKAGECONFIG` for feature flags
- **Scenario:** recipe exposes `ssl` + `examples` feature flags that toggle `DEPENDS`, `EXTRA_OECONF`, and runtime deps.
- **Implicit signal:** "users should be able to disable SSL without editing the recipe".
- **Factor:** F6.
- **Key checks:** `packageconfig_declared`, `packageconfig_ssl_tuple_has_four_fields`, `packageconfig_default_respected`, `extra_oeconf_uses_packageconfig_confargs`, `depends_conditional_on_flag`.
- **Difficulty:** medium. **Tier:** core.

#### `boot-uboot-002` — FIT image `.its` description
- **Scenario:** bootable FIT image with kernel + FDT + ramdisk, a single configuration entry, and `default`/`config-1` selection.
- **Implicit signal:** "the target expects a FIT, not a legacy uImage".
- **Factor:** F6, E4.
- **Key checks:** `fit_has_images_node`, `kernel_subimage_has_load_entry`, `fdt_subimage_present`, `configurations_default_set`, `hash_node_on_each_image`.
- **Difficulty:** hard. **Tier:** challenge.

#### `boot-uboot-003` — `extlinux.conf` / distro_boot
- **Scenario:** `/boot/extlinux/extlinux.conf` for U-Boot's distro boot command.
- **Implicit signal:** "the bootloader will scan known paths — give it a BLS-compatible config".
- **Factor:** F6.
- **Key checks:** `extlinux_has_default`, `label_block_present`, `kernel_fdt_initrd_keys`, `append_has_root`, `no_hardcoded_fs_uuid_placeholder`.
- **Difficulty:** medium. **Tier:** core.

#### `boot-uboot-004` — Verified boot FIT signature keys
- **Scenario:** `.its` for a signed FIT image + control FDT snippet embedding the public key node.
- **Implicit signal:** "the board must refuse to boot unsigned images".
- **Factor:** E4, security.
- **Key checks:** `signature_node_present`, `required_property_set_on_conf`, `hash_sha256_declared`, `key_name_hint_set`, `algo_rsa_sha256_or_stronger`.
- **Difficulty:** hard. **Tier:** challenge.

### Alternatives considered

- **Option B (breadth, new `linux-userspace` category):** rejected for Phase A. Expanding `CaseCategory` enum forces reporter/scorer/SDK_LAYOUT/per_check_metrics churn (see `PLAN-expand-categories.md`); Phase B will take that cost deliberately. Phase A stays additive-only.
- **Option C (Yocto-only 12-TC push):** rejected. yocto 70%/80% inversion is likely single-flaky-case artifact (n=3 stdev is 1.5-2.2%p per memory notes); depth investment in `linux-driver` (true 70%/70% across n=3) returns more factor-coverage per TC.
- **Reuse existing TC format as-is vs. new `context/` directory content:** keep `context/` empty for Phase A (matches all 8 existing linux-driver TCs). `PLAN-context-quality-mode.md` owns context-pack authoring; decoupled.
- **"context7 + Linux 6.6 docs" auto-generation:** tempting for API pinning, but regenerating every TC is overkill. Pin `sdk_version: '6.6'` per metadata and keep references hand-authored against `docs.kernel.org/v6.6/`.
- **Add new `Sdk.U_BOOT` bucket:** rejected; u-boot TCs stay under `embedded-linux` bucket as `boot-uboot-001` already does. Renaming is future work and out of scope.

### Affected files

**New (~90 TC files):**
- `cases/embedded-linux/linux-driver-009..016/` — 8 × 6 files = 48
- `cases/embedded-linux/yocto-009..012/` — 4 × 6 files = 24
- `cases/embedded-linux/boot-uboot-002..004/` — 3 × 6 files = 18
- (six = `metadata.yaml`, `prompt.md`, `src/main.c`, `reference/main.c` or `.bb` or `.its`, `checks/static.py`, `checks/behavior.py`, `checks/negatives.py`; `context/` dir created empty; `__pycache__/` excluded via existing `.gitignore`)

**Modified:**
- `src/embedeval/check_utils.py` — add `has_devm_alloc_without_manual_free`, `has_is_err_guard`, `has_regmap_api`, `in_init_scope_only`, `has_sleepable_api_in_atomic_ctx`, `extract_module_init_body`, `extract_module_exit_body`, and (for Yocto/U-Boot text-only) `scoped_contains_yocto` helper honoring `#` comments.
- `cases/SDK_LAYOUT.yaml` — 15 new entries, all `sdk: embedded-linux`.
- `tests/test_check_utils_linux.py` — NEW; happy-path + known-trap regression tests for the 7 new helpers.
- `docs/METHODOLOGY.md`, `README.md` — auto-updated by `sync_docs.py`.
- `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` — append new check names to D4/D5/D6/E1/E2/E6/F2/F4/F6 mapped-checks rows (line 135, 153, 174, 195, 224, 243 areas). Manual edit.
- `docs/BENCHMARK-linux-tc-expansion-phase-a.md` — NEW, baseline delta report.
- `plans/negatives-progress.json` — append 15 new TC oracle statuses.

**NOT touched (explicit non-goals):**
- `src/embedeval/models.py` — no enum extension.
- `src/embedeval/reporter.py`, `scorer.py`, `evaluator.py` — no behavior changes.
- `src/embedeval/runner.py` — `discover_cases()` auto-picks up new dirs.
- Existing 233 TC files — no edits, `case_git_hash` preserved.

## Implementation phases

### Phase 1: Shared check helpers + tests — **DONE** (2026-04-19)
- [x] Add helpers to `src/embedeval/check_utils.py` (`extract_module_init_body`, `extract_module_exit_body`, `has_manual_free_paired_with_devm`, `returns_err_ptr`, `has_is_err_guard`, `sleepable_calls_in_atomic_ctx`, `strip_yocto_comments`, `yocto_contains`, `yocto_has_override`, `yocto_has_legacy_override`). Shipped.
- [x] `tests/test_check_utils_linux.py` — 26 tests across 7 classes, all false-positive traps covered (struct-member LHS, kfree_rcu word-boundary, plain-NULL-check reject, URI preservation, colon vs underscore override).
- [x] `uv run pytest tests/test_check_utils_linux.py -q` → 26 passed.
- [x] `uv run ruff format --check src/ && uv run ruff check src/` → PASS. `mypy src/` → clean.

### Phase 2: linux-driver-009..016 (kernel core, highest value) — **8/8 DONE**
- [x] **linux-driver-009 (GFP flag discipline: GFP_KERNEL vs GFP_ATOMIC)** — reference 22/22, oracle 12/12. Shipped 2026-04-19.
- [x] **linux-driver-010 (IRQ-safe spin_lock_irqsave on chardev ring)** — reference 23/23, oracle 12/12. Shipped 2026-04-19.
- [x] **linux-driver-011 (workqueue deferred work + cancel_work_sync UAF safety)** — reference 22/22, oracle 12/12. Shipped 2026-04-19.
- [x] **linux-driver-012 (request_threaded_irq primary/thread split)** — reference 21/21, oracle 12/12. Shipped 2026-04-19.
- [x] **linux-driver-013 (devm managed resources, CVE-2026-23068 pattern)** — reference 20/20, oracle 12/12. Shipped 2026-04-19.
- [x] **linux-driver-014 (cooperative kthread + kthread_should_stop)** — reference 19/19, oracle 12/12. Shipped 2026-04-19.
- [x] **linux-driver-015 (regmap MMIO abstraction, no raw readl/writel)** — reference 19/19, oracle 12/12. Shipped 2026-04-19.
- [x] **linux-driver-016 (mixed error-return discipline: ERR_PTR vs NULL vs int<0)** — reference 24/24, oracle 12/12. Shipped 2026-04-19.
- [ ] Write `prompt.md` — implicit discipline, forbidden words: `devm_`, `IS_ERR`, `spin_lock_irqsave`, `INIT_WORK`, `request_threaded_irq`, `kthread_run`, `regmap`, `GFP_ATOMIC`, `GFP_KERNEL`.
- [ ] Write `checks/static.py` + `checks/behavior.py` using Phase 1 helpers + `scoped_contains(scope='code_only')`; verify reference passes 100%.
- [ ] Write `checks/negatives.py` (≥12 mutations, each with `must_fail` targeting at least one check by name, each tagged with `factor_id` per `LLM-EMBEDDED-FAILURE-FACTORS.md` codes).
- [ ] `python scripts/verify_negatives_oracle.py cases/embedded-linux/linux-driver-<id>` — every mutation's `must_fail` list triggers.
- [ ] Commit per-TC (`test(linux): add linux-driver-<id> TC + mutation oracle`).

### Phase 3: yocto-009..012 (kirkstone feature surface) — **4/4 DONE**
- [x] **yocto-009 (meta-layer conf/layer.conf with LAYERSERIES_COMPAT=kirkstone)** — reference 12/12, oracle 12/12. Shipped 2026-04-19.
- [x] **yocto-010 (.bbappend with colon-form overrides)** — reference 12/12, oracle 12/12. Shipped 2026-04-19.
- [x] **yocto-011 (linux-imx kernel config fragment via .cfg)** — reference 12/12, oracle 12/12. Shipped 2026-04-19.
- [x] **yocto-012 (PACKAGECONFIG ssl/examples feature flags)** — reference 16/16, oracle 12/12. Shipped 2026-04-19.

### Phase 4: boot-uboot-002..004 (FIT + distro_boot + verified boot) — **3/3 DONE**
- [x] **boot-uboot-002 (FIT image .its: kernel + fdt + ramdisk + default config)** — reference 15/15, oracle 12/12. Shipped 2026-04-19.
- [x] **boot-uboot-003 (extlinux.conf for distro_boot on i.MX8MP)** — reference 15/15, oracle 12/12. Shipped 2026-04-19.
- [x] **boot-uboot-004 (signed FIT with sha256+rsa4096 signature)** — reference 14/14, oracle 12/12. Shipped 2026-04-19.

### Phase 5: SDK layout + docs sync — **DONE**
- [x] Update `cases/SDK_LAYOUT.yaml` — 15 new `sdk: embedded-linux` rows added.
- [x] `uv run python scripts/sync_docs.py` — `docs/METHODOLOGY.md` + `README.md` updated to 248 TC (200 public + 48 private).
- [ ] Manually extend `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` "EmbedEval checks mapped" lines — deferred to follow-up.

### Phase 6: Quality gates + verification — **DONE** (per-TC + repo-wide)
- [x] `ruff format --check src/` / `ruff check src/` / `mypy src/` / `pytest tests/` — all green (1266 passed, 4 skipped).
- [x] `embedeval validate --cases cases/` — 200/200 PASS.
- [x] Per-TC reference and oracle verified at authoring time (15 TCs × 180 total mutations triggered).

### Phase 7: Baseline benchmark (Phase A delta) — **NOT STARTED**
- [ ] `uv run embedeval run` against Haiku + Sonnet on the 15 new TCs (n=1 sanity → n=3 if stable).
- [ ] Generate `docs/BENCHMARK-linux-tc-expansion-phase-a.md` with per-TC pass rates and factor-coverage matrix.
- [ ] Update `memory/MEMORY.md` with TC count + Phase A completion note.

## Testing strategy

- **Unit tests (`tests/test_check_utils_linux.py`):** every new helper gets ≥3 cases. Use small synthetic snippets (not whole driver files) so failures localize.
- **Reference build tests:** `scripts/verify_references_build.py --sdk embedded-linux` compiles every reference against the kernel 6.6 / Yocto 5.0 Docker image. Any reference build failure blocks the TC.
- **Oracle verification:** `scripts/verify_negatives_oracle.py` applies every mutation to the reference; every mutation's `must_fail` check name(s) must actually fail. Any un-triggered mutation blocks the TC.
- **Reference 100% check pass:** implicit in oracle verification (the un-mutated reference is checked first and must pass all checks).
- **Implicit-prompt guard:** `grep -i -E 'devm_|IS_ERR|spin_lock_irqsave|INIT_WORK|request_threaded_irq|kthread_|regmap_|GFP_|\.bbappend|_append |\.its' cases/embedded-linux/linux-driver-009..016/prompt.md cases/embedded-linux/yocto-009..012/prompt.md cases/embedded-linux/boot-uboot-002..004/prompt.md` — must return empty. Added as a one-liner CI check in `scripts/verify_references_build.py` if convenient.
- **Quality gates (before commit):** `uv run ruff format --check src/ tests/`, `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/`.
- **Doc sync (before commit):** `uv run python scripts/sync_docs.py` — confirm diff is exactly "TC count 233 → 248" in `docs/METHODOLOGY.md` + `README.md`.
- **Integration:** full `uv run embedeval validate --cases cases/` + `uv run embedeval list --cases cases/` sanity.
- **Benchmark smoke:** 1 TC × 1 model at n=1 before each commit cluster — cheap sanity.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Kernel API drift — 5.15 vs later: `class_create(THIS_MODULE, name)` 2-arg form (removed in 6.4); `proc_ops` (5.6+, so fine on 5.15); `i2c_driver` `probe_new` valid on 5.15 (removed in 6.12). Building new TC references on a later kernel would silently compile-fail. | Med | Pin `sdk_version: '5.15'` in every linux-driver metadata; state "Linux kernel 5.15 API" in every prompt's implicit context; reference code compiles under user's actual BSP kernel headers (`~/EDGE/sources`-derived) before commit. |
| User's BSP layers (`meta-qcells-*`) at `~/EDGE/sources` contain proprietary customer code — **must not be copied** into `cases/embedded-linux/` references | High | Use public kirkstone + linux-imx 5.15 idioms only; author references from scratch based on mainline patterns (docs.kernel.org/v5.15, yoctoproject.org/docs/4.0); never `cp` from `~/EDGE/sources/meta-qcells-*`. |
| `devm_*` + manual-free mutation (CVE-2026-23068 replica) introduces a *valid* second pattern the check rejects | Med | Pilot `no_manual_free_for_devm_resource` on 3 trusted open-source drivers (drivers/tty/serial/8250_* etc.) before finalizing the check; document the "mixed devm + manual is sometimes valid" caveat in helper docstring. |
| Yocto `bitbake-layers parse` unavailable in CI Docker → recipe validation falls back to regex | Med | Document fallback in PLAN; track as "reference validation is syntactic, not semantic" in `BENCHMARK-linux-tc-expansion-phase-a.md`; open a follow-up issue to enable full Yocto parse in CI. |
| `mkimage -f .its` unavailable → FIT TC reference validation is DTS-syntactic only | Low | Accept for Phase A; document in TC readme. Validation only weakens reference correctness, not oracle correctness — all negatives still trigger. |
| Implicit-prompt discipline drift (one TC leaks an API name) | Med | Automated grep in verification step; manual review before commit. |
| `scoped_contains` default `scope='stripped'` bug repeats (CLAUDE.md 2026-04-19) | High | Every new check MUST pass `scope='code_only'` explicitly (C) or `scope='raw'` (Yocto). Add a test in `test_check_utils_linux.py` that confirms this explicitly. |
| Check name collisions with existing 97 checks | Low | Before commit, run `python -c "from embedeval import discover_cases, ..."` to list new check names and grep-verify uniqueness; rename collisions by prefixing with TC ID if needed. |
| Benchmark cost overrun (Sonnet n=3 × 15 new TCs ≈ 45 calls × ~600 tokens each ≈ \$4-6) | Low | Run n=1 sanity first; only proceed to n=3 if n=1 shows TCs are discriminating (neither 0% nor 100%). Log run cost in BENCHMARK-*.md. |
| Mutation oracle over-fitting: mutations that technically pass all checks because the reference-specific wording is matched | Med | Oracle must target `must_fail` check names explicitly; reference-wording mutations are disallowed; every mutation references a `factor_id`. |
| Phase B ("linux-userspace") blocked by Phase A decisions | Low | Phase A is strictly additive; zero enum churn. Phase B can independently propose `Sdk.EMBEDDED_LINUX_USERSPACE` or reuse `embedded-linux` — both remain open after Phase A. |

## Future work (Phase B — out of scope here)

- New `CaseCategory.LINUX_USERSPACE` enum value OR reuse existing + new tag — decide in `PLAN-linux-tc-expansion-phase-b`.
- ~6-8 userspace TCs: libgpiod v2 CDEV API, systemd unit with resource limits, udev rule for hotplug, spidev/i2c-dev direct I/O, D-Bus via sd-bus, eBPF CO-RE kprobe attach.
- Reporter + per-category scoring extension if new enum added.
- Phase A's shared helpers (`scoped_contains_yocto`, scope discipline, factor_id tagging) apply directly in Phase B — no rework.

**Phase C scoping (post-Phase-B):** see [PHASE-C-CANDIDATES.md](PHASE-C-CANDIDATES.md) for the ranked shortlist of four candidates (eBPF multi-file, Linux OTA, linux-networking-kernel, kernel DT bindings) and the recommended next slug.

## Review checklist (verify before /execute)

- [ ] Scope limited to **15 TCs across 3 existing categories** — no enum extension, no reporter/scorer changes, no existing-TC edits.
- [ ] Every TC maps to at least one specific 42-factor cell currently uncovered in the factor-to-check table.
- [ ] Every prompt passes the implicit-prompt grep (no direct API names).
- [ ] Every TC has a ≥12-entry mutation oracle with `factor_id` tags per CLAUDE.md convention.
- [ ] Shared helpers are added to `check_utils.py` (not inlined per TC) and have unit tests.
- [ ] `SDK_LAYOUT.yaml` updated; `scripts/sync_docs.py` brings `docs/METHODOLOGY.md` + `README.md` to 248 TC.
- [ ] Existing 233 TC files are untouched (verify with `git diff --stat cases/` excludes everything under existing TC dirs).
- [ ] All four quality gates (ruff format, ruff check, mypy, pytest) green.
- [ ] `verify_references_build.py` + `verify_negatives_oracle.py` both green on new TCs.
- [ ] Phase A's re-run budget is scoped to new 15 TCs × 2 models × n={1, then 3} — not a full 248-TC re-run.
- [ ] Phase B explicitly deferred; PLAN mentions but does not implement linux-userspace.
- [ ] Risk table addresses kernel API drift, `scoped_contains` scope discipline, and Yocto/FIT validation limitations.
