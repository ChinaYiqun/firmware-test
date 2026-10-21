"""Static analysis checks for watchdog-fed-by-timer cascaded safety application."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate cascaded safety code structure and required elements."""
    details: list[CheckDetail] = []

    # Check 1: Includes zephyr/drivers/watchdog.h
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

    # Check 2: Includes zephyr/kernel.h
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

    # Check 3: Uses wdt_install_timeout
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

    # Check 4: Uses wdt_setup
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

    # Check 5: wdt_feed called in timer callback (not main loop)
    has_wdt_feed = scoped_contains(generated_code, 'wdt_feed', scope='code_only')
    details.append(
        CheckDetail(
            check_name="wdt_feed_called",
            passed=has_wdt_feed,
            expected="wdt_feed() called (in timer callback)",
            actual="present" if has_wdt_feed else "missing",
            check_type="exact_match",
        )
    )

    # Check 6: k_timer used (not a bare thread with k_sleep for feeding)
    has_k_timer = scoped_contains(generated_code, 'k_timer', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_k_timer_for_wdt_feed",
            passed=has_k_timer,
            expected="k_timer used to feed WDT periodically",
            actual="present" if has_k_timer else "missing",
            check_type="exact_match",
        )
    )

    return details
