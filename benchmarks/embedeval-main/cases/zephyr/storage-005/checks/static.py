"""Static analysis checks for NVS wear-leveling awareness."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate NVS wear-leveling code structure."""
    details: list[CheckDetail] = []

    # Check 1: NVS header included
    has_nvs_h = scoped_contains(generated_code, 'zephyr/fs/nvs.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="nvs_header_included",
            passed=has_nvs_h,
            expected="zephyr/fs/nvs.h included",
            actual="present" if has_nvs_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: nvs_mount called
    has_mount = scoped_contains(generated_code, 'nvs_mount', scope='code_only')
    details.append(
        CheckDetail(
            check_name="nvs_mount_called",
            passed=has_mount,
            expected="nvs_mount() called",
            actual="present" if has_mount else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: nvs_calc_free_space called
    has_free_space = scoped_contains(generated_code, 'nvs_calc_free_space', scope='code_only')
    details.append(
        CheckDetail(
            check_name="nvs_calc_free_space_called",
            passed=has_free_space,
            expected="nvs_calc_free_space() called",
            actual="present" if has_free_space else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: nvs_delete called
    has_delete = scoped_contains(generated_code, 'nvs_delete', scope='code_only')
    details.append(
        CheckDetail(
            check_name="nvs_delete_called",
            passed=has_delete,
            expected="nvs_delete() called to remove old entries",
            actual="present" if has_delete else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: ENOSPC referenced
    has_enospc = scoped_contains(generated_code, 'ENOSPC', scope='code_only')
    details.append(
        CheckDetail(
            check_name="enospc_handled",
            passed=has_enospc,
            expected="ENOSPC error code referenced for storage-full handling",
            actual="present" if has_enospc else "missing",
            check_type="exact_match",
        )
    )

    return details
