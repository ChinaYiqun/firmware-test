"""Static analysis checks for hardware counter precise timing application."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate hardware counter code structure and required elements."""
    details: list[CheckDetail] = []

    # Check 1: Includes zephyr/drivers/counter.h
    has_counter_h = scoped_contains(generated_code, 'zephyr/drivers/counter.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="counter_header_included",
            passed=has_counter_h,
            expected="zephyr/drivers/counter.h included",
            actual="present" if has_counter_h else "missing",
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

    # Check 3: counter_start called before alarm
    has_counter_start = scoped_contains(generated_code, 'counter_start', scope='code_only')
    details.append(
        CheckDetail(
            check_name="counter_start_called",
            passed=has_counter_start,
            expected="counter_start() called before setting alarm",
            actual="present" if has_counter_start else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: counter_get_value used for measurement
    has_get_value = scoped_contains(generated_code, 'counter_get_value', scope='code_only')
    details.append(
        CheckDetail(
            check_name="counter_get_value_used",
            passed=has_get_value,
            expected="counter_get_value() used for timing measurement",
            actual="present" if has_get_value else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: Cross-platform — no FreeRTOS timer APIs
    has_freertos = any(
        p in generated_code for p in ["xTimerCreate", "xTimerStart", "vTimerSetTimerID"]
    )
    details.append(
        CheckDetail(
            check_name="no_freertos_timer_apis",
            passed=not has_freertos,
            expected="No FreeRTOS timer APIs (wrong RTOS)",
            actual="FreeRTOS API found" if has_freertos else "clean",
            check_type="constraint",
        )
    )

    # Check 6: Cross-platform — no Linux timerfd
    has_linux_timer = scoped_contains(generated_code, 'timerfd_create', scope='code_only') or scoped_contains(generated_code, 'timerfd_settime', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_linux_timerfd",
            passed=not has_linux_timer,
            expected="timerfd_create/settime not used (Linux API, wrong platform)",
            actual="Linux timerfd found" if has_linux_timer else "clean",
            check_type="constraint",
        )
    )

    # Check 7: counter_set_channel_alarm used (correct Zephyr counter alarm API)
    has_alarm = scoped_contains(generated_code, 'counter_set_channel_alarm', scope='code_only')
    details.append(
        CheckDetail(
            check_name="counter_set_channel_alarm_called",
            passed=has_alarm,
            expected="counter_set_channel_alarm() called",
            actual="present" if has_alarm else "missing",
            check_type="exact_match",
        )
    )

    return details
