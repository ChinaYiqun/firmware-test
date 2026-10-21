"""Static checks for yocto-010 (.bbappend with colon overrides)."""

from embedeval.check_utils import yocto_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for tok, name in [
        ("FILESEXTRAPATHS", "filesextrapaths_directive_present"),
        ("SRC_URI", "src_uri_directive_present"),
        ("RDEPENDS", "rdepends_directive_present"),
        ("do_install", "do_install_directive_present"),
    ]:
        p = yocto_contains(generated_code, tok)
        details.append(
            CheckDetail(
                check_name=name,
                passed=p,
                expected=f"{tok} directive present",
                actual="present" if p else "missing",
                check_type="exact_match",
            )
        )
    return details
