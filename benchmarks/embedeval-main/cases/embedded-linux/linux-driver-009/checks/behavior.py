"""Behavioral checks for linux-driver-009 (GFP flag context awareness).

Validates that allocations pick the correct GFP flag for their context:
  - hardirq handler MUST use GFP_ATOMIC (GFP_KERNEL may sleep → BUG)
  - probe() MUST use GFP_KERNEL (GFP_ATOMIC is wasteful, uses reserved pool)
"""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_function_body,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    sleepable_calls_in_atomic_ctx,
    strip_comments,
    strip_string_literals,
)
from embedeval.models import CheckDetail


def _find_isr_body(code: str) -> str:
    stripped = strip_comments(code)
    m = re.search(r"irqreturn_t\s+(\w+)\s*\([^)]*\)\s*\{", stripped)
    if not m:
        return ""
    return extract_function_body(stripped, m.group(1)) or ""


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)
    # Strip string literals too so a token appearing inside pr_err("use
    # GFP_KERNEL") doesn't false-positive identifier checks.
    isr_body = strip_string_literals(_find_isr_body(generated_code))
    init_body = strip_string_literals(extract_module_init_body(generated_code) or "")
    exit_body = extract_module_exit_body(generated_code) or ""

    # 1. ISR allocates with GFP_ATOMIC, or via a memory-cache allocator
    # with GFP_ATOMIC. Accept kmalloc / kzalloc / kmem_cache_alloc —
    # kmem_cache_alloc(pool, GFP_ATOMIC) is an equally valid pattern.
    isr_allocates = (
        has_api_call(isr_body, "kmalloc")
        or has_api_call(isr_body, "kzalloc")
        or has_api_call(isr_body, "kmem_cache_alloc")
    )
    isr_uses_gfp_atomic = isr_allocates and "GFP_ATOMIC" in isr_body
    details.append(
        CheckDetail(
            check_name="isr_uses_gfp_atomic",
            passed=isr_uses_gfp_atomic,
            expected="ISR allocation uses GFP_ATOMIC",
            actual="present" if isr_uses_gfp_atomic else "missing or wrong flag",
            check_type="constraint",
        )
    )

    # 2. ISR MUST NOT use GFP_KERNEL (may sleep).
    isr_uses_gfp_kernel = "GFP_KERNEL" in isr_body
    details.append(
        CheckDetail(
            check_name="isr_no_gfp_kernel",
            passed=not isr_uses_gfp_kernel,
            expected="ISR does NOT use GFP_KERNEL (sleeping in hardirq = BUG)",
            actual="clean"
            if not isr_uses_gfp_kernel
            else "WRONG: GFP_KERNEL in hardirq handler",
            check_type="constraint",
        )
    )

    # 3. probe uses GFP_KERNEL for state allocation.
    probe_uses_gfp_kernel = "GFP_KERNEL" in init_body
    details.append(
        CheckDetail(
            check_name="probe_uses_gfp_kernel",
            passed=probe_uses_gfp_kernel,
            expected="probe() allocation uses GFP_KERNEL",
            actual="present" if probe_uses_gfp_kernel else "missing",
            check_type="constraint",
        )
    )

    # 4. ISR has no sleepable calls other than the allocation itself
    # (which with GFP_ATOMIC is non-sleeping).
    # sleepable_calls_in_atomic_ctx includes "kmalloc" on its forbidden list
    # because GFP_KERNEL variants sleep; we refine by checking if the call
    # appears with GFP_ATOMIC right next to it.
    isr_sleepable = sleepable_calls_in_atomic_ctx(isr_body)
    # Remove kmalloc from violation list if GFP_ATOMIC is used.
    if "kmalloc" in isr_sleepable and "GFP_ATOMIC" in isr_body:
        isr_sleepable = [s for s in isr_sleepable if s != "kmalloc"]
    details.append(
        CheckDetail(
            check_name="isr_no_sleepable_calls",
            passed=len(isr_sleepable) == 0,
            expected="ISR body has no sleepable calls (except GFP_ATOMIC allocations)",
            actual="clean" if not isr_sleepable else f"forbidden in ISR: {isr_sleepable}",
            check_type="constraint",
        )
    )

    # 5. spinlock_t declared, list_head declared.
    has_spinlock = bool(re.search(r"\bspinlock_t\s+\w+\s*;", stripped))
    has_list_head = bool(re.search(r"\bstruct\s+list_head\s+\w+\s*;", stripped))
    details.append(
        CheckDetail(
            check_name="spinlock_t_declared",
            passed=has_spinlock,
            expected="spinlock_t field in per-device state",
            actual="present" if has_spinlock else "missing",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="list_head_declared",
            passed=has_list_head,
            expected="struct list_head field for the record queue",
            actual="present" if has_list_head else "missing",
            check_type="constraint",
        )
    )

    # 6. INIT_LIST_HEAD + spin_lock_init called in probe.
    inits_list = has_api_call(init_body, "INIT_LIST_HEAD")
    inits_lock = has_api_call(init_body, "spin_lock_init")
    details.append(
        CheckDetail(
            check_name="list_and_lock_initialized_in_probe",
            passed=inits_list and inits_lock,
            expected="probe() calls INIT_LIST_HEAD and spin_lock_init",
            actual=f"list={inits_list}, lock={inits_lock}",
            check_type="constraint",
        )
    )

    # 7a. ISR null-checks the allocation result before dereferencing.
    # Find the LHS of the kmalloc/kzalloc/kmem_cache_alloc assignment
    # (variable name is not hardcoded — may be r, rec, record, entry, p, …)
    # then verify a NULL check exists on that variable inside the ISR.
    alloc_lhs_match = re.search(
        r"(\w+)\s*=\s*(?:kmalloc|kzalloc|kmem_cache_alloc)\s*\(",
        isr_body,
    )
    alloc_lhs = alloc_lhs_match.group(1) if alloc_lhs_match else ""
    isr_null_checks = bool(alloc_lhs) and bool(
        re.search(rf"if\s*\(\s*!\s*{re.escape(alloc_lhs)}\s*\)", isr_body)
        or re.search(rf"if\s*\(\s*{re.escape(alloc_lhs)}\s*==\s*NULL\s*\)", isr_body)
    )
    details.append(
        CheckDetail(
            check_name="isr_null_checks_alloc_result",
            passed=isr_null_checks,
            expected="ISR null-checks the kmalloc result before dereferencing",
            actual="present" if isr_null_checks else "missing — dereferences NULL on OOM",
            check_type="constraint",
        )
    )

    # 7. ISR adds to list (list_add or list_add_tail).
    isr_adds = has_api_call(isr_body, "list_add") or has_api_call(
        isr_body, "list_add_tail"
    )
    details.append(
        CheckDetail(
            check_name="isr_appends_record",
            passed=isr_adds,
            expected="ISR adds record via list_add / list_add_tail",
            actual="present" if isr_adds else "missing",
            check_type="constraint",
        )
    )

    # 8. ISR's list_add is spinlock-protected (spin_lock_irqsave paired).
    isr_locks = has_api_call(isr_body, "spin_lock_irqsave") and has_api_call(
        isr_body, "spin_unlock_irqrestore"
    )
    details.append(
        CheckDetail(
            check_name="isr_uses_spin_lock_irqsave",
            passed=isr_locks,
            expected="ISR guards list with spin_lock_irqsave / _irqrestore",
            actual="present" if isr_locks else "missing",
            check_type="constraint",
        )
    )

    # 9. remove() drains the list (list_for_each_entry_safe + list_del + kfree).
    remove_drains = (
        has_api_call(exit_body, "list_for_each_entry_safe")
        and has_api_call(exit_body, "list_del")
        and has_api_call(exit_body, "kfree")
    )
    details.append(
        CheckDetail(
            check_name="remove_drains_list",
            passed=remove_drains,
            expected="remove() drains queued records with list_for_each_entry_safe + list_del + kfree",
            actual="present" if remove_drains else "missing — record leak on unbind",
            check_type="constraint",
        )
    )

    # 10. remove() calls free_irq before draining (so no new records appear).
    free_irq_pos = exit_body.find("free_irq")
    drain_pos = exit_body.find("list_for_each_entry_safe")
    order_ok = free_irq_pos != -1 and drain_pos != -1 and free_irq_pos < drain_pos
    details.append(
        CheckDetail(
            check_name="free_irq_before_list_drain",
            passed=order_ok,
            expected="remove() calls free_irq before draining the list",
            actual=(
                f"order ok: free_irq@{free_irq_pos} < drain@{drain_pos}"
                if order_ok
                else f"WRONG order: free_irq@{free_irq_pos}, drain@{drain_pos}"
            ),
            check_type="constraint",
        )
    )

    # 11. No cross-platform APIs.
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
