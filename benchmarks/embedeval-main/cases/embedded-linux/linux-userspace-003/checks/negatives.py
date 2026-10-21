"""Negative tests for linux-userspace-003 (systemd watchdog triad)."""

import re


def _swap_type_to_simple(code: str) -> str:
    return code.replace("Type=notify", "Type=simple")


def _swap_type_to_exec(code: str) -> str:
    return code.replace("Type=notify", "Type=exec")


def _drop_type_entirely(code: str) -> str:
    return re.sub(r"^Type=.*\n", "", code, count=1, flags=re.MULTILINE)


def _drop_watchdog_sec(code: str) -> str:
    return re.sub(r"^WatchdogSec=.*\n", "", code, count=1, flags=re.MULTILINE)


def _watchdog_sec_wrong_value(code: str) -> str:
    """Duration string that doesn't match the 30s requirement."""
    return code.replace("WatchdogSec=30", "WatchdogSec=5")


def _swap_restart_to_no(code: str) -> str:
    return code.replace("Restart=on-watchdog", "Restart=no")


def _swap_restart_to_on_success(code: str) -> str:
    return code.replace("Restart=on-watchdog", "Restart=on-success")


def _drop_restart(code: str) -> str:
    return re.sub(r"^Restart=.*\n", "", code, count=1, flags=re.MULTILINE)


def _restart_sec_zero(code: str) -> str:
    return code.replace("RestartSec=5", "RestartSec=0")


def _half_start_limit_burst_only(code: str) -> str:
    return re.sub(r"^StartLimitIntervalSec=.*\n", "", code, count=1, flags=re.MULTILINE)


def _drop_install_section(code: str) -> str:
    return re.sub(r"\n\[Install\][\s\S]*$", "\n", code, count=1)


def _exec_start_relative_path(code: str) -> str:
    return code.replace(
        "ExecStart=/usr/bin/vendor-example-daemon",
        "ExecStart=vendor-example-daemon",
    )


NEGATIVES = [
    {
        "name": "type_simple_with_watchdog",
        "description": "Swap Type=notify → Type=simple. Classic two-of-three trap: WatchdogSec is set but the simple type does not listen for sd_notify pings, so the watchdog can never fire.",
        "mutation": _swap_type_to_simple,
        "must_fail": ["type_notify_set", "no_watchdog_with_simple_type"],
        "factor_id": "E5.1",
    },
    {
        "name": "type_exec_with_watchdog",
        "description": "Swap Type=notify → Type=exec. Same class of trap as simple — notification channel closed, watchdog inert.",
        "mutation": _swap_type_to_exec,
        "must_fail": ["type_notify_set"],
        "factor_id": "E5.1",
    },
    {
        "name": "drop_type_directive",
        "description": "Remove Type= entirely. systemd defaults to Type=simple for a service without Type, reproducing the simple-with-watchdog trap.",
        "mutation": _drop_type_entirely,
        "must_fail": ["type_notify_set", "type_directive_present"],
        "factor_id": "E5.1",
    },
    {
        "name": "drop_watchdog_sec",
        "description": "Remove WatchdogSec. Daemon can sd_notify all day but supervisor never times out. Watchdog silently disabled.",
        "mutation": _drop_watchdog_sec,
        "must_fail": [
            "watchdogsec_directive_present",
            "watchdog_sec_positive_duration",
            "watchdog_sec_matches_30s_requirement",
        ],
        "factor_id": "B2.1",
    },
    {
        "name": "watchdog_sec_wrong_value",
        "description": "WatchdogSec=5 instead of 30 — violates the prompt's explicit 30-second requirement; daemon's 10-second ping period guarantees starvation.",
        "mutation": _watchdog_sec_wrong_value,
        "must_fail": ["watchdog_sec_matches_30s_requirement"],
        "factor_id": "B2.2",
    },
    {
        "name": "restart_no_with_watchdog",
        "description": "Restart=no with WatchdogSec. Watchdog kills the daemon on timeout but supervisor does not restart it — device is dead until manual intervention.",
        "mutation": _swap_restart_to_no,
        "must_fail": ["restart_covers_watchdog_timeout"],
        "factor_id": "E4.1",
    },
    {
        "name": "restart_on_success_only",
        "description": "Restart=on-success with WatchdogSec — watchdog kill is SIGABRT (non-zero exit), so on-success never triggers. Same class of bug.",
        "mutation": _swap_restart_to_on_success,
        "must_fail": ["restart_covers_watchdog_timeout"],
        "factor_id": "E4.1",
    },
    {
        "name": "drop_restart",
        "description": "Remove Restart. systemd defaults to Restart=no; watchdog kill does not trigger restart.",
        "mutation": _drop_restart,
        "must_fail": ["restart_directive_present", "restart_covers_watchdog_timeout"],
        "factor_id": "E4.1",
    },
    {
        "name": "restart_sec_zero",
        "description": "RestartSec=0 — immediate restart storm on crash, quickly exhausting StartLimitBurst.",
        "mutation": _restart_sec_zero,
        "must_fail": ["restart_sec_positive"],
        "factor_id": "B2.2",
    },
    {
        "name": "start_limit_burst_only",
        "description": "StartLimitBurst set without StartLimitIntervalSec — ratelimit window undefined.",
        "mutation": _half_start_limit_burst_only,
        "must_fail": [
            "start_limit_burst_and_interval_paired",
            "start_limit_not_half_declared",
        ],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_install_section",
        "description": "Remove [Install] section. Unit cannot be enabled; systemctl enable fails.",
        "mutation": _drop_install_section,
        "must_fail": ["install_section_header", "wantedby_multi_user_target"],
        "factor_id": "F6.1",
    },
    {
        "name": "exec_start_relative_path",
        "description": "ExecStart uses relative path. systemd rejects non-absolute ExecStart.",
        "mutation": _exec_start_relative_path,
        "must_fail": ["exec_start_absolute_path"],
        "factor_id": "F6.2",
    },
]
