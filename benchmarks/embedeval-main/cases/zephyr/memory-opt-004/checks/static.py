"""Static analysis checks for Zephyr thread stack analyzer."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate thread analyzer code structure."""
    details: list[CheckDetail] = []

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

    has_analyzer_h = scoped_contains(generated_code, 'thread_analyzer.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="thread_analyzer_header",
            passed=has_analyzer_h,
            expected="thread_analyzer.h included",
            actual="present" if has_analyzer_h else "missing",
            check_type="exact_match",
        )
    )

    # Intentional raw scope: the check expects CONFIG_THREAD_ANALYZER
    # to appear in a prj.conf-style comment block (see expected= below).
    # code_only would strip it out.
    has_config_comment = scoped_contains(generated_code, 'CONFIG_THREAD_ANALYZER', scope='raw')
    details.append(
        CheckDetail(
            check_name="thread_analyzer_config",
            passed=has_config_comment,
            expected="CONFIG_THREAD_ANALYZER referenced (in comment or prj.conf)",
            actual="present" if has_config_comment else "missing",
            check_type="exact_match",
        )
    )

    has_thread_stack = scoped_contains(generated_code, 'K_THREAD_STACK_DEFINE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="thread_stack_defined",
            passed=has_thread_stack,
            expected="K_THREAD_STACK_DEFINE for worker thread",
            actual="present" if has_thread_stack else "missing",
            check_type="exact_match",
        )
    )

    has_thread_create = scoped_contains(generated_code, 'k_thread_create', scope='code_only')
    details.append(
        CheckDetail(
            check_name="thread_created",
            passed=has_thread_create,
            expected="k_thread_create() called",
            actual="present" if has_thread_create else "missing",
            check_type="exact_match",
        )
    )

    has_analyzer_print = scoped_contains(generated_code, 'thread_analyzer_print', scope='code_only')
    details.append(
        CheckDetail(
            check_name="thread_analyzer_print_called",
            passed=has_analyzer_print,
            expected="thread_analyzer_print() called",
            actual="present" if has_analyzer_print else "missing",
            check_type="exact_match",
        )
    )

    return details
