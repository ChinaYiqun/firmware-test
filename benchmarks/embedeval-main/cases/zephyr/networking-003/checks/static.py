"""Static analysis checks for TCP client with connection retry."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate TCP retry client code structure."""
    details: list[CheckDetail] = []

    has_socket_h = scoped_contains(generated_code, 'zephyr/net/socket.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="socket_header",
            passed=has_socket_h,
            expected="zephyr/net/socket.h included",
            actual="present" if has_socket_h else "missing",
            check_type="exact_match",
        )
    )

    has_errno_h = scoped_contains(generated_code, 'errno.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="errno_header",
            passed=has_errno_h,
            expected="errno.h included",
            actual="present" if has_errno_h else "missing",
            check_type="exact_match",
        )
    )

    has_sock_stream = scoped_contains(generated_code, 'SOCK_STREAM', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sock_stream_used",
            passed=has_sock_stream,
            expected="SOCK_STREAM used for TCP socket",
            actual="present" if has_sock_stream else "missing",
            check_type="exact_match",
        )
    )

    has_connect = scoped_contains(generated_code, 'zsock_connect', scope='code_only')
    details.append(
        CheckDetail(
            check_name="zsock_connect_called",
            passed=has_connect,
            expected="zsock_connect() called",
            actual="present" if has_connect else "missing",
            check_type="exact_match",
        )
    )

    has_max_retries = scoped_contains(generated_code, 'MAX_RETRIES', scope='code_only') or scoped_contains(generated_code, 'max_retries', scope='code_only') or scoped_contains(generated_code, '3', scope='code_only')
    details.append(
        CheckDetail(
            check_name="max_retries_defined",
            passed=has_max_retries,
            expected="MAX_RETRIES or equivalent constant defined",
            actual="present" if has_max_retries else "missing",
            check_type="exact_match",
        )
    )

    has_sleep = scoped_contains(generated_code, 'k_sleep', scope='code_only')
    details.append(
        CheckDetail(
            check_name="backoff_sleep",
            passed=has_sleep,
            expected="k_sleep() used for backoff delay between retries",
            actual="present" if has_sleep else "missing",
            check_type="exact_match",
        )
    )

    has_close = scoped_contains(generated_code, 'zsock_close', scope='code_only')
    details.append(
        CheckDetail(
            check_name="zsock_close_called",
            passed=has_close,
            expected="zsock_close() called",
            actual="present" if has_close else "missing",
            check_type="exact_match",
        )
    )

    return details
