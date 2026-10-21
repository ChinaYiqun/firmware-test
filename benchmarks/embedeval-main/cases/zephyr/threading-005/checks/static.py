"""Static analysis checks for custom work queue with delayed submission."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate work queue code structure and required elements."""
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

    # Check 2: Custom stack defined with K_THREAD_STACK_DEFINE
    has_stack = scoped_contains(generated_code, 'K_THREAD_STACK_DEFINE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="thread_stack_defined",
            passed=has_stack,
            expected="K_THREAD_STACK_DEFINE used for work queue stack",
            actual="present" if has_stack else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: k_work_q declared
    has_work_q = scoped_contains(generated_code, 'struct k_work_q', scope='code_only') or scoped_contains(generated_code, 'k_work_q', scope='code_only')
    details.append(
        CheckDetail(
            check_name="work_queue_declared",
            passed=has_work_q,
            expected="struct k_work_q declared for custom queue",
            actual="present" if has_work_q else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: k_work_delayable declared
    has_dwork = scoped_contains(generated_code, 'k_work_delayable', scope='code_only')
    details.append(
        CheckDetail(
            check_name="delayable_work_declared",
            passed=has_dwork,
            expected="struct k_work_delayable declared",
            actual="present" if has_dwork else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: k_work_queue_start called
    has_wq_start = scoped_contains(generated_code, 'k_work_queue_start', scope='code_only')
    details.append(
        CheckDetail(
            check_name="work_queue_started",
            passed=has_wq_start,
            expected="k_work_queue_start() called to initialize queue",
            actual="present" if has_wq_start else "missing",
            check_type="exact_match",
        )
    )

    # Check 6: k_work_schedule_for_queue called (not just k_work_schedule)
    has_schedule_for_queue = scoped_contains(generated_code, 'k_work_schedule_for_queue', scope='code_only')
    details.append(
        CheckDetail(
            check_name="schedule_for_custom_queue",
            passed=has_schedule_for_queue,
            expected="k_work_schedule_for_queue() used (not k_work_schedule)",
            actual="present" if has_schedule_for_queue else "missing",
            check_type="exact_match",
        )
    )

    return details
