"""Static analysis checks for UART async API with DMA application."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate UART async code structure and required elements."""
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

    # Check 3: Uses uart_callback_set (async API, not polling)
    has_callback_set = scoped_contains(generated_code, 'uart_callback_set', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_uart_callback_set",
            passed=has_callback_set,
            expected="uart_callback_set() used (async API)",
            actual="present" if has_callback_set else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: Uses uart_tx (async transmit)
    has_uart_tx = scoped_contains(generated_code, 'uart_tx', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_uart_tx",
            passed=has_uart_tx,
            expected="uart_tx() used for async transmit",
            actual="present" if has_uart_tx else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: Uses uart_rx_enable
    has_rx_enable = scoped_contains(generated_code, 'uart_rx_enable', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_uart_rx_enable",
            passed=has_rx_enable,
            expected="uart_rx_enable() called to enable async RX",
            actual="present" if has_rx_enable else "missing",
            check_type="exact_match",
        )
    )

    # Check 6: Hallucination — uart_read() and uart_write() do not exist in Zephyr
    has_fake_read = scoped_contains(generated_code, 'uart_read(', scope='code_only')
    has_fake_write = scoped_contains(generated_code, 'uart_write(', scope='code_only')
    has_hallucination = has_fake_read or has_fake_write
    details.append(
        CheckDetail(
            check_name="no_uart_read_write_hallucination",
            passed=not has_hallucination,
            expected="uart_read()/uart_write() not used (not Zephyr APIs)",
            actual="hallucinated API found" if has_hallucination else "clean",
            check_type="constraint",
        )
    )

    # Check 7: No polling API (uart_poll_in/out should not be used in async context)
    has_polling = scoped_contains(generated_code, 'uart_poll_in', scope='code_only') or scoped_contains(generated_code, 'uart_poll_out', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_polling_uart_api",
            passed=not has_polling,
            expected="uart_poll_in/poll_out not used (async API required)",
            actual="polling API found" if has_polling else "clean",
            check_type="constraint",
        )
    )

    return details
