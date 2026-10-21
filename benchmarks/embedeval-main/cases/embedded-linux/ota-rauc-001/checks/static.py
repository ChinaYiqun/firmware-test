"""Static checks for ota-rauc-001 (minimal RAUC manifest)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for tok, name in [
        ("[update]", "update_section_header"),
        ("[bundle]", "bundle_section_header"),
        ("compatible=", "compatible_directive_present"),
        ("version=", "version_directive_present"),
        ("format=", "format_directive_present"),
        ("filename=", "filename_directive_present"),
        ("sha256=", "sha256_directive_present"),
        ("size=", "size_directive_present"),
    ]:
        p = scoped_contains(generated_code, tok, scope="raw")
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
