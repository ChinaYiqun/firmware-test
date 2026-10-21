"""Behavioral checks for linux-driver-010 (IRQ-safe locking).

Validates that the ring buffer is protected by ``spin_lock_irqsave`` in
BOTH the IRQ handler AND the read() syscall path, and that paired
``spin_unlock_irqrestore`` calls appear with a flags argument.

Failure modes covered:
  - Plain spin_lock/unlock (no IRQ disable) — race when read() is
    preempted by the IRQ on the same CPU.
  - Mutex-based locking — ILLEGAL in hardirq context.
  - Missing wake_up after enqueue — reader stays blocked forever.
  - Missing wait_event_interruptible — read() busy-spins.
"""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_function_body,
    extract_module_init_body,
    has_api_call,
    sleepable_calls_in_atomic_ctx,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def _find_isr_body(code: str) -> str:
    """Extract the body of a function with return type irqreturn_t."""
    stripped = strip_comments(code)
    m = re.search(r"irqreturn_t\s+(\w+)\s*\([^)]*\)\s*\{", stripped)
    if not m:
        return ""
    body = extract_function_body(stripped, m.group(1))
    return body or ""


def _find_read_body(code: str) -> str:
    """Extract body of .read fop — the function assigned to file_operations.read."""
    stripped = strip_comments(code)
    # Match: .read = name,
    m = re.search(r"\.read\s*=\s*(\w+)\s*[,}]", stripped)
    if m:
        body = extract_function_body(stripped, m.group(1))
        if body:
            return body
    # Fallback: any function returning ssize_t with __user in signature.
    m = re.search(r"ssize_t\s+(\w+)\s*\([^)]*__user[^)]*\)\s*\{", stripped)
    if m:
        body = extract_function_body(stripped, m.group(1))
        if body:
            return body
    return ""


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)
    isr_body = _find_isr_body(generated_code)
    read_body = _find_read_body(generated_code)
    init_body = extract_module_init_body(generated_code) or ""

    # 1. spinlock_t field declared (not mutex).
    has_spinlock_field = bool(re.search(r"\bspinlock_t\s+\w+\s*;", stripped))
    details.append(
        CheckDetail(
            check_name="spinlock_t_declared",
            passed=has_spinlock_field,
            expected="spinlock_t field declared in per-device struct",
            actual="present" if has_spinlock_field else "missing",
            check_type="constraint",
        )
    )

    # 2. No mutex used for shared state between IRQ and process context.
    # (mutex_lock in hardirq is a BUG — kernel will warn.)
    has_mutex = has_api_call(stripped, "mutex_lock") or has_api_call(stripped, "mutex_init")
    details.append(
        CheckDetail(
            check_name="no_mutex_for_irq_shared_state",
            passed=not has_mutex,
            expected="No mutex used; mutex_lock in hardirq context is illegal",
            actual="clean" if not has_mutex else "WRONG: mutex in IRQ-shared path",
            check_type="constraint",
        )
    )

    # 3. ISR uses spin_lock_irqsave + spin_unlock_irqrestore with flags.
    isr_uses_irqsave = has_api_call(isr_body, "spin_lock_irqsave")
    isr_uses_irqrestore = has_api_call(isr_body, "spin_unlock_irqrestore")
    details.append(
        CheckDetail(
            check_name="isr_uses_spin_lock_irqsave",
            passed=isr_uses_irqsave and isr_uses_irqrestore,
            expected="hardirq handler uses spin_lock_irqsave / spin_unlock_irqrestore",
            actual=f"lock_irqsave={isr_uses_irqsave}, unlock_irqrestore={isr_uses_irqrestore}",
            check_type="constraint",
        )
    )

    # 4. read() uses spin_lock_irqsave + spin_unlock_irqrestore, NOT plain spin_lock.
    read_uses_irqsave = has_api_call(read_body, "spin_lock_irqsave")
    read_uses_irqrestore = has_api_call(read_body, "spin_unlock_irqrestore")
    details.append(
        CheckDetail(
            check_name="read_uses_spin_lock_irqsave",
            passed=read_uses_irqsave and read_uses_irqrestore,
            expected="read() uses spin_lock_irqsave — plain spin_lock races on same-CPU IRQ",
            actual=f"lock_irqsave={read_uses_irqsave}, unlock_irqrestore={read_uses_irqrestore}",
            check_type="constraint",
        )
    )

    # 5. read() does NOT use plain spin_lock()/spin_unlock() on the shared state.
    read_has_plain_lock = bool(
        re.search(r"\bspin_lock\s*\(", read_body)
    )
    details.append(
        CheckDetail(
            check_name="read_no_plain_spin_lock",
            passed=not read_has_plain_lock,
            expected="read() must NOT use plain spin_lock() — needs IRQ-disabling variant",
            actual="clean" if not read_has_plain_lock else "WRONG: plain spin_lock on IRQ-shared data",
            check_type="constraint",
        )
    )

    # 6. ISR body contains no sleepable calls (copy_to_user, msleep, mutex_lock,
    # kmalloc, etc.). sleepable_calls_in_atomic_ctx exists for exactly this.
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

    # 7. wake_up_interruptible (or wake_up) called in ISR after enqueue.
    isr_wakes = has_api_call(isr_body, "wake_up_interruptible") or has_api_call(
        isr_body, "wake_up"
    )
    details.append(
        CheckDetail(
            check_name="isr_wakes_readers",
            passed=isr_wakes,
            expected="hardirq handler wakes waiters after enqueue",
            actual="present" if isr_wakes else "missing — reader will block forever",
            check_type="constraint",
        )
    )

    # 8. read() uses wait_event_interruptible (or similar blocking helper).
    read_waits = has_api_call(read_body, "wait_event_interruptible") or has_api_call(
        read_body, "wait_event"
    )
    details.append(
        CheckDetail(
            check_name="read_uses_wait_event",
            passed=read_waits,
            expected="read() blocks via wait_event_interruptible",
            actual="present" if read_waits else "missing — read() would busy-spin",
            check_type="constraint",
        )
    )

    # 9. spin_lock_init called in probe to initialize the lock.
    probe_inits_lock = has_api_call(init_body, "spin_lock_init") or has_api_call(
        stripped, "DEFINE_SPINLOCK"
    )
    details.append(
        CheckDetail(
            check_name="spin_lock_init_called",
            passed=probe_inits_lock,
            expected="spin_lock_init(&lock) called in probe (or DEFINE_SPINLOCK used)",
            actual="present" if probe_inits_lock else "missing",
            check_type="constraint",
        )
    )

    # 10. init_waitqueue_head called in probe.
    probe_inits_wq = has_api_call(init_body, "init_waitqueue_head") or scoped_contains(
        generated_code, "DECLARE_WAIT_QUEUE_HEAD", scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="waitqueue_initialized",
            passed=probe_inits_wq,
            expected="init_waitqueue_head() called in probe",
            actual="present" if probe_inits_wq else "missing — wake_up on uninit wq is UB",
            check_type="constraint",
        )
    )

    # 11. copy_to_user used in read() (not outside of it, which would be wrong
    # context — but at minimum it must be present).
    read_has_copy = has_api_call(read_body, "copy_to_user")
    details.append(
        CheckDetail(
            check_name="read_uses_copy_to_user",
            passed=read_has_copy,
            expected="read() uses copy_to_user to transfer byte",
            actual="present" if read_has_copy else "missing",
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
