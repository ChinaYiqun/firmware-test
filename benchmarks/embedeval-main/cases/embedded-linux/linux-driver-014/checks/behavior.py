"""Behavioral checks for linux-driver-014 (cooperative kthread)."""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_function_body,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    has_is_err_guard,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def _find_thread_body(code: str) -> str:
    """Extract the kthread body: ``static int name(void *data)`` that
    contains a kthread_should_stop call, or the target of kthread_run."""
    stripped = strip_comments(code)
    # Prefer: the function passed to kthread_run/kthread_create.
    m = re.search(r"kthread_(?:run|create)\s*\(\s*(\w+)\s*,", stripped)
    if m:
        body = extract_function_body(stripped, m.group(1))
        if body:
            return body
    # Fallback: any ``int name(void *...)`` with kthread_should_stop inside.
    for fm in re.finditer(r"int\s+(\w+)\s*\(\s*void\s*\*\s*\w+\s*\)\s*\{", stripped):
        body = extract_function_body(stripped, fm.group(1))
        if body and "kthread_should_stop" in body:
            return body
    return ""


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    init_body = extract_module_init_body(generated_code) or ""
    exit_body = extract_module_exit_body(generated_code) or ""
    thread_body = _find_thread_body(generated_code)
    stripped = strip_comments(generated_code)

    # 1. task_struct field declared.
    has_task_field = bool(
        re.search(r"\bstruct\s+task_struct\s*\*\s*\w+\s*;", stripped)
    )
    details.append(
        CheckDetail(
            check_name="task_struct_field_declared",
            passed=has_task_field,
            expected="struct task_struct *task field in per-device state",
            actual="present" if has_task_field else "missing",
            check_type="constraint",
        )
    )

    # 2. kthread_run used in probe (not kthread_create without wake_up).
    uses_kthread_run = has_api_call(init_body, "kthread_run")
    uses_kthread_create_and_wake = has_api_call(
        init_body, "kthread_create"
    ) and has_api_call(init_body, "wake_up_process")
    kthread_started = uses_kthread_run or uses_kthread_create_and_wake
    details.append(
        CheckDetail(
            check_name="kthread_started_in_probe",
            passed=kthread_started,
            expected="probe() starts the thread via kthread_run or kthread_create + wake_up_process",
            actual=(
                "present (kthread_run)"
                if uses_kthread_run
                else "present (kthread_create+wake_up_process)"
                if uses_kthread_create_and_wake
                else "missing"
            ),
            check_type="constraint",
        )
    )

    # 3. IS_ERR guards the kthread_run / kthread_create return value.
    guarded = has_is_err_guard(init_body, "kthread_run") or has_is_err_guard(
        init_body, "kthread_create"
    )
    details.append(
        CheckDetail(
            check_name="is_err_guards_kthread_start",
            passed=guarded,
            expected="IS_ERR guards kthread_run / kthread_create result",
            actual="present" if guarded else "missing — NULL check on ERR_PTR API",
            check_type="constraint",
        )
    )

    # 4. Thread body checks kthread_should_stop as loop predicate.
    checks_should_stop = has_api_call(thread_body, "kthread_should_stop")
    details.append(
        CheckDetail(
            check_name="thread_checks_should_stop",
            passed=checks_should_stop,
            expected="Thread body's loop predicate is kthread_should_stop",
            actual="present" if checks_should_stop else "missing — kthread_stop would hang forever",
            check_type="constraint",
        )
    )

    # 5. Thread body has a sleep (msleep / usleep / schedule_timeout).
    thread_sleeps = (
        has_api_call(thread_body, "msleep")
        or has_api_call(thread_body, "msleep_interruptible")
        or has_api_call(thread_body, "usleep_range")
        or has_api_call(thread_body, "schedule_timeout")
    )
    details.append(
        CheckDetail(
            check_name="thread_has_sleep",
            passed=thread_sleeps,
            expected="Thread body sleeps between polls (msleep / usleep_range / schedule_timeout)",
            actual="present" if thread_sleeps else "missing — thread would busy-spin at 100% CPU",
            check_type="constraint",
        )
    )

    # 6. Thread body reads the status register.
    thread_reads = (
        has_api_call(thread_body, "readl")
        or has_api_call(thread_body, "readw")
        or has_api_call(thread_body, "readb")
        or has_api_call(thread_body, "ioread32")
    )
    details.append(
        CheckDetail(
            check_name="thread_reads_register",
            passed=thread_reads,
            expected="Thread reads status register (readl / ioread32)",
            actual="present" if thread_reads else "missing",
            check_type="constraint",
        )
    )

    # 7. remove() calls kthread_stop.
    remove_stops = has_api_call(exit_body, "kthread_stop")
    details.append(
        CheckDetail(
            check_name="remove_calls_kthread_stop",
            passed=remove_stops,
            expected="remove() calls kthread_stop to cleanly terminate the thread",
            actual="present" if remove_stops else "missing — thread outlives module",
            check_type="constraint",
        )
    )

    # 8. kthread_stop is called BEFORE kfree / iounmap — otherwise the
    # thread dereferences freed state on its last iteration.
    # Known limitation: helper-function indirection (kfree inside a
    # driver_cleanup() called from remove) makes this position check
    # return -1 and fail correct-but-refactored code. Inline-in-remove
    # is the common idiom; revisit via caller tracing if the TC
    # evolves.
    stop_pos = exit_body.find("kthread_stop")
    kfree_pos = exit_body.find("kfree")
    iounmap_pos = exit_body.find("iounmap")
    uaf_safe = (
        stop_pos != -1
        and (kfree_pos == -1 or stop_pos < kfree_pos)
        and (iounmap_pos == -1 or stop_pos < iounmap_pos)
    )
    details.append(
        CheckDetail(
            check_name="kthread_stop_before_kfree",
            passed=uaf_safe,
            expected="remove() calls kthread_stop before kfree/iounmap (UAF safety)",
            actual=(
                f"order ok: stop@{stop_pos} < kfree@{kfree_pos}, iounmap@{iounmap_pos}"
                if uaf_safe
                else f"WRONG: stop@{stop_pos}, kfree@{kfree_pos}, iounmap@{iounmap_pos}"
            ),
            check_type="constraint",
        )
    )

    # 9. PTR_ERR used to propagate the kthread_run error.
    has_ptr_err = scoped_contains(generated_code, "PTR_ERR(", scope="code_only")
    details.append(
        CheckDetail(
            check_name="ptr_err_propagated",
            passed=has_ptr_err,
            expected="PTR_ERR() propagates kthread_run failure errno",
            actual="present" if has_ptr_err else "missing",
            check_type="constraint",
        )
    )

    # 10. No cross-platform APIs.
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
