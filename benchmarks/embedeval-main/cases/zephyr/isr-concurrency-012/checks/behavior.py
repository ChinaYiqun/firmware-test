"""Behavioral checks for isr-concurrency-012."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    # Shared struct declared static (not on stack)
    has_shared_struct = (
        scoped_contains(generated_code, 'static', scope='code_only') and "shared" in generated_code.lower()
    )
    details.append(
        CheckDetail(
            check_name="shared_state_static",
            passed=has_shared_struct,
            expected="Shared state in static storage, not on stack",
            actual="present" if has_shared_struct else "missing",
            check_type="constraint",
        )
    )

    has_worker_thread = (
        scoped_contains(generated_code, 'k_thread_create', scope='code_only') or scoped_contains(generated_code, 'K_THREAD_DEFINE', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="worker_thread_defined",
            passed=has_worker_thread,
            expected="Worker thread via k_thread_create or K_THREAD_DEFINE",
            actual="present" if has_worker_thread else "missing",
            check_type="constraint",
        )
    )

    return details
