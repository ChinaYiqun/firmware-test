"""Static analysis checks for DFU target flash write."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate DFU target code structure."""
    details: list[CheckDetail] = []

    has_dfu_target_h = scoped_contains(generated_code, 'dfu/dfu_target.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dfu_target_header",
            passed=has_dfu_target_h,
            expected="zephyr/dfu/dfu_target.h included",
            actual="present" if has_dfu_target_h else "missing",
            check_type="exact_match",
        )
    )

    has_init = scoped_contains(generated_code, 'dfu_target_init', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dfu_target_init",
            passed=has_init,
            expected="dfu_target_init() called",
            actual="present" if has_init else "missing",
            check_type="exact_match",
        )
    )

    has_write = scoped_contains(generated_code, 'dfu_target_write', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dfu_target_write",
            passed=has_write,
            expected="dfu_target_write() called",
            actual="present" if has_write else "missing",
            check_type="exact_match",
        )
    )

    has_done = scoped_contains(generated_code, 'dfu_target_done', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dfu_target_done",
            passed=has_done,
            expected="dfu_target_done() called",
            actual="present" if has_done else "missing",
            check_type="exact_match",
        )
    )

    has_mcuboot_type = scoped_contains(generated_code, 'DFU_TARGET_IMAGE_TYPE_MCUBOOT', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mcuboot_image_type",
            passed=has_mcuboot_type,
            expected="DFU_TARGET_IMAGE_TYPE_MCUBOOT used",
            actual="present" if has_mcuboot_type else "missing or wrong type",
            check_type="exact_match",
        )
    )

    has_reboot = scoped_contains(generated_code, 'sys_reboot', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sys_reboot_after_dfu",
            passed=has_reboot,
            expected="sys_reboot() called after DFU complete",
            actual="present" if has_reboot else "missing",
            check_type="exact_match",
        )
    )

    return details
