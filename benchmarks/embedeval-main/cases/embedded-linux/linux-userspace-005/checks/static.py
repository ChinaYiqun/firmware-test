"""Static checks for linux-userspace-005 (udev USB hotplug rule)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for tok, name in [
        ("SUBSYSTEM", "subsystem_directive_present"),
        ("ACTION", "action_directive_present"),
        ("ATTRS{idVendor}", "idvendor_attr_present"),
        ("ATTRS{idProduct}", "idproduct_attr_present"),
        ("TAG", "tag_directive_present"),
        ("SYSTEMD_WANTS", "systemd_wants_env_present"),
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
