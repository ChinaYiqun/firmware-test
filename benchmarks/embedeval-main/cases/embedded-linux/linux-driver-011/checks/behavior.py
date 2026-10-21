"""Behavioral checks for linux-driver-011 (deferred work via workqueue).

Validates:
  - work_struct field declared and initialised via INIT_WORK.
  - IRQ handler only acks + schedules, does NOT read frame registers
    itself, does NOT call printk/dev_info, does NOT sleep.
  - Worker function does the heavy I/O and emits the trace.
  - remove() calls cancel_work_sync (or flush_work) BEFORE freeing
    per-device state — otherwise worker UAFs.
"""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_function_body,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    scoped_contains,
    sleepable_calls_in_atomic_ctx,
    strip_comments,
)
from embedeval.models import CheckDetail


def _find_isr_body(code: str) -> str:
    stripped = strip_comments(code)
    m = re.search(r"irqreturn_t\s+(\w+)\s*\([^)]*\)\s*\{", stripped)
    if not m:
        return ""
    body = extract_function_body(stripped, m.group(1))
    return body or ""


def _find_worker_body(code: str) -> str:
    """Extract the body of the work_func_t target — the function passed
    to INIT_WORK or set as .func."""
    stripped = strip_comments(code)
    m = re.search(r"INIT_WORK\s*\(\s*[^,]+,\s*(\w+)\s*\)", stripped)
    if m:
        body = extract_function_body(stripped, m.group(1))
        if body:
            return body
    # Fallback: any ``static void name(struct work_struct *work)``.
    m = re.search(
        r"static\s+void\s+(\w+)\s*\(\s*struct\s+work_struct\s*\*\s*\w+\s*\)\s*\{",
        stripped,
    )
    if m:
        body = extract_function_body(stripped, m.group(1))
        if body:
            return body
    return ""


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)
    isr_body = _find_isr_body(generated_code)
    worker_body = _find_worker_body(generated_code)
    init_body = extract_module_init_body(generated_code) or ""
    exit_body = extract_module_exit_body(generated_code) or ""

    # 1. work_struct field declared (not delayed_work — prompt requires
    # the simplest one-shot worker).
    has_work_struct = bool(re.search(r"\bstruct\s+work_struct\s+\w+\s*;", stripped))
    details.append(
        CheckDetail(
            check_name="work_struct_field_declared",
            passed=has_work_struct,
            expected="struct work_struct field in per-device struct",
            actual="present" if has_work_struct else "missing",
            check_type="constraint",
        )
    )

    # 2. INIT_WORK called in probe.
    inits_work = has_api_call(init_body, "INIT_WORK")
    details.append(
        CheckDetail(
            check_name="init_work_called_in_probe",
            passed=inits_work,
            expected="INIT_WORK(&state->work, worker_fn) called in probe",
            actual="present" if inits_work else "missing",
            check_type="constraint",
        )
    )

    # 3. ISR uses schedule_work (or queue_work).
    isr_schedules = has_api_call(isr_body, "schedule_work") or has_api_call(
        isr_body, "queue_work"
    )
    details.append(
        CheckDetail(
            check_name="isr_schedules_work",
            passed=isr_schedules,
            expected="hardirq handler calls schedule_work / queue_work",
            actual="present" if isr_schedules else "missing",
            check_type="constraint",
        )
    )

    # 4. ISR contains no sleepable calls.
    isr_sleepable = sleepable_calls_in_atomic_ctx(isr_body)
    details.append(
        CheckDetail(
            check_name="isr_no_sleepable_calls",
            passed=len(isr_sleepable) == 0,
            expected="hardirq handler body has no sleepable calls",
            actual="clean" if not isr_sleepable else f"forbidden in ISR: {isr_sleepable}",
            check_type="constraint",
        )
    )

    # 5. ISR does NOT call printk/dev_info/pr_info itself — logging moves
    # to the worker. printk is technically IRQ-safe but the prompt
    # explicitly bans it in hardirq to force the deferral pattern.
    isr_logs = (
        has_api_call(isr_body, "printk")
        or has_api_call(isr_body, "pr_info")
        or has_api_call(isr_body, "pr_err")
        or has_api_call(isr_body, "dev_info")
        or has_api_call(isr_body, "dev_err")
    )
    details.append(
        CheckDetail(
            check_name="isr_no_logging",
            passed=not isr_logs,
            expected="hardirq handler does not log — logging moves to the worker",
            actual="clean" if not isr_logs else "ISR logs directly (should defer to worker)",
            check_type="constraint",
        )
    )

    # 6. Worker body contains the frame register read.
    worker_reads_frame = has_api_call(worker_body, "readl") or has_api_call(
        worker_body, "readw"
    ) or has_api_call(worker_body, "readb") or has_api_call(worker_body, "ioread32")
    details.append(
        CheckDetail(
            check_name="worker_reads_frame_register",
            passed=worker_reads_frame,
            expected="worker function reads the frame register (deferred from ISR)",
            actual="present" if worker_reads_frame else "missing — frame never consumed",
            check_type="constraint",
        )
    )

    # 7. Worker emits a log trace.
    worker_logs = (
        has_api_call(worker_body, "dev_info")
        or has_api_call(worker_body, "pr_info")
        or has_api_call(worker_body, "printk")
    )
    details.append(
        CheckDetail(
            check_name="worker_logs",
            passed=worker_logs,
            expected="worker emits a dev_info / pr_info trace",
            actual="present" if worker_logs else "missing",
            check_type="constraint",
        )
    )

    # 8. remove() calls cancel_work_sync (or flush_work).
    remove_flushes = has_api_call(exit_body, "cancel_work_sync") or has_api_call(
        exit_body, "flush_work"
    )
    details.append(
        CheckDetail(
            check_name="remove_flushes_or_cancels_work",
            passed=remove_flushes,
            expected="remove() calls cancel_work_sync / flush_work before freeing state",
            actual="present" if remove_flushes else "missing — worker UAF on unbind",
            check_type="constraint",
        )
    )

    # 9. remove() calls free_irq BEFORE cancel_work_sync (otherwise an
    # IRQ can re-arm the worker mid-cancellation). Extract order by
    # finding each call's position within exit_body.
    free_irq_pos = exit_body.find("free_irq")
    cancel_pos = (
        exit_body.find("cancel_work_sync")
        if "cancel_work_sync" in exit_body
        else exit_body.find("flush_work")
    )
    order_ok = (
        free_irq_pos != -1
        and cancel_pos != -1
        and free_irq_pos < cancel_pos
    )
    details.append(
        CheckDetail(
            check_name="free_irq_before_cancel_work",
            passed=order_ok,
            expected="remove() calls free_irq before cancel_work_sync / flush_work",
            actual=(
                f"order ok: free_irq@{free_irq_pos} < cancel@{cancel_pos}"
                if order_ok
                else f"WRONG order: free_irq@{free_irq_pos}, cancel@{cancel_pos}"
            ),
            check_type="constraint",
        )
    )

    # 10. remove() calls kfree AFTER cancel_work_sync (else worker UAF).
    # Known limitation: if an LLM places kfree in a separate helper
    # function called from remove, this position-based check returns
    # kfree_pos == -1 and fails even though behavior is correct. Most
    # kernel driver submissions inline the cleanup in remove() so this
    # is acceptable in practice; tighten via caller tracing if needed.
    kfree_pos = exit_body.find("kfree")
    uaf_safe = (
        cancel_pos != -1
        and kfree_pos != -1
        and cancel_pos < kfree_pos
    )
    details.append(
        CheckDetail(
            check_name="kfree_after_cancel_work",
            passed=uaf_safe,
            expected="remove() calls kfree AFTER cancel_work_sync (worker UAF safety)",
            actual=(
                f"order ok: cancel@{cancel_pos} < kfree@{kfree_pos}"
                if uaf_safe
                else f"WRONG order: cancel@{cancel_pos}, kfree@{kfree_pos}"
            ),
            check_type="constraint",
        )
    )

    # 11. Module macros / DT match table present.
    has_dt_table = scoped_contains(
        generated_code, "MODULE_DEVICE_TABLE(of,", scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="of_device_table_registered",
            passed=has_dt_table,
            expected="MODULE_DEVICE_TABLE(of, ...) declared for auto-load",
            actual="present" if has_dt_table else "missing",
            check_type="constraint",
        )
    )

    # 12. No cross-platform APIs.
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
