"""Static analysis checks for MCUboot swap type check."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate swap type check code structure."""
    details: list[CheckDetail] = []

    has_mcuboot_h = scoped_contains(generated_code, 'dfu/mcuboot.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mcuboot_header",
            passed=has_mcuboot_h,
            expected="zephyr/dfu/mcuboot.h included",
            actual="present" if has_mcuboot_h else "missing",
            check_type="exact_match",
        )
    )

    has_swap_type_call = scoped_contains(generated_code, 'mcuboot_swap_type', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mcuboot_swap_type_call",
            passed=has_swap_type_call,
            expected="mcuboot_swap_type() called",
            actual="present" if has_swap_type_call else "missing",
            check_type="exact_match",
        )
    )

    has_none = scoped_contains(generated_code, 'BOOT_SWAP_TYPE_NONE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="swap_type_none",
            passed=has_none,
            expected="BOOT_SWAP_TYPE_NONE handled",
            actual="present" if has_none else "missing",
            check_type="exact_match",
        )
    )

    has_test = scoped_contains(generated_code, 'BOOT_SWAP_TYPE_TEST', scope='code_only')
    details.append(
        CheckDetail(
            check_name="swap_type_test",
            passed=has_test,
            expected="BOOT_SWAP_TYPE_TEST handled",
            actual="present" if has_test else "missing",
            check_type="exact_match",
        )
    )

    has_perm = scoped_contains(generated_code, 'BOOT_SWAP_TYPE_PERM', scope='code_only')
    details.append(
        CheckDetail(
            check_name="swap_type_perm",
            passed=has_perm,
            expected="BOOT_SWAP_TYPE_PERM handled",
            actual="present" if has_perm else "missing",
            check_type="exact_match",
        )
    )

    has_revert = scoped_contains(generated_code, 'BOOT_SWAP_TYPE_REVERT', scope='code_only')
    details.append(
        CheckDetail(
            check_name="swap_type_revert",
            passed=has_revert,
            expected="BOOT_SWAP_TYPE_REVERT handled",
            actual="present" if has_revert else "missing",
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
