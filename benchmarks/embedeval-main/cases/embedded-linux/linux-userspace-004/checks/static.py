"""Static checks for linux-userspace-004 (systemd timer + service pair)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for tok, name in [
        ("[Timer]", "timer_section_header"),
        ("[Service]", "service_section_header"),
        ("OnBootSec=", "on_boot_sec_present"),
        ("Persistent=", "persistent_directive_present"),
        ("Unit=", "unit_directive_present"),
        ("Type=", "type_directive_present"),
        ("ExecStart=", "exec_start_present"),
        ("# === vendor-cleanup.service ===", "delimiter_present"),
    ]:
        p = scoped_contains(generated_code, tok, scope="raw")
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
