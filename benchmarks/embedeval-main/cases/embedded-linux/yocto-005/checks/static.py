"""Static analysis checks for Yocto out-of-tree kernel module recipe."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate kernel module BitBake recipe structure."""
    details: list[CheckDetail] = []

    has_summary = scoped_contains(generated_code, 'SUMMARY', scope='raw')
    details.append(
        CheckDetail(
            check_name="summary_defined",
            passed=has_summary,
            expected="SUMMARY variable defined",
            actual="present" if has_summary else "missing",
            check_type="exact_match",
        )
    )

    has_license = scoped_contains(generated_code, 'LICENSE', scope='raw')
    details.append(
        CheckDetail(
            check_name="license_defined",
            passed=has_license,
            expected="LICENSE variable defined",
            actual="present" if has_license else "missing",
            check_type="exact_match",
        )
    )

    has_inherit_module = scoped_contains(generated_code, 'inherit module', scope='raw')
    details.append(
        CheckDetail(
            check_name="inherit_module",
            passed=has_inherit_module,
            expected="inherit module present",
            actual="present" if has_inherit_module else "missing",
            check_type="exact_match",
        )
    )

    has_src_uri = scoped_contains(generated_code, 'SRC_URI', scope='raw')
    details.append(
        CheckDetail(
            check_name="src_uri_defined",
            passed=has_src_uri,
            expected="SRC_URI defined",
            actual="present" if has_src_uri else "missing",
            check_type="exact_match",
        )
    )

    has_autoload = scoped_contains(generated_code, 'KERNEL_MODULE_AUTOLOAD', scope='raw')
    details.append(
        CheckDetail(
            check_name="kernel_module_autoload",
            passed=has_autoload,
            expected="KERNEL_MODULE_AUTOLOAD set for boot loading",
            actual="present" if has_autoload else "missing",
            check_type="exact_match",
        )
    )

    has_lic_chksum = scoped_contains(generated_code, 'LIC_FILES_CHKSUM', scope='raw')
    details.append(
        CheckDetail(
            check_name="lic_files_chksum",
            passed=has_lic_chksum,
            expected="LIC_FILES_CHKSUM defined",
            actual="present" if has_lic_chksum else "missing",
            check_type="exact_match",
        )
    )

    return details
