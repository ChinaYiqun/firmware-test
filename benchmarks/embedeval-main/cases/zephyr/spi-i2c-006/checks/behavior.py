"""Behavioral checks for I2C clock stretching timeout handling."""

from embedeval.models import CheckDetail
from embedeval.check_utils import check_no_cross_platform_apis, has_output_call
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate I2C clock stretching behavioral properties and domain invariants."""
    details: list[CheckDetail] = []

    # Check 1: Error handling on timeout (negative return value checked)
    has_error_check = (
        scoped_contains(generated_code, '< 0', scope='code_only')
        or scoped_contains(generated_code, '!= 0', scope='code_only')
        or scoped_contains(generated_code, 'ret ==', scope='code_only')
        or scoped_contains(generated_code, 'ETIMEDOUT', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="timeout_error_handled",
            passed=has_error_check,
            expected="Return value from i2c_read checked for error/timeout",
            actual="present" if has_error_check else "return value not checked",
            check_type="constraint",
        )
    )

    # Check 2: Not using K_FOREVER for timeout (dangerous with clock stretching)
    has_k_forever = scoped_contains(generated_code, 'K_FOREVER', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_k_forever_timeout",
            passed=not has_k_forever,
            expected="Timeout must not be K_FOREVER — can hang bus with clock stretching",
            actual="safe" if not has_k_forever else "K_FOREVER used — dangerous for clock stretching devices",
            check_type="constraint",
        )
    )

    # Check 3: Finite timeout mechanism present (K_MSEC or similar)
    has_finite_timeout = (
        scoped_contains(generated_code, 'K_MSEC', scope='code_only')
        or scoped_contains(generated_code, 'K_SECONDS', scope='code_only')
        or scoped_contains(generated_code, 'TIMEOUT', scope='code_only')
        or "timeout" in generated_code.lower()
    )
    details.append(
        CheckDetail(
            check_name="finite_timeout_used",
            passed=has_finite_timeout,
            expected="Finite timeout (K_MSEC, K_SECONDS, or named timeout) used",
            actual="present" if has_finite_timeout else "missing timeout mechanism",
            check_type="constraint",
        )
    )

    # Check 4: Sensor address 0x48 referenced
    has_sensor_addr = scoped_contains(generated_code, '0x48', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_address_0x48",
            passed=has_sensor_addr,
            expected="Sensor I2C address 0x48 referenced",
            actual="present" if has_sensor_addr else "missing or wrong address",
            check_type="exact_match",
        )
    )

    # Check 5: Error message printed on failure
    has_error_print = (
        has_output_call(generated_code)
        and ("error" in generated_code.lower() or "fail" in generated_code.lower()
             or "timeout" in generated_code.lower())
    )
    details.append(
        CheckDetail(
            check_name="error_message_printed",
            passed=has_error_print,
            expected="Error message printed on I2C failure or timeout",
            actual="present" if has_error_print else "missing error output",
            check_type="constraint",
        )
    )

    # Check: No cross-platform API contamination
    cross_plat = check_no_cross_platform_apis(generated_code, skip_platforms=["Linux_Userspace"])
    details.append(CheckDetail(
        check_name="no_cross_platform_apis",
        passed=len(cross_plat) == 0,
        expected="No FreeRTOS/Arduino/STM32_HAL/POSIX APIs",
        actual="clean" if not cross_plat else f"found: {[a for a, _ in cross_plat]}",
        check_type="constraint",
    ))

    return details
