"""Static analysis checks for Linux platform driver with Device Tree binding."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate platform driver code structure."""
    details: list[CheckDetail] = []

    has_module_h = scoped_contains(generated_code, 'linux/module.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="module_header",
            passed=has_module_h,
            expected="linux/module.h included",
            actual="present" if has_module_h else "missing",
            check_type="exact_match",
        )
    )

    has_platform_h = scoped_contains(generated_code, 'linux/platform_device.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="platform_device_header",
            passed=has_platform_h,
            expected="linux/platform_device.h included",
            actual="present" if has_platform_h else "missing",
            check_type="exact_match",
        )
    )

    has_license = scoped_contains(generated_code, 'MODULE_LICENSE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="module_license",
            passed=has_license,
            expected="MODULE_LICENSE defined",
            actual="present" if has_license else "missing",
            check_type="exact_match",
        )
    )

    has_of_match = scoped_contains(generated_code, 'of_device_id', scope='code_only')
    details.append(
        CheckDetail(
            check_name="of_device_id_table",
            passed=has_of_match,
            expected="struct of_device_id table defined",
            actual="present" if has_of_match else "missing",
            check_type="exact_match",
        )
    )

    has_compatible = scoped_contains(generated_code, '.compatible', scope='code_only')
    details.append(
        CheckDetail(
            check_name="compatible_string",
            passed=has_compatible,
            expected=".compatible string set in of_device_id",
            actual="present" if has_compatible else "missing",
            check_type="exact_match",
        )
    )

    has_module_device_table = scoped_contains(generated_code, 'MODULE_DEVICE_TABLE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="module_device_table",
            passed=has_module_device_table,
            expected="MODULE_DEVICE_TABLE(of, ...) declared",
            actual="present" if has_module_device_table else "missing",
            check_type="exact_match",
        )
    )

    has_platform_driver = scoped_contains(generated_code, 'platform_driver', scope='code_only')
    details.append(
        CheckDetail(
            check_name="platform_driver_struct",
            passed=has_platform_driver,
            expected="struct platform_driver defined",
            actual="present" if has_platform_driver else "missing",
            check_type="exact_match",
        )
    )

    return details
