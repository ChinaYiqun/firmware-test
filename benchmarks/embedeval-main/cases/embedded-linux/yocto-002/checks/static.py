"""Static analysis checks for Yocto CMake recipe."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate CMake BitBake recipe structure."""
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

    has_inherit_cmake = scoped_contains(generated_code, 'inherit cmake', scope='raw')
    details.append(
        CheckDetail(
            check_name="inherit_cmake",
            passed=has_inherit_cmake,
            expected="inherit cmake present",
            actual="present" if has_inherit_cmake else "missing",
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

    has_srcrev = scoped_contains(generated_code, 'SRCREV', scope='raw')
    details.append(
        CheckDetail(
            check_name="srcrev_defined",
            passed=has_srcrev,
            expected="SRCREV defined for git fetch",
            actual="present" if has_srcrev else "missing",
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
