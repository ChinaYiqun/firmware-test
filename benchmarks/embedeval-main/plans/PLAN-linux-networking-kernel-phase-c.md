---
type: plan
task_slug: linux-networking-kernel-phase-c
status: planning
created: 2026-04-19
tags: [embedeval, plan, networking, linux-kernel, netfilter, netlink, sk_buff, phase-c]
---

# PLAN: Linux networking kernel expansion — Phase C-2

**Task:** Add 5 kernel-side Linux networking TCs (`networking-kernel-001..005`) under the existing `networking` category + `embedded-linux` SDK bucket, targeting netfilter hooks, sk_buff handling, netlink sockets, generic netlink families, and rtnetlink notifiers. Pinned to linux-imx 5.15 LTS. Zero enum churn.
**Created:** 2026-04-19

## Executive summary

**TL;DR:** Five kernel-module TCs extending the `networking` category with Linux-kernel-side coverage (softirq context discipline + sk_buff lifecycle + netlink message handling), reusing Phase A's linux-driver patterns and 12-mutation oracle convention.

### What

Author 5 single-file kernel module TCs under `cases/embedded-linux/networking-kernel-{001..005}/`, each with the canonical 6-file layout (metadata.yaml, prompt.md, src/main.c placeholder, reference/main.c, checks/{static,behavior,negatives}.py). Add 4 new shared helpers to `src/embedeval/check_utils.py` (netfilter hook detection, sk_buff lifecycle, netlink API detection, genl family detection) with ≥3 unit tests each. Reuse Phase A helpers (`extract_module_init_body`, `has_api_call`, `sleepable_calls_in_atomic_ctx`, `strip_comments`). `SDK_LAYOUT.yaml` gets 5 new rows; `sync_docs.py` bumps 262 → 267 TCs.

### Why

Phase C-1 (OTA) strengthened E4 across a second platform. Phase C-2 targets the other gap PHASE-C-CANDIDATES.md flagged: **softirq concurrency context is empirically absent from the benchmark**. Phase A's linux-driver TCs cover hardirq and process context; netfilter hooks and packet-path code run in softirq — a distinct context with its own restrictions (no sleeping, can't use `GFP_KERNEL`, `rcu_read_lock` expected). LLMs frequently conflate softirq with process context because both look "non-hardirq" in the code. Plus: no academic LLM+Linux-networking-kernel benchmark exists (web search empty), making this the user's pick for fresh signal.

### Key decisions

- **Reuse `CaseCategory.NETWORKING`, no enum extension.** PHASE-C-CANDIDATES.md Candidate 3 recommendation. Category is about failure domain (networking protocols, socket lifecycles, packet handling), not platform. → zero reporter/scorer/SDK_LAYOUT churn.
- **TC IDs use `networking-kernel-*` prefix, not `networking-009..013`.** Resolves the PHASE-C-CANDIDATES.md review nit #5. The `-kernel-` infix is a linguistic cue that these are kernel modules, distinct from the 8 Zephyr-userspace `networking-001..008` TCs already in the bucket. Directory listing remains alphabetical and self-describing.
- **5 TCs, no stretch.** Matches Phase B's 8-TC cutoff discipline relative to Phase A's 15. The 5 TCs cover 5 distinct kernel-networking APIs: netfilter, sk_buff, netlink kernel socket, generic netlink family, rtnetlink notifier. Adding a 6th (e.g., TC classifier) would overlap with netfilter on the hook-registration axis.
- **Kernel 5.15 LTS APIs only.** Matches Phase A linux-driver sdk_version. Specific 5.15 facts: `nf_register_net_hooks(net, ops, n)` (3-arg form stable since 4.13); `netlink_kernel_create(net, unit, cfg)` with `struct netlink_kernel_cfg` (stable since 3.10); `genl_register_family` with `struct genl_family` (stable since 3.13); `register_netdevice_notifier(nb)` with `struct notifier_block` (stable since pre-3.0). Do not use APIs that appeared in 5.16+ or were removed before 5.15.
- **All 5 TCs: `platform: docker_only`, `l1_skip: true`, `l2_skip: true`.** Kernel modules can't run in native_sim and the Docker image doesn't carry kernel headers + build infrastructure for parse-and-link compile checks. Static + behavior + negatives oracle is the entire validation surface. Matches Phase A `linux-driver-009..016`.
- **Implicit-prompt discipline, with C-code-API exemption.** Prompts MUST NOT name function-call APIs as required (`nf_register_net_hooks`, `skb_clone`, `netlink_kernel_create`, `genl_register_family`, `register_netdevice_notifier`) — those are what we're testing. Allowed to name kernel facility classes in prose ("register a netfilter hook", "a kernel netlink endpoint", "a generic netlink family"). Allowed to name required-header paths (`linux/netfilter.h`) only if the hook name itself doesn't appear. Kernel-struct names (`struct sk_buff`, `struct nf_hook_ops`) are grammar surface and may appear.
- **Every TC gets a 12-mutation oracle with `factor_id` tags.** Matches Phase A/B/C-1 convention. Dominant factor per TC: 001→D5 (softirq context); 002→E2/E3 (skb lifecycle); 003→E1/E2 (netlink cleanup on init failure); 004→F5 (genl_family struct members); 005→E1/E2 (notifier register/unregister).
- **Reference files vendor-neutral.** Use `embedeval,netfilter-example` / `embedeval,netlink-example` string identifiers. No `qcells` / `/edge/` paths; grep-verify before commit.
- **FAILURE-FACTORS v1.7 deferred.** Same cadence as Phase C-1 — new check names accumulate across Phase C-1 and C-2, then a single follow-up PLAN syncs v1.7 (mirror of commit `959de3d`).

### Impact

- Complexity: **Medium**
- Risk: **Low** (additive; reuses existing category; C-source kernel modules with `docker_only` + `l1_skip`; no runner/evaluator changes)
- Files changed: **~38** (5 TCs × 6 files = 30, +4 helpers in check_utils.py, +1 test module, +SDK_LAYOUT.yaml, +3 doc touchpoints via sync_docs)
- Estimated effort: **10–14h** implementation + 2–3h baseline benchmark

## Prior work

- [plans/PHASE-C-CANDIDATES.md](PHASE-C-CANDIDATES.md) — scoped this as Phase C-2. Candidate 3 spec: 5–7 TCs, reuse `networking` category, factor delta = softirq concurrency context + netfilter unregister on failure + skb error paths.
- [plans/PLAN-linux-tc-expansion-phase-a.md](PLAN-linux-tc-expansion-phase-a.md) — kernel module TC template (linux-driver-009..016). Helpers in `check_utils.py` — `extract_module_init_body`, `extract_module_exit_body`, `has_api_call`, `has_manual_free_paired_with_devm`, `sleepable_calls_in_atomic_ctx`, `check_no_cross_platform_apis`, `in_init_scope_only` — all reusable here. Phase A established the 12-mutation oracle + `factor_id` tag discipline + implicit-prompt exemption for grammar-surface.
- [plans/PLAN-linux-ota-expansion-phase-c.md](PLAN-linux-ota-expansion-phase-c.md) — Phase C-1 precedent for scoped directive-heavy TCs with implicit-prompt exemption; this PLAN mirrors the shape at a smaller scale (5 TCs vs 6).
- [cases/embedded-linux/linux-driver-011](cases/embedded-linux/linux-driver-011) — closest single-TC analogue. Uses `INIT_WORK` + `schedule_work` to defer from hardirq to process context via workqueue. `networking-kernel-001` (netfilter hook) has the same softirq→process deferral pattern via `schedule_work`, so `linux-driver-011`'s helpers (`_find_isr_body`, `_find_worker_body`, `sleepable_calls_in_atomic_ctx`) generalize cleanly.
- [cases/embedded-linux/linux-driver-010](cases/embedded-linux/linux-driver-010) — IRQ + waitqueue + copy_to_user pattern. `networking-kernel-003` (netlink kernel socket) uses the same user-kernel-boundary pattern (`nlmsg_parse` + `nla_*` accessors), just over netlink rather than chardev.
- **CLAUDE.md corrections directly applied:**
  - 2026-04-19 (v1.6): `scoped_contains` default strips string literals → always pass `scope='code_only'` in kernel-C-code TCs.
  - 2026-04-19 (Phase A fixup — `has_devm_alloc_without_manual_free`): check regexes must NOT hardcode reference variable names; extract LHS from assignment pattern first.
  - 2026-04-19 (Phase A fixup): implicit-prompt + grammar-surface exemption — applied: prompts name kernel struct names + required header paths but NOT function-call APIs.
  - 2026-04-19 (Phase A first wrap): vendor-namespace neutrality — `embedeval,*` identifiers only.
  - 2026-04-19 (Phase C-1 review): mutation regex must not rely on reference-specific field ordering or hex-value patterns (rauc-002 had this); use order-independent walkers. Applied in Risk table R3 mitigation.

## Problem analysis

### Current state

**TC inventory as of commit `e1a92ee` (post-Phase-C-1):**
- 214 public + 48 private = 262 TCs. 24 categories, 6 platforms.
- `networking` category: 10 TCs (8 Zephyr + 1 ESP-IDF WiFi + 1 STM32 UART). All userspace/MCU; **kernel-side networking is 0 TCs**.
- `embedded-linux` SDK bucket: 46 TCs (linux-driver, yocto, boot-uboot, linux-userspace, ota-*). No networking kernel module.

**Infrastructure already in place:**
- `CaseCategory.NETWORKING = "networking"` at `src/embedeval/models.py:22` — reused.
- `CaseCategory.LINUX_DRIVER`-equivalent TC patterns: `platform: docker_only`, `l1_skip: true`, `l2_skip: true`, static + behavior + negatives modules.
- Phase A helpers in `check_utils.py`: `extract_function_body`, `extract_module_init_body`, `extract_module_exit_body`, `has_api_call`, `check_no_cross_platform_apis`, `sleepable_calls_in_atomic_ctx`, `in_init_scope_only`, `strip_comments`, `scoped_contains`.
- 12-mutation oracle pattern established.
- `scripts/verify_negatives_oracle.py --category networking` exists (currently green for Zephyr TCs).
- `sync_docs.py` auto-refreshes TC count.

**API references (upstream, neutral, 5.15-stable):**
- `linux/netfilter.h` — `struct nf_hook_ops { nf_hookfn *hook; unsigned int hooknum; u_int8_t pf; int priority; };` + `nf_register_net_hooks(net, ops, n)` / `nf_unregister_net_hooks(net, ops, n)`.
- `linux/netlink.h`, `net/netlink.h` — `netlink_kernel_create(net, unit, cfg)` with `struct netlink_kernel_cfg { void (*input)(struct sk_buff *); ... };` + `netlink_kernel_release(sock)`.
- `net/genetlink.h` — `struct genl_family { .name, .version, .maxattr, .ops, .n_ops, ... };` + `genl_register_family(family)` / `genl_unregister_family(family)`.
- `linux/netdevice.h`, `linux/notifier.h` — `register_netdevice_notifier(nb)` with `struct notifier_block { notifier_fn_t notifier_call; };` + events `NETDEV_UP`, `NETDEV_DOWN`, `NETDEV_REGISTER`, etc.
- `linux/skbuff.h` — `skb_clone`, `skb_queue_tail`, `skb_dequeue`, `kfree_skb`, `consume_skb`, `skb_copy_bits`.

### Success criteria

- [ ] 5 new TC directories under `cases/embedded-linux/networking-kernel-{001..005}/` with complete 6-file layout.
- [ ] Every `metadata.yaml` validates: `category: networking`, `sdk: embedded-linux`, `platform: docker_only`, `l1_skip: true`, `l2_skip: true`, `sdk_version: '5.15'`, `tier: core | challenge`.
- [ ] Every reference `main.c` passes 100% of its own static + behavior checks.
- [ ] Every `negatives.py` has ≥12 mutations with `factor_id` tags; all mutations trigger their `must_fail` check names (verified by `scripts/verify_negatives_oracle.py`).
- [ ] 4 new helpers in `src/embedeval/check_utils.py`:
  1. `has_nf_hook_ops_struct(code) -> bool` — detects `struct nf_hook_ops` declaration.
  2. `has_nf_register_call(code) -> bool` — detects `nf_register_net_hooks` or `nf_register_net_hook` (both valid on 5.15).
  3. `has_netlink_kernel_api(code) -> list[str]` — returns list of detected netlink-kernel-side symbols (`netlink_kernel_create`, `netlink_kernel_release`, `nlmsg_parse`, `nla_put_*`).
  4. `has_genl_family_struct(code) -> bool` — detects `struct genl_family` declaration with at least one of `.ops` / `.small_ops` / `.n_ops`.
- [ ] Unit tests at `tests/test_check_utils_networking_kernel.py` with ≥3 cases per helper (happy + false-positive trap + API-variant acceptance).
- [ ] `cases/SDK_LAYOUT.yaml` extended with 5 `sdk: embedded-linux` rows.
- [ ] `uv run python scripts/sync_docs.py` updates TC count 262 → 267 (214 → 219 public).
- [ ] Implicit-prompt grep passes: no function-call API names in prompts outside the declared grammar-surface exemption (kernel struct names + required header paths OK).
- [ ] `qcells` / customer-specific paths absent from all 5 TCs (grep returns empty).
- [ ] `uv run embedeval validate --cases cases/` — all 267 TCs pass.
- [ ] Quality gates green: `ruff format --check src/`, `ruff check src/ tests/`, `mypy src/`, `pytest tests/`.
- [ ] Baseline n=1 sanity benchmark (Haiku + Sonnet) on the 5 new TCs; if non-degenerate, re-run n=3; produce `docs/BENCHMARK-networking-kernel-phase-c.md` with per-TC pass rates + commentary on softirq-context failure modes.
- [ ] FAILURE-FACTORS v1.7 trailer sync: **deferred** to a follow-up PLAN after Phase C-2 ships (same cadence as v1.6 commit `959de3d`).

## Design

### Approach — single batch, bottom-up

Five TCs authored in dependency order (helpers first, then hardest-to-easiest TCs so template drift surfaces early):

1. **Phase 1 — shared helpers + unit tests.** 4 helpers, 12+ tests.
2. **Phase 2 — TC authoring sub-batch** (factor-coverage order):
   - `networking-kernel-001` (netfilter hook, softirq context) — hardest, locks context discipline.
   - `networking-kernel-002` (sk_buff lifecycle) — depends on skb patterns from 001.
   - `networking-kernel-003` (netlink kernel socket) — independent API surface.
   - `networking-kernel-004` (generic netlink family) — independent, shares netlink headers with 003.
   - `networking-kernel-005` (rtnetlink notifier) — smallest, pure error-path discipline.
3. **Phase 3 — SDK layout + docs sync + integration checks.**
4. **Phase 4 — full quality gates + oracle verification.**
5. **Phase 5 — baseline benchmark delta report.**

### Per-TC design sheet

**networking-kernel-001: Netfilter pre-routing hook with softirq-safe logging**
- **Scenario:** Register a netfilter hook at `NF_INET_PRE_ROUTING`. Hook inspects incoming packets, counts them via a per-netns atomic, defers verbose logging to a workqueue worker. Unregister on module exit AND on init failure (partial cleanup).
- **Implicit signal:** "LLM must recognize netfilter hook runs in softirq → no sleeping, no `printk` at non-`KERN_ERR` level (OK but spammy), no `GFP_KERNEL`. Must use `GFP_ATOMIC` for any skb allocation. Deferral to workqueue for heavy work. Partial cleanup if `nf_register_net_hooks` fails after kthread_create succeeds."
- **Factors:** D5 (softirq context restrictions), E1 (error-path cleanup in init), F5 (`linux/netfilter.h`, `linux/netfilter_ipv4.h`).
- **Reference highlights:** `struct nf_hook_ops ops = { .hook = my_hookfn, .hooknum = NF_INET_PRE_ROUTING, .pf = PF_INET, .priority = NF_IP_PRI_FIRST };` + `nf_register_net_hooks(&init_net, &ops, 1)` in init + `nf_unregister_net_hooks` in exit + `schedule_work(&stats_work)` from the hook + `INIT_WORK` in init.
- **Behavior checks (~12):** `nf_hook_ops_struct_declared`, `nf_hook_ops_has_hooknum_pre_routing`, `nf_hook_ops_has_pf_inet`, `nf_register_call_in_init`, `nf_unregister_call_in_exit`, `hook_fn_has_softirq_safe_body` (no `kmalloc(GFP_KERNEL)`, no `kthread_run`, no `msleep`), `hook_fn_returns_nf_accept_or_drop`, `work_struct_declared_for_deferral`, `init_err_path_unregisters_on_failure`, `no_cross_platform_apis`, `no_gfp_kernel_in_hook_body`, `hook_counter_is_atomic_t`.
- **Difficulty:** hard. **Tier:** challenge.

**networking-kernel-002: sk_buff clone + queue + kfree_skb discipline**
- **Scenario:** Per-module kernel skb queue. Module's init creates a workqueue worker that `skb_dequeue`s and processes skbs; a netfilter hook (or exported function) enqueues cloned skbs via `skb_clone(GFP_ATOMIC)` + `skb_queue_tail`. On clone failure: `kfree_skb` the clone (NULL-guarded, no-op if clone is NULL). On worker processing: `consume_skb` (not `kfree_skb`) on success. On module exit: drain the queue via `skb_queue_purge`.
- **Implicit signal:** "skb_clone can fail, returns NULL. `kfree_skb(NULL)` is a no-op but best practice is to null-guard anyway. `consume_skb` vs `kfree_skb` distinction — consume_skb for normal completion, kfree_skb for error drops (dropwatch tooling uses this). `skb_queue_purge` on module unload to prevent leaks."
- **Factors:** E2 (return value checking on skb_clone), E3 (resource lifecycle), D5 (softirq-safe enqueue).
- **Reference highlights:** `struct sk_buff_head my_queue;` + `skb_queue_head_init(&my_queue)` + `skb_clone(skb, GFP_ATOMIC)` with NULL check + `skb_queue_tail(&my_queue, clone)` + worker loop: `while ((skb = skb_dequeue(&my_queue))) { ... consume_skb(skb); }` + exit: `skb_queue_purge(&my_queue)`.
- **Behavior checks (~12):** `sk_buff_head_declared`, `skb_queue_head_init_called`, `skb_clone_return_null_checked`, `skb_clone_uses_gfp_atomic`, `skb_queue_tail_called`, `worker_uses_skb_dequeue`, `worker_uses_consume_skb_on_success`, `no_kfree_skb_on_success_path`, `exit_calls_skb_queue_purge`, `no_cross_platform_apis`, `no_raw_skb_copy`, `gfp_atomic_used_in_enqueue_path`.
- **Difficulty:** hard. **Tier:** challenge.

**networking-kernel-003: Netlink kernel socket with input callback**
- **Scenario:** Create a kernel-side netlink socket on a custom protocol number. Register an `input` callback that receives user-space messages via `sk_buff`, parses the first netlink message with `nlmsg_hdr` + `nlmsg_data`, and emits a reply via `netlink_unicast`. Release the socket on module exit. Handle socket creation failure in init with proper cleanup.
- **Implicit signal:** "`netlink_kernel_create` takes a `struct netlink_kernel_cfg` with `.input` function pointer. Input callback runs in process context (on the socket's recv queue), so sleeping is allowed. `netlink_kernel_release` pairs with create. `nlmsg_hdr` + `NLMSG_DATA` macros for header access; `netlink_unicast` for reply. `NETLINK_USERSOCK` is a reserved generic family — use a custom number (>= 24 typically)."
- **Factors:** E1 (cleanup on create failure), E2 (check socket creation return), F5 (netlink headers).
- **Reference highlights:** `static struct sock *nl_sk;` + `struct netlink_kernel_cfg cfg = { .input = my_input_cb };` + `nl_sk = netlink_kernel_create(&init_net, MY_NETLINK_PROTO, &cfg)` with NULL check + `netlink_kernel_release(nl_sk)` in exit + input cb uses `nlmsg_hdr(skb)` + `netlink_unicast(nl_sk, reply, pid, 0)`.
- **Behavior checks (~12):** `netlink_kernel_create_called`, `netlink_kernel_create_return_null_checked`, `netlink_kernel_cfg_has_input_field`, `netlink_kernel_release_in_exit`, `input_cb_uses_nlmsg_hdr`, `input_cb_processes_skb`, `unicast_reply_path_present`, `init_err_returns_enomem_on_null`, `custom_netlink_proto_not_generic_usersock`, `no_cross_platform_apis`, `nl_sk_is_static_or_module_local`, `no_plain_sock_release`.
- **Difficulty:** hard. **Tier:** challenge.

**networking-kernel-004: Generic netlink family registration**
- **Scenario:** Register a generic netlink family with a single operation `MY_CMD_ECHO`. The family declares `.name`, `.version = 1`, `.maxattr`, `.module = THIS_MODULE`, and a static `.ops` array with one `struct genl_ops` entry. The op handler runs in process context, reads an attribute, and emits a reply. On module exit: `genl_unregister_family`.
- **Implicit signal:** "Generic netlink replaces custom netlink protocols for new designs. `genl_register_family` since 3.13, single-arg form. Must declare `.module = THIS_MODULE` so userspace `genlctl` can discover the family. Ops table needs `.cmd`, `.doit` (handler), `.flags` (e.g., `GENL_ADMIN_PERM`). Attribute array bounded by `.maxattr` — accessing `attrs[n]` for `n > maxattr` is UB."
- **Factors:** F5 (genl_family / genl_ops struct surface), E1 (unregister on exit), F1 (avoiding older deprecated `genl_register_family_with_ops` variant).
- **Reference highlights:** `static struct genl_ops my_ops[] = { { .cmd = MY_CMD_ECHO, .doit = my_doit, ... } };` + `static struct genl_family my_family = { .name = "embedeval_netlink_ex", .version = 1, .module = THIS_MODULE, .ops = my_ops, .n_ops = ARRAY_SIZE(my_ops), .maxattr = MY_ATTR_MAX };` + `genl_register_family(&my_family)` in init + `genl_unregister_family` in exit.
- **Behavior checks (~12):** `genl_family_struct_declared`, `genl_family_has_name_field`, `genl_family_has_module_this_module`, `genl_family_has_ops_array`, `genl_family_has_n_ops`, `genl_family_has_maxattr`, `genl_ops_has_cmd_and_doit`, `genl_register_family_in_init`, `genl_unregister_family_in_exit`, `no_deprecated_genl_register_family_with_ops`, `no_cross_platform_apis`, `family_name_is_neutral_not_qcells`.
- **Difficulty:** hard. **Tier:** challenge.

**networking-kernel-005: Netdevice notifier for NETDEV_UP / NETDEV_DOWN events**
- **Scenario:** Register a netdevice notifier that logs when any network interface goes up or down. Notifier callback receives `NETDEV_*` event + `struct net_device *`. Register in init with `register_netdevice_notifier`; unregister in exit with `unregister_netdevice_notifier`. If registration fails, return the error (no partial state to unwind).
- **Implicit signal:** "Notifier chain registration is a standard kernel-wide pattern. `struct notifier_block { notifier_fn_t notifier_call; };` + register/unregister. Callback returns `NOTIFY_OK` / `NOTIFY_DONE`. Events are #define'd in `linux/netdevice.h` (NETDEV_UP, NETDEV_DOWN, NETDEV_REGISTER, NETDEV_UNREGISTER, etc.)."
- **Factors:** E1 (register/unregister balance), E2 (check register return), F5 (notifier_block struct).
- **Reference highlights:** `static struct notifier_block my_nb = { .notifier_call = my_event_cb };` + `register_netdevice_notifier(&my_nb)` in init + check return != 0 + `unregister_netdevice_notifier(&my_nb)` in exit + callback switches on event, returns `NOTIFY_OK`.
- **Behavior checks (~12):** `notifier_block_struct_declared`, `notifier_block_has_notifier_call`, `register_netdevice_notifier_in_init`, `unregister_netdevice_notifier_in_exit`, `init_checks_register_return`, `callback_returns_notify_ok_or_done`, `callback_switches_on_netdev_up_or_down`, `callback_gets_net_device_from_ptr`, `no_cross_platform_apis`, `exit_always_unregisters`, `no_duplicate_register_calls`, `notifier_block_is_static_or_global`.
- **Difficulty:** medium. **Tier:** core.

### Alternatives considered

- **Extend networking enum with `LINUX_NETWORKING_KERNEL` variant.** Rejected per PHASE-C-CANDIDATES.md — category is about failure domain, not platform. Kernel vs userspace distinction is already captured by `sdk: embedded-linux` vs `sdk: zephyr`.
- **Use `networking-009..013` IDs instead of `networking-kernel-*`.** Rejected. The `-kernel-` infix gives readers an immediate clue that these are kernel modules, without needing to open `metadata.yaml`. Also prevents accidental conflation with future Zephyr networking TCs.
- **Ship 7 TCs including packet socket AF_PACKET + TC classifier.** Rejected for v1. Packet socket with classic BPF filter (sock_filter array) is technically userspace, not kernel; the BPF runs on the kernel side but from a userspace TC perspective. TC classifier hook (`cls_ops`) overlaps with netfilter on the hook-registration axis without adding novel factor coverage. 5 is the right cutoff; 6th+ would be single-factor drills.
- **Include user-mode eBPF attach via netlink.** Rejected. Multi-file reference is deferred to the infra refactor candidate; single-file eBPF attach requires either the BPF program embedded as a byte array in the kernel module (unusual / confusing) or splitting into userspace loader + BPF program (multi-file). Stick to pure kernel C modules.
- **Include IP/TCP/UDP packet construction (skb_put + ip_hdr).** Rejected. Constructing packets from scratch inside a kernel module is niche; most production kernel modules inspect or filter packets rather than generate them. Skips to a lower-frequency failure mode.
- **Promote TC 005 (notifier) from medium to hard.** Rejected. The register/unregister pattern is shared with Zephyr listeners and Linux device models — LLMs handle it reasonably well. Medium is the honest tier.
- **Combine TC 003 + TC 004 into a single "netlink" TC.** Rejected. The discriminator is "LLM selects the right netlink variant for the declared design" — merging hides that. Kernel-protocol netlink (003) vs generic netlink (004) have distinct register/unregister APIs; an LLM that conflates them fails one TC cleanly, demonstrating the discriminator.

### Affected files

**New TC directories (30 files):**
- `cases/embedded-linux/networking-kernel-{001..005}/` — each with 6 files (metadata.yaml, prompt.md, src/main.c placeholder, reference/main.c, checks/{static,behavior,negatives}.py).

**Modified source:**
- `src/embedeval/check_utils.py` — 4 helpers appended under a new "Linux networking-kernel helpers (Phase C-2)" section, after the OTA helpers block:
  1. `has_nf_hook_ops_struct(code) -> bool`
  2. `has_nf_register_call(code) -> bool`
  3. `has_netlink_kernel_api(code) -> list[str]`
  4. `has_genl_family_struct(code) -> bool`
- `tests/test_check_utils_networking_kernel.py` — NEW; 12+ tests across 4 helpers.

**Modified manifests / docs:**
- `cases/SDK_LAYOUT.yaml` — 5 new rows (`networking-kernel-001..005`, `sdk: embedded-linux`).
- `docs/METHODOLOGY.md` — auto-refreshed (TC count 262 → 267).
- `README.md` — auto-refreshed (test + case badges).
- `docs/BENCHMARK-networking-kernel-phase-c.md` — NEW baseline delta report (Phase 5).
- `plans/PLAN-linux-networking-kernel-phase-c.md` — this file.

**NOT touched (explicit non-goals):**
- `src/embedeval/models.py` — no enum change.
- `src/embedeval/{reporter,scorer,evaluator,runner,cli}.py` — all iterate dynamically; no change.
- `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` — v1.7 trailer sync deferred to a follow-up PLAN.
- Existing 262 TC directories — 0 edits; `case_git_hash` preserved.
- Docker image — no additions (kernel modules compile-check is out of scope for v1).

## Implementation phases

### Phase 1: Shared helpers + unit tests

- [x] Add 4 helpers to `src/embedeval/check_utils.py` under a new "Linux networking-kernel helpers (Phase C-2)" section.
- [x] Add `tests/test_check_utils_networking_kernel.py` — 16 tests (4 per helper: happy + false-positive trap + API-variant + edge case).
- [x] Quality gates: `ruff format --check src/ tests/`, `ruff check src/ tests/`, `mypy src/`, `pytest tests/test_check_utils_networking_kernel.py` — green.

### Phase 2: TC authoring (5 TCs in factor-coverage order)

- [x] **networking-kernel-001 (netfilter hook + softirq context)** — hardest; authors D5/E1/F5 discipline first.
- [x] **networking-kernel-002 (sk_buff lifecycle)** — builds on 001's skb handling.
- [x] **networking-kernel-003 (netlink kernel socket)** — introduces netlink headers + `netlink_kernel_cfg`.
- [x] **networking-kernel-004 (generic netlink family)** — second netlink pattern; pins `struct genl_family` surface.
- [x] **networking-kernel-005 (netdevice notifier)** — smallest; pure register/unregister discipline.
- [x] For each TC: metadata + prompt + reference + static.py + behavior.py + negatives.py; verify reference 100% pass + oracle trigger.

### Phase 3: SDK layout + docs sync + integration checks

- [x] `cases/SDK_LAYOUT.yaml` — appended 5 `networking-kernel-00*: sdk: embedded-linux` rows.
- [x] `scripts/sync_docs.py` — 262 → 267 TC, 24 categories, negatives 73 → 78 TCs, mutations 584 → 649 (+65 = 5 × 13).
- [x] `embedeval validate --cases cases/` — 219 public TCs pass.
- [x] Implicit-prompt grep: FORBIDDEN returns empty on the 5 new prompt.md files.
- [x] Vendor-namespace grep: `qcells` appearances are only inside the `family_name_is_neutral_not_qcells` check pattern itself (intentional anti-pattern detector), not in TC content.

### Phase 4: Quality gates + oracle verification

- [x] `ruff format --check src/`, `ruff check src/`, `mypy src/`, `pytest tests/` — all green (1406 passed, 4 skipped).
- [x] `scripts/verify_negatives_oracle.py --category networking` — 6 networking TCs PASS, 7 SKIP; 0 FAIL. All 5 new TCs PASS.
- [x] Reference 100% pass for each new TC verified via ad-hoc snippet.
- [x] Oracle mutation reliability: no regex hardcodes reference variable names; no single-letter anchors; all 65 mutations trigger their `must_fail` targets.

### Phase 5: Baseline benchmark (delta)

- [ ] **Deferred — user-executable.** No `ANTHROPIC_API_KEY` in session env; subscription `claude -p` route would recursively spawn from inside an executing Claude Code session. Run commands + expected-discrimination hypothesis shipped in `docs/BENCHMARK-networking-kernel-phase-c.md`; populate numbers after out-of-session run.
- [x] Update `memory/MEMORY.md` — TC count bumped to 267 with Phase C-2 completion note.

## Testing strategy

- **Unit tests (`tests/test_check_utils_networking_kernel.py`):** 4 helpers × ≥3 cases = ≥12 tests. Pin each false-positive trap:
  - `has_nf_hook_ops_struct` must match both `struct nf_hook_ops ops = { ... };` and `static struct nf_hook_ops ops[] = { ... };` — array form is more common.
  - `has_nf_register_call` must accept both `nf_register_net_hooks` (plural, 3-arg, new) AND `nf_register_net_hook` (singular, deprecated on 5.15 but still present).
  - `has_netlink_kernel_api` must not false-positive on `netlink_rcv` / `netlink_broadcast` (also valid netlink APIs but not kernel-endpoint-creation).
  - `has_genl_family_struct` must match even when `.ops = ...` is on a separate line from the struct opening brace (common formatting).
- **Reference self-check:** every reference passes 100% of its own static + behavior checks via ad-hoc snippet per TC (pattern from Phase A/B/C-1).
- **Oracle verification:** `scripts/verify_negatives_oracle.py --category networking` — 5 new TCs × 12 mutations = 60 mutations trigger their must_fail targets.
- **Implicit-prompt guard:** grep patterns from Phase 3 applied pre-commit.
- **Quality gates:** all four green before any commit.
- **Doc sync:** after Phase 3, diff METHODOLOGY.md + README.md to confirm exact changes (TC count bump, no category-list shift).
- **Mutation regex robustness:** every mutation reviewed against the Phase C-1 review findings — no reference-variable-name hardcoding, no reference-specific literal values, no lazy regex terminating on nested braces. Where section-scoped mutations are needed, use brace-counting or bounded-region walkers (same pattern as `_strip_key_from_section` from `ota-rauc-002`).

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| 5.15 API variant ambiguity — both `nf_register_net_hook` (singular, legacy) and `nf_register_net_hooks` (plural, preferred) work on 5.15. Helper must accept either; prompt must not force a single form. | Med | Helper `has_nf_register_call` matches both. Prompts state "register the hook with the kernel" without naming the function; reference uses the plural form but the check accepts either. Unit test exercises both variants. |
| Netlink protocol number collision — `NETLINK_USERSOCK` (2) is public, `NETLINK_GENERIC` (16) is reserved for genl, custom numbers ≥ 24 are fair game. Reference must use a number that doesn't conflict with stock kernel families. | Low | Reference uses protocol 31 (highest defined number is `NETLINK_GENERIC`=16; anything ≥ 24 is safe on 5.15). Documented in TC 003 metadata + reference comment. |
| `struct genl_family` layout changed between 5.6 and 5.15 — `.ops` + `.n_ops` replaced older embedded arrays around 4.10. Reference must use 5.15 form only. | Med | Reference + checks target the 5.15 form (`.ops` pointer + `.n_ops` count + `.maxattr`). Helper rejects deprecated `genl_register_family_with_ops` (it was removed in 4.10). `deprecated_genl_register_family_with_ops` check + must_fail target documents the boundary. |
| Kernel module can't be compile-checked in current Docker image (no kernel headers) → `l1_skip: true` for all 5 TCs. Reference correctness relies on static + behavior + negatives only. | Med | Accepted per PLAN non-goals. Reference matches `~/EDGE/sources` linux-imx 5.15 kernel module idioms verified by eye against 3+ known-good open-source drivers (e.g., `net/netfilter/nf_conntrack_*`, `net/netlink/genetlink.c`). Do NOT copy code from user BSP. |
| Phase C-1 review finding (oracle-robustness against reference reordering) recurs — brittle regex that only mutates the reference-specific form. | High | Every mutation reviewed pre-commit for the Phase C-1 findings classes: (a) no regex anchoring on reference field ordering; (b) no hex-value / literal-value hardcoding; (c) no lazy regex terminating on nested braces. Use the Phase C-1 `_strip_key_from_section` pattern where section-scoped mutation is needed. Helper functions (when needed per TC) live in the TC's `negatives.py` not the shared check_utils (to keep scope small). |
| `softirq context` discipline checks may be over-aggressive — `printk` is actually softirq-safe (ratelimited), but `pr_info` / `dev_info` chain into printk. Don't flag printk as forbidden. | Med | `hook_fn_has_softirq_safe_body` check explicitly whitelists printk family; flags only `msleep`, `schedule_timeout`, `kmalloc(GFP_KERNEL)`, `down_interruptible`, `mutex_lock_interruptible`. Document whitelist in check docstring. |
| Implicit-prompt drift — netfilter struct member names (`.hooknum`, `.priority`, `.pf`) feel naturally like grammar surface but could reasonably be derived by the LLM from the header. | Low | Treat struct member names as grammar surface (per Phase A/B policy). Prompt MAY mention `hooknum` / `priority` / `pf` in the context of declaring the struct — these are directive-surface analogues. Function-call APIs (`nf_register_net_hooks`) stay forbidden. |
| `genl_family` name collision — if the TC's chosen family name matches a real in-tree family, a real kernel would return -EEXIST at registration. | Low | Use `embedeval_netlink_ex` (48-char limit is 16 — keep under). Grep against `Documentation/netlink/specs/*.yaml` in linux-imx 5.15 to verify no collision. Neutral, no vendor prefix. |
| Netdevice notifier callback receives `struct netdev_notifier_info *` wrapper (introduced 3.11) — NOT `struct net_device *` directly. Legacy code uses `netdev_notifier_info_to_dev()` on 5.15. | Med | Reference uses `netdev_notifier_info_to_dev(ptr)` helper. `callback_gets_net_device_from_ptr` check accepts either form (direct cast from `void *` to `struct net_device *` was the pre-3.11 form; LLMs often write the legacy form). Document the accepted variants in check docstring. |
| Mutation oracle coverage gap for TC 002 — skb_clone returning NULL is a runtime failure, hard to trigger via static mutation. | Low | Focus mutations on the presence/absence of the NULL check, the GFP_ATOMIC flag, and the consume_skb vs kfree_skb distinction. These are static-checkable. Runtime skb_clone failure is out of scope for static evaluation. |
| Benchmark cost: 5 TCs × 2 models × n=3 ≈ 30 calls × ~600 tokens ≈ \$3–5. | Low | n=1 sanity first; proceed to n=3 if discriminating. Log cost in `docs/BENCHMARK-networking-kernel-phase-c.md`. |
| FAILURE-FACTORS v1.6 trailers don't know about new `networking-kernel-*` check names; they'll show as "unknown" in context-diagnose rollups. | Low | Accepted per PLAN non-goals. Follow-up `linux-tc-phase-c-wrapup` PLAN will bump v1.7 covering Phase C-1 + C-2 accumulated check names in one pass. Same cadence as v1.6 commit `959de3d`. |

## Review checklist (verify before /execute)

- [ ] Scope correct: 5 TCs, 4 helpers, 1 new test module, 0 enum changes, 0 runner/evaluator edits, 0 existing-TC edits.
- [ ] Factor-coverage delta documented: D4/D5/D6 (softirq context strengthen), E1/E2/E3 (netfilter/netlink/notifier error paths), F5 (kernel networking headers). No new factor cells.
- [ ] Every prompt passes the implicit-prompt grep (FORBIDDEN empty; grammar surface documented).
- [ ] Every TC has a ≥12-entry mutation oracle with `factor_id` tags.
- [ ] Shared helpers live in `check_utils.py` (not inlined per TC) and have ≥3 unit tests each.
- [ ] `scoped_contains` called with `scope='code_only'` or explicit scope in every new behavior.py (no default-scope landmines).
- [ ] `SDK_LAYOUT.yaml` updated; `sync_docs.py` runs clean.
- [ ] Existing 262 TC dirs untouched (`git diff --stat cases/` restricted to `networking-kernel-*`).
- [ ] All four quality gates green.
- [ ] `verify_negatives_oracle.py --category networking` green on 5 new TCs.
- [ ] Additive-only — no reporter/scorer/evaluator logic change; no `case_git_hash` churn on the existing 262 TCs.
- [ ] Mutation regex robustness: all mutations use order-independent section walkers OR bounded-region string walkers; no reference-specific field ordering assumed; no hex-value / literal-value hardcoding.
- [ ] Risk table addresses 5.15 API variants, netlink protocol collision, struct-layout drift, softirq whitelist, netdevice notifier info variant.
- [ ] CLAUDE.md corrections applied throughout (scoped_contains scope, vendor-namespace neutrality, implicit-prompt + grammar-surface exemption, numeric-claim discipline, Phase C-1 mutation-robustness discipline).
- [ ] FAILURE-FACTORS v1.7 trailer sync explicitly deferred — not squeezed into this PLAN.
- [ ] Docker image additions (kernel headers for compile-check) explicitly deferred — `l1_skip: true` ships first.
