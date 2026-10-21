"""Behavioral checks for linux-driver-012 (threaded IRQ primary/thread split).

Validates that request_threaded_irq is used with BOTH a primary and a
thread handler, that the primary returns IRQ_WAKE_THREAD, and that the
thread handler is where msleep (sleepable) lives.
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
)
from embedeval.models import CheckDetail


def _find_isr_functions(code: str) -> list[tuple[str, str]]:
    """Return (name, body) pairs for every function declared as
    ``irqreturn_t name(...)`` in order of appearance."""
    stripped = strip_comments(code)
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"irqreturn_t\s+(\w+)\s*\([^)]*\)\s*\{", stripped):
        name = m.group(1)
        body = extract_function_body(stripped, name)
        if body is not None:
            out.append((name, body))
    return out


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    init_body = extract_module_init_body(generated_code) or ""
    exit_body = extract_module_exit_body(generated_code) or ""
    isr_funcs = _find_isr_functions(generated_code)

    # 1. request_threaded_irq used in probe.
    uses_threaded = has_api_call(init_body, "request_threaded_irq")
    details.append(
        CheckDetail(
            check_name="request_threaded_irq_used",
            passed=uses_threaded,
            expected="probe() uses request_threaded_irq (not request_irq)",
            actual="present" if uses_threaded else "missing",
            check_type="constraint",
        )
    )

    # 2. Two distinct irqreturn_t functions exist (primary + thread).
    has_two_isrs = len(isr_funcs) >= 2
    details.append(
        CheckDetail(
            check_name="two_isr_functions",
            passed=has_two_isrs,
            expected="Both primary and thread IRQ handlers defined",
            actual=f"found {len(isr_funcs)} irqreturn_t functions",
            check_type="constraint",
        )
    )

    # 3. Identify primary vs thread: primary returns IRQ_WAKE_THREAD.
    primary_body = ""
    thread_body = ""
    for name, body in isr_funcs:
        if "IRQ_WAKE_THREAD" in body and not primary_body:
            primary_body = body
        elif not thread_body:
            thread_body = body

    primary_returns_wake = "IRQ_WAKE_THREAD" in primary_body
    details.append(
        CheckDetail(
            check_name="primary_returns_irq_wake_thread",
            passed=primary_returns_wake,
            expected="Primary handler returns IRQ_WAKE_THREAD",
            actual="present" if primary_returns_wake else "missing",
            check_type="constraint",
        )
    )

    # 4. Primary handler has NO sleepable calls.
    primary_sleepable = sleepable_calls_in_atomic_ctx(primary_body)
    details.append(
        CheckDetail(
            check_name="primary_no_sleepable_calls",
            passed=len(primary_sleepable) == 0,
            expected="Primary handler contains no sleepable calls (no msleep, no mutex_lock, no copy_*_user)",
            actual="clean" if not primary_sleepable else f"forbidden in primary: {primary_sleepable}",
            check_type="constraint",
        )
    )

    # 4a. Primary handler does NOT log — logging belongs in the thread.
    primary_logs = (
        has_api_call(primary_body, "dev_info")
        or has_api_call(primary_body, "pr_info")
        or has_api_call(primary_body, "printk")
        or has_api_call(primary_body, "dev_err")
        or has_api_call(primary_body, "pr_err")
    )
    details.append(
        CheckDetail(
            check_name="primary_no_logging",
            passed=not primary_logs,
            expected="Primary handler does NOT log — logging belongs in the thread",
            actual="clean" if not primary_logs else "primary logs directly (defeats deferral)",
            check_type="constraint",
        )
    )

    # 5. Thread handler uses msleep (or similar) — proves it runs in
    # sleepable context.
    thread_sleeps = (
        has_api_call(thread_body, "msleep")
        or has_api_call(thread_body, "usleep_range")
        or has_api_call(thread_body, "msleep_interruptible")
    )
    details.append(
        CheckDetail(
            check_name="thread_handler_sleeps",
            passed=thread_sleeps,
            expected="Thread handler sleeps (msleep / usleep_range) for debounce",
            actual="present" if thread_sleeps else "missing — defeats the purpose of threading",
            check_type="constraint",
        )
    )

    # 6. IRQF_ONESHOT flag passed — required when a thread handler is
    # provided without a primary (or to keep IRQ masked until thread
    # completes).
    has_oneshot = "IRQF_ONESHOT" in init_body
    details.append(
        CheckDetail(
            check_name="irqf_oneshot_flag_used",
            passed=has_oneshot,
            expected="IRQF_ONESHOT flag passed to request_threaded_irq",
            actual="present" if has_oneshot else "missing",
            check_type="constraint",
        )
    )

    # 7. ktime_get used in primary handler for timestamp.
    primary_timestamps = has_api_call(primary_body, "ktime_get") or has_api_call(
        primary_body, "ktime_get_ns"
    )
    details.append(
        CheckDetail(
            check_name="primary_timestamps_event",
            passed=primary_timestamps,
            expected="Primary handler records ktime_get timestamp",
            actual="present" if primary_timestamps else "missing",
            check_type="constraint",
        )
    )

    # 8. Thread handler emits dev_info trace.
    thread_logs = (
        has_api_call(thread_body, "dev_info")
        or has_api_call(thread_body, "pr_info")
    )
    details.append(
        CheckDetail(
            check_name="thread_handler_logs",
            passed=thread_logs,
            expected="Thread handler emits dev_info/pr_info trace",
            actual="present" if thread_logs else "missing",
            check_type="constraint",
        )
    )

    # 9. free_irq called in remove.
    remove_frees = has_api_call(exit_body, "free_irq")
    details.append(
        CheckDetail(
            check_name="remove_frees_irq",
            passed=remove_frees,
            expected="remove() calls free_irq",
            actual="present" if remove_frees else "missing",
            check_type="constraint",
        )
    )

    # 10. Plain request_irq NOT used (ambiguous with threaded variant).
    uses_plain_request_irq = re.search(
        r"\brequest_irq\s*\(", init_body
    ) is not None
    details.append(
        CheckDetail(
            check_name="no_plain_request_irq",
            passed=not uses_plain_request_irq,
            expected="Do NOT use request_irq — use request_threaded_irq",
            actual="clean"
            if not uses_plain_request_irq
            else "plain request_irq found (wrong API for the task)",
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
