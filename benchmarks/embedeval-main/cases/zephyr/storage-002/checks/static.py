"""Static analysis checks for Settings subsystem load/save."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate Settings subsystem code structure."""
    details: list[CheckDetail] = []

    # Check 1: Settings header included
    has_settings_h = scoped_contains(generated_code, 'zephyr/settings/settings.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="settings_header_included",
            passed=has_settings_h,
            expected="zephyr/settings/settings.h included",
            actual="present" if has_settings_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: settings_subsys_init called
    has_init = scoped_contains(generated_code, 'settings_subsys_init', scope='code_only')
    details.append(
        CheckDetail(
            check_name="settings_subsys_init_called",
            passed=has_init,
            expected="settings_subsys_init() called",
            actual="present" if has_init else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: settings_save_one called
    has_save = scoped_contains(generated_code, 'settings_save_one', scope='code_only')
    details.append(
        CheckDetail(
            check_name="settings_save_one_called",
            passed=has_save,
            expected="settings_save_one() called",
            actual="present" if has_save else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: settings_load called
    has_load = scoped_contains(generated_code, 'settings_load', scope='code_only')
    details.append(
        CheckDetail(
            check_name="settings_load_called",
            passed=has_load,
            expected="settings_load() called",
            actual="present" if has_load else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: settings key uses namespace/key path format
    has_key_path = scoped_contains(generated_code, '/', scope='code_only') and (
        scoped_contains(generated_code, '"app/', scope='code_only') or scoped_contains(generated_code, 'settings_save_one', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="settings_key_path_format",
            passed=has_key_path,
            expected="Settings key uses namespace/key path (e.g. 'app/mykey')",
            actual="present" if has_key_path else "missing",
            check_type="exact_match",
        )
    )

    return details
