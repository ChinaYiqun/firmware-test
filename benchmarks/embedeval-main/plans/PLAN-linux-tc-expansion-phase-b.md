---
type: plan
task_slug: linux-tc-expansion-phase-b
status: planning
created: 2026-04-19
tags: [embedeval, plan, linux-userspace, systemd, libgpiod, udev, sd-bus, ebpf, tc-authoring]
---

# PLAN: Linux TC Expansion — Phase B (userspace: libgpiod v2 + systemd + udev + sd-bus + eBPF)

**Task:** Add 8 Linux userspace TCs under a new `CaseCategory.LINUX_USERSPACE` — libgpiod v2 (×2), systemd service + timer, udev, spidev ioctl, sd-bus service, eBPF CO-RE kprobe — pinned to the user's real BSP (linux-imx 5.15, Yocto kirkstone, i.MX8M Plus, systemd-only distro) and picking up Phase A's 12-mutation-oracle + implicit-prompt discipline.
**Created:** 2026-04-19

## Executive summary

**TL;DR:** Add `CaseCategory.LINUX_USERSPACE = "linux-userspace"` (Tier 3, alongside `yocto`/`linux-driver`/`memory-opt`) and ship 8 TCs covering the highest-signal userspace LLM failure modes — libgpiod v1→v2 regression, systemd `Type=notify` + `WatchdogSec` + `Restart=on-watchdog` triad, udev rule `==` vs `=` trap, spidev `SPI_IOC_MESSAGE` ioctl, sd-bus vs libdbus selection, eBPF CO-RE kprobe with `BPF_CORE_READ`. Enum blast radius is O(3 files) manual + rest dynamic (verified via audit).

### What

Extend `src/embedeval/models.py:CaseCategory` with one new Tier-3 entry, add 8 TCs under `cases/embedded-linux/linux-userspace-{001..008}/`, author 5 new shared helper functions in `src/embedeval/check_utils.py` (systemd/udev/libgpiod/dbus/bpf parsers), update 2 manual doc touchpoints (README.md "23 → 24 categories", `docs/METHODOLOGY.md:348` per-category L1/L2 applicability table), preserve additive-only discipline (existing 248 TC `case_git_hash` untouched).

### Why

Phase A closed the kernel-space gap (linux-driver 16 TCs) and build/boot gaps (yocto 12 + boot-uboot 4 = 16 TCs). **Userspace is the single largest unaddressed Linux surface** — systemd units, udev rules, libgpiod consumers, sd-bus services, eBPF programs — and carries distinctive LLM failure modes due to training-data skew: libgpiod v1 dominates tutorials despite v2 being mandatory on kernel 5.10+ since March 2023; libdbus dominates over sd-bus despite sd-bus being the post-2015 standard; `WatchdogSec` without `Type=notify` is a silent-no-op trap documented in systemd upstream. No academic benchmark measures LLM userspace-Linux capability — web search returned zero direct hits (see research).

### Key decisions

- **Add `CaseCategory.LINUX_USERSPACE`.** Per blast-radius audit: enum addition touches `models.py` + 2 doc rows; all scorer/reporter/sync_docs/CLI logic iterates categories dynamically from case metadata. Phase A PLAN's "O(repo) blast radius" characterization was overclaim. The precedent is `PLAN-expand-categories.md` (Mar 2026) which added 7 categories cleanly.
- **8 TCs, not 12.** After TC 8 the marginal factor-coverage drops — additional userspace APIs (netlink, libudev monitor, capabilities, mmap /dev/mem) would be single-factor drills. 8 is symmetric with Phase A's 8-TC linux-driver batch.
- **Drop eBPF userspace-loader; keep BPF-source-only + `l1_skip: true`.** The libbpf-bootstrap CO-RE pattern is inherently multi-file (`.bpf.c` + userspace `.c` + generated skeleton header); forcing single-file breaks compilation. BPF program alone captures the high-signal failure modes (SEC macros, vmlinux.h, BPF_CORE_READ, license string) and can be parse-checked without `clang -target bpf` in the Docker image. Multi-file `reference/` support is deferred to a Phase C refactor.
- **TC 7 (sd-bus) over libdbus despite user's BSP not using custom D-Bus.** Web research (Poettering 2015, LWN, freedesktop.org) confirms sd-bus is the official recommendation for Linux-only embedded; user's stack (systemd-only, kernel 5.15) is the exact target profile. TC teaches forward-looking practice; prompt phrasing emphasizes "Linux-only embedded, systemd available".
- **Implicit-prompt discipline + directive exemption**, per Phase A's established policy. systemd unit / udev rule / libgpiod v2 prompts will necessarily name directive surface (`Type=`, `WatchdogSec=`, `SUBSYSTEM==`, `gpiod_chip_open_by_name`) — these are the language being tested, analogous to Yocto's `PACKAGECONFIG`. Document the exemption in TC metadata.
- **Every TC carries a 12-entry mutation oracle + factor_id tags**, using the Phase A convention (recent commit 15df732). Cross-platform API check (`check_no_cross_platform_apis`) applied where a C source exists.
- **Reference environment mirrors user's BSP for realism.** kernel 5.15 implies libgpiod v2 available (5.10+ requirement met), sd-bus via `libsystemd-dev` available (systemd-only distro), eBPF CO-RE possible if `CONFIG_DEBUG_INFO_BTF=y` (user's kernel config may not set this — parse-only check sidesteps this). Target declared as i.MX8M Plus where hardware-specific (spidev bus numbers, udev USB IDs).
- **All C-source TCs use `platform: docker_only`**; systemd/udev text TCs use `platform: native_sim` (following boot-uboot-001 convention for text-only validation).

### Impact

- Complexity: **Medium**
- Risk: **Low** (additive; enum extension has 3-file manual surface; existing TCs untouched)
- Files changed: **~70** (8 TCs × 6-7 files = 48-56, +5 helper additions in check_utils.py, +1 test module, +3 doc touchpoints)
- Estimated effort: **10-14h** implementation + 2-3h baseline benchmark (Haiku + Sonnet n=1 sanity → n=3 if stable)

## Prior work

- [plans/PLAN-linux-tc-expansion-phase-a.md](PLAN-linux-tc-expansion-phase-a.md) — Phase A precedent, template for TC authoring, shared-helpers pattern, implicit-prompt discipline, 12-mutation oracle convention. Phase B inherits the entire methodology; differences are category (+1 enum), TC domain (userspace vs kernelspace/build/boot), and helper set (new parsers for systemd/udev/libgpiod/dbus/bpf vs existing kernel parsers).
- [plans/PLAN-expand-categories.md](PLAN-expand-categories.md) — template for enum extension (added 7 categories in Mar 2026). Correctly identified `models.py` + README + METHODOLOGY as manual touchpoints. Phase B follows same pattern at ~1/7 the cost.
- Commit **48e2bbd** + **15df732** — Phase A complete (15 TCs total: 8 linux-driver + 4 yocto + 3 boot-uboot + pilot 013 in the first). Shared helpers already in `check_utils.py`: `extract_module_init_body/_exit_body`, `has_manual_free_paired_with_devm`, `has_is_err_guard`, `sleepable_calls_in_atomic_ctx`, `strip_yocto_comments`, `yocto_contains`, `yocto_has_override`, `yocto_has_legacy_override`. Most are kernel-module specific and don't apply to Phase B.
- **CLAUDE.md corrections directly applied:**
  - 2026-04-19 (first): `scoped_contains` default scope is `stripped` — always pass `scope='code_only'` (C) or `scope='raw'` (text-with-`#`-comments). Phase B systemd/udev parsers reuse `strip_yocto_comments` (identical `#` line-comment semantics).
  - 2026-04-19 (second): Yocto `.bb` URI preservation — same concern for systemd ExecStart paths if any have `://`.
  - 2026-04-19 (Phase A fixup): TC check regexes must NOT hardcode reference variable names — Phase B checks extract LHS from assignment pattern.
  - 2026-04-19 (Phase A fixup): Implicit-prompt discipline across TC families + Yocto/DTS exemption — Phase B extends exemption to systemd / udev / libgpiod v2 directive surface.
  - 2026-04-19 (Phase A first wrap): Public TC namespaces must stay neutral (`vendor,*` / `embedeval,*`) — Phase B udev rule TC uses vendor 0x1234 / product 0xabcd and service name `vendor-example-daemon`, not `qcells-*`.
- [plans/PLAN-remaining-blindspots.md](PLAN-remaining-blindspots.md) — `init_error_path_cleanup` mutation bypass via `__exit` function scope leak. Phase B daemons have `setup()` + signal-handler pattern; same scope-discipline applies to "cleanup in SIGTERM handler only, not in normal-exit path".
- [plans/PLAN-sdk-bucket-split.md](PLAN-sdk-bucket-split.md) — confirms `case_git_hash` is content-addressed. Phase B TCs are net-new directories under `cases/embedded-linux/linux-userspace-*/`; existing 248 TC hashes unchanged.

## Problem analysis

### Current state

Embedeval coverage as of commit 15df732 (Phase A complete):
- **248 TCs** (200 public + 48 private); 23 categories; 6 platforms
- Linux kernelspace: linux-driver-{001..016} (excluding 009 — was there; indices: 001-008 pre-Phase-A + 009-016 Phase-A = 16 total)
- Linux build: yocto-{001..012}
- Linux bootloader: boot-uboot-{001..004}
- Linux userspace: **0 TCs** — entire domain unrepresented

Category enum (`src/embedeval/models.py:8-38`):
- Tier 1 (platform-agnostic C, 14): gpio-basic, uart, adc, pwm, spi-i2c, dma, isr-concurrency, threading, timer, sensor-driver, networking, ble, security, storage
- Tier 2 (system-level, 6): kconfig, device-tree, boot, ota, power-mgmt, watchdog
- Tier 3 (platform-specific, 3): yocto, linux-driver, memory-opt

Reporter / scorer / CLI / sync_docs.py all iterate categories dynamically from case metadata — verified via Explore agent audit during research pass.

Manual doc touchpoints for enum extension:
- `README.md:204` — `## 23 Categories, 6 Platforms` → must update to 24
- `docs/METHODOLOGY.md:348` — Per-Category L1/L2 Layer Applicability table is hand-authored (not regenerated by sync_docs.py); requires a manual row for `linux-userspace`
- `docs/METHODOLOGY.md:12` / difficulty table / category counts — **automatic** via `sync_docs.py` (regenerates from metadata discovery)

Shared helpers in `check_utils.py` as of commit 15df732: kernel-focused (devm/IS_ERR/spinlock/workqueue/kthread) + yocto recipe (colon-override/strip-comments). No userspace parsers.

### Success criteria

- [ ] `src/embedeval/models.py:CaseCategory` has `LINUX_USERSPACE = "linux-userspace"` as a new Tier-3 entry, validated by `CaseMetadata(...).category` roundtrip.
- [ ] 8 new TCs under `cases/embedded-linux/linux-userspace-{001..008}/` with complete 6-file layout each (metadata.yaml, prompt.md, src/main.c placeholder, reference/main.c, checks/static.py, checks/behavior.py, checks/negatives.py).
- [ ] Every reference passes 100% of its own checks.
- [ ] Every negatives.py has ≥12 mutations; every mutation's `must_fail` check names actually fail when applied to the reference.
- [ ] New shared helpers added to `check_utils.py`: `strip_systemd_comments` (may be alias of `strip_yocto_comments`), `systemd_unit_section_has`, `udev_rule_matches`, `has_libgpiod_v1_api`, `has_libgpiod_v2_api`, `has_sd_bus_api`, `has_libdbus_api`, `has_bpf_sec_macro`, `has_bpf_core_read`. Each with ≥3 unit tests covering happy path + false-positive trap + API-variant acceptance.
- [ ] `cases/SDK_LAYOUT.yaml` extended with 8 new `sdk: embedded-linux` rows.
- [ ] `uv run python scripts/sync_docs.py` updates TC count 248 → 256, category count 23 → 24 automatically in `docs/METHODOLOGY.md`.
- [ ] `README.md:204` manually updated: "23 Categories, 6 Platforms" → "24 Categories, 6 Platforms".
- [ ] `docs/METHODOLOGY.md:348` per-category L1/L2 applicability table gets a `linux-userspace` row (applicability: L1 subset of TCs compile-checkable, L2 all skip).
- [ ] Implicit-prompt grep passes: no direct API names in prompts except documented directive exemption (systemd `Type=`, udev `SUBSYSTEM==`, libgpiod v2 `gpiod_*`). Prompt footer per TC declares the exemption explicitly.
- [ ] `qcells` vendor namespace absent from all Phase B TCs (grep returns empty).
- [ ] `uv run embedeval validate --cases cases/` — all 256 TCs pass validation.
- [ ] Quality gates: `ruff format --check src/`, `ruff check src/`, `mypy src/`, `pytest tests/` — all green.
- [ ] `scripts/verify_negatives_oracle.py cases/embedded-linux/linux-userspace-*` — all 96 mutations trigger their must_fail check names.
- [ ] Baseline n=1 sanity benchmark (Haiku + Sonnet) over the 8 new TCs completes and produces a delta report (`docs/BENCHMARK-linux-userspace-phase-b.md`) with per-TC pass rates. n=3 re-run if n=1 shows no degenerate 0%/100% TCs.

## Design

### Approach — Option A from research

Enum-extended, dynamic-iteration-friendly, additive-only. 6-phase implementation:

1. **Shared helpers first** — 9 new helper functions in `check_utils.py` with ≥3 tests each. Reuse `strip_yocto_comments` for systemd units (identical `#` comment syntax).
2. **Enum extension + doc manual edits** — 3 files touched (models.py, README.md, METHODOLOGY.md L1/L2 table). Verify with `CaseMetadata` roundtrip test.
3. **TC authoring in 3 sub-batches** (difficulty-ordered, easiest first for rhythm):
   - Sub-batch A — text-only TCs (003 systemd service, 004 systemd timer, 005 udev rule): simplest, reuse `strip_yocto_comments` for parsing
   - Sub-batch B — C-source TCs (001 libgpiod v2 CLI, 002 libgpiod v2 event, 006 spidev, 007 sd-bus, 008 eBPF BPF-only): more complex, each needs its own helper set
4. **SDK_LAYOUT update + sync_docs run**.
5. **Full verification** — quality gates + reference-build + oracle-trigger + implicit-prompt grep + case validation.
6. **Baseline benchmark** — n=1 sanity on the 8 TCs, then n=3 if clean.

### Per-TC design sheet

**linux-userspace-001: libgpiod v2 CLI toggle**
- **Scenario:** CLI tool `gpio_toggle <chip> <line> <0|1>` that opens the GPIO character device, configures the line as output, drives the requested value, releases.
- **Implicit signal:** "kernel 5.15 character-device GPIO uAPI, post-2020 generation — the 2016-era interface is unsupported on this distro".
- **Platform:** `docker_only`; **compile:** requires `libgpiod-dev` v2.x package.
- **Factor:** F2 (cross-platform API), F4 (SDK version), F1 (API hallucination).
- **Reference highlights:** `gpiod_chip_open("/dev/gpiochip0")`, `gpiod_chip_request_lines(chip, NULL, &config)`, `gpiod_line_settings_set_direction(settings, GPIOD_LINE_DIRECTION_OUTPUT)`, `gpiod_line_request_set_value(request, line_offset, GPIOD_LINE_VALUE_ACTIVE)`, release.
- **Behavior checks (~10):** `libgpiod_v2_api_used`, `no_libgpiod_v1_api_used` (reject `gpiod_chip_get_line`, `gpiod_line_request_output`, `gpiod_chip_open_lookup`), `chip_opened_before_request`, `request_released_on_exit`, `no_sysfs_gpio_fallback` (reject `/sys/class/gpio/export`), `no_cross_platform_apis`, `argv_parsed_safely`, `exit_code_nonzero_on_error`.
- **Negatives (12):** LLM emits v1 `gpiod_chip_get_line`, LLM falls back to sysfs, LLM forgets `gpiod_line_settings_free`, LLM uses `atoi` without errno check, etc.
- **Difficulty:** medium. **Tier:** core. **l1_skip:** false if Docker has libgpiod v2, else true + document.

**linux-userspace-002: libgpiod v2 edge-event monitor**
- **Scenario:** A daemon that configures a GPIO line for rising-edge events and prints a timestamp on each event; exits on SIGTERM.
- **Implicit signal:** "non-polling edge-triggered monitoring with bounded-time blocking read".
- **Factor:** F2, F4, B3 (bounded polling), E4 (graceful shutdown).
- **Reference highlights:** `gpiod_edge_event_buffer_new`, `gpiod_line_request_wait_edge_events(req, timeout_ns)`, `gpiod_line_request_read_edge_events(req, buffer, max)`, SIGTERM handler flips exit flag, main loop checks flag.
- **Behavior checks (~11):** `libgpiod_v2_event_api_used`, `edge_event_buffer_allocated_and_freed`, `wait_has_finite_timeout` (reject `-1` forever), `sigterm_handler_registered`, `main_loop_checks_exit_flag`, `event_read_in_batch` (accepts buffer), `no_libgpiod_v1_event_api` (reject `gpiod_line_event_wait`), `no_cross_platform_apis`.
- **Negatives (12):** v1 event API, infinite timeout, no SIGTERM, forgotten buffer free, etc.
- **Difficulty:** hard. **Tier:** challenge.

**linux-userspace-003: systemd service with Type=notify + WatchdogSec + Restart=on-watchdog**
- **Scenario:** `.service` unit file for a daemon that heartbeats via sd_notify; supervisor kills on missed heartbeat, restarts automatically.
- **Implicit signal:** "systemd-managed service on kernel 5.15 + systemd >= 244 (kirkstone ships 250). Watchdog mechanism requires explicit service-type declaration, heartbeat timeout, and restart policy — getting two of three right silently disables the watchdog."
- **Platform:** `native_sim` (text-only).
- **Factor:** F6 (build/unit syntax), E5 (watchdog management), B2 (timing margins).
- **Reference highlights:** `[Unit]` Description + After=network.target; `[Service]` ExecStart + Type=notify + WatchdogSec=30 + Restart=on-watchdog + RestartSec=5 + StartLimitBurst=3 + StartLimitIntervalSec=60; `[Install]` WantedBy=multi-user.target.
- **Behavior checks (~11):** `type_notify_set`, `watchdog_sec_positive_integer`, `restart_on_watchdog_set` (reject `Restart=no` or `Restart=always` alone without watchdog context), `restart_sec_bounded` (reject 0 or >60), `start_limit_burst_and_interval_paired`, `service_section_present`, `install_section_present`, `exec_start_absolute_path`, `no_dbus_type` (Type=dbus without BusName= is invalid).
- **Negatives (12):** WatchdogSec without Type=notify, Type=simple + WatchdogSec, missing Restart directive, Restart=no + WatchdogSec, etc.
- **Difficulty:** medium. **Tier:** core.

**linux-userspace-004: systemd timer unit + paired service**
- **Scenario:** A pair of `.timer` + `.service` units that run a log-rotation script weekly after boot, persistently.
- **Implicit signal:** "run a script on schedule; survive reboots without drifting".
- **Platform:** `native_sim`.
- **Factor:** F6, B2.
- **Reference highlights:** `cleanup.timer` with `[Timer] OnBootSec=15min OnUnitActiveSec=1w Persistent=true Unit=cleanup.service`; `cleanup.service` with `[Service] Type=oneshot ExecStart=/usr/bin/cleanup.sh`.
- **Behavior checks (~10):** `timer_section_present`, `on_boot_sec_or_on_calendar_set`, `on_unit_active_sec_or_on_calendar_set`, `persistent_true` (required for "survived reboots"), `unit_references_service`, `service_type_oneshot`, `service_exec_start_set`, `timer_file_and_service_file_both_present` (the reference is authored as 2 concatenated units in `reference/main.c` with a `# -- cleanup.service --` delimiter).
- **Negatives (12):** Missing Persistent, Type=simple instead of oneshot, Unit pointing to nonexistent, etc.
- **Difficulty:** medium. **Tier:** core. **Note:** TC authors TWO files concatenated in a single `reference/main.c` with delimiter comments; checks parse sections.

**linux-userspace-005: udev rule for USB hotplug + systemctl action**
- **Scenario:** udev rule matching a specific USB vendor/product, triggering a systemctl restart of a named service on `add` action.
- **Implicit signal:** "classical USB hotplug integration; match-vs-assign discipline".
- **Platform:** `native_sim`.
- **Factor:** F6, E2.
- **Reference highlights:** `SUBSYSTEM=="usb", ACTION=="add", ATTRS{idVendor}=="1d6b", ATTRS{idProduct}=="0002", TAG+="systemd", ENV{SYSTEMD_WANTS}="vendor-example-daemon.service"`.
- **Behavior checks (~11):** `subsystem_match_double_eq`, `action_match_double_eq`, `attr_match_double_eq`, `tag_systemd_added_via_plus_eq` (assignment, not match), `env_or_run_directive_present`, `no_assign_where_match_expected` (reject `SUBSYSTEM="usb"`), `no_match_where_assign_expected` (reject `RUN=="..."`), `vendor_product_ids_hex`.
- **Negatives (12):** `SUBSYSTEM="usb"` (assign not match), `ACTION="add"`, vendor ID as decimal, RUN without `+=`, missing action, etc.
- **Difficulty:** hard. **Tier:** challenge. — `==` vs `=` trap is a classic subtle bug.

**linux-userspace-006: spidev ioctl SPI_IOC_MESSAGE**
- **Scenario:** C program that opens `/dev/spidev0.0`, configures mode 0 + 8 bpw + 1MHz clock, performs a simultaneous TX+RX 4-byte transaction via `SPI_IOC_MESSAGE(1)`.
- **Implicit signal:** "direct UAPI access, no higher-level library; typical Yocto board debug tool".
- **Platform:** `docker_only`; **compile:** needs `linux/spi/spidev.h` (glibc-headers).
- **Factor:** A8 (protocol details), F1, F5.
- **Reference highlights:** `open("/dev/spidev0.0", O_RDWR)`, `ioctl(fd, SPI_IOC_WR_MODE, &mode)`, `ioctl(fd, SPI_IOC_WR_BITS_PER_WORD, &bpw)`, `ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &hz)`, `struct spi_ioc_transfer tr = {.tx_buf = (unsigned long)tx, .rx_buf = (unsigned long)rx, .len = 4, ...}`, `ioctl(fd, SPI_IOC_MESSAGE(1), &tr)`, close.
- **Behavior checks (~11):** `open_rdwr_spidev`, `ioctl_mode_set_before_transfer`, `ioctl_bpw_set`, `ioctl_speed_set`, `spi_ioc_transfer_has_both_tx_rx_buf_cast`, `tx_rx_buf_cast_to_unsigned_long`, `ioctl_message_1_used`, `close_called`, `no_arduino_spi_api` (reject `SPI.transfer`), `return_nonzero_on_error`.
- **Negatives (12):** Use `SPI_IOC_RD_*` for writes, missing `(unsigned long)` cast (silent ABI break), `SPI_IOC_MESSAGE(0)`, no close, `SPI.transfer()` Arduino leak, etc.
- **Difficulty:** hard. **Tier:** challenge.

**linux-userspace-007: sd-bus service with vtable**
- **Scenario:** A daemon that claims bus name `com.embedeval.Example`, exposes one method `Ping(s)→s`, processes messages in a loop.
- **Implicit signal:** "modern systemd-based embedded Linux — prefer the kernel-integrated bus API over the older cross-platform library".
- **Platform:** `docker_only`; **compile:** needs `libsystemd-dev`. If Docker lacks, set `l1_skip: true`.
- **Factor:** F2, F4.
- **Reference highlights:** `sd_bus_open_system(&bus)`, `sd_bus_add_object_vtable(bus, &slot, "/com/embedeval/Example", "com.embedeval.Example", vtable, NULL)`, `sd_bus_request_name(bus, "com.embedeval.Example", 0)`, loop with `sd_bus_process` + `sd_bus_wait`, cleanup with `sd_bus_slot_unref` + `sd_bus_unref`. Vtable declares `SD_BUS_VTABLE_START`, `SD_BUS_METHOD("Ping", "s", "s", method_ping, 0)`, `SD_BUS_VTABLE_END`.
- **Behavior checks (~12):** `sd_bus_api_used`, `no_libdbus_api` (reject `dbus_connection_open`, `dbus_message_new_method_return`, `DBusConnection`), `vtable_declared`, `bus_name_requested`, `process_wait_loop`, `slot_and_bus_unref_on_exit`, `method_callback_returns_int`, `sd_bus_error_propagation` (reject `return 0` on error), `no_cross_platform_apis`, `gpl_or_lgpl_compat_license_comment`.
- **Negatives (12):** LLM uses libdbus, missing vtable END, bus name request error unchecked, loop without wait, etc.
- **Difficulty:** hard. **Tier:** challenge.

**linux-userspace-008: eBPF CO-RE kprobe (BPF program only)**
- **Scenario:** BPF program attaching to `do_unlinkat` kprobe, reading the filename argument via CO-RE, pushing to a ringbuf for userspace consumption. **Only the `.bpf.c` program is authored** — userspace loader is out of scope per the "single-file reference" constraint.
- **Implicit signal:** "CO-RE portable BPF program targeting modern libbpf (1.x) on kernel 5.15 with BTF-enabled kernel image".
- **Platform:** `docker_only` with `l1_skip: true` (Docker image may lack `clang -target bpf` + `bpftool` + kernel BTF). Reference validated by static/behavior parse only.
- **Factor:** F1 (API hallucination), F2 (cross-platform API — BCC legacy), A1 (register access via pt_regs), A7 (kernel data struct awareness).
- **Reference highlights:** `#include "vmlinux.h"`, `#include <bpf/bpf_helpers.h>`, `#include <bpf/bpf_core_read.h>`, `#include <bpf/bpf_tracing.h>`, `char LICENSE[] SEC("license") = "GPL";`, `struct { __uint(type, BPF_MAP_TYPE_RINGBUF); __uint(max_entries, 4096); } events SEC(".maps");`, `SEC("kprobe/do_unlinkat") int BPF_KPROBE(trace_unlink, int dfd, struct filename *name) { ... BPF_CORE_READ(...); bpf_ringbuf_submit(...); return 0; }`.
- **Behavior checks (~11):** `vmlinux_h_included`, `bpf_helpers_h_included`, `bpf_core_read_h_included`, `sec_kprobe_macro_used`, `bpf_kprobe_signature`, `bpf_core_read_used`, `ringbuf_map_declared`, `license_section_gpl_compat` (`GPL` / `Dual BSD/GPL` / `LGPL`), `no_bcc_legacy_api` (reject `bpf_get_current_task`-style BCC or Python), `return_int_from_handler`, `no_kernel_pointer_deref` (must use BPF_CORE_READ not `->`).
- **Negatives (12):** Missing `SEC("license")`, missing `vmlinux.h`, using `task->comm` directly (no BPF_CORE_READ), BCC-style `BPF_KPROBE` typos, `SEC("kretprobe")` without `BPF_KRETPROBE`, etc.
- **Difficulty:** hard. **Tier:** challenge.

### Alternatives considered

- **Option B (scatter across existing categories):** Rejected in research — libgpiod → `gpio-basic` (was Zephyr), systemd → `security`, eBPF → no natural home. Would conflate benchmark aggregation signals and lose the Linux-userspace aggregate metric. The enum-churn savings (0 files) are swapped for permanent reporting confusion.
- **Option C (12 TCs including SWUpdate, cgroup/memory, netlink, libudev monitor, capabilities):** Rejected. After TC 8 the marginal factor-coverage drops to single-factor drills; SWUpdate is sufficiently covered by existing `ota` category (though Zephyr-side); cgroup tuning is niche; libudev monitor overlaps with udev rule + libgpiod event TC. 8 TCs is the right cutoff.
- **Keep full eBPF multi-file (BPF + userspace loader):** Rejected. Would force runner/evaluator refactor to support multi-file `reference/`. Defer to Phase C; BPF-source-only captures 80% of the failure-mode value at 30% of the complexity.
- **Include SWUpdate/RAUC OTA TC:** Rejected. User's BSP uses SWUpdate + Azure ADU; this is real but overlaps with `ota-*` category which already has 9 Zephyr MCUboot TCs. Adding Linux OTA deserves its own mini-plan (`PLAN-linux-ota-expansion`), not a squeeze into Phase B. **[Scoped in [PHASE-C-CANDIDATES.md](PHASE-C-CANDIDATES.md) — recommended Phase C-1.]**
- **Include D-Bus with dbus-c++ or GDBus as a third alternative:** Rejected. Three D-Bus binding TCs (sd-bus + libdbus + dbus-c++) triple the TC count with no factor novelty after the sd-bus-vs-libdbus discriminator. TC 007's single-sd-bus + reject-libdbus is the cleanest test.
- **Split TC 003 into `Type=notify` + `Restart policy` + `Sandboxing` 3 TCs:** Rejected as over-drilling. The triad (notify + WatchdogSec + Restart=on-watchdog) is the atomic failure mode; splitting would each be ~6-check TCs with little novelty. Sandboxing directives (NoNewPrivileges, PrivateTmp) can become a Phase C TC.

### Affected files

**New TC directories (64 files):**
- `cases/embedded-linux/linux-userspace-{001..008}/` — each with 7 files (metadata, prompt, src placeholder, reference, static, behavior, negatives) + empty `context/` dir. 8 × 8 = 64 file-system entries.

**Modified source:**
- `src/embedeval/models.py` — add `LINUX_USERSPACE = "linux-userspace"` enum value at end of Tier 3 block.
- `src/embedeval/check_utils.py` — add 9 new helpers:
  1. `strip_systemd_comments` — alias for `strip_yocto_comments` with docstring noting systemd/udev/NetworkManager share `#` line-comment semantics (factor out into one helper rather than aliasing).
  2. `systemd_unit_section_has(text, section, directive) -> str | None` — return the RHS of a `Directive=value` line inside the named `[Section]`, or None.
  3. `udev_rule_matches(text, key) -> str | None` / `udev_rule_assigns(text, key) -> str | None` — distinguish `key=="val"` match vs `key="val"` / `key+="val"` assignment.
  4. `has_libgpiod_v1_api(code) -> list[str]` — return list of detected v1 symbols (reject list: `gpiod_chip_get_line`, `gpiod_line_request_output`, `gpiod_line_request_input`, `gpiod_line_get_value`, `gpiod_chip_open_lookup`, `gpiod_line_request_rising_edge_events`, etc.)
  5. `has_libgpiod_v2_api(code) -> list[str]` — detect v2 symbols (`gpiod_chip_request_lines`, `gpiod_line_settings_*`, `gpiod_edge_event_*`, `gpiod_line_config_*`, `gpiod_request_config_*`).
  6. `has_sd_bus_api(code) -> list[str]` — detect `sd_bus_*` calls.
  7. `has_libdbus_api(code) -> list[str]` — detect `dbus_*` / `DBusConnection` / `dbus_message_*` patterns; reject list for TC 007.
  8. `has_bpf_sec_macro(code) -> list[str]` — detect `SEC("kprobe/...")`, `SEC("tp/...")`, `SEC("xdp")`, etc.; return the list of discovered sections.
  9. `has_bpf_core_read(code) -> bool` — detect `BPF_CORE_READ(` usage.
- `tests/test_check_utils_userspace.py` — NEW; unit tests for the 9 helpers, ≥3 cases each (happy, API-variant, false-positive trap).

**Modified manifests / docs:**
- `cases/SDK_LAYOUT.yaml` — 8 new `sdk: embedded-linux` rows (`linux-userspace-001..008`).
- `README.md:204` — `23 Categories` → `24 Categories`.
- `docs/METHODOLOGY.md:348` — Per-Category L1/L2 Applicability table gets a `linux-userspace` row: L1 applicable for subset (001, 002, 006, 007 — C sources), L2 skip (all userspace is docker_only or native_sim).
- `docs/METHODOLOGY.md:12` — **auto-refreshed** by `sync_docs.py` (TC count 248 → 256, category count 23 → 24 picked up from discovered metadata).
- `docs/BENCHMARK-linux-userspace-phase-b.md` — NEW, baseline delta report (deferred to Phase 6).
- `plans/PLAN-linux-tc-expansion-phase-b.md` — this file.

**NOT touched (explicit non-goals):**
- `src/embedeval/reporter.py` / `scorer.py` / `evaluator.py` / `runner.py` / `cli.py` — all iterate dynamically; no code change.
- `scripts/sync_docs.py` — category discovery is dynamic.
- `tests/test_reporter.py` / `test_runner.py` / `test_sdk_buckets.py` — hardcoded `CaseCategory.KCONFIG`/`.BLE` references still valid; no category-set assertion to update beyond the min_count in `test_sdk_buckets.py:91` which is already at 30 and covers 40+ embedded-linux cases by Phase B end (8 new + 32 existing).
- Existing 248 TC directories — 0 edits; `case_git_hash` preserved.
- `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` — follow-up task; check-name mapping updates deferred like Phase A.

## Implementation phases

### Phase 1: Shared helpers + unit tests — **DONE** (2026-04-19)
- [x] Added 9 helpers to `src/embedeval/check_utils.py` (`strip_systemd_comments` alias, `systemd_unit_section_has`, `udev_rule_matches`, `udev_rule_assigns`, `udev_match_key_used_as_assign`, `has_libgpiod_v1_api`, `has_libgpiod_v2_api`, `has_sd_bus_api`, `has_libdbus_api`, `has_bpf_sec_macro`, `has_bpf_core_read`) — 10 total including alias.
- [x] `tests/test_check_utils_userspace.py` — 40 tests across 7 classes (happy/edge/trap per helper, plus parametrized constant coverage).
- [x] Full gates green: `ruff format --check src/` + `ruff check src/` + `mypy src/` + `pytest`.

### Phase 2: Enum + doc manual edits — **DONE**
- [x] `src/embedeval/models.py` — appended `LINUX_USERSPACE = "linux-userspace"` under Tier 3.
- [x] `README.md:204` — "23 Categories" → "24 Categories".
- [x] `docs/METHODOLOGY.md:348` — added `linux-userspace` row in per-category L1/L2 applicability table.
- [x] Enum roundtrip verified: `CaseCategory("linux-userspace") == CaseCategory.LINUX_USERSPACE`.

### Phase 3: TC authoring — sub-batch A (text-only TCs 003, 004, 005) — **3/3 DONE**
- [x] **linux-userspace-003 (systemd Type=notify + WatchdogSec + Restart triad)** — ref 20/20, oracle 12/12.
- [x] **linux-userspace-004 (systemd timer + paired service, Persistent=true)** — ref 19/19, oracle 12/12.
- [x] **linux-userspace-005 (udev USB hotplug rule, ==/=/+= discipline)** — ref 14/14, oracle 12/12.

### Phase 4: TC authoring — sub-batch B (C-source TCs 001, 002, 006, 007, 008) — **5/5 DONE**
- [x] **linux-userspace-001 (libgpiod v2 CLI toggle)** — ref 15/15, oracle 12/12, `l1_skip: true` (Docker lacks libgpiod-dev v2).
- [x] **linux-userspace-002 (libgpiod v2 edge event monitor + SIGTERM)** — ref 15/15, oracle 12/12, `l1_skip: true`.
- [x] **linux-userspace-006 (spidev ioctl SPI_IOC_MESSAGE)** — ref 18/18, oracle 12/12, `l1_skip`: false (kernel headers suffice).
- [x] **linux-userspace-007 (sd-bus service vtable + no libdbus)** — ref 15/15, oracle 12/12, `l1_skip: true` (libsystemd-dev optional in Docker).
- [x] **linux-userspace-008 (eBPF CO-RE kprobe, BPF-only)** — ref 16/16, oracle 12/12, `l1_skip: true` (BPF toolchain deferred to Phase C).

### Phase 5: SDK layout + docs sync + tracker refresh — **DONE**
- [x] `cases/SDK_LAYOUT.yaml` — 8 new `linux-userspace-00*: sdk: embedded-linux` rows appended.
- [x] `scripts/sync_docs.py` — 248 → 256 TC, 23 → 24 categories, 59 → 67 negative TCs, 410 → 506 mutations.
- [x] `embedeval refresh-tracker` — 0 pairs marked (clean), TEST_RESULTS.md refreshed.

### Phase 6: Quality gates + verification — **DONE**
- [x] Full gates green (1330 pytest passed, 4 skipped; ruff/mypy clean).
- [x] `embedeval validate --cases cases/` — 208/208 PASS.
- [x] Implicit-prompt grep: only "do NOT use v1 API" / "do NOT use libdbus" (negative prescription — policy-compliant, different from positive "use X" prescription).
- [x] `qcells` vendor namespace: 0 occurrences in Phase B TCs.
- [x] Per-TC oracle verification — 8 TCs × 12 mutations = 96 mutations, all triggering their must_fail targets.

### Phase 7: Baseline benchmark (optional, out of core Phase-B scope)
- [ ] `uv run embedeval run --cases cases/ --model claude-haiku-4-5-20251001 --case-ids linux-userspace-001,...,008 --output runs/phase-b-delta-haiku` — n=1 sanity.
- [ ] Same for Sonnet.
- [ ] If n=1 shows no degenerate TC (all between 10% and 90%), re-run n=3.
- [ ] Generate `docs/BENCHMARK-linux-userspace-phase-b.md` — per-TC pass rates, factor-coverage matrix, commentary on which TCs discriminate.
- [ ] Update `memory/MEMORY.md` with TC count 256 + Phase B completion.

## Testing strategy

- **Unit tests (`tests/test_check_utils_userspace.py`):** 9 helpers × ≥3 cases = ≥27 tests. Pin each documented false-positive trap (libgpiod v1/v2 symbol overlap, udev match-vs-assign, systemd section boundary, sd-bus/libdbus prefix collision, BPF SEC macro variants).
- **Reference self-check:** every `reference/main.c` passes 100% of its own static + behavior checks before the TC is marked complete. Verified via an ad-hoc Python snippet during authoring (pattern established in Phase A).
- **Oracle verification:** `scripts/verify_negatives_oracle.py` applies every mutation to the reference and asserts the `must_fail` check names actually fail. Any un-triggered mutation blocks the TC.
- **Implicit-prompt guard:**
  ```
  FORBIDDEN = 'devm_|IS_ERR|PTR_ERR|kthread_run|kthread_should_stop|INIT_WORK|schedule_work|request_threaded_irq|regmap_init|GFP_ATOMIC|GFP_KERNEL|IRQF_ONESHOT|spin_lock_irqsave|cancel_work_sync|workqueue|task_struct|work_struct'
  ALLOWED_DIRECTIVE_SURFACE = 'Type=|WatchdogSec=|Restart=|ExecStart=|After=|OnBootSec=|OnUnitActiveSec=|Persistent=|SUBSYSTEM==|ACTION==|ATTRS|RUN+=|TAG+=|SYMLINK+=|ENV{|gpiod_chip_|gpiod_line_|gpiod_edge_|SPI_IOC_|sd_bus_|SEC\("|BPF_CORE_READ'
  ```
  Grep prompts: `FORBIDDEN` must return empty; `ALLOWED_DIRECTIVE_SURFACE` hits are OK (exempt per Phase A/B policy).
- **Cross-TC helper reuse discipline:** after writing each TC's behavior.py, grep for repeated local regex patterns; if a pattern appears in ≥2 TCs, extract into a check_utils helper.
- **Quality gates before every commit:** `ruff format --check src/ tests/`, `ruff check src/ tests/`, `mypy src/`, `pytest tests/`.
- **Doc sync:** after Phase 5, diff `docs/METHODOLOGY.md` + `README.md` to confirm exactly the expected changes (+1 category row, TC/case counts bumped).
- **Benchmark smoke:** 1 TC × 1 model × n=1 before batch commit, to catch broken prompts cheaply.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Docker image lacks `libgpiod-dev` v2.x → TC 001, 002 fail L1 compile. | Med | Verify during Phase 4 by attempting `apt list --installed libgpiod-dev` in the CI Docker image. If absent, set `l1_skip: true` and document in metadata.yaml; reference's correctness relies on static + behavior checks only. |
| Docker image lacks `libsystemd-dev` → TC 007 fails L1 compile. | Med | Same pattern: `l1_skip: true` fallback. Sanity-check the sd-bus reference by reading libsystemd's headers from `meta-qcells-edge` or upstream source to pin symbol list. |
| Docker image lacks `clang -target bpf` + `bpftool` + BTF → TC 008 fails L1. | High | **Preempt:** TC 008 metadata has `l1_skip: true` from the start. BPF reference is parse-checked only. Note in TC README that compile verification requires a BTF-enabled kernel + BPF toolchain (reserved for a Phase C refactor). |
| libgpiod v2 symbol overlap with v1 — `gpiod_chip_open` exists in both. `has_libgpiod_v1_api` must list only v1-EXCLUSIVE symbols. | High | Pilot the helper on known v1 reference files (upstream `libgpiod v1.6` examples) and v2 reference files (`libgpiod v2.0+` examples) before it's used in a TC check. Document the v1/v2 symbol boundary in the helper docstring. |
| udev rule `==` vs `=` trap regex too naive — `ENV{FOO}="bar"` (assignment, correct) is easy to false-flag. | Med | Distinguish via directive context: some keys (`SUBSYSTEM`, `ACTION`, `KERNEL`, `ATTRS{...}`, `DRIVERS`) are match-only; others (`ENV{...}`, `NAME`, `SYMLINK`, `TAG`, `RUN`, `OWNER`, `GROUP`, `MODE`) are assign-only (with `=`/`+=`). Encode this in the helper. |
| systemd `Type=notify` without `sd_notify` call — LLM writes the unit but forgets the daemon side (out of scope for TC 003 which is unit-file-only). | Low | TC 003 is strictly the `.service` unit. Document in prompt that the daemon-side `sd_notify(..., "WATCHDOG=1")` logic is assumed provided. Do NOT check for daemon-side C code in this TC. |
| eBPF TC's `vmlinux.h` stub — reference claims `#include "vmlinux.h"` but file not present in the TC dir. | Med | TC 008's `reference/` includes a minimal `vmlinux.h` stub (~20 lines covering `struct task_struct`, `struct filename` — just enough to make `BPF_CORE_READ` valid for the reference's specific reads). Alternative: don't ship vmlinux.h and rely on parse-only checking. Pick the latter; document. |
| Cross-platform API check pulls false positives on udev rule text — e.g., `delay(` substring. | Low | `check_no_cross_platform_apis` is only called on TCs with C source (001, 002, 006, 007, 008). Text-only TCs (003, 004, 005) skip it. |
| `sync_docs.py` output differs from expected — regenerated difficulty table missing `linux-userspace` row. | Low | After Phase 5 sync, grep `docs/METHODOLOGY.md` for `linux-userspace` — should appear in 2 tables (difficulty by category + L1/L2 applicability). Manually add the L1/L2 row if absent. |
| TC 004 (timer + service paired) — `reference/main.c` holds two concatenated unit files; some check_utils regex may cross the delimiter. | Med | Delimiter is `# === cleanup.service ===` on its own line. Behavior.py splits on this delimiter before running section checks. Document the split in the check docstring. |
| TC 005 udev rule contains `vendor,example` / `1d6b` / `0002` (Linux Foundation's USB VID) — confirm no proprietary customer USB IDs leaked. | High | USB VID `0x1d6b` is Linux Foundation's (used in `usb/quirks.c`, public). PID `0x0002` is xHCI Root Hub (public). Confirm by grep against `~/EDGE/sources/meta-qcells-*` (must be absent); grep should return empty. Otherwise pick a different public VID/PID pair. |
| Phase A RLHF-bias mutations (LLM omits safety patterns) don't translate cleanly to Phase B — userspace failure modes are different class (API selection, not safety pattern). | Low | Phase B mutations target API-selection and directive-semantics failure modes — documented per TC. This is a feature, not a bug; it expands embedeval's factor coverage. |
| Enum extension breaks `tests/test_reporter.py` due to stale enum iteration. | Low | `test_reporter.py` uses hardcoded `CaseCategory.KCONFIG`/`.BLE` only; doesn't iterate the full enum. Full `pytest tests/` in Phase 6 will catch any regression. |
| `test_sdk_buckets.py:91` min_count assertion — we set it to 30 in Phase A; Phase B adds 8 more, bringing `embedded-linux` bucket to 40+. Test still passes. | Nil | None needed. |
| Benchmark cost: Haiku + Sonnet × 8 new TCs × n=3 ≈ 48 calls × ~600 tokens ≈ \$5-8. | Low | Run n=1 sanity first; only proceed to n=3 if TCs are discriminating. Log cost in BENCHMARK-linux-userspace-phase-b.md. |

## Review checklist (verify before /execute)

- [ ] Scope correct: 8 TCs, 1 enum value, 9 helpers, 3 doc touchpoints, 0 touches to existing 248 TCs.
- [ ] Enum-extension blast radius matches the audit (3 manual files; rest dynamic).
- [ ] Every TC has a specific 42-factor cell target (F2/F4/F6/A8/E2/E5/B2/B3 — confirmed).
- [ ] Every prompt passes the implicit-prompt grep (with documented directive exemption for systemd/udev/libgpiod v2/spidev/sd-bus/eBPF directive surface).
- [ ] Every TC has a ≥12-entry mutation oracle with `factor_id` tags.
- [ ] Shared helpers live in `check_utils.py` (not inlined per TC) and have unit tests.
- [ ] `SDK_LAYOUT.yaml` updated; `sync_docs.py` runs clean.
- [ ] Existing 248 TC dirs untouched (verify with `git diff --stat cases/` restricted to `linux-userspace-*`).
- [ ] All four quality gates green.
- [ ] `verify_references_build.py` + `verify_negatives_oracle.py` both green on new TCs.
- [ ] Phase B is strictly additive — no reporter/scorer/evaluator logic change; no existing-category reshuffling; `case_git_hash` preserved for 248 TCs.
- [ ] Risk table addresses Docker image dependencies (libgpiod v2, libsystemd, BPF toolchain) + libgpiod v1/v2 symbol overlap + udev match/assign disambiguation + USB VID safety.
- [ ] Phase A's CLAUDE.md corrections applied throughout (scoped_contains scope, variable-name hardcoding, vendor namespace neutrality, implicit-prompt discipline with directive exemption).
