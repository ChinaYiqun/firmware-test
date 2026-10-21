"""Static analysis checks for OTA image confirmation."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate OTA code structure."""
    details: list[CheckDetail] = []

    has_mcuboot_h = scoped_contains(generated_code, 'dfu/mcuboot.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mcuboot_dfu_header",
            passed=has_mcuboot_h,
            expected="zephyr/dfu/mcuboot.h included",
            actual="present" if has_mcuboot_h else "missing",
            check_type="exact_match",
        )
    )

    has_confirmed = scoped_contains(generated_code, 'boot_is_img_confirmed', scope='code_only')
    details.append(
        CheckDetail(
            check_name="img_confirmed_check",
            passed=has_confirmed,
            expected="boot_is_img_confirmed() called",
            actual="present" if has_confirmed else "missing",
            check_type="exact_match",
        )
    )

    has_write = scoped_contains(generated_code, 'boot_write_img_confirmed', scope='code_only')
    details.append(
        CheckDetail(
            check_name="img_write_confirmed",
            passed=has_write,
            expected="boot_write_img_confirmed() called",
            actual="present" if has_write else "missing",
            check_type="exact_match",
        )
    )

    has_kernel = scoped_contains(generated_code, 'zephyr/kernel.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="kernel_header",
            passed=has_kernel,
            expected="zephyr/kernel.h included",
            actual="present" if has_kernel else "missing",
            check_type="exact_match",
        )
    )

    return details
