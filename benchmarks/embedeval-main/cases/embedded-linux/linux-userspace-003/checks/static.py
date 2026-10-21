"""Static checks for linux-userspace-003 (systemd service unit)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for tok, name in [
        ("[Unit]", "unit_section_header"),
        ("[Service]", "service_section_header"),
        ("[Install]", "install_section_header"),
        ("Description=", "description_present"),
        ("ExecStart=", "exec_start_present"),
        ("Type=", "type_directive_present"),
        ("WatchdogSec=", "watchdogsec_directive_present"),
        ("Restart=", "restart_directive_present"),
        ("WantedBy=", "wantedby_present"),
    ]:
        p = scoped_contains(generated_code, tok, scope="raw")
        details.append(
            CheckDetail(
                check_name=name,
                passed=p,
                expected=f"{tok} directive",
                actual="present" if p else "missing",
                check_type="exact_match",
            )
        )
    return details
