"""Negative tests for networking-kernel-001 (netfilter PRE_ROUTING hook).

Reference: cases/embedded-linux/networking-kernel-001/reference/main.c
Checks:    cases/embedded-linux/networking-kernel-001/checks/{static,behavior}.py

Each mutation reviewed for the Phase C-1 robustness classes:
  - No regex anchored on reference field ordering.
  - No regex hardcoding reference-specific variable names (hook fn is
    located by its signature, not by the reference's ``embedeval_nf_hookfn``
    spelling; worker found via INIT_WORK target).
  - Bounded-region walkers, not greedy regex across nested braces.
"""

import re


def _swap_hooknum_to_local_out(code: str) -> str:
    """Move the hook off PRE_ROUTING — the counter loses its
    pre-routing semantics and fails the hooknum check."""
    return code.replace("NF_INET_PRE_ROUTING", "NF_INET_LOCAL_OUT")


def _swap_pf_to_unspec(code: str) -> str:
    """Wrong protocol family — hook never fires for IPv4 packets."""
    return re.sub(
        r"\.pf\s*=\s*(PF_INET|NFPROTO_IPV4)\b",
        ".pf       = NFPROTO_UNSPEC",
        code,
        count=1,
    )


def _drop_nf_register_call(code: str) -> str:
    """Remove the registration call — hook never attaches."""
    return re.sub(
        r"\n[^\n]*nf_register_(net_)?hooks?\s*\([^;]*\);",
        "",
        code,
        count=1,
    )


def _drop_nf_unregister_call(code: str) -> str:
    """Remove exit's unregister call — hook outlives module unload."""
    return re.sub(
        r"\n[^\n]*nf_unregister_(net_)?hooks?\s*\([^;]*\);",
        "",
        code,
        count=1,
    )


def _counter_name(code: str) -> str | None:
    """Extract the atomic counter identifier from its declaration so
    mutations don't hardcode the reference's spelling."""
    m = re.search(r"\batomic_t\s+(\w+)\s*=\s*ATOMIC_INIT\b", code)
    if m:
        return m.group(1)
    m = re.search(r"\batomic_t\s+(\w+)\s*[=;]", code)
    return m.group(1) if m else None


def _inject_before_atomic_inc(code: str, injected_stmt: str) -> str:
    """Prepend ``injected_stmt`` before the first atomic_inc on the
    counter. Works regardless of the counter variable name."""
    name = _counter_name(code)
    if not name:
        return code
    escaped = re.escape(name)
    return re.sub(
        rf"(atomic_inc\s*\(\s*&\s*{escaped}\s*\)\s*;)",
        injected_stmt + r"\n\t\1",
        code,
        count=1,
    )


def _inject_msleep_in_hook(code: str) -> str:
    """Insert msleep in the hook body — illegal from softirq."""
    return _inject_before_atomic_inc(code, "msleep(1);")


def _inject_mutex_lock_in_hook(code: str) -> str:
    """Inject mutex_lock in hook body — sleepable, illegal in softirq."""
    return _inject_before_atomic_inc(code, "mutex_lock(&some_mutex);")


def _inject_gfp_kernel_alloc_in_hook(code: str) -> str:
    """Allocate with GFP_KERNEL from hook — can sleep under memory
    pressure, illegal in softirq."""
    return _inject_before_atomic_inc(code, "kmalloc(16, GFP_KERNEL);")


def _drop_schedule_work(code: str) -> str:
    """Worker never runs — observability lost and unread counter."""
    return re.sub(r"\n[^\n]*schedule_work\s*\([^;]*\);", "", code, count=1)


def _drop_init_work(code: str) -> str:
    """INIT_WORK removed — schedule_work on uninitialised work_struct is UB."""
    return re.sub(r"\n[^\n]*INIT_WORK\s*\([^;]*\);", "", code, count=1)


def _drop_cancel_work_sync(code: str) -> str:
    """cancel_work_sync removed — worker may run after module text unload."""
    return re.sub(r"\n[^\n]*cancel_work_sync\s*\([^;]*\);", "", code, count=1)


def _change_verdict_to_invalid(code: str) -> str:
    """Return a non-verdict integer (1) instead of NF_ACCEPT."""
    return code.replace("return NF_ACCEPT;", "return 1;")


def _change_counter_to_plain_int(code: str) -> str:
    """Race-prone plain-int counter instead of atomic_t.

    Mutates both the declaration and the atomic_inc / atomic_read
    call sites so the transformed program compiles conceptually —
    then the atomic check catches the regression. Variable name is
    extracted from the declaration to avoid hardcoding."""
    name = _counter_name(code)
    if not name:
        return code
    escaped = re.escape(name)
    code = re.sub(
        rf"\bstatic\s+atomic_t\s+{escaped}\s*=\s*ATOMIC_INIT\s*\([^)]*\)\s*;",
        f"static int {name} = 0;",
        code,
        count=1,
    )
    code = re.sub(rf"atomic_inc\s*\(\s*&\s*{escaped}\s*\)", f"{name}++", code)
    code = re.sub(rf"atomic_read\s*\(\s*&\s*{escaped}\s*\)", name, code)
    return code


def _inject_freertos_xsemaphore(code: str) -> str:
    """Cross-RTOS contamination in a Linux kernel module."""
    return _inject_before_atomic_inc(code, "xSemaphoreTake(NULL, 0);")


NEGATIVES = [
    {
        "name": "swap_hooknum_to_local_out",
        "description": "Replace PRE_ROUTING with LOCAL_OUT — hook sits on the wrong chain.",
        "mutation": _swap_hooknum_to_local_out,
        "must_fail": ["nf_hook_ops_has_hooknum_pre_routing"],
        "factor_id": "F5.1",
    },
    {
        "name": "swap_pf_to_unspec",
        "description": "Use NFPROTO_UNSPEC for pf — wrong protocol family binding.",
        "mutation": _swap_pf_to_unspec,
        "must_fail": ["nf_hook_ops_has_pf_inet"],
        "factor_id": "F5.2",
    },
    {
        "name": "drop_nf_register_call",
        "description": "Remove nf_register_net_hook from init — hook never activates.",
        "mutation": _drop_nf_register_call,
        "must_fail": ["nf_register_call_in_init"],
        "factor_id": "E1.1",
    },
    {
        "name": "drop_nf_unregister_call",
        "description": "Remove nf_unregister from exit — dangling hook reference after rmmod.",
        "mutation": _drop_nf_unregister_call,
        "must_fail": ["nf_unregister_call_in_exit"],
        "factor_id": "E1.2",
    },
    {
        "name": "inject_msleep_in_hook",
        "description": "Insert msleep into hook — sleeping in softirq is illegal.",
        "mutation": _inject_msleep_in_hook,
        "must_fail": ["hook_fn_has_softirq_safe_body"],
        "factor_id": "D5.1",
    },
    {
        "name": "inject_mutex_lock_in_hook",
        "description": "Inject mutex_lock in hook — sleepable primitive, illegal in softirq.",
        "mutation": _inject_mutex_lock_in_hook,
        "must_fail": ["hook_fn_has_softirq_safe_body"],
        "factor_id": "D5.2",
    },
    {
        "name": "inject_gfp_kernel_alloc_in_hook",
        "description": "Allocate with GFP_KERNEL from hook — may sleep; softirq cannot.",
        "mutation": _inject_gfp_kernel_alloc_in_hook,
        "must_fail": ["hook_fn_has_softirq_safe_body"],
        "factor_id": "D5.3",
    },
    {
        "name": "drop_schedule_work",
        "description": "Worker never scheduled — observability regression.",
        "mutation": _drop_schedule_work,
        "must_fail": [],  # Structural regression; captured indirectly via worker_logs_count
        "factor_id": "E2.1",
    },
    {
        "name": "drop_init_work",
        "description": "INIT_WORK removed — scheduling on uninitialised descriptor is UB.",
        "mutation": _drop_init_work,
        "must_fail": ["init_work_called_in_init"],
        "factor_id": "E6.2",
    },
    {
        "name": "drop_cancel_work_sync",
        "description": "No cancel_work_sync in exit — worker may run after module unload.",
        "mutation": _drop_cancel_work_sync,
        "must_fail": ["exit_cancels_pending_work"],
        "factor_id": "E3.1",
    },
    {
        "name": "change_verdict_to_invalid",
        "description": "Return raw integer 1 instead of NF_ACCEPT — undefined verdict.",
        "mutation": _change_verdict_to_invalid,
        "must_fail": ["hook_fn_returns_nf_accept_or_drop"],
        "factor_id": "F5.3",
    },
    {
        "name": "change_counter_to_plain_int",
        "description": "Plain int counter — data race across CPUs in the receive path.",
        "mutation": _change_counter_to_plain_int,
        "must_fail": ["hook_counter_is_atomic_t"],
        "factor_id": "D6.1",
    },
    {
        "name": "inject_freertos_xsemaphore",
        "description": "Inject FreeRTOS xSemaphoreTake — cross-RTOS contamination.",
        "mutation": _inject_freertos_xsemaphore,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]
