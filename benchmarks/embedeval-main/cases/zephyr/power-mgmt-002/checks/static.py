"""Static analysis checks for simple system sleep."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate sleep code structure and required elements."""
    details: list[CheckDetail] = []

    # Check 1: kernel header
    has_kernel_h = scoped_contains(generated_code, 'zephyr/kernel.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="kernel_header_included",
            passed=has_kernel_h,
            expected="zephyr/kernel.h included",
            actual="present" if has_kernel_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: k_sleep or k_msleep used (not busy-wait)
    has_sleep = scoped_contains(generated_code, 'k_sleep', scope='code_only') or scoped_contains(generated_code, 'k_msleep', scope='code_only')
    details.append(
        CheckDetail(
            check_name="k_sleep_used",
            passed=has_sleep,
            expected="k_sleep() or k_msleep() called for CPU yield",
            actual="present" if has_sleep else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: K_MSEC used with k_sleep (not needed for k_msleep which takes raw int ms)
    has_kmsec = scoped_contains(generated_code, 'K_MSEC', scope='code_only')
    has_kmsleep = scoped_contains(generated_code, 'k_msleep', scope='code_only')
    kmsec_ok = has_kmsec or has_kmsleep
    details.append(
        CheckDetail(
            check_name="k_msec_time_macro",
            passed=kmsec_ok,
            expected="K_MSEC() time macro used (or k_msleep with raw ms)",
            actual="present" if kmsec_ok else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: k_uptime_get called for timestamps
    has_uptime = scoped_contains(generated_code, 'k_uptime_get', scope='code_only')
    details.append(
        CheckDetail(
            check_name="k_uptime_get_used",
            passed=has_uptime,
            expected="k_uptime_get() called for timestamps",
            actual="present" if has_uptime else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: No busy-wait loop (k_busy_wait is forbidden here)
    has_busy_wait = scoped_contains(generated_code, 'k_busy_wait', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_busy_wait",
            passed=not has_busy_wait,
            expected="k_busy_wait() NOT used (must use k_sleep)",
            actual="busy-wait present" if has_busy_wait else "absent",
            check_type="exact_match",
        )
    )

    return details
