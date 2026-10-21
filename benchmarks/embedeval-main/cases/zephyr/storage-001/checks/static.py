"""Static analysis checks for NVS key-value store."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate NVS code structure."""
    details: list[CheckDetail] = []

    # Check 1: NVS header
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

    # Check 3: nvs_write called
    has_write = scoped_contains(generated_code, 'nvs_write', scope='code_only')
    details.append(
        CheckDetail(
            check_name="nvs_write_called",
            passed=has_write,
            expected="nvs_write() called",
            actual="present" if has_write else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: nvs_read called
    has_read = scoped_contains(generated_code, 'nvs_read', scope='code_only')
    details.append(
        CheckDetail(
            check_name="nvs_read_called",
            passed=has_read,
            expected="nvs_read() called",
            actual="present" if has_read else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: struct nvs_fs defined
    has_fs = scoped_contains(generated_code, 'struct nvs_fs', scope='code_only') or scoped_contains(generated_code, 'nvs_fs', scope='code_only')
    details.append(
        CheckDetail(
            check_name="nvs_fs_struct",
            passed=has_fs,
            expected="struct nvs_fs defined",
            actual="present" if has_fs else "missing",
            check_type="exact_match",
        )
    )

    return details
