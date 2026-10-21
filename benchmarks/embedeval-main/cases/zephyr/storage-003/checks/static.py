"""Static analysis checks for LittleFS file read/write."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate LittleFS code structure."""
    details: list[CheckDetail] = []

    # Check 1: LittleFS header included
    has_littlefs_h = scoped_contains(generated_code, 'zephyr/fs/littlefs.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="littlefs_header_included",
            passed=has_littlefs_h,
            expected="zephyr/fs/littlefs.h included",
            actual="present" if has_littlefs_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: fs.h included
    has_fs_h = scoped_contains(generated_code, 'zephyr/fs/fs.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="fs_header_included",
            passed=has_fs_h,
            expected="zephyr/fs/fs.h included",
            actual="present" if has_fs_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: fs_mount called
    has_mount = scoped_contains(generated_code, 'fs_mount', scope='code_only')
    details.append(
        CheckDetail(
            check_name="fs_mount_called",
            passed=has_mount,
            expected="fs_mount() called",
            actual="present" if has_mount else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: FS_O_CREATE flag used
    has_create = scoped_contains(generated_code, 'FS_O_CREATE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="fs_o_create_flag",
            passed=has_create,
            expected="FS_O_CREATE flag used in fs_open()",
            actual="present" if has_create else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: fs_close called
    has_close = scoped_contains(generated_code, 'fs_close', scope='code_only')
    details.append(
        CheckDetail(
            check_name="fs_close_called",
            passed=has_close,
            expected="fs_close() called after file operations",
            actual="present" if has_close else "missing",
            check_type="exact_match",
        )
    )

    return details
