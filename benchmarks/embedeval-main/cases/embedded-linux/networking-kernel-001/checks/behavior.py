"""Behavioral checks for networking-kernel-001 (netfilter PRE_ROUTING hook).

Validates:
  - ``struct nf_hook_ops`` declared with hooknum/pf populated.
  - Hook registration happens in init, unregistration in exit.
  - Hook callback stays softirq-safe (no sleep / mutex / GFP_KERNEL /
    copy_*_user), returns NF_ACCEPT or NF_DROP, and defers heavy work.
  - Module uses atomic_t for the packet counter, work_struct for the
    deferral target.
"""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_function_body,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    has_nf_hook_ops_struct,
    has_nf_register_call,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def _find_hook_body(code: str) -> str:
    """Locate the netfilter hook callback body.

    The hook has the signature ``<retty> <name>(void *priv,
    struct sk_buff *skb, const struct nf_hook_state *state)`` where
    ``<retty>`` is one of ``unsigned int`` / ``u32`` / ``__u32`` (all
    equivalent on 5.15 — kernel code commonly uses the short u32 form).
    Extract the first matching function's body regardless of the
    specific name the LLM chose — we never hardcode a reference
    variable name.
    """
    stripped = strip_comments(code)
    m = re.search(
        r"\b(?:unsigned\s+int|u32|__u32)\s+(\w+)\s*\(\s*void\s*\*\s*\w+\s*,"
        r"\s*struct\s+sk_buff\s*\*\s*\w+\s*,"
        r"\s*const\s+struct\s+nf_hook_state\s*\*",
        stripped,
    )
    if not m:
        return ""
    return extract_function_body(stripped, m.group(1)) or ""


def _find_worker_body(code: str) -> str:
    stripped = strip_comments(code)
    m = re.search(r"INIT_WORK\s*\(\s*[^,]+,\s*(\w+)\s*\)", stripped)
    if m:
        body = extract_function_body(stripped, m.group(1))
        if body:
            return body
    m = re.search(
        r"static\s+void\s+(\w+)\s*\(\s*struct\s+work_struct\s*\*\s*\w+\s*\)\s*\{",
        stripped,
    )
    if m:
        return extract_function_body(stripped, m.group(1)) or ""
    return ""


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)
    init_body = extract_module_init_body(generated_code) or ""
    exit_body = extract_module_exit_body(generated_code) or ""
    hook_body = _find_hook_body(generated_code)
    worker_body = _find_worker_body(generated_code)

    # 1. nf_hook_ops struct declared.
    has_struct = has_nf_hook_ops_struct(generated_code)
    details.append(
        CheckDetail(
            check_name="nf_hook_ops_struct_declared",
            passed=has_struct,
            expected="struct nf_hook_ops <name> = { ... }; declared",
            actual="present" if has_struct else "missing",
            check_type="constraint",
        )
    )

    # 2. Struct populates .hooknum with PRE_ROUTING.
    has_pre_routing = bool(
        re.search(
            r"\.hooknum\s*=\s*NF_INET_PRE_ROUTING\b", stripped
        )
    )
    details.append(
        CheckDetail(
            check_name="nf_hook_ops_has_hooknum_pre_routing",
            passed=has_pre_routing,
            expected=".hooknum = NF_INET_PRE_ROUTING",
            actual="present" if has_pre_routing else "missing or wrong chain",
            check_type="constraint",
        )
    )

    # 3. Struct populates .pf with PF_INET or NFPROTO_IPV4.
    has_pf_inet = bool(
        re.search(r"\.pf\s*=\s*(PF_INET|NFPROTO_IPV4)\b", stripped)
    )
    details.append(
        CheckDetail(
            check_name="nf_hook_ops_has_pf_inet",
            passed=has_pf_inet,
            expected=".pf = PF_INET or NFPROTO_IPV4",
            actual="present" if has_pf_inet else "missing or wrong family",
            check_type="constraint",
        )
    )

    # 4. Registration call present in init.
    register_in_init = has_nf_register_call(init_body)
    details.append(
        CheckDetail(
            check_name="nf_register_call_in_init",
            passed=register_in_init,
            expected="nf_register_net_hook(s) invoked from init",
            actual="present" if register_in_init else "missing",
            check_type="constraint",
        )
    )

    # 5. Unregistration in exit. Accept both plural and singular forms.
    unregister_in_exit = bool(
        re.search(r"\bnf_unregister_(net_)?hooks?\s*\(", exit_body)
    )
    details.append(
        CheckDetail(
            check_name="nf_unregister_call_in_exit",
            passed=unregister_in_exit,
            expected="nf_unregister_net_hook(s) invoked from exit",
            actual="present" if unregister_in_exit else "missing",
            check_type="constraint",
        )
    )

    # 6. Hook body is softirq-safe: no msleep / mutex_lock / kmalloc
    # with GFP_KERNEL / copy_*_user. printk / pr_info are allowed
    # (IRQ-safe, rate-limited).
    forbidden_in_softirq: list[str] = []
    for bad in (
        "msleep",
        "usleep_range",
        "mutex_lock",
        "down_interruptible",
        "wait_for_completion",
        "copy_to_user",
        "copy_from_user",
        "schedule_timeout",
    ):
        if has_api_call(hook_body, bad):
            forbidden_in_softirq.append(bad)
    has_gfp_kernel = bool(re.search(r"\bGFP_KERNEL\b", hook_body))
    if has_gfp_kernel:
        forbidden_in_softirq.append("GFP_KERNEL")
    details.append(
        CheckDetail(
            check_name="hook_fn_has_softirq_safe_body",
            passed=len(forbidden_in_softirq) == 0,
            expected="hook body free of sleeping / GFP_KERNEL / user-copy calls",
            actual="clean" if not forbidden_in_softirq else f"forbidden: {forbidden_in_softirq}",
            check_type="constraint",
        )
    )

    # 7. Hook returns a valid verdict.
    returns_verdict = bool(
        re.search(r"\breturn\s+NF_(ACCEPT|DROP|STOLEN|QUEUE|REPEAT)\b", hook_body)
    )
    details.append(
        CheckDetail(
            check_name="hook_fn_returns_nf_accept_or_drop",
            passed=returns_verdict,
            expected="return NF_ACCEPT / NF_DROP / NF_STOLEN from hook",
            actual="present" if returns_verdict else "missing or non-verdict return",
            check_type="constraint",
        )
    )

    # 8. work_struct declared at module scope for deferral.
    has_work_struct = bool(
        re.search(r"\bstruct\s+work_struct\s+\w+\s*;", stripped)
    )
    details.append(
        CheckDetail(
            check_name="work_struct_declared_for_deferral",
            passed=has_work_struct,
            expected="module-scope struct work_struct for deferred logging",
            actual="present" if has_work_struct else "missing",
            check_type="constraint",
        )
    )

    # 9. INIT_WORK called in init.
    init_work_called = has_api_call(init_body, "INIT_WORK")
    details.append(
        CheckDetail(
            check_name="init_work_called_in_init",
            passed=init_work_called,
            expected="INIT_WORK(&stats_work, worker) in init",
            actual="present" if init_work_called else "missing",
            check_type="constraint",
        )
    )

    # 10. Worker emits a log line.
    worker_logs = (
        has_api_call(worker_body, "pr_info")
        or has_api_call(worker_body, "pr_debug")
        or has_api_call(worker_body, "printk")
    )
    details.append(
        CheckDetail(
            check_name="worker_logs_count",
            passed=worker_logs,
            expected="worker emits pr_info / printk of the counter value",
            actual="present" if worker_logs else "missing",
            check_type="constraint",
        )
    )

    # 11. Packet counter uses atomic_t (or atomic64_t).
    has_atomic_counter = bool(
        re.search(r"\batomic(64)?_t\s+\w+", stripped)
    ) or bool(re.search(r"ATOMIC(64)?_INIT\s*\(", stripped))
    details.append(
        CheckDetail(
            check_name="hook_counter_is_atomic_t",
            passed=has_atomic_counter,
            expected="module-scope atomic_t counter (not plain int)",
            actual="present" if has_atomic_counter else "missing",
            check_type="constraint",
        )
    )

    # 12. Exit calls cancel_work_sync (prevents worker UAF after unregister).
    exit_cancels_work = has_api_call(exit_body, "cancel_work_sync") or has_api_call(
        exit_body, "flush_work"
    )
    details.append(
        CheckDetail(
            check_name="exit_cancels_pending_work",
            passed=exit_cancels_work,
            expected="exit calls cancel_work_sync / flush_work after unregister",
            actual="present" if exit_cancels_work else "missing",
            check_type="constraint",
        )
    )

    # 13. No cross-platform APIs.
    cross_plat = check_no_cross_platform_apis(
        generated_code, skip_platforms=["Linux_Userspace", "POSIX"]
    )
    details.append(
        CheckDetail(
            check_name="no_cross_platform_apis",
            passed=len(cross_plat) == 0,
            expected="No FreeRTOS / Zephyr / Arduino / STM32 HAL APIs",
            actual="clean" if not cross_plat else f"found: {[a for a, _ in cross_plat]}",
            check_type="constraint",
        )
    )

    return details
