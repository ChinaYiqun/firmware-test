"""Static analysis checks for watchdog timer application."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate watchdog code structure and required elements."""
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

    # Check 5: Uses wdt_feed
    has_feed = scoped_contains(generated_code, 'wdt_feed', scope='code_only')
    details.append(
        CheckDetail(
            check_name="wdt_feed_called",
            passed=has_feed,
            expected="wdt_feed() called",
            actual="present" if has_feed else "missing",
            check_type="exact_match",
        )
    )

    return details
