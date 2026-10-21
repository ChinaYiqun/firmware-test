"""Static analysis checks for Flash Area erase and write."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate flash area code structure."""
    details: list[CheckDetail] = []

    # Check 1: flash_map header included
    has_flash_map_h = scoped_contains(generated_code, 'zephyr/storage/flash_map.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="flash_map_header_included",
            passed=has_flash_map_h,
            expected="zephyr/storage/flash_map.h included",
            actual="present" if has_flash_map_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: flash_area_open called
    has_open = scoped_contains(generated_code, 'flash_area_open', scope='code_only')
    details.append(
        CheckDetail(
            check_name="flash_area_open_called",
            passed=has_open,
            expected="flash_area_open() called",
            actual="present" if has_open else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: flash_area_erase called
    has_erase = scoped_contains(generated_code, 'flash_area_erase', scope='code_only')
    details.append(
        CheckDetail(
            check_name="flash_area_erase_called",
            passed=has_erase,
            expected="flash_area_erase() called before write",
            actual="present" if has_erase else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: flash_area_write called
    has_write = scoped_contains(generated_code, 'flash_area_write', scope='code_only')
    details.append(
        CheckDetail(
            check_name="flash_area_write_called",
            passed=has_write,
            expected="flash_area_write() called",
            actual="present" if has_write else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: flash_area_close called
    has_close = scoped_contains(generated_code, 'flash_area_close', scope='code_only')
    details.append(
        CheckDetail(
            check_name="flash_area_close_called",
            passed=has_close,
            expected="flash_area_close() called after operations",
            actual="present" if has_close else "missing",
            check_type="exact_match",
        )
    )

    return details
