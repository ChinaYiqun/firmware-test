"""Static checks for yocto-012 (PACKAGECONFIG feature flags)."""

from embedeval.check_utils import yocto_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for tok, name in [
        ("SUMMARY", "summary_defined"),
        ("LICENSE", "license_defined"),
        ("LIC_FILES_CHKSUM", "lic_files_chksum_defined"),
        ("SRC_URI", "src_uri_defined"),
        ("inherit autotools", "autotools_inherited"),
        ("PACKAGECONFIG", "packageconfig_directive_present"),
        ("EXTRA_OECONF", "extra_oeconf_present"),
    ]:
        p = yocto_contains(generated_code, tok)
        details.append(
            CheckDetail(
                check_name=name,
                passed=p,
                expected=f"{tok} present",
                actual="present" if p else "missing",
                check_type="exact_match",
            )
        )
    return details
