---
type: plan
task_slug: linux-tc-phase-c-prep
status: planning
created: 2026-04-19
tags: [embedeval, plan, docs, failure-factors, linux-userspace, linux-driver, yocto, ota, phase-c, scoping]
---

# PLAN: Phase A/B → FAILURE-FACTORS sync + Phase C candidate scoping

**Task:** (1) Register Phase A/B's new check names (Phase A: 16 linux-driver + 4 yocto + 3 boot-uboot = 100+ new checks; Phase B: 8 linux-userspace = 80+ new checks) into `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` **EmbedEval checks mapped** trailers. (2) Research + scope the four Phase C candidates (eBPF multi-file reference support, Linux OTA with SWUpdate/RAUC, linux-networking-kernel, kernel DT bindings YAML) into selection-ready mini-scopes.
**Created:** 2026-04-19

## Executive summary

**TL;DR:** Mechanical doc sync for Phase A/B (~180 new check-name entries across 6 A–F categories) + a Phase C selection document that ranks the four candidates on signal-per-TC, implementation cost, and dependency blast radius.

### What

Two separable sub-tasks in one PLAN:

1. **FAILURE-FACTORS.md check-name mapping sync.** Append Phase A/B check names into the `**EmbedEval checks mapped:**` trailer line under each A–F category. The parser at `src/embedeval/failure_factors.py:129-156` keys off those exact trailer lines to build `{check_name: category_letter}`, which `context_diagnose.py` uses to attribute LLM failures to factor categories. Right now the mapping is frozen at v1.5 (pre-Phase-A) and every Phase A/B check is silently "uncategorised" from the diagnostic's perspective.
2. **Phase C candidate scoping doc** — a new `plans/PHASE-C-CANDIDATES.md` that compares the four directions on: factor-coverage delta against the current 42-factor taxonomy, implementation cost (enum churn, runner refactor depth, TC authoring hours), baseline-benchmark blast radius, and external dependency exposure. Output is a ranked shortlist + one recommended "next PLAN slug" so `/myplan` can pick up with minimal re-research.

### Why

- **Task 1 is a latent-bug fix.** `parse_check_category_map` → `context_diagnose` → any `embedeval context-diagnose` invocation today attributes ~180 Phase A/B check failures to "unknown" because the trailer lines haven't moved. Symptom is invisible until a user runs the diagnostic and sees empty category rollups for Linux TCs — Haiku's weak-category report will under-count Linux factor failures. The tests at `tests/test_failure_factors.py:120-129` already enforce cross-consistency between factor letters and map entries; the mapping silently under-covers because it lacks knowledge of the new names, not because it's broken.
- **Task 2 sequences Phase C.** Phase A PLAN (line 336) explicitly defers linux-userspace to Phase B; Phase B PLAN (line 30, 202) explicitly defers eBPF-userspace-loader (multi-file reference) and Linux OTA to Phase C. Neither plan commits to which lands first. A short comparison doc lets `/myplan <next-slug>` start from a sized, risk-tagged scope, preventing the "pick randomly and discover mid-execute the reference layout needs refactoring" failure mode Phase B narrowly avoided.

### Key decisions

- **Single PLAN, two sub-tasks.** Both tasks touch `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` (task 1 edits trailers; task 2 reads current factor coverage to argue candidate ranking). Separating them into two PLANs would force task 2 to duplicate task 1's factor-table read. Keep one PLAN, two clearly-scoped phases.
- **Task 1 edits only trailer lines — never factor rows.** No new factor IDs are introduced; Phase A/B's 42-factor coverage is the same as before (F6/D5/E1/E2/etc.). Adding Phase C will likely stay within the 42. If a genuinely new factor cell emerges during Phase C scoping, raise it for a separate v1.6 bump — not this PLAN.
- **First-letter-wins precedence holds.** When a Phase A/B check is arguably cross-category (e.g. `isr_no_sleepable_calls` spans D5 + E2), place it under the single most-descriptive letter. Parser's "first A→F wins" semantics mean the first listing controls; document the placement rule in the commit message so reviewers can audit.
- **Task 2 produces a scoping doc, NOT four Phase C PLANs.** Writing four `PLAN-*.md` stubs (one per candidate) creates four zombie plans that drift from reality. Deliver one `PHASE-C-CANDIDATES.md` with a ranked shortlist + recommended "next PLAN slug" — the real Phase C PLAN is authored later by `/myplan` from that recommendation.
- **Ranking rubric is explicit**: (a) factor-coverage delta — how many 42-factor cells gain empirical coverage; (b) blast radius — enum churn, runner/evaluator refactor, multi-file reference support; (c) TC authoring hours (calibrated against Phase A's 9-12h for 15 TCs and Phase B's 10-14h for 8 TCs); (d) external dependency exposure (Docker image, toolchain availability, kernel BTF, SWUpdate/RAUC binaries). Each candidate gets a score per axis.
- **eBPF multi-file reference is treated as an infrastructure sub-task**, not a TC-authoring task. Lifting the `reference/main.c` constraint (`src/embedeval/cli.py:864,920`, `src/embedeval/bugfix.py:88`) unblocks both eBPF user+kernel pairs AND any future TC that legitimately needs multiple files (OTA descriptor + signed payload, Yocto multi-recipe layer). Rank it as "infra-first, TCs later" vs. "TCs first under single-file constraint".
- **OTA (SWUpdate/RAUC) is scoped against existing `ota` category**, not a new one. 9 Zephyr MCUboot OTA TCs exist; Linux-side OTA is category reuse + `sdk: embedded-linux` bucket — no enum churn. Contrast with `linux-networking-kernel` which may need a new category or reuse `networking`/`linux-driver`.

### Impact

- Complexity: **Low** (task 1 is mechanical; task 2 is reading + writing)
- Risk: **Low** (additive doc edits; no code changes; no TC churn; no existing `case_git_hash` rewrites)
- Files changed: **~3** (`docs/LLM-EMBEDDED-FAILURE-FACTORS.md`, `plans/PHASE-C-CANDIDATES.md` [new], `plans/PLAN-linux-tc-phase-c-prep.md` [this file])
- Estimated effort: **2–3 hours** total (1.5h task 1 including test verify; 1–1.5h task 2 research + write)

## Prior work

- [plans/PLAN-linux-tc-expansion-phase-a.md](PLAN-linux-tc-expansion-phase-a.md) — Phase A complete (commit `15df732`). Line 336–339 defers linux-userspace to Phase B. Line 238 of Phase B PLAN ("docs/LLM-EMBEDDED-FAILURE-FACTORS.md — follow-up task; check-name mapping updates deferred like Phase A") is the explicit reason Task 1 exists: both Phases punted this to a follow-up.
- [plans/PLAN-linux-tc-expansion-phase-b.md](PLAN-linux-tc-expansion-phase-b.md) — Phase B complete (commit `8423040`). Line 30: "Multi-file `reference/` support is deferred to a Phase C refactor" — origin of Phase C candidate #1 (eBPF multi-file). Line 202: "Adding Linux OTA deserves its own mini-plan (`PLAN-linux-ota-expansion`), not a squeeze into Phase B" — origin of candidate #2.
- [src/embedeval/failure_factors.py](../src/embedeval/failure_factors.py) — parser for factor tables + trailer-based check mapping. `parse_check_category_map` + `load_check_category_map` are the consumers task 1 feeds.
- [tests/test_failure_factors.py](../tests/test_failure_factors.py) — existing coverage: `test_parse_factors_total_is_42` (v1.5 freeze), `test_parse_check_category_map_covers_known_checks` (spot-checks `volatile_error_flag`, `dma_config_called`, etc.), `test_parse_factors_and_map_agree_on_categories` (cross-consistency). These stay green; we add spot-check assertions for Phase A/B representatives.
- [src/embedeval/context_diagnose.py](../src/embedeval/context_diagnose.py) — downstream consumer of the mapping. `high_strength_factors` + `factor_names` (line 251) feed diagnostic output. Task 1's effect is that Phase A/B check failures stop falling through the "unknown category" gap.
- [scripts/build_expert_pack.py](../scripts/build_expert_pack.py) — drift detector. Only reads factor rows (not trailers), so task 1's trailer additions do not require re-running `--write` on `expert-coverage.md`. Confirm during Phase 1 verification.
- CLAUDE.md corrections still in effect: TC prompts must not name target APIs; scope migration note (2026-04-19) explaining why every `metadata.yaml` hash changed on SDK-bucket split — relevant because task 1 is a doc-only change and will NOT rewrite any `metadata.yaml`, so the n=3 baseline results remain valid.

## Problem analysis

### Current state

**Task 1 — mapping gaps:**

`docs/LLM-EMBEDDED-FAILURE-FACTORS.md` **EmbedEval checks mapped** trailers were last updated for the pre-Phase-A set (97 unique checks, v1.5). Phase A added ~103 new check names across 15 TCs (`linux-driver-009..016` + `yocto-009..012` + `boot-uboot-002..004`); Phase B added ~88 across 8 TCs (`linux-userspace-001..008`). Net: ~180 new check names that have no category trailer entry.

Concretely, known new checks by A–F category (compiled from `grep check_name` across Phase A/B TCs):

- **A (Hardware Awareness):** `kernel_arch_arm64`, `kernel_load_and_entry_addresses`, `kernel_load_and_entry`, `kernel_os_linux`, `kernel_and_ramdisk_have_compression`, `idvendor_match_1d6b`, `idproduct_match_0002`, `subsystem_match_usb`, `spi_ioc_transfer_struct_used`, `spi_ioc_wr_mode_used`, `spi_ioc_wr_bits_per_word_used`, `spi_ioc_wr_max_speed_hz_used`, `spi_ioc_message_nonzero_count`, `speed_1mhz_configured`, `open_spidev0_0_rdwr`, `tx_rx_buf_cast_to_unsigned_long` (A8 protocol details + A7/DT compatible for udev).
- **B (Temporal):** `on_boot_sec_15min`, `on_unit_active_sec_7d`, `persistent_true`, `timer_has_on_boot_sec`, `timer_has_on_unit_active_sec`, `restart_sec_positive`, `start_limit_burst_and_interval_paired`, `watchdog_sec_positive_duration`, `watchdog_sec_matches_30s_requirement`, `wait_has_finite_timeout`, `main_loop_checks_exit_flag` (B2/B3/B4).
- **C:** — likely none new from Phase A/B (Linux drivers use GFP flags which map to D5 context rather than C5 dynamic-alloc prohibition). Verify during authoring.
- **D (Concurrency):** `isr_no_sleepable_calls`, `isr_no_gfp_kernel`, `isr_no_logging`, `isr_null_checks_alloc_result`, `isr_uses_gfp_atomic`, `isr_uses_spin_lock_irqsave`, `isr_wakes_readers`, `read_no_plain_spin_lock`, `read_uses_spin_lock_irqsave`, `spinlock_t_declared`, `spin_lock_init_called`, `waitqueue_initialized`, `no_mutex_for_irq_shared_state`, `no_plain_request_irq`, `irqf_oneshot_flag_used`, `primary_no_logging`, `primary_no_sleepable_calls`, `primary_timestamps_event`, `primary_returns_irq_wake_thread`, `request_threaded_irq_used`, `thread_handler_sleeps`, `thread_handler_logs`, `two_isr_functions`, `exit_flag_is_sig_atomic_volatile`, `sigterm_handler_registered`.
- **E (Error Handling):** `free_irq_before_list_drain`, `free_irq_before_cancel_work`, `kfree_after_cancel_work`, `remove_drains_list`, `remove_flushes_or_cancels_work`, `remove_frees_irq`, `remove_does_not_double_free`, `remove_releases_all_resources`, `all_resources_released`, `init_work_called_in_probe`, `list_and_lock_initialized_in_probe`, `list_head_declared`, `work_struct_field_declared`, `worker_reads_frame_register`, `worker_logs`, `devm_clk_get_used`, `devm_gpiod_get_used`, `devm_ioremap_used`, `devm_kzalloc_used_in_probe`, `devm_threaded_irq_used`, `devm_regmap_init_mmio_used`, `is_err_guards_err_ptr_apis`, `is_err_guards_kthread_start`, `is_err_guards_regmap_init`, `is_err_guards_clk_get`, `is_err_guards_reset_control_get`, `no_manual_free_for_devm_resource`, `no_plain_kzalloc_for_device_state`, `ptr_err_used_for_error_propagation`, `ptr_err_propagated`, `kthread_started_in_probe`, `kthread_stop_before_kfree`, `thread_checks_should_stop`, `thread_has_sleep`, `thread_reads_register`, `task_struct_field_declared`, `of_device_table_registered`, `regmap_config_declared`, `regmap_config_stride_and_max`, `regmap_field_in_state`, `regmap_read_used`, `regmap_write_used`, `null_check_on_ioremap`, `null_check_on_kzalloc`, `neg_check_on_platform_get_irq`, `no_devm_apis_used`, `no_is_err_on_ioremap`, `no_is_err_on_platform_get_irq`, `no_raw_mmio_accessors`, `uses_traditional_clk_get`, `events_read_on_wait_success`, `rising_edge_detection_configured`, `direction_set_output`, `direction_set_input`, `chip_opened`, `argc_validated`, `error_reported_to_stderr`, `nonzero_exit_on_error`, `request_consumer_set`, `no_sysfs_gpio_fallback`, `no_libgpiod_v1_api`, `no_libgpiod_v1_event_api`, `libgpiod_v2_config_composition_used`, `libgpiod_v2_edge_api_used`, `close_called`, `perror_on_failure`, `no_write_read_fallback`, `error_propagation_r_lt_0`, `vtable_start_and_end_markers`, `process_wait_loop_present`, `bus_unref_on_exit`, `bus_name_is_com_embedeval_example`, `interface_name_correct`, `object_path_set`, `ping_method_registered`, `sd_bus_api_used`, `no_libdbus_api`, `ringbuf_reserve_null_checked`, `ringbuf_reserve_and_submit_paired`, `ringbuf_map_type_declared`, `no_raw_task_struct_deref`, `license_section_gpl_compatible`, `maps_section_declared`, `event_struct_has_pid_and_comm_fields`, `comm_array_size_16_bytes`, `current_pid_tgid_used`, `bpf_core_read_used`, `bpf_kprobe_signature_macro`, `sec_kprobe_macro_used`, `no_bcc_legacy_markers`, `after_network_target`, `exec_start_absolute_path`, `no_watchdog_with_simple_type`, `restart_covers_watchdog_timeout`, `service_exec_start_points_to_script`, `timer_unit_references_service`, `wantedby_multi_user_target`, `both_units_present`, `timer_wantedby_timers_target`, `service_type_oneshot`, `service_has_no_install_section`, `systemd_wants_env_set_to_service`, `tag_systemd_append_assign`, `action_match_add`, `no_match_only_key_assigned`, `no_run_systemctl_antipattern`.
- **F (Toolchain/Platform):** `no_cross_platform_apis` (already exists broadly, confirm), `no_arduino_spi_api`, Yocto 009–012 + u-boot 002–004 bbclass/SRC_URI/config-1/FIT/extlinux/signature: `bbfile_pattern_anchored`, `bbfile_priority_is_numeric`, `bbfiles_covers_bb_and_bbappend`, `bbpath_uses_append_form`, `collection_name_declared`, `layerseries_compat_kirkstone`, `do_install_colon_append`, `filesextrapaths_colon_prepend`, `install_mode_0644`, `no_legacy_filesextrapaths_prepend`, `no_legacy_rdepends_append`, `no_legacy_src_uri_append`, `rdepends_colon_append_audit`, `src_uri_colon_append_with_file`, `cfg_suffix_not_scc`, `no_do_compile`, `no_do_install`, `no_inherit_module`, `no_legacy_filesextrapaths`, `no_summary_redeclared`, `src_uri_colon_append_debug_cfg`, `examples_autoconf_flags_correct`, `examples_dep_fields_empty`, `examples_packageconfig_5_fields`, `extra_oeconf_uses_packageconfig_confargs`, `packageconfig_default_ssl_only`, `ssl_autoconf_flags_correct`, `ssl_build_depends_openssl`, `ssl_packageconfig_5_fields`, `ssl_runtime_depends_openssl_bin`, `config1_references_all_three_images`, `default_points_to_config1`, `hash_sha256_on_every_subimage`, `incbin_directive_used`, `append_has_console_ttymxc`, `append_has_rootwait`, `append_root_mmcblk1p2`, `default_matches_label`, `fdt_path_absolute_under_boot`, `initrd_path_absolute_under_boot`, `kernel_path_absolute_under_boot`, `timeout_positive_integer`, `kernel_hash_sha256`, `key_name_hint_boot_key`, `no_weak_hash_algorithms`, `signature_algo_sha256_rsa_2048_or_stronger`, `signature_node_in_configuration`, `signature_uses_rsa4096`, `sign_images_property_set`, `type_notify_set`, `start_limit_not_half_declared` (systemd directive surface — F6).

The above grouping is the working starting point; exact placement is finalised during Phase 1 authoring using each TC's dominant `factor_id` tag from `negatives.py` as tiebreaker.

**Task 2 — candidate facts:**

| Candidate | Motivation ref | Blocking question |
|-----------|---------------|-------------------|
| eBPF multi-file reference | Phase B line 30 | How deep is the runner/evaluator refactor to support multi-file `reference/` dirs? (cli.py:864, bugfix.py:88 hardcode `reference/main.c`) |
| Linux OTA (SWUpdate/RAUC) | Phase B line 202 | Can it reuse `ota` category + `embedded-linux` SDK bucket, or does it need a new enum? Any SWUpdate/RAUC static-check tooling available? |
| linux-networking-kernel | Phase A cleanup | Does it fit in existing `linux-driver` category or need own? What's the factor-coverage delta over the 2 existing `networking` TCs (Zephyr-side)? |
| Kernel DT bindings YAML | Phase A gap | Is there a static validator (`dt-validate`) usable in Docker? How does it interact with existing `device-tree` category (Zephyr DT overlays)? |

### Success criteria

- [ ] **Task 1 — every Phase A/B check name appears in exactly one A–F trailer line** in `docs/LLM-EMBEDDED-FAILURE-FACTORS.md`.
- [ ] `load_check_category_map()` returns a dict whose key set is a superset of the Phase A/B check-name inventory (verified by a new test in `test_failure_factors.py`).
- [ ] `test_parse_factors_and_map_agree_on_categories` stays green.
- [ ] At least 3 Phase A/B representative checks get spot-check assertions added to `test_parse_check_category_map_covers_known_checks` (e.g. `isr_uses_spin_lock_irqsave` → D, `devm_kzalloc_used_in_probe` → E, `type_notify_set` → F).
- [ ] `scripts/build_expert_pack.py --check` still exits 0 after the edit (no factor-row change → no drift).
- [ ] **Task 2 — `plans/PHASE-C-CANDIDATES.md` exists** and for each of 4 candidates documents: scope sketch (TC count, categories affected), factor-coverage delta table (which 42-factor cells gain / remain gap), blast-radius score, estimated effort, dependency-risk notes, and a "Go/No-Go/Defer" recommendation.
- [ ] The doc ends with a "Recommended next PLAN slug" line naming exactly one candidate as Phase C-1 — with a one-paragraph rationale.
- [ ] Doc cites at least one external reference per candidate (upstream SWUpdate doc for OTA, libbpf-bootstrap for eBPF multi-file, netdev DT bindings docs for kernel DT, etc.).
- [ ] Version-bump note added to FAILURE-FACTORS.md Changelog (v1.6: "added Phase A/B check mappings; no factor row change").
- [ ] Quality gates pass: `ruff format --check src/ tests/`, `ruff check src/ tests/`, `mypy src/`, `pytest tests/`. Doc sync (`scripts/sync_docs.py`) shows clean if `cases/` untouched.

## Design

### Task 1 — mechanical trailer extension

**Approach:** single-file edit to `docs/LLM-EMBEDDED-FAILURE-FACTORS.md`. Walk each A–F category, append Phase A/B check names to the existing `**EmbedEval checks mapped:**` trailer line as additional backtick-wrapped tokens. Preserve the first-letter-wins semantics — if a check is ambiguous, place under the earliest letter that fits its dominant failure mode (derived from the TC's negatives.py `factor_id` tag).

Concretely, the placement rule per check:
1. Parse `cases/embedded-linux/<phase-A/B TC>/checks/negatives.py` for `factor_id` values.
2. For each check name, identify the most-common `factor_id` across its mutations.
3. Map `factor_id` → letter via first-letter prefix (`A1.1` → A, `F6.2` → F).
4. Append the check name to that letter's trailer.

Ties broken by: (a) check name itself — if it starts with `isr_`, `spin_`, `mutex_`, `volatile_` → D regardless of `factor_id`; (b) if it starts with `devm_`, `remove_`, `free_`, `kfree_`, `unref`, `release`, `is_err`, `ptr_err`, `error_` → E; (c) if it mentions systemd unit directives, udev rule keys, Yocto bbclass/SRC_URI, FIT/extlinux → F.

**Verification:**
- Add unit test `test_phase_a_b_checks_mapped` in `tests/test_failure_factors.py` that asserts ~20 representative check names resolve to the expected letter (spread across all six categories where possible).
- Re-run `pytest tests/test_failure_factors.py`. Green → safe to commit.
- `build_expert_pack.py --check` — exits 0 (trailers are ignored by coverage render, so no `expert-coverage.md` regeneration needed). If it flags drift, investigate before commit (shouldn't happen per the parser inspection).

### Task 2 — Phase C candidate scoping doc

**Approach:** single new file `plans/PHASE-C-CANDIDATES.md`. For each of four candidates, fill in a standard template:

```markdown
## Candidate N: <name>

**Origin:** <which Phase PLAN deferred it, file:line>
**Scope sketch:** <TC count, categories affected, new shared helpers needed>
**Factor-coverage delta:** <table — which 42-factor cells gain empirical coverage vs current state>
**Blast radius:**
  - Enum change: <yes/no + count>
  - Runner/evaluator refactor: <scope>
  - Multi-file reference support: <yes/no>
  - `case_git_hash` churn: <yes/no>
**Estimated effort:** <hours, calibrated against Phase A/B>
**External dependency risk:**
  - Docker image additions: <list>
  - Toolchain / runtime dependencies: <list>
  - Kernel feature requirements (BTF, config-options): <list>
**Recommendation:** Go / No-Go / Defer, with one-paragraph rationale.
```

Then a final section:

```markdown
## Ranking + recommended next PLAN

| # | Candidate | Factor-coverage | Blast radius | Effort | Dep. risk | Overall |
|---|-----------|-----------------|--------------|--------|-----------|---------|
| 1 | <name>    | H/M/L           | H/M/L        | hours  | H/M/L     | score   |
...

**Recommended next PLAN slug:** `<slug>` — <1-para rationale>
```

Research inputs per candidate (to gather in Phase 2 before drafting):

1. **eBPF multi-file reference:**
   - Grep `src/embedeval/{cli,bugfix,evaluator,runner}.py` for hardcoded `reference/main.c` — estimate refactor touch count.
   - Check `models.py:CaseMetadata` schema — does it already support multi-file references (unlikely; likely flat single-file assumption).
   - Upstream reference: libbpf-bootstrap project layout (`.bpf.c` + `.c` + generated skel header).
2. **Linux OTA (SWUpdate/RAUC):**
   - Verify existing `ota` category + `embedded-linux` SDK bucket can be reused (no enum churn expected).
   - Static-check surface for SWUpdate: `sw-description` YAML syntax, `bundle-*.sh` scripts. RAUC: `manifest.raucm` INI-style + cert chain. Both have directive-heavy grammar analogous to systemd units → implicit-prompt exemption applies.
   - Upstream references: SWUpdate docs (sbabic/swupdate), RAUC docs (rauc/rauc). User's BSP uses SWUpdate + Azure ADU per MEMORY context.
3. **linux-networking-kernel:**
   - Current `networking` category has Zephyr-side only (MQTT, DNS, TLS). Kernel-side would cover netfilter hooks, socket filter BPF, sk_buff handling, netlink.
   - Big question: does this overlap `linux-driver` (kernel module) + `networking` in a way that creates bucket ambiguity? Likely reuse `networking` category with `sdk: embedded-linux`.
   - Factor coverage: new D4/D5/D6 cells (netfilter hooks run in softirq context), E1/E2 (skb_consume_skb / skb_dequeue error paths).
4. **Kernel DT bindings YAML:**
   - `device-tree` category today covers Zephyr DT overlays. Kernel DT bindings are `.yaml` files in `Documentation/devicetree/bindings/` with `dt-validate` as the static checker.
   - External dep risk: `dt-validate` + `yamllint` must be in the Docker image. Check if current `linux-driver-002` TC (platform driver + DT) uses `dt-validate`; probably not.
   - Factor coverage: mostly A7 (DT property correctness) + F6 (bindings file integration with `Documentation/devicetree/bindings/vendor/prefixes.yaml`).

**Output:** `plans/PHASE-C-CANDIDATES.md` with all four candidates filled in, ranked, and one recommended slug. That slug becomes input to the next `/myplan` invocation.

### Alternatives considered

- **Auto-generate check-name mapping from TC negatives.py `factor_id` tags.** Rejected. `factor_id` tags are per-mutation, not per-check — a single check may be targeted by mutations of multiple factors. The trailer line is the canonical check→letter source of truth; inverting it is a bigger refactor than one-off doc sync. Revisit if the doc drift becomes recurring.
- **Split into PLAN-failure-factors-sync + PLAN-phase-c-candidates.** Rejected. Both are sub-day tasks touching overlapping context; one PLAN amortises the "read factor table" step. Splitting adds coordination cost, not clarity.
- **Skip Task 2; just go write Phase C PLANs directly.** Rejected. Each of the four candidates has 1+ blocking design decision (multi-file reference refactor, category reuse, Docker toolchain). Starting a PLAN without scoping forces the ambiguity resolution mid-`/myplan`, which Phase B partially avoided by calling out Phase C deferrals up-front; we should preserve that discipline.
- **Produce one full Phase C PLAN (pick the winner now) instead of a candidates doc.** Rejected. Picking without side-by-side comparison risks locking in the flashiest (eBPF multi-file) when pragmatic priorities (OTA/SWUpdate matches the user's real BSP) may matter more. The ~1h comparison cost prevents a potential 8–12h misaligned implementation.
- **Bump FAILURE-FACTORS to v2.0 with new factor rows (e.g. new "F7: Linux unit-file grammar").** Rejected. Phase A/B checks fit inside the existing 42 factors (F6 build-system absorbs systemd/udev/yocto directive grammar; D5 absorbs ISR context restrictions for kernel modules). Adding rows invalidates the test `test_parse_factors_total_is_42`, cascades into `expert.md` drift, and is out of scope.

### Affected files

**New:**
- `plans/PHASE-C-CANDIDATES.md` — scoping doc for the four Phase C candidates (task 2 output).

**Modified:**
- `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` — six trailer lines appended (A–F); Changelog v1.6 entry added.
- `tests/test_failure_factors.py` — new test `test_phase_a_b_checks_mapped` (spot-check ≥20 Phase A/B representatives); existing `test_parse_check_category_map_covers_known_checks` extended with 3–4 new assertions.

**NOT touched (non-goals):**
- Any file under `cases/` — zero TC edits; `case_git_hash` preserved.
- `src/embedeval/failure_factors.py` — parser logic unchanged.
- `src/embedeval/context_diagnose.py` — consumer already handles arbitrary category letters.
- `src/embedeval/context_packs/expert.md` / `expert-coverage.md` — no factor-row change.
- `docs/METHODOLOGY.md` / `README.md` — TC count unchanged (233 public + 48 private still = 281 after Phase B's `sync_docs` run; no new cases this PLAN).
- `scripts/sync_docs.py` — not required (no `cases/`/`src/`/`tests/` change affects generated doc counts).
- `memory/MEMORY.md` — consider adding a reference line to the new FAILURE-FACTORS v1.6 + PHASE-C-CANDIDATES doc (optional; do in `/wrapup`).

## Implementation phases

### Phase 1: FAILURE-FACTORS.md check-name mapping sync — **DONE** (2026-04-19)

- [x] Generated Phase A/B check-name inventory: 222 unique new checks across 23 TCs via script.
- [x] Dominant `factor_id` extracted from each TC's `negatives.py` via regex; votes aggregated per check.
- [x] Placement applied: 195 via vote + 27 via prefix-rule fallback; 0 unknown. Distribution: A:12 / B:14 / C:1 / D:16 / E:73 / F:106.
- [x] Six A–F trailers extended in `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` — existing pre-v1.5 entries untouched; new entries appended per letter.
- [x] v1.6 Changelog entry added; Version header bumped 1.5 → 1.6 (2026-04-19).
- [x] `test_parse_check_category_map_covers_known_checks` extended with 4 Phase A/B assertions (A, D, E, F).
- [x] New `test_phase_a_b_checks_mapped` covers 26 representative checks across all six categories.
- [x] New `test_mapping_has_at_least_v1_6_size` asserts mapping ≥350 entries (actual: 359).
- [x] `pytest tests/test_failure_factors.py` — 12/12 passed.
- [x] `python scripts/build_expert_pack.py --check` — exit 0 (no drift).
- [x] Trailer count preserved: `grep -c '**EmbedEval checks mapped:**'` returns 6.

### Phase 2: Research inputs for Phase C candidates — **DONE**

- [x] Multi-file reference blast radius: ~8 touch sites across `src/embedeval/{bugfix,cli,evaluator}.py` + 5 scripts hardcode `reference/main.c`.
- [x] `CaseMetadata` has no `reference_files` / `reference_dir` field — schema extension required for multi-file support.
- [x] SWUpdate uses `sw-description` (libconfig/YAML), RAUC uses `manifest.raucm` (INI) — both directive-heavy, fit Phase B's implicit-prompt exemption pattern.
- [x] Existing networking category: 8 Zephyr + 1 ESP-IDF + 1 STM32 = 10 TCs, all userspace/MCU; kernel-space networking is unrepresented.
- [x] Existing device-tree category: 8 Zephyr DT overlays, 0 kernel-DT-binding YAML.
- [x] `dt-validate` availability noted as pip-installable `dtschema` package (low dep risk).

### Phase 3: Write plans/PHASE-C-CANDIDATES.md — **DONE**

- [x] 4 candidates fully filled in (scope sketch, factor-coverage delta table, blast radius, effort, dep risk, recommendation, upstream references).
- [x] Comparison table with 5 axes (factor-coverage, blast radius, effort, dep risk, overall) + overall ranking.
- [x] Recommended next PLAN slug: **`linux-ota-expansion-phase-c`** with rationale + follow-up Phase C-2 nomination (linux-networking-kernel).
- [x] Cross-link added to `PLAN-linux-tc-expansion-phase-a.md:Future work` and `PLAN-linux-tc-expansion-phase-b.md:Alternatives considered` (SWUpdate row).

### Phase 4: Wrap-up hygiene — **DONE**

- [x] `git diff --stat` confirms only intended files touched: 2 PLAN files + FAILURE-FACTORS.md + test file + 2 new files (PHASE-C-CANDIDATES.md, this PLAN) + README.md (sync_docs badge bump).
- [x] `scripts/sync_docs.py` — only README.md test badge bumped 1338 → 1340 (expected; +2 new tests). METHODOLOGY.md already in sync.
- [ ] Commit split (deferred to `/wrapup`):
  1. `docs(factors): v1.6 — map Phase A/B check names into A–F trailers + tests`
  2. `docs(phase-c): scope + rank four Phase C candidates, recommend next slug`

## Testing strategy

- **Unit tests (`tests/test_failure_factors.py`):**
  - Extend `test_parse_check_category_map_covers_known_checks` with ≥3 Phase A/B spot-checks (representative of D, E, F categories).
  - Add new `test_phase_a_b_checks_mapped` asserting a representative set of ≥20 Phase A/B check names are in the parsed map.
- **Drift detector:** `python scripts/build_expert_pack.py --check` must stay exit 0 throughout (no factor row change).
- **Cross-consistency:** existing `test_parse_factors_and_map_agree_on_categories` stays green — every check letter is A–F.
- **Doc rendering sanity:** open the edited FAILURE-FACTORS.md in a markdown renderer (or `cat` the trailer lines) to confirm no accidental line breaks inside backtick spans — `_CHECK_NAME_RE` tolerates whitespace but mis-escaped backticks silently drop entries.
- **Quality gates:** `ruff format --check src/ tests/`, `ruff check src/ tests/`, `mypy src/`, `pytest tests/`. All must be green before commit.
- **Doc sync:** `scripts/sync_docs.py` — confirm no unexpected count change (test count bumps by 1 from the new test function; nothing else).
- **Negative test:** after edits, `grep -c 'EmbedEval checks mapped' docs/LLM-EMBEDDED-FAILURE-FACTORS.md` must return **6** (one per A–F section). If a trailer line got duplicated or split across lines, fix before commit.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| A check name mis-assigned to the "wrong" letter (e.g. `isr_no_sleepable_calls` placed under E instead of D) — downstream context-diagnose rollups skew | Med | Apply tiebreaker rules deterministically (design section a/b/c); cross-check a sample of 10 placements manually; note placements in the commit message for reviewer audit. |
| First-letter-wins precedence re-classifies a pre-existing check silently (adding `foo` to A's trailer when it was already in D would make A win going forward) | Low | Only append to trailers — never re-add a check already present in an earlier letter. Pre-commit grep: for each new check, confirm absence from earlier letters' trailers. |
| Trailer line gets too long (>1000 char) and markdown renderers break | Low | Pandoc/gfm handles arbitrary trailer length; no enforcement limit. If cosmetic concern: split into multiple paragraph-separated `**EmbedEval checks mapped:**` lines under the same section — parser iterates across all of them. |
| `build_expert_pack.py --check` unexpectedly fails (drift) because the doc version header changed | Low | `expert-coverage.md` rendering keys off factor rows, not version header. Verify locally before committing; if it does flag drift, investigate whether Phase A/B silently changed a factor row somewhere we missed. |
| Phase 1 tests pass locally but CI differs (missing CI env factor) | Low | CI and local both run `pytest tests/test_failure_factors.py`; no env-specific branch. Standard risk. |
| Phase C candidates doc becomes stale within a week (Phase C-1 starts, other candidates shift) | Med | Mark the doc with `last-reviewed: 2026-04-19`; the real PLAN for the chosen candidate will supersede. Other candidates remain as a lightweight scoping reference. |
| Recommended next slug in the doc conflicts with actual user priority | Low | The recommendation is advisory, not binding. `/myplan` invokes with an explicit slug; the user can override. Rationale paragraph is the value, not the slug itself. |
| Accidentally editing non-trailer parts of FAILURE-FACTORS.md (e.g. factor descriptions) while in the file | Med | Use targeted `Edit` tool calls keyed on the unique `**EmbedEval checks mapped:**` line per section. Diff review before commit. Chunk the commit cleanly. |
| Phase A/B check-name inventory has duplicates (same name in 2 TCs with different factor_id tags) | Low | Grep `sort -u` dedupes. Placement uses the most-common factor_id; in true ties, apply name-pattern rules (isr_/devm_/etc.) for determinism. |

## Review checklist (verify before /execute)

- [ ] Scope covers exactly: (1) FAILURE-FACTORS.md trailer sync + tests, (2) `PHASE-C-CANDIDATES.md` scoping doc, (3) cross-link touch in Phase A/B PLANs' Future-work sections. Nothing else.
- [ ] No `cases/` edits → no `case_git_hash` churn → no benchmark re-run budget impact.
- [ ] No new factor rows in FAILURE-FACTORS.md → `test_parse_factors_total_is_42` stays true.
- [ ] Parser consumption path validated: `parse_check_category_map` → `context_diagnose.py` — Phase A/B checks now resolve to a letter, not "unknown".
- [ ] First-letter-wins precedence preserved; no check listed under >1 earlier-letter trailer.
- [ ] Tiebreaker rules for letter placement documented in the commit message (visible to reviewers).
- [ ] Representative spot-check assertions added across D, E, F (Phase A/B's dominant categories).
- [ ] Changelog v1.6 entry present; version header bumped.
- [ ] `PHASE-C-CANDIDATES.md` contains: 4 candidates, standard template each, comparison table, recommended slug + rationale.
- [ ] Doc cites at least one upstream reference per candidate.
- [ ] `build_expert_pack.py --check` exits 0 (no unintended factor-row change).
- [ ] Quality gates green (ruff format + check, mypy, pytest).
- [ ] Commits split cleanly (factors sync separate from phase-c scoping).
