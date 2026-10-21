"""Static analysis checks for Yocto systemd service recipe."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate systemd BitBake recipe structure."""
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

    has_inherit_systemd = scoped_contains(generated_code, 'inherit systemd', scope='raw')
    details.append(
        CheckDetail(
            check_name="inherit_systemd",
            passed=has_inherit_systemd,
            expected="inherit systemd present",
            actual="present" if has_inherit_systemd else "missing",
            check_type="exact_match",
        )
    )

    has_service_var = scoped_contains(generated_code, 'SYSTEMD_SERVICE', scope='raw')
    details.append(
        CheckDetail(
            check_name="systemd_service_var",
            passed=has_service_var,
            expected="SYSTEMD_SERVICE variable defined",
            actual="present" if has_service_var else "missing",
            check_type="exact_match",
        )
    )

    has_service_in_src_uri = scoped_contains(generated_code, '.service', scope='raw') and scoped_contains(generated_code, 'SRC_URI', scope='raw')
    details.append(
        CheckDetail(
            check_name="service_in_src_uri",
            passed=has_service_in_src_uri,
            expected=".service file referenced in SRC_URI",
            actual="present" if has_service_in_src_uri else "missing",
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
