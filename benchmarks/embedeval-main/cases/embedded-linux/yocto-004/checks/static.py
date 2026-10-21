"""Static analysis checks for Yocto recipe with DEPENDS and RDEPENDS."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate dependency BitBake recipe structure."""
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

    has_depends = scoped_contains(generated_code, 'DEPENDS', scope='raw')
    details.append(
        CheckDetail(
            check_name="depends_defined",
            passed=has_depends,
            expected="DEPENDS defined for build-time deps",
            actual="present" if has_depends else "missing",
            check_type="exact_match",
        )
    )

    has_rdepends = scoped_contains(generated_code, 'RDEPENDS', scope='raw')
    details.append(
        CheckDetail(
            check_name="rdepends_defined",
            passed=has_rdepends,
            expected="RDEPENDS defined for runtime deps",
            actual="present" if has_rdepends else "missing",
            check_type="exact_match",
        )
    )

    has_do_compile = scoped_contains(generated_code, 'do_compile', scope='raw')
    details.append(
        CheckDetail(
            check_name="do_compile_defined",
            passed=has_do_compile,
            expected="do_compile() function defined",
            actual="present" if has_do_compile else "missing",
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
