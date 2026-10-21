"""Behavioral checks for storage-013."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    has_init = scoped_contains(generated_code, 'settings_subsys_init', scope='code_only')
    details.append(
        CheckDetail(
            check_name="settings_subsys_init",
            passed=has_init,
            expected="settings_subsys_init() called",
            actual="present" if has_init else "missing",
            check_type="exact_match",
        )
    )

    has_handler = (
        scoped_contains(generated_code, 'settings_handler', scope='code_only') or scoped_contains(generated_code, 'settings_register', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="handler_registered",
            passed=has_handler,
            expected="settings_handler registered (struct + settings_register())",
            actual="present" if has_handler else "missing",
            check_type="constraint",
        )
    )

    return details
