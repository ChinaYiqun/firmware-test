"""Static analysis checks for UART echo application."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate UART echo code structure and required elements."""
    details: list[CheckDetail] = []

    # Check 1: Includes zephyr/drivers/uart.h
    has_uart_h = scoped_contains(generated_code, 'zephyr/drivers/uart.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uart_header_included",
            passed=has_uart_h,
            expected="zephyr/drivers/uart.h included",
            actual="present" if has_uart_h else "missing",
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

    # Check 3: Gets UART device from devicetree
    has_device_dt = scoped_contains(generated_code, 'DEVICE_DT_GET', scope='code_only') or scoped_contains(generated_code, 'DT_ALIAS', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_devicetree_binding",
            passed=has_device_dt,
            expected="DEVICE_DT_GET or DT_ALIAS used to get UART device",
            actual="present" if has_device_dt else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: Uses uart_poll_in (not printf or other non-UART APIs)
    has_uart_poll_in = scoped_contains(generated_code, 'uart_poll_in', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_uart_poll_in",
            passed=has_uart_poll_in,
            expected="uart_poll_in() called for reading",
            actual="present" if has_uart_poll_in else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: Uses uart_poll_out (not printf)
    has_uart_poll_out = scoped_contains(generated_code, 'uart_poll_out', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_uart_poll_out",
            passed=has_uart_poll_out,
            expected="uart_poll_out() called for writing",
            actual="present" if has_uart_poll_out else "missing",
            check_type="exact_match",
        )
    )

    # Check 6: No use of printf (AI failure pattern: using printf instead of UART API)
    has_printf = scoped_contains(generated_code, 'printf', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_printf_usage",
            passed=not has_printf,
            expected="No printf — uses UART API directly",
            actual="printf found" if has_printf else "no printf",
            check_type="constraint",
        )
    )

    # Check 7: No raw register access
    has_raw_register = any(
        p in generated_code for p in ["volatile uint32_t", "*(uint32_t*)", "MMIO"]
    )
    details.append(
        CheckDetail(
            check_name="no_raw_register_access",
            passed=not has_raw_register,
            expected="Uses UART API, not raw register access",
            actual="raw register found" if has_raw_register else "API only",
            check_type="constraint",
        )
    )

    return details
