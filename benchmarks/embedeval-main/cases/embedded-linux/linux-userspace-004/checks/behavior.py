"""Behavioral checks for linux-userspace-004 (timer + service pair)."""

import re

from embedeval.check_utils import strip_systemd_comments, systemd_unit_section_has
from embedeval.models import CheckDetail

DELIM = "# === vendor-cleanup.service ==="


def _split_pair(text: str) -> tuple[str, str]:
    """Return (timer_body, service_body) by splitting on DELIM.

    If DELIM is absent, returns (text, "") — downstream checks will
    see the service-unit directives as missing.
    """
    if DELIM not in text:
        return text, ""
    before, _, after = text.partition(DELIM)
    return before, after


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    timer_body, service_body = _split_pair(generated_code)

    # 1. Timer has OnBootSec (any positive duration — prompt says 15min
    # but accept any integer>=1).
    on_boot = systemd_unit_section_has(timer_body, "Timer", "OnBootSec")
    on_boot_ok = bool(on_boot) and bool(re.match(r"^\d+", on_boot.strip()))
    on_boot_15min = bool(on_boot) and re.match(
        r"^15\s*(?:m|min|minutes)\b", on_boot.strip()
    )
    details.append(
        CheckDetail(
            check_name="timer_has_on_boot_sec",
            passed=on_boot_ok,
            expected="OnBootSec set to a positive duration",
            actual=f"OnBootSec={on_boot!r}" if on_boot else "missing",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="on_boot_sec_15min",
            passed=bool(on_boot_15min),
            expected="OnBootSec=15min (per prompt)",
            actual=f"OnBootSec={on_boot!r}" if on_boot else "missing",
            check_type="constraint",
        )
    )

    # 2. Timer has OnUnitActiveSec for periodic re-fire.
    on_active = systemd_unit_section_has(timer_body, "Timer", "OnUnitActiveSec")
    on_active_ok = bool(on_active) and bool(re.match(r"^\d+", on_active.strip()))
    on_active_7d = bool(on_active) and re.match(
        r"^7\s*(?:d|day|days|w|week|weeks)\b|^1\s*(?:w|week|weeks)\b",
        on_active.strip(),
    )
    details.append(
        CheckDetail(
            check_name="timer_has_on_unit_active_sec",
            passed=on_active_ok,
            expected="OnUnitActiveSec set to a positive duration",
            actual=f"OnUnitActiveSec={on_active!r}" if on_active else "missing",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="on_unit_active_sec_7d",
            passed=bool(on_active_7d),
            expected="OnUnitActiveSec=7d (or 1w) per prompt",
            actual=f"OnUnitActiveSec={on_active!r}" if on_active else "missing",
            check_type="constraint",
        )
    )

    # 3. Persistent=true — the drift-free semantic.
    persistent = systemd_unit_section_has(timer_body, "Timer", "Persistent")
    persistent_true = bool(persistent) and persistent.strip().lower() in {
        "true",
        "yes",
        "1",
        "on",
    }
    details.append(
        CheckDetail(
            check_name="persistent_true",
            passed=persistent_true,
            expected="Persistent=true (missed runs catch up after boot)",
            actual=f"Persistent={persistent!r}" if persistent else "missing",
            check_type="constraint",
        )
    )

    # 4. Timer's Unit= points at the paired service.
    unit_ref = systemd_unit_section_has(timer_body, "Timer", "Unit")
    unit_ref_ok = bool(unit_ref) and "vendor-cleanup.service" in unit_ref
    details.append(
        CheckDetail(
            check_name="timer_unit_references_service",
            passed=unit_ref_ok,
            expected="Unit=vendor-cleanup.service",
            actual=f"Unit={unit_ref!r}" if unit_ref else "missing",
            check_type="constraint",
        )
    )

    # 5. Timer [Install] WantedBy=timers.target (so ``systemctl enable``
    # actually links it into the boot path).
    timer_wanted_by = systemd_unit_section_has(timer_body, "Install", "WantedBy")
    details.append(
        CheckDetail(
            check_name="timer_wantedby_timers_target",
            passed=bool(timer_wanted_by) and "timers.target" in timer_wanted_by,
            expected="Timer [Install] WantedBy=timers.target",
            actual=f"WantedBy={timer_wanted_by!r}" if timer_wanted_by else "missing",
            check_type="constraint",
        )
    )

    # 6. Service Type=oneshot.
    svc_type = systemd_unit_section_has(service_body, "Service", "Type")
    details.append(
        CheckDetail(
            check_name="service_type_oneshot",
            passed=svc_type == "oneshot",
            expected="[Service] Type=oneshot (not simple / notify — the task is run-to-completion)",
            actual=f"Type={svc_type!r}" if svc_type else "missing",
            check_type="constraint",
        )
    )

    # 7. Service ExecStart absolute path to cleanup script.
    exec_start = systemd_unit_section_has(service_body, "Service", "ExecStart")
    exec_ok = (
        bool(exec_start)
        and exec_start.lstrip().startswith("/")
        and "vendor-cleanup.sh" in exec_start
    )
    details.append(
        CheckDetail(
            check_name="service_exec_start_points_to_script",
            passed=exec_ok,
            expected="ExecStart=/usr/bin/vendor-cleanup.sh (absolute)",
            actual=f"ExecStart={exec_start!r}" if exec_start else "missing",
            check_type="constraint",
        )
    )

    # 8. Service MUST NOT have an [Install] section — triggered by timer.
    # If stray [Install] appears in service body, the reviewer would
    # accidentally enable the service directly, breaking the timer pairing.
    service_install = bool(re.search(r"^\s*\[Install\]", service_body, re.MULTILINE))
    details.append(
        CheckDetail(
            check_name="service_has_no_install_section",
            passed=not service_install,
            expected="Service has no [Install] section (triggered by timer only)",
            actual="clean" if not service_install else "WRONG: [Install] present",
            check_type="constraint",
        )
    )

    # 9. Both bodies actually present (delimiter split produced non-empty
    # second half).
    both_present = bool(strip_systemd_comments(service_body).strip())
    details.append(
        CheckDetail(
            check_name="both_units_present",
            passed=both_present,
            expected="Both timer and service bodies present (delimiter split)",
            actual="present" if both_present else "service half missing",
            check_type="constraint",
        )
    )

    return details
