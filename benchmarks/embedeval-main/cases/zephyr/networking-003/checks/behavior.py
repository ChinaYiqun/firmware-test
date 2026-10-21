"""Behavioral checks for TCP client with connection retry."""

import re

from embedeval.models import CheckDetail
from embedeval.check_utils import check_no_cross_platform_apis
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate TCP retry behavioral properties."""
    details: list[CheckDetail] = []

    # Check 1: Retry loop exists (for or while loop with connect inside)
    has_loop = (
        (scoped_contains(generated_code, 'for', scope='code_only') or scoped_contains(generated_code, 'while', scope='code_only'))
        and scoped_contains(generated_code, 'zsock_connect', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="retry_loop_present",
            passed=has_loop,
            expected="Loop containing zsock_connect() for retry logic",
            actual="present" if has_loop else "missing — no retry loop",
            check_type="constraint",
        )
    )

    # Check 2: Bounded retry (not infinite) — MAX_RETRIES or numeric bound
    has_bound = (
        scoped_contains(generated_code, 'MAX_RETRIES', scope='code_only')
        or scoped_contains(generated_code, 'max_retries', scope='code_only')
        or scoped_contains(generated_code, '<= 3', scope='code_only')
        or scoped_contains(generated_code, '< 3', scope='code_only')
        or scoped_contains(generated_code, '<= MAX', scope='code_only')
        or scoped_contains(generated_code, 'attempt <', scope='code_only')
        or scoped_contains(generated_code, 'retries <', scope='code_only')
        or scoped_contains(generated_code, 'retry <', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="bounded_retry",
            passed=has_bound,
            expected="Retry limited by MAX_RETRIES or numeric bound (not infinite)",
            actual="present" if has_bound else "missing — may be infinite retry",
            check_type="constraint",
        )
    )

    # Check 3: Exponential backoff (delay doubles: *2 or <<1 or 2* pattern)
    has_backoff = (
        scoped_contains(generated_code, 'delay *= 2', scope='code_only')
        or scoped_contains(generated_code, 'delay = delay * 2', scope='code_only')
        or scoped_contains(generated_code, 'delay << 1', scope='code_only')
        or scoped_contains(generated_code, 'delay * 2', scope='code_only')
        or "backoff" in generated_code.lower()
    )
    details.append(
        CheckDetail(
            check_name="exponential_backoff",
            passed=has_backoff,
            expected="Exponential backoff: delay doubles each retry",
            actual="present" if has_backoff else "missing — no exponential growth",
            check_type="constraint",
        )
    )

    # Check 4: k_sleep used for delay (not busy-wait)
    has_sleep = scoped_contains(generated_code, 'k_sleep', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sleep_between_retries",
            passed=has_sleep,
            expected="k_sleep() used for delay between retries",
            actual="present" if has_sleep else "missing — no sleep/delay between retries",
            check_type="exact_match",
        )
    )

    # Check 5: TCP socket type (SOCK_STREAM not SOCK_DGRAM)
    has_stream = scoped_contains(generated_code, 'SOCK_STREAM', scope='code_only')
    has_dgram = scoped_contains(generated_code, 'SOCK_DGRAM', scope='code_only')
    details.append(
        CheckDetail(
            check_name="tcp_socket_type",
            passed=has_stream and not has_dgram,
            expected="SOCK_STREAM for TCP (not SOCK_DGRAM)",
            actual=f"SOCK_STREAM={has_stream}, SOCK_DGRAM={has_dgram}",
            check_type="constraint",
        )
    )

    # Check 6: Connect return value checked
    has_connect_check = scoped_contains(generated_code, 'zsock_connect', scope='code_only') and (
        scoped_contains(generated_code, '== 0', scope='code_only') or scoped_contains(generated_code, '< 0', scope='code_only') or scoped_contains(generated_code, '!= 0', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="connect_return_checked",
            passed=has_connect_check,
            expected="zsock_connect() return value checked",
            actual="present" if has_connect_check else "missing — return value ignored",
            check_type="constraint",
        )
    )

    # Check 7: Socket cleanup present (close after all retries fail, or recreate per retry)
    has_close_in_retry = bool(re.search(
        r'(zsock_close|close)\s*\([^)]*\).*zsock_connect',
        generated_code,
        re.DOTALL,
    )) or bool(re.search(
        r'zsock_connect.*?(zsock_close|close)\s*\([^)]*\).*zsock_socket',
        generated_code,
        re.DOTALL,
    ))
    # Also accept: socket closed on final failure (cleanup path)
    has_close_on_fail = bool(re.search(
        r'zsock_close|close\s*\(\s*sock', generated_code
    ))
    details.append(
        CheckDetail(
            check_name="socket_cleanup_on_failure",
            passed=has_close_in_retry or has_close_on_fail,
            expected="Socket closed on failure path (recreate per retry or cleanup after all retries fail)",
            actual="present" if (has_close_in_retry or has_close_on_fail) else "missing — socket leaked on failure",
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
