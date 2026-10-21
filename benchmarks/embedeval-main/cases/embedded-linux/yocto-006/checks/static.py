"""Static analysis checks for Yocto recipe with patch."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate Yocto patch recipe structure."""
    details: list[CheckDetail] = []

    has_patch_in_uri = scoped_contains(generated_code, '.patch', scope='raw') and scoped_contains(generated_code, 'SRC_URI', scope='raw')
    details.append(
        CheckDetail(
            check_name="patch_file_in_src_uri",
            passed=has_patch_in_uri,
            expected=".patch file listed in SRC_URI",
            actual="present" if has_patch_in_uri else "missing (.patch not in SRC_URI)",
            check_type="exact_match",
        )
    )

    has_filesextrapaths = scoped_contains(generated_code, 'FILESEXTRAPATHS', scope='raw')
    details.append(
        CheckDetail(
            check_name="filesextrapaths_set",
            passed=has_filesextrapaths,
            expected="FILESEXTRAPATHS set to locate patch file",
            actual="present" if has_filesextrapaths else "missing",
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

    has_lic_chksum = scoped_contains(generated_code, 'LIC_FILES_CHKSUM', scope='raw')
    details.append(
        CheckDetail(
            check_name="lic_files_chksum_defined",
            passed=has_lic_chksum,
            expected="LIC_FILES_CHKSUM defined",
            actual="present" if has_lic_chksum else "missing",
            check_type="exact_match",
        )
    )

    has_do_install = scoped_contains(generated_code, 'do_install', scope='raw')
    details.append(
        CheckDetail(
            check_name="do_install_defined",
            passed=has_do_install,
            expected="do_install() function defined",
            actual="present" if has_do_install else "missing",
            check_type="exact_match",
        )
    )

    return details
