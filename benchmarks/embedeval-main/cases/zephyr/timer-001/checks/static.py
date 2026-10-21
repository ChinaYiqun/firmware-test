"""Static analysis checks for periodic kernel timer application."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate timer code structure and required elements."""
    details: list[CheckDetail] = []

    # Check 1: Includes zephyr/kernel.h
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

    # Check 2: Uses K_TIMER_DEFINE or k_timer_init
    has_timer_def = (
        scoped_contains(generated_code, 'K_TIMER_DEFINE', scope='code_only') or scoped_contains(generated_code, 'k_timer_init', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="timer_defined",
            passed=has_timer_def,
            expected="K_TIMER_DEFINE or k_timer_init used",
            actual="present" if has_timer_def else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: Uses k_timer_start
    has_timer_start = scoped_contains(generated_code, 'k_timer_start', scope='code_only')
    details.append(
        CheckDetail(
            check_name="timer_started",
            passed=has_timer_start,
            expected="k_timer_start() called",
            actual="present" if has_timer_start else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: Uses K_MSEC or K_SECONDS for duration
    has_duration = scoped_contains(generated_code, 'K_MSEC', scope='code_only') or scoped_contains(generated_code, 'K_SECONDS', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_duration_macro",
            passed=has_duration,
            expected="K_MSEC or K_SECONDS used for timer duration",
            actual="present" if has_duration else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: Has a counter variable
    has_counter = "counter" in generated_code.lower()
    details.append(
        CheckDetail(
            check_name="counter_variable",
            passed=has_counter,
            expected="Counter variable defined",
            actual="present" if has_counter else "missing",
            check_type="exact_match",
        )
    )

    return details
