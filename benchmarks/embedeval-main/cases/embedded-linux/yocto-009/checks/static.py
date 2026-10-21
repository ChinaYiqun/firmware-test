"""Static checks for yocto-009 (meta-layer conf/layer.conf)."""

from embedeval.check_utils import yocto_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for tok, name in [
        ("BBPATH", "bbpath_defined"),
        ("BBFILES", "bbfiles_defined"),
        ("BBFILE_COLLECTIONS", "bbfile_collections_defined"),
        ("BBFILE_PATTERN_", "bbfile_pattern_defined"),
        ("BBFILE_PRIORITY_", "bbfile_priority_defined"),
        ("LAYERSERIES_COMPAT_", "layerseries_compat_defined"),
    ]:
        present = yocto_contains(generated_code, tok)
        details.append(
            CheckDetail(
                check_name=name,
                passed=present,
                expected=f"{tok} directive present",
                actual="present" if present else "missing",
                check_type="exact_match",
            )
        )
    return details
