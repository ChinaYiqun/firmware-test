"""Negative tests for linux-userspace-004 (systemd timer + service pair)."""

import re


def _drop_persistent(code: str) -> str:
    return re.sub(r"^Persistent=.*\n", "", code, count=1, flags=re.MULTILINE)


def _persistent_false(code: str) -> str:
    return code.replace("Persistent=true", "Persistent=false")


def _drop_on_boot_sec(code: str) -> str:
    return re.sub(r"^OnBootSec=.*\n", "", code, count=1, flags=re.MULTILINE)


def _drop_on_unit_active_sec(code: str) -> str:
    return re.sub(r"^OnUnitActiveSec=.*\n", "", code, count=1, flags=re.MULTILINE)


def _on_boot_wrong_duration(code: str) -> str:
    return code.replace("OnBootSec=15min", "OnBootSec=3min")


def _service_type_simple(code: str) -> str:
    return code.replace("Type=oneshot", "Type=simple")


def _service_type_notify(code: str) -> str:
    return code.replace("Type=oneshot", "Type=notify")


def _timer_unit_nonexistent(code: str) -> str:
    return code.replace("Unit=vendor-cleanup.service", "Unit=nonexistent.service")


def _exec_start_relative(code: str) -> str:
    return code.replace(
        "ExecStart=/usr/bin/vendor-cleanup.sh", "ExecStart=vendor-cleanup.sh"
    )


def _service_adds_install(code: str) -> str:
    return code + "\n[Install]\nWantedBy=multi-user.target\n"


def _drop_delimiter(code: str) -> str:
    return code.replace("# === vendor-cleanup.service ===", "")


def _drop_timer_install_section(code: str) -> str:
    """Drop the [Install] before the delimiter."""
    return re.sub(
        r"\[Install\]\nWantedBy=timers\.target\n",
        "",
        code,
        count=1,
    )


NEGATIVES = [
    {
        "name": "drop_persistent",
        "description": "Remove Persistent= — missed runs are lost on reboot; timer drifts.",
        "mutation": _drop_persistent,
        "must_fail": ["persistent_directive_present", "persistent_true"],
        "factor_id": "B2.1",
    },
    {
        "name": "persistent_false",
        "description": "Persistent=false — explicit negation of drift-free semantic; missed runs skip.",
        "mutation": _persistent_false,
        "must_fail": ["persistent_true"],
        "factor_id": "B2.1",
    },
    {
        "name": "drop_on_boot_sec",
        "description": "Remove OnBootSec — timer fires only on OnUnitActiveSec interval after an external trigger; may never start.",
        "mutation": _drop_on_boot_sec,
        "must_fail": [
            "on_boot_sec_present",
            "timer_has_on_boot_sec",
            "on_boot_sec_15min",
        ],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_on_unit_active_sec",
        "description": "Remove OnUnitActiveSec — timer fires exactly once after boot, never re-fires.",
        "mutation": _drop_on_unit_active_sec,
        "must_fail": ["timer_has_on_unit_active_sec", "on_unit_active_sec_7d"],
        "factor_id": "F6.1",
    },
    {
        "name": "on_boot_wrong_duration",
        "description": "OnBootSec=3min instead of 15min — violates prompt requirement.",
        "mutation": _on_boot_wrong_duration,
        "must_fail": ["on_boot_sec_15min"],
        "factor_id": "B2.2",
    },
    {
        "name": "service_type_simple",
        "description": "Type=simple for a run-to-completion script — systemd considers service active for the lifetime of the script rather than returning to inactive; timer re-fires interact badly.",
        "mutation": _service_type_simple,
        "must_fail": ["service_type_oneshot"],
        "factor_id": "F6.2",
    },
    {
        "name": "service_type_notify",
        "description": "Type=notify for a non-daemon script — systemd waits for sd_notify readiness that never arrives, startup hangs.",
        "mutation": _service_type_notify,
        "must_fail": ["service_type_oneshot"],
        "factor_id": "F6.2",
    },
    {
        "name": "timer_unit_nonexistent",
        "description": "Unit= points at a non-existent service — systemd load-time error.",
        "mutation": _timer_unit_nonexistent,
        "must_fail": ["timer_unit_references_service"],
        "factor_id": "F6.2",
    },
    {
        "name": "exec_start_relative",
        "description": "ExecStart uses relative path — systemd rejects.",
        "mutation": _exec_start_relative,
        "must_fail": ["service_exec_start_points_to_script"],
        "factor_id": "F6.2",
    },
    {
        "name": "service_adds_install",
        "description": "Service has [Install] section — operator may enable service directly, triggering it independently of the timer and breaking the pairing semantic.",
        "mutation": _service_adds_install,
        "must_fail": ["service_has_no_install_section"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_delimiter",
        "description": "Remove the delimiter line — checker cannot separate the two unit bodies; treats the concatenated blob as a single unit.",
        "mutation": _drop_delimiter,
        "must_fail": ["delimiter_present", "both_units_present"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_timer_install",
        "description": "Remove timer [Install] section — systemctl enable fails; timer never runs on boot.",
        "mutation": _drop_timer_install_section,
        "must_fail": ["timer_wantedby_timers_target"],
        "factor_id": "F6.1",
    },
]
