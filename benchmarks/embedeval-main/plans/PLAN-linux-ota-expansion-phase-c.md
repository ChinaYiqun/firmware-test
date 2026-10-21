---
type: plan
task_slug: linux-ota-expansion-phase-c
status: planning
created: 2026-04-19
tags: [embedeval, plan, ota, swupdate, rauc, embedded-linux, phase-c]
---

# PLAN: Linux OTA expansion — Phase C-1 (SWUpdate + RAUC)

**Task:** Author 6 Linux OTA TCs (4 SWUpdate + 2 RAUC) under the existing `ota` category + `embedded-linux` SDK bucket, strengthening E4 (rollback/recovery) across a second platform beyond Zephyr MCUboot. Pinned to the user's real BSP (SWUpdate on kirkstone with RSA+AES, RAUC 1.7 canonical). Zero enum churn, zero infra refactor.
**Created:** 2026-04-19

## Executive summary

**TL;DR:** Add 6 OTA TCs (`ota-swupdate-001..004`, `ota-rauc-001..002`) that exercise SWUpdate `sw-description` grammar + RAUC `manifest.raucm` INI grammar, each with 12-mutation oracle and factor_id tags, reusing Phase B's directive-exemption + `strip_systemd_comments` + `scoped_contains` patterns.

### What

Six text-file TCs under `cases/embedded-linux/ota-{swupdate-001..004,rauc-001..002}/`, each with the canonical 6-file shape (metadata.yaml, prompt.md, src/main.c placeholder, reference/main.c [sw-description or manifest.raucm verbatim], checks/{static,behavior,negatives}.py). Two new shared helpers in `check_utils.py` (`swupdate_libconfig_has`, `rauc_manifest_section_has`) with ≥3 unit tests each. `SDK_LAYOUT.yaml` extended with 6 new rows; `sync_docs.py` bumps 256 → 262 TCs. No `CaseCategory` enum change — `OTA` already exists (Zephyr MCUboot side).

### Why

Phase A/B established Linux depth at the kernel + userspace layers; OTA is the natural next rung up the stack. The user's BSP runs SWUpdate + Azure ADU in production (confirmed via `~/EDGE/sources/meta-qcells-edge/recipes-support/swupdate/` — RSA+AES-encrypted update chain with bootcnt failback). Current `ota` category has 9 Zephyr MCUboot TCs; adding Linux OTA is a cross-platform **E4 discriminator** — an LLM that over-fits on MCUboot idioms should fail on SWUpdate's `sw-description` hardware-compatibility + selection-group semantics. No academic benchmark covers Linux OTA generation (web search was empty in Phase A research).

### Key decisions

- **Reuse `CaseCategory.OTA`, no enum extension.** The category is about the failure domain (rollback, dual-bank, signing), not the platform. Confirmed in PHASE-C-CANDIDATES.md scoping. → zero `reporter.py`/`scorer.py`/SDK_LAYOUT churn for the enum surface.
- **6 TCs total (4 SWUpdate + 2 RAUC), no stretch TCs.** After the 4+2 set, marginal factor coverage per added TC drops below Phase A/B cutoff threshold. Better to ship 6 solid than 8 thin. Stretch ideas (`ota-rauc-003` hooks, `ota-rauc-004` slot group, `ota-swupdate-005` Lua handler) deferred to a future sub-phase only if benchmark reveals under-discrimination.
- **Use upstream public idioms, NOT user BSP customer code.** `~/EDGE/sources/meta-qcells-edge/recipes-support/swupdate/` has Qcells-specific paths (`/edge/sp/secrets/...`), service names (`swupdate-progress.service`), and product-specific conventions. References MUST use neutral names (`/etc/swupdate/...`, `vendor-example-update.service`, compatible strings `vendor,example-device`) per CLAUDE.md 2026-04-19 vendor-namespace-neutrality rule.
- **`platform: native_sim` + `l1_skip: true` + `l2_skip: true`.** All 6 TCs are text-file generation; no C compilation, no runtime execution. Matches `boot-uboot-002..004` + `linux-userspace-003..005` convention. Docker image optionally carries `swupdate -c` + `rauc info` binaries for compile-check uplift later, but MUST NOT be a hard dep in the first commit.
- **Directive-heavy grammar → implicit-prompt exemption continues** per Phase A/B policy. SWUpdate uses `software = { ... }` libconfig syntax with named sections (`software`, `images`, `files`, `scripts`, `hardware-compatibility`); RAUC uses INI sections (`[update]`, `[bundle]`, `[image.<slot>]`, `[hooks]`). Prompts MAY name these directives + section labels because they ARE the language surface being tested. Cannot use API/function/command names outside the grammar surface (e.g., must NOT say "call swupdate with -v flag" or "use rauc install").
- **New helpers mirror Phase B's systemd pattern.** `swupdate_libconfig_has(text, section, key)` + `rauc_manifest_section_has(text, section, key)` both reuse `strip_systemd_comments` (libconfig + INI both use `#` line comments). Avoid per-TC regex drift per CLAUDE.md "Check regexes must accept API variants".
- **Every TC gets a 12-entry mutation oracle with factor_id tags.** Dominant factor per TC: `ota-swupdate-001` → F6; `ota-swupdate-002` → E4; `ota-swupdate-003` → E4 + E7; `ota-swupdate-004` → E3 + E6; `ota-rauc-001` → F6; `ota-rauc-002` → E4. No new factor cells needed.
- **Benchmark scope: delta only.** Re-run the 6 new TCs on Haiku + Sonnet n=1 sanity → n=3 if no degenerate TCs. Existing 256 TC `case_git_hash` values untouched (additive).

### Impact

- Complexity: **Medium**
- Risk: **Low** (additive; reuses existing category; text-only TCs; no runner/evaluator changes)
- Files changed: **~48** (6 TCs × 6 files = 36, +2 helpers in check_utils.py, +1 new test module, +SDK_LAYOUT.yaml, +3 doc touchpoints via sync_docs)
- Estimated effort: **8–12h** implementation + 2–3h baseline benchmark

## Prior work

- [plans/PHASE-C-CANDIDATES.md](PHASE-C-CANDIDATES.md) — scoping doc that ranked this candidate as Phase C-1. Scope sketch (6 TCs), factor-coverage delta (E4 cross-platform strengthen + F6 grammar), and upstream references documented there. This PLAN is the implementation commitment.
- [plans/PLAN-linux-tc-expansion-phase-b.md](PLAN-linux-tc-expansion-phase-b.md) — template for directive-heavy TCs with implicit-prompt exemption + `strip_systemd_comments` helper reuse. `linux-userspace-003` (systemd watchdog triad) is the closest analogue — same platform (`native_sim`), same shape (text-only reference), same check structure (directive-grammar parsers + 12-mutation oracle).
- [plans/PLAN-linux-tc-expansion-phase-a.md](PLAN-linux-tc-expansion-phase-a.md) — 12-mutation oracle convention, factor_id tagging, implicit-prompt discipline. `boot-uboot-002..004` (FIT/extlinux/signed boot) are the closest analogues on the hash+signature side — informs `ota-swupdate-003` signed-update TC.
- [cases/zephyr/ota-001..008,011](cases/zephyr/ota-001) — 9 existing MCUboot OTA TCs. Factor coverage: E2, E4, E6, F1/F3 (CONFIG options). New Linux OTA TCs MUST NOT duplicate the MCUboot-specific checks; they should target SWUpdate/RAUC-specific failure modes: hardware-compatibility list, sw-description selection groups, RAUC manifest version string format, slot naming (rootfs.0 / rootfs.1).
- [cases/embedded-linux/boot-uboot-004](cases/embedded-linux/boot-uboot-004) — signed boot TC with `signature_uses_rsa4096`, `signature_algo_sha256_rsa_2048_or_stronger`, `no_weak_hash_algorithms`. `ota-swupdate-003` signed-update TC should reuse these check-name patterns (they already appear in the E-trailer of FAILURE-FACTORS v1.6).
- **CLAUDE.md corrections directly applied:**
  - 2026-04-19 (v1.6): `scoped_contains` default strips string literals — always pass `scope='raw'` for libconfig/INI (match inside quoted strings) or `scope='stripped'` as appropriate per text type.
  - 2026-04-19 (Phase A fixup): check regexes must NOT hardcode variable/slot names from the reference — extract the LHS from the assignment pattern before anchoring checks.
  - 2026-04-19 (Phase A fixup): Implicit-prompt discipline + directive exemption — extend exemption to SWUpdate (`software = {`, `images: (`, `files: (`, `hardware-compatibility: [`, `version =`, `sha256 =`) and RAUC (`[update]`, `[bundle]`, `[image.*]`, `compatible=`, `version=`, `format=`) directive surface. Document the exemption per TC.
  - 2026-04-19 (Phase A first wrap): neutral vendor namespace — `vendor,example-device` / `embedeval,ota-example` compatible strings, never `qcells,*`. Grep-verify against `qcells` in the 6 new TCs before commit.
  - 2026-04-19 (Phase B first wrap): TC prompts MUST NOT state byte counts / struct sizes / version-string-digit-counts that the reference doesn't actually match — either omit or verify.
- [PHASE-C-CANDIDATES.md recommended next-PLAN specifications](PHASE-C-CANDIDATES.md#recommended-next-plan-slug-linux-ota-expansion-phase-c) — 4 items inherited: (a) target 6 TCs with optional 2 stretch; (b) implicit-prompt exemption extended with SWUpdate/RAUC directive lists; (c) helper module for libconfig + INI parsing with ≥3 unit tests each; (d) Docker image addition for `swupdate -c` with `l1_skip: true` fallback if unavailable.

## Problem analysis

### Current state

**TC inventory as of commit `17be4b0` (post-Phase-C-prep):**
- 208 public + 48 private = 256 TCs. 24 categories, 6 platforms.
- `ota` category: 9 TCs (all Zephyr MCUboot).
- `embedded-linux` SDK bucket: 40 TCs (linux-driver, yocto, boot-uboot, linux-userspace). No OTA.

**Infrastructure already in place:**
- `CaseCategory.OTA = "ota"` at `src/embedeval/models.py:31` — reused, no change.
- `CaseCategory.BOOT` + existing boot-uboot patterns — text-only TC template precedent.
- `strip_systemd_comments` + `systemd_unit_section_has` at `src/embedeval/check_utils.py:747,750` — reusable for SWUpdate/RAUC (both use `#` line comments).
- `scoped_contains(scope='raw')` — text-file match helper.
- 12-mutation oracle pattern — established in `yocto-005..007`, `linux-driver-009..016`, `linux-userspace-001..008`.
- `scripts/verify_negatives_oracle.py` — oracle triggerer.
- `scripts/sync_docs.py` — auto-updates TC count in `docs/METHODOLOGY.md` + `README.md`.
- FAILURE-FACTORS v1.6 — E4 (rollback), E7 (coding standards, MISRA proxy for signing rigor), F6 (build integration) trailers already contain Phase A's signing+boot check names; new SWUpdate/RAUC checks extend them additively.

**Grammar references (upstream, neutral):**
- SWUpdate `sw-description` libconfig: https://sbabic.github.io/swupdate/sw-description.html
  - Top-level: `software = { version = "..."; description = "..."; hardware-compatibility = [ ... ]; <board> = { ... }; }`
  - `images: ( { filename = "..."; device = "..."; sha256 = "..."; }, ... );`
  - `files: ( { filename; path; sha256; }, ... );`
  - `scripts: ( { filename = "..."; type = "preinstall" | "postinstall" | "shellscript" | "lua"; }, ... );`
  - `hardware-compatibility = [ "1.0", "1.2" ];` — array of allowed hardware revisions
  - Selection groups for A/B: `stable = { copy-1 = { ... }; copy-2 = { ... }; };`
- RAUC `manifest.raucm` INI: https://rauc.readthedocs.io/en/latest/reference.html#manifest
  - `[update]` — `compatible=`, `version=`, `description=`, `build=`
  - `[bundle]` — `format=plain | verity | crypt`
  - `[image.<slot-class>]` — `filename=`, `sha256=`, `size=`, `hooks=`, `adaptive=`
  - `[hooks]` — `filename=`, optional global hook
- No TC shall ship actual signed bytes — references use `sha256 = "deadbeef..."` placeholders where the LLM is expected to match `sha256` key presence, not the hex value.

### Success criteria

- [ ] 6 new TC directories exist under `cases/embedded-linux/ota-{swupdate-001..004,rauc-001..002}/` with the complete 6-file layout.
- [ ] Every `metadata.yaml` validates against `CaseMetadata` pydantic model: `category: ota`, `sdk: embedded-linux`, `platform: native_sim`, `l1_skip: true`, `l2_skip: true`, `sdk_version: '2022.12'` (SWUpdate) or `'1.7'` (RAUC), `tier: core | challenge`.
- [ ] Every `reference/main.c` (actually sw-description or manifest.raucm content) passes 100% of its own `static.py` + `behavior.py` checks.
- [ ] Every `negatives.py` has ≥12 mutations; every mutation's `must_fail` check names actually fail when applied to the reference; `scripts/verify_negatives_oracle.py` passes.
- [ ] New shared helpers added to `check_utils.py`: `swupdate_libconfig_has(text, section_path, key) -> str | None`, `swupdate_images_has_sha256(text) -> bool`, `swupdate_hardware_compatibility_list(text) -> list[str]`, `rauc_manifest_section_has(text, section, key) -> str | None`, `rauc_image_slots(text) -> list[str]`.
- [ ] Unit tests at `tests/test_check_utils_ota.py` with ≥3 cases per helper (happy path + false-positive trap + grammar-variant acceptance).
- [ ] `cases/SDK_LAYOUT.yaml` extended with 6 new `sdk: embedded-linux` rows.
- [ ] `uv run python scripts/sync_docs.py` updates TC count 256 → 262 (208 → 214 public).
- [ ] Implicit-prompt grep passes on all 6 prompts: no direct API/command names outside declared directive surface (SWUpdate section labels + RAUC INI keys). Prompt footer per TC declares the exemption explicitly.
- [ ] `qcells` / customer-specific paths (`/edge/sp/secrets/`, `/edge/etc/swupdate/`) absent from all 6 TCs (grep returns empty).
- [ ] `uv run embedeval validate --cases cases/` — all 262 TCs pass validation.
- [ ] Quality gates: `ruff format --check src/`, `ruff check src/ tests/`, `mypy src/`, `pytest tests/` — all green.
- [ ] Baseline n=1 sanity benchmark (Haiku + Sonnet) on the 6 new TCs completes; if all TCs discriminate (between 10% and 90%), re-run n=3; generate `docs/BENCHMARK-linux-ota-phase-c.md` with per-TC pass rates and factor-coverage commentary.
- [ ] FAILURE-FACTORS.md trailer updates (follow-up): NOT part of this PLAN — deferred to a v1.7 bump via the existing `PLAN-linux-tc-phase-c-prep` pattern (commit `959de3d` established the cadence).

## Design

### Approach — Option A: six text-only TCs, 3-batch authoring order

Batch-based implementation so review catches template drift early:

1. **Batch A — shared helpers + unit tests.** 5 new helpers in `check_utils.py`, ≥3 tests each. Reuse `strip_systemd_comments` (libconfig + INI both use `#` line comments).
2. **Batch B — SWUpdate sub-batch (ota-swupdate-001..004).** Ordered easy → hard: 001 (minimal sw-description) first for rhythm, then 002 (A/B + bootcnt), 003 (signed), 004 (scripts + idempotency).
3. **Batch C — RAUC sub-batch (ota-rauc-001..002).** 001 (minimal manifest) + 002 (slot config + atomic switchover).
4. **Batch D — SDK_LAYOUT + sync_docs + implicit-prompt grep + negatives oracle verify + case validate + quality gates.**
5. **Batch E — baseline benchmark delta report.**

### Per-TC design sheet

**ota-swupdate-001: Minimal sw-description triple (bootloader + kernel + rootfs)**
- **Scenario:** Write a libconfig `sw-description` that installs three partition images (U-Boot, kernel, rootfs) onto a single-bank eMMC layout.
- **Implicit signal:** "LLM must select libconfig over YAML/JSON, produce `software = { ... }` top-level, and know that each image needs `filename`, `device`, and `sha256` fields (without being told)."
- **Platform:** `native_sim`; `l1_skip: true`; `l2_skip: true`.
- **Factors:** F6 (build integration grammar), F1 (avoiding YAML/JSON hallucination).
- **Reference highlights:** `software = { version = "1.0.0"; description = "..."; hardware-compatibility = [ "1.0" ]; stable = { copy-1 = { images: ( {filename = "u-boot.imx"; device = "/dev/mmcblk0boot0"; sha256 = "...";}, ... ); }; }; };`
- **Behavior checks (~11):** `software_block_top_level`, `version_field_present`, `hardware_compatibility_list_nonempty`, `images_list_present`, `each_image_has_filename`, `each_image_has_device`, `each_image_has_sha256`, `three_images_declared`, `selection_group_declared`, `no_yaml_syntax` (no `---` or top-level `image:` without braces), `no_json_syntax` (no `{"software":`).
- **Negatives (12):** YAML-style top-level, missing `sha256` on one image, missing `hardware-compatibility`, `filename` typo to `name`, missing `device`, `images` as object instead of list, etc.
- **Difficulty:** medium. **Tier:** core.

**ota-swupdate-002: Dual-bank A/B with bootcnt failback**
- **Scenario:** Extend a sw-description with two selection groups (`copy-1`, `copy-2`) writing to distinct partition devices, plus a bootloader environment pre-script that sets `bootcount_enable=1` and `upgrade_available=1` so U-Boot's bootcnt mechanism can trigger failback on boot failure.
- **Implicit signal:** "LLM must understand A/B slot semantics as TWO selection groups with DIFFERENT device paths, and that the bootloader env scripting is part of the sw-description."
- **Factors:** E4 (rollback/recovery), F6.
- **Reference highlights:** `stable = { copy-1 = { images: ( {device = "/dev/mmcblk0p2";}, ... ); }; copy-2 = { images: ( {device = "/dev/mmcblk0p3";}, ... ); }; };` + `bootenv: ( { name = "bootcount_enable"; value = "1"; }, { name = "upgrade_available"; value = "1"; } );`
- **Behavior checks (~11):** `two_selection_groups`, `selection_groups_have_distinct_devices`, `bootenv_list_present`, `bootcount_enable_set`, `upgrade_available_set`, `selection_group_names_are_copy_1_copy_2`, `each_group_has_bootloader_image`, `each_group_has_kernel_image`, `each_group_has_rootfs_image`, `no_single_selection_group`, `mountpoint_or_device_unique_per_group`.
- **Negatives (12):** single selection group, both groups pointing to same device, missing bootenv, `bootcount_enable=0` (disables failback), `upgrade_available` misspelled (`upgraded_available`), bootenv as object instead of list, etc.
- **Difficulty:** hard. **Tier:** challenge.

**ota-swupdate-003: Signed update (RSA+SHA256)**
- **Scenario:** A sw-description that requires RSA-signed CMS envelope (`encrypted = true` + per-image `sha256` verification), consistent with SWUpdate's `-k <pubkey>` startup flag convention.
- **Implicit signal:** "Signing is per-image hash + envelope signature; the LLM must NOT emit MD5/SHA1 hashes and MUST declare each image's `sha256` alongside `encrypted = true` for the envelope."
- **Factors:** E4, E7 (signing rigor / MISRA-proxy), F6.
- **Reference highlights:** each image entry has `sha256 = "<64-hex-chars>";` + optional `encrypted = true;`; top-level `version` + a `build` field for traceability.
- **Behavior checks (~12):** `all_images_have_sha256`, `no_md5_hashes`, `no_sha1_hashes`, `sha256_values_are_64_hex`, `encrypted_flag_present_per_image_when_required`, `version_semver_format`, `build_field_present`, `no_plain_text_password_in_description`, `hardware_compatibility_present`, `top_level_description_present`.
- **Negatives (12):** sha1 instead of sha256, missing per-image hash, 32-char (md5-length) hash string, plaintext password in description field, `encrypted = "true"` as string instead of boolean, etc.
- **Difficulty:** hard. **Tier:** challenge.

**ota-swupdate-004: Embedded scripts (pre/post-install) + idempotency**
- **Scenario:** A sw-description that runs a `preinstall` shell script (capture pre-state), installs images, then a `postinstall` Lua handler (write post-state + trigger sd_notify). Idempotency constraint: repeated application must produce the same final state.
- **Implicit signal:** "Scripts section structure + hook types (preinstall vs postinstall vs shellscript vs lua) + idempotent operations (no `echo >> file`, use `echo > file`)."
- **Factors:** E3 (resource lifecycle), E6 (defensive checks/bounds), F6.
- **Reference highlights:** `scripts: ( { filename = "pre.sh"; type = "preinstall"; }, { filename = "post.lua"; type = "lua"; sha256 = "..."; } );`
- **Behavior checks (~11):** `scripts_list_present`, `preinstall_type_valid`, `postinstall_or_lua_type_valid`, `each_script_has_sha256`, `each_script_has_filename`, `script_types_from_allowed_set` (preinstall / postinstall / shellscript / lua / swupdate), `no_duplicate_script_filenames`, `no_inline_shell_commands_in_description`, `scripts_execute_before_reboot`.
- **Negatives (12):** missing script sha256, `type = "custom"` (not allowed), duplicate filenames, inline `rm -rf` in description, `type = "preinstal"` typo, etc.
- **Difficulty:** medium. **Tier:** core.

**ota-rauc-001: Minimal manifest.raucm**
- **Scenario:** Write a minimal RAUC bundle manifest in INI format: `[update]` with `compatible`, `version`, `description`; `[bundle]` with `format=plain`; `[image.rootfs]` with `filename` + `sha256` + `size`.
- **Implicit signal:** "INI grammar (NOT YAML, NOT libconfig) + compatible-string format + slot-class naming (`image.rootfs` not `images.rootfs` or `[rootfs]`)."
- **Factors:** F6.
- **Reference highlights:** 3-section INI: `[update]\ncompatible=vendor,example-device\nversion=1.0.0\ndescription=Example update\n\n[bundle]\nformat=plain\n\n[image.rootfs]\nfilename=rootfs.ext4\nsha256=<64-hex>\nsize=<bytes>`
- **Behavior checks (~10):** `update_section_present`, `update_has_compatible`, `update_has_version`, `bundle_section_present`, `bundle_has_format`, `format_value_plain_verity_or_crypt`, `image_slot_section_present`, `image_slot_has_filename`, `image_slot_has_sha256`, `image_slot_section_uses_image_prefix` (rejects `[rootfs]` without `image.`).
- **Negatives (12):** missing `compatible`, `[rootfs]` instead of `[image.rootfs]`, `format=invalid`, missing `sha256`, YAML/JSON syntax leaked in, etc.
- **Difficulty:** medium. **Tier:** core.

**ota-rauc-002: Slot config + atomic switchover**
- **Scenario:** Write a RAUC bundle manifest covering atomic A/B switchover: two `[image.rootfs.N]` slots (N=0, 1) with distinct filenames + sha256, plus `[hooks]` global install-check hook for signature verification.
- **Implicit signal:** "A/B slot class naming (`image.rootfs.0` / `image.rootfs.1`) + hook registration semantics + atomic-switchover-by-slot-swap (NOT by in-place write)."
- **Factors:** E4, F6.
- **Reference highlights:** INI with `[image.rootfs.0]`, `[image.rootfs.1]`, plus `[hooks]` + `[handler]` sections for install-check.
- **Behavior checks (~11):** `two_rootfs_slots_declared`, `slot_class_naming_correct` (matches `image\.rootfs\.\d+`), `slot_filenames_distinct`, `slot_sha256_distinct`, `hooks_section_present`, `handler_section_present` (optional — skip if absent), `no_inplace_write_flags` (reject hypothetical `inplace=true`), `atomic_switchover_implied_by_two_slots`, `no_single_slot_config`.
- **Negatives (12):** single slot, slot class `[rootfs.0]` without `image.` prefix, slots with same filename, slots with same sha256, `[hooks]` section malformed, etc.
- **Difficulty:** hard. **Tier:** challenge.

### Alternatives considered

- **Extend `ota` enum with `LINUX_OTA` variant.** Rejected. Category is about failure domain (rollback/signing/A-B), not tool. Splitting MCUboot vs SWUpdate vs RAUC into three enum variants would fragment the aggregate metric. Zero-enum-churn is the key advantage this candidate has over eBPF/networking-kernel.
- **Ship only 4 SWUpdate TCs, defer RAUC entirely.** Rejected. RAUC is used by many kirkstone BSPs (Pengutronix, mender competitor); excluding it would leave `image.rootfs.N` INI-vs-libconfig discriminator uncovered. 2 minimal RAUC TCs is the right cutoff — same logic as Phase B's 8-TC stopping point.
- **Include `ota-swupdate-005` Lua handler or `ota-rauc-003` hooks sub-TC.** Rejected for v1; mark as stretch only if benchmark reveals under-discrimination. Lua handler TC would need a `.lua` sub-file, and the current `reference/main.c` single-file contract doesn't support multi-file — tying into Candidate 1 (eBPF multi-file) infra which we explicitly deferred.
- **Use `platform: docker_only` with actual `swupdate -c` + `rauc info` compile-check.** Rejected for v1. Adding `swupdate` + `rauc` to the Docker image is a CI commitment we don't need yet. Text-file validation + `l1_skip: true` achieves 100% of the TC's discriminating value; compile-check is polish. Revisit in a follow-up PLAN once a stable Docker image diff is justified.
- **Include Azure IoT Edge / Azure ADU TCs (user's actual production integration).** Rejected. Azure ADU is proprietary Microsoft tooling; `apt-manifest.json` schema is Azure-specific and not widely used in embedded Linux. Violates the public-upstream-idioms-only rule. User's production use doesn't justify a public TC.
- **Merge SWUpdate + RAUC TCs (one prompt covers both).** Rejected. The discriminator is "LLM selects the right grammar for the declared tool" — merging hides that. Each TC's prompt names the tool explicitly (SWUpdate → libconfig; RAUC → INI), following the same tool-pinning discipline as `linux-userspace-007` (sd-bus vs libdbus).

### Affected files

**New TC directories (36 files):**
- `cases/embedded-linux/ota-swupdate-{001..004}/` — each with 6 files (metadata, prompt, src/main.c placeholder, reference/main.c, checks/{static,behavior,negatives}.py) = 24 files.
- `cases/embedded-linux/ota-rauc-{001,002}/` — 12 files.

**Modified source:**
- `src/embedeval/check_utils.py` — add 5 helpers under a new "OTA helpers (Phase C-1)" section, after the Linux userspace helpers block:
  1. `swupdate_libconfig_has(text, section_path, key) -> str | None` — libconfig-aware directive lookup with nested-section support (`section_path = "stable.copy-1"`).
  2. `swupdate_images_has_sha256(text) -> bool` — returns True iff every `images: ( ... )` entry has a `sha256` field.
  3. `swupdate_hardware_compatibility_list(text) -> list[str]` — returns the parsed array.
  4. `rauc_manifest_section_has(text, section, key) -> str | None` — INI-aware lookup; supports nested-dot sections (`image.rootfs.0`).
  5. `rauc_image_slots(text) -> list[str]` — enumerates `[image.<slot>]` sections.
- `tests/test_check_utils_ota.py` — NEW; ≥3 tests per helper (15+ tests).

**Modified manifests / docs:**
- `cases/SDK_LAYOUT.yaml` — 6 new rows (ota-swupdate-001..004, ota-rauc-001..002), `sdk: embedded-linux`.
- `docs/METHODOLOGY.md` — auto-refreshed by `sync_docs.py` (TC count 256 → 262).
- `README.md` — auto-refreshed (test badge + case count badge).
- `docs/BENCHMARK-linux-ota-phase-c.md` — NEW baseline delta report (Batch E).
- `plans/PLAN-linux-ota-expansion-phase-c.md` — this file.

**NOT touched (explicit non-goals):**
- `src/embedeval/models.py` — no enum change.
- `src/embedeval/{reporter,scorer,evaluator,runner,cli}.py` — all iterate dynamically from metadata; no change.
- `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` — v1.6 trailers still accurate after this PLAN (new check names go to E4 and F6 which already exist). FAILURE-FACTORS v1.7 bump deferred to the next `linux-tc-phase-c-prep`-style follow-up PLAN covering Phase C accumulated checks.
- Existing 256 TC directories — 0 edits; `case_git_hash` preserved.
- Docker image — no additions; text-only TCs fall back cleanly.

## Implementation phases

### Phase 1: Shared helpers + unit tests — **DONE** (2026-04-19)

- [x] Added 5 public helpers + 2 internal brace-walkers to `src/embedeval/check_utils.py` under "OTA helpers (Phase C-1)": `libconfig_section_body`, `libconfig_list_body`, `libconfig_list_entries`, `swupdate_libconfig_has`, `swupdate_images_has_sha256`, `swupdate_hardware_compatibility_list`, `rauc_manifest_section_has`, `rauc_image_slots`.
- [x] `tests/test_check_utils_ota.py` — 21 tests covering happy path + false-positive trap + grammar-variant acceptance per helper.
- [x] Quality gates green (ruff format/check, mypy, pytest on helper suite).

### Phase 2: SWUpdate sub-batch (ota-swupdate-001..004) — **DONE**

- [x] **ota-swupdate-001 (minimal triple)** — ref 19/19 pass, 13/13 mutations trigger, factors F1/F2/F6/E4/E6/E7.
- [x] **ota-swupdate-002 (A/B + bootcnt failback)** — ref 19/19 pass, 13/13 mutations trigger, factors E4/E6/E7/F1/F6.
- [x] **ota-swupdate-003 (signed RSA+SHA256)** — ref 22/22 pass, 13/13 mutations trigger, factors E4/E6/E7/F1/F6.
- [x] **ota-swupdate-004 (scripts + idempotency)** — ref 18/18 pass, 13/13 mutations trigger, factors E3/E6/E7/F1/F6.
- [x] Cross-TC helper reuse audit — all grammar parsing flows through the Phase 1 helpers; no local regex duplicated across ≥2 TCs.

### Phase 3: RAUC sub-batch (ota-rauc-001..002) — **DONE**

- [x] **ota-rauc-001 (minimal manifest)** — ref 20/20 pass, 13/13 mutations trigger, factors E6/E7/F1/F2/F6.
- [x] **ota-rauc-002 (A/B slots + hook)** — ref 19/19 pass, 13/13 mutations trigger, factors E4/E6/E7/F1/F6.

### Phase 4: SDK layout + docs sync + integration checks — **DONE**

- [x] `cases/SDK_LAYOUT.yaml` — 6 new `ota-*` rows with `sdk: embedded-linux` appended.
- [x] `scripts/sync_docs.py` — TC count 256 → 262, categories still 24, negatives 67 → 73 TCs, mutations 506 → 584; METHODOLOGY.md + README.md updated.
- [x] `embedeval validate --cases cases/` — 214/214 public TCs pass.
- [x] Implicit-prompt grep: only "Do NOT reference" negative-prescription hits — policy-compliant per Phase B precedent. Positive API-name prescriptions absent.
- [x] Vendor-namespace grep: 0 hits for `qcells` / `/edge/sp/` / `/edge/etc/`.

### Phase 5: Quality gates + oracle verification — **DONE**

- [x] `ruff format --check src/` PASS (24 files clean).
- [x] `ruff check src/ tests/test_check_utils_ota.py` PASS.
- [x] `mypy src/` PASS (24 files, no issues).
- [x] `pytest tests/` PASS (1375 passed, 4 skipped — was 1340 baseline + 21 OTA helper + 14 other test bumps from Phase A/B alignment).
- [x] `scripts/verify_negatives_oracle.py --category ota` — 7/7 OTA TCs with negatives PASS (8 Zephyr MCUboot TCs skip — no negatives authored there).
- [x] Reference 100% pass for each new TC verified via ad-hoc snippet.

### Phase 6: Baseline benchmark (delta)

- [ ] `uv run embedeval run --cases cases/ --model claude-haiku-4-5-20251001 --case-ids ota-swupdate-001,ota-swupdate-002,ota-swupdate-003,ota-swupdate-004,ota-rauc-001,ota-rauc-002 --output runs/phase-c-ota-haiku` — n=1 sanity.
- [ ] Same for Sonnet (`claude-sonnet-4-6`).
- [ ] If n=1 shows no degenerate TC (all between 10% and 90%), re-run n=3.
- [ ] Generate `docs/BENCHMARK-linux-ota-phase-c.md` — per-TC pass rates, factor-coverage matrix (E4 cross-platform delta emphasis), commentary on which TCs discriminate best.
- [ ] Update `memory/MEMORY.md` with TC count 262 + Phase C-1 completion note.

## Testing strategy

- **Unit tests (`tests/test_check_utils_ota.py`):** 5 helpers × ≥3 cases = ≥15 tests. Pin each documented false-positive trap:
  - libconfig comment inside a quoted string
  - INI section with trailing whitespace
  - nested libconfig `stable = { copy-1 = { ... } }` vs flat section
  - RAUC slot name `image.rootfs` vs `image.rootfs.0` — helper must enumerate both
  - hardware-compatibility with single-quoted vs double-quoted strings
- **Reference self-check:** every reference passes 100% of its own static + behavior checks. Verified via an ad-hoc Python snippet per TC.
- **Oracle verification:** `scripts/verify_negatives_oracle.py cases/embedded-linux/ota-*` — all 72 mutations trigger `must_fail`.
- **Implicit-prompt guard:** grep patterns from Phase 4 applied pre-commit.
- **Quality gates:** all four green before any commit.
- **Doc sync:** after Phase 4, diff METHODOLOGY.md + README.md to confirm exactly the expected changes (TC count bump, no category-list shift).
- **Benchmark smoke:** 1 TC × 1 model × n=1 before batch commit, to catch broken prompts cheaply.
- **Cross-TC helper reuse audit:** after each sub-batch, grep `behavior.py` for repeated patterns; extract to `check_utils.py` if appearing in ≥2 TCs.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| SWUpdate `sw-description` libconfig grammar is subtle (nested `{ }` + `( )` lists with `;` terminators); helper regex may over-match or under-match on edge cases. | Med | Ground-truth validation: parse the reference with SWUpdate upstream's `sw-description` libconfig parser (Python `libconf` package) during Phase 1 unit-test authoring. If `libconf` rejects the reference, the helper AND the reference are wrong — fix before moving on. |
| RAUC INI grammar has dotted section names (`[image.rootfs.0]`); Python `configparser` chokes on dots in section names unless a custom delimiter is used. | Med | Use `configparser.RawConfigParser(allow_no_value=True)` + treat sections as flat strings; do NOT rely on dot-as-hierarchy semantics. Unit-test with an explicit `image.rootfs.0` section name. |
| A sha256 check accepts any 64-char string including all-zeros or the literal `deadbeef...` placeholder in the reference, so mutations that replace with different 64-char garbage silently pass. | Med | The check asserts `sha256` KEY presence + 64-hex-char regex; mutations target key ABSENCE or wrong-length values (32 chars = md5 length). Do NOT assert sha256 VALUE equality — that would be a useless check. |
| Implicit-prompt drift: one prompt leaks `swupdate` command-line flags or `rauc install` CLI name. | Med | Automated grep in Phase 4 + manual review before commit. FORBIDDEN list documented explicitly (see Phase 4). |
| Customer-specific paths from `~/EDGE/sources/meta-qcells-edge/recipes-support/swupdate/` leak into references (`/edge/sp/secrets/`, `/edge/etc/swupdate/`, `vendor-example-update.service` prefix typos). | High | Post-authoring grep for `qcells` + `edge/sp` + `edge/etc` on all 6 TCs; must return empty. Author references from scratch using upstream examples (sbabic.github.io), never copy-paste from user's BSP. |
| `ota-swupdate-002` bootenv A/B mutation oracle over-fits to specific device paths (`/dev/mmcblk0p2`, `/dev/mmcblk0p3`); mutations swap the paths and check incorrectly passes. | Med | Check asserts "two distinct `device =` values in the two selection groups", not specific path strings. Extract device values with regex, then assert distinctness. |
| Phase B's `scoped_contains(..., scope='stripped')` default-scope gotcha recurs in new behavior.py checks — comments inside libconfig reference are stripped + match fails. | High | Every check in new TCs MUST pass `scope='raw'` explicitly. Test covers this in Phase 1 via a helper unit test. Add a one-line comment in each behavior.py header: `# scoped_contains: always scope='raw' for libconfig/INI text`. |
| Re-authoring references using upstream grammar examples introduces accidental grammar errors (missing `;`, wrong nesting) that pass current helper regex but would fail real SWUpdate parsing. | Med | Python `libconf` (PyPI) parse validation during Phase 1; add to `tests/test_check_utils_ota.py` a `test_reference_parses_with_libconf` per SWUpdate TC. |
| Benchmark cost: 6 TCs × 2 models × n=3 ≈ 36 calls × ~500 tokens ≈ \$3–5. | Low | n=1 sanity first; proceed to n=3 only if discriminating. Log cost in `docs/BENCHMARK-linux-ota-phase-c.md`. |
| FAILURE-FACTORS v1.6 trailers don't know about new ota-* check names → new checks show up as "unknown" in context-diagnose until a v1.7 bump. | Low | Accepted. Follow-up PLAN (`linux-tc-phase-c-wrapup` or similar) bumps v1.7 to cover Phase C accumulated check names. Same cadence as v1.6 sync commit `959de3d`. Not blocking for this PLAN. |
| SWUpdate `encrypted = true` vs `encrypted = 1` vs `encrypted = "true"` — grammar accepts all three but the TC check only accepts one form. | Med | Helper accepts all three (bool / int-1 / string-"true"); documented in `swupdate_libconfig_has` docstring. Test covers the three variants. |
| RAUC `compatible` string format — upstream accepts arbitrary strings but convention is `<vendor>,<product>`. Check must accept flexibility without losing discrimination. | Low | `rauc_manifest_section_has(text, "update", "compatible")` returns the raw string; check validates presence + "contains a comma" as a loose convention. |
| TC 003 signed-update prompt says "RSA+SHA256" but SWUpdate upstream supports CMS / PKCS#7 envelope with configurable hash — prompt could be over-specific. | Low | Prompt phrasing: "hash algorithm must be SHA256 (not MD5 / SHA1) and signature algorithm must be RSA-based (CMS-RSA-* or RSA-PSS)". Check accepts both canonical spellings. |

## Review checklist (verify before /execute)

- [ ] Scope correct: 6 TCs (4 SWUpdate + 2 RAUC), 5 helpers, 1 new test module, 0 enum changes, 0 runner/evaluator edits.
- [ ] Factor-coverage delta documented: E4 cross-platform strengthen + F6 grammar (libconfig + INI) — matches PHASE-C-CANDIDATES.md recommendation.
- [ ] Every prompt passes the implicit-prompt grep (FORBIDDEN list empty; ALLOWED directive surface documented per TC).
- [ ] Every TC has a ≥12-entry mutation oracle with `factor_id` tags.
- [ ] Shared helpers live in `check_utils.py` (not inlined per TC) and have ≥3 unit tests each.
- [ ] `scoped_contains` called with `scope='raw'` in every new behavior.py (no default-scope landmines).
- [ ] `SDK_LAYOUT.yaml` updated; `sync_docs.py` runs clean.
- [ ] Existing 256 TC dirs untouched (verify with `git diff --stat cases/` restricted to `ota-*`).
- [ ] All four quality gates green.
- [ ] `verify_negatives_oracle.py cases/embedded-linux/ota-*` green.
- [ ] Additive-only — no reporter/scorer/evaluator logic change; no `case_git_hash` churn on the existing 256 TCs.
- [ ] Risk table addresses libconfig grammar subtlety, dotted INI section names, vendor-namespace leaks, scoped_contains scope gotcha, and prompt flexibility for signing algorithm variants.
- [ ] CLAUDE.md corrections applied throughout (scoped_contains scope, implicit-prompt directive exemption, vendor-namespace neutrality, numeric-claim discipline).
- [ ] FAILURE-FACTORS v1.7 explicitly deferred to follow-up PLAN (not squeezed into this one).
- [ ] Docker image additions (`swupdate -c`, `rauc info`) explicitly deferred — text-only TCs with `l1_skip: true` ship first; compile-check is a later uplift.
