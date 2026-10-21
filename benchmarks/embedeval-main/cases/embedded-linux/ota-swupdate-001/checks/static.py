"""Static checks for ota-swupdate-001 (SWUpdate minimal triple).

Scoped as ``raw`` throughout — libconfig text is NOT C; stripping C-style
comments or string literals would break ``#`` directives and quoted RHS.
"""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for tok, name in [
        ("software", "software_keyword_present"),
        ("version", "version_keyword_present"),
        ("description", "description_keyword_present"),
        ("hardware-compatibility", "hardware_compatibility_keyword_present"),
        ("images", "images_keyword_present"),
        ("filename", "filename_keyword_present"),
        ("device", "device_keyword_present"),
        ("sha256", "sha256_keyword_present"),
    ]:
        p = scoped_contains(generated_code, tok, scope="raw")
        details.append(
            CheckDetail(
                check_name=name,
                passed=p,
                expected=f"{tok} keyword present",
                actual="present" if p else "missing",
                check_type="exact_match",
            )
        )
    return details
