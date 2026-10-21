"""Static analysis checks for multi-thread watchdog monitoring application."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate multi-thread WDT code structure and required elements."""
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

    # Check 2: Includes zephyr/sys/atomic.h
    has_atomic_h = scoped_contains(generated_code, 'zephyr/sys/atomic.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="atomic_header_included",
            passed=has_atomic_h,
            expected="zephyr/sys/atomic.h included",
            actual="present" if has_atomic_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: Uses atomic_t for health flags (not volatile int)
    has_atomic_t = scoped_contains(generated_code, 'atomic_t', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_atomic_t_for_flags",
            passed=has_atomic_t,
            expected="atomic_t used for health flags",
            actual="present" if has_atomic_t else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: atomic_set used to set flags
    has_atomic_set = scoped_contains(generated_code, 'atomic_set', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_atomic_set",
            passed=has_atomic_set,
            expected="atomic_set() used to set health flags",
            actual="present" if has_atomic_set else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: atomic_clear or atomic_set to 0 used to clear flags after check
    has_atomic_clear = scoped_contains(generated_code, 'atomic_clear', scope='code_only') or (
        scoped_contains(generated_code, 'atomic_set', scope='code_only') and scoped_contains(generated_code, ', 0)', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="flags_cleared_after_check",
            passed=has_atomic_clear,
            expected="atomic_clear() or atomic_set(..., 0) used to reset flags",
            actual="present" if has_atomic_clear else "missing",
            check_type="exact_match",
        )
    )

    # Check 6: wdt_install_timeout and wdt_setup called
    has_install = scoped_contains(generated_code, 'wdt_install_timeout', scope='code_only')
    has_setup = scoped_contains(generated_code, 'wdt_setup', scope='code_only')
    details.append(
        CheckDetail(
            check_name="wdt_configured",
            passed=has_install and has_setup,
            expected="wdt_install_timeout() and wdt_setup() both called",
            actual=f"install={has_install}, setup={has_setup}",
            check_type="exact_match",
        )
    )

    return details
