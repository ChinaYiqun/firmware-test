"""Static analysis checks for watchdog with thread health monitoring application."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate watchdog thread health monitoring code structure."""
    details: list[CheckDetail] = []

    # Check 1: Includes watchdog header
    has_wdt_h = scoped_contains(generated_code, 'zephyr/drivers/watchdog.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="watchdog_header_included",
            passed=has_wdt_h,
            expected="zephyr/drivers/watchdog.h included",
            actual="present" if has_wdt_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: Includes kernel header
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

    # Check 3: worker_alive flag is declared volatile (AI failure: non-volatile shared flag)
    has_volatile_flag = scoped_contains(generated_code, 'volatile', scope='code_only') and (
        scoped_contains(generated_code, 'worker_alive', scope='code_only') or "alive" in generated_code.lower()
    )
    details.append(
        CheckDetail(
            check_name="health_flag_is_volatile",
            passed=has_volatile_flag,
            expected="Worker alive flag declared volatile for cross-thread visibility",
            actual="present" if has_volatile_flag else "missing - flag may not be volatile",
            check_type="constraint",
        )
    )

    # Check 4: Uses wdt_install_timeout
    has_install = scoped_contains(generated_code, 'wdt_install_timeout', scope='code_only')
    details.append(
        CheckDetail(
            check_name="wdt_install_timeout_called",
            passed=has_install,
            expected="wdt_install_timeout() called",
            actual="present" if has_install else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: Uses wdt_setup
    has_setup = scoped_contains(generated_code, 'wdt_setup', scope='code_only')
    details.append(
        CheckDetail(
            check_name="wdt_setup_called",
            passed=has_setup,
            expected="wdt_setup() called",
            actual="present" if has_setup else "missing",
            check_type="exact_match",
        )
    )

    # Check 6: Uses worker thread (k_thread_create or K_THREAD_DEFINE)
    has_thread = (
        scoped_contains(generated_code, 'k_thread_create', scope='code_only') or scoped_contains(generated_code, 'K_THREAD_DEFINE', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="worker_thread_created",
            passed=has_thread,
            expected="Worker thread created with k_thread_create or K_THREAD_DEFINE",
            actual="present" if has_thread else "missing",
            check_type="exact_match",
        )
    )

    return details
