"""Static checks for boot-uboot-004 (signed FIT)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for tok, name in [
        ("/dts-v1/;", "dts_v1_header"),
        ("images", "images_node_present"),
        ("configurations", "configurations_node_present"),
        ('default = "config-1"', "default_configuration_set"),
        ('type = "kernel"', "kernel_subimage_present"),
    ]:
        p = scoped_contains(generated_code, tok, scope="code_only")
        details.append(
            CheckDetail(
                check_name=name,
                passed=p,
                expected=f"{tok}",
                actual="present" if p else "missing",
                check_type="exact_match",
            )
        )
    return details
