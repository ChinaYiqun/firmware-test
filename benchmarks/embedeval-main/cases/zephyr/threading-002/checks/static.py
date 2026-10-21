"""Static analysis checks for mutex-protected shared counter."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate mutex counter code structure and required elements."""
    details: list[CheckDetail] = []

    # Check 1: kernel header
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

    # Check 2: Mutex defined (K_MUTEX_DEFINE or struct k_mutex)
    has_mutex_define = scoped_contains(generated_code, 'K_MUTEX_DEFINE', scope='code_only')
    has_mutex_struct = scoped_contains(generated_code, 'struct k_mutex', scope='code_only')
    has_mutex = has_mutex_define or has_mutex_struct
    details.append(
        CheckDetail(
            check_name="mutex_defined",
            passed=has_mutex,
            expected="K_MUTEX_DEFINE or struct k_mutex declared",
            actual="present" if has_mutex else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: k_mutex_lock called
    has_lock = scoped_contains(generated_code, 'k_mutex_lock', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mutex_lock_called",
            passed=has_lock,
            expected="k_mutex_lock() called",
            actual="present" if has_lock else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: k_mutex_unlock called
    has_unlock = scoped_contains(generated_code, 'k_mutex_unlock', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mutex_unlock_called",
            passed=has_unlock,
            expected="k_mutex_unlock() called",
            actual="present" if has_unlock else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: Shared counter (global variable)
    has_counter = (
        scoped_contains(generated_code, 'uint32_t', scope='code_only')
        or scoped_contains(generated_code, 'int', scope='code_only')
    ) and (
        scoped_contains(generated_code, 'counter', scope='code_only')
        or scoped_contains(generated_code, 'shared', scope='code_only')
        or scoped_contains(generated_code, 'count', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="shared_counter_declared",
            passed=has_counter,
            expected="Shared counter variable declared",
            actual="present" if has_counter else "missing",
            check_type="exact_match",
        )
    )

    # Check 6: Two threads defined
    thread_count = generated_code.count("K_THREAD_DEFINE")
    if thread_count < 2:
        thread_count += generated_code.count("k_thread_create")
    has_two_threads = thread_count >= 2
    details.append(
        CheckDetail(
            check_name="two_threads_defined",
            passed=has_two_threads,
            expected="At least 2 threads defined",
            actual=f"{thread_count} threads found",
            check_type="exact_match",
        )
    )

    return details
