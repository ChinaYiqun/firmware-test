"""Negative tests for linux-userspace-005 (udev match/assign discipline)."""

import re


def _subsystem_assign_not_match(code: str) -> str:
    """Classic bug: SUBSYSTEM="usb" (assign) instead of ==."""
    return code.replace('SUBSYSTEM=="usb"', 'SUBSYSTEM="usb"')


def _action_assign_not_match(code: str) -> str:
    return code.replace('ACTION=="add"', 'ACTION="add"')


def _attrs_assign_not_match(code: str) -> str:
    return code.replace('ATTRS{idVendor}=="1d6b"', 'ATTRS{idVendor}="1d6b"')


def _tag_plain_equal(code: str) -> str:
    """TAG="systemd" (=) instead of TAG+="systemd" (+=). Plain =
    overwrites existing tags rather than adding."""
    return code.replace('TAG+="systemd"', 'TAG="systemd"')


def _tag_double_equal(code: str) -> str:
    """TAG=="systemd" (==). Match operator on an assign-only key —
    udev won't set the tag."""
    return code.replace('TAG+="systemd"', 'TAG=="systemd"')


def _drop_systemd_tag(code: str) -> str:
    return code.replace(', TAG+="systemd"', "")


def _drop_systemd_wants(code: str) -> str:
    return re.sub(r',\s*ENV\{SYSTEMD_WANTS\}\s*=\s*"[^"]*"', "", code)


def _systemd_wants_double_eq(code: str) -> str:
    """SYSTEMD_WANTS=="..." — match instead of assign, silently no-ops."""
    return code.replace('ENV{SYSTEMD_WANTS}="', 'ENV{SYSTEMD_WANTS}=="')


def _wrong_vendor_id(code: str) -> str:
    return code.replace('ATTRS{idVendor}=="1d6b"', 'ATTRS{idVendor}=="2222"')


def _wrong_product_id(code: str) -> str:
    return code.replace('ATTRS{idProduct}=="0002"', 'ATTRS{idProduct}=="9999"')


def _run_systemctl_antipattern(code: str) -> str:
    return code.replace(
        'ENV{SYSTEMD_WANTS}="vendor-example-daemon.service"',
        'RUN+="/bin/systemctl restart vendor-example-daemon.service"',
    )


def _action_wrong_value(code: str) -> str:
    return code.replace('ACTION=="add"', 'ACTION=="change"')


NEGATIVES = [
    {
        "name": "subsystem_assign_not_match",
        "description": 'SUBSYSTEM="usb" (single =) — assignment to a match-only key. Rule silently fails to filter.',
        "mutation": _subsystem_assign_not_match,
        "must_fail": ["subsystem_match_usb", "no_match_only_key_assigned"],
        "factor_id": "F6.2",
    },
    {
        "name": "action_assign_not_match",
        "description": 'ACTION="add" — same class of match/assign confusion. Rule fires on every event.',
        "mutation": _action_assign_not_match,
        "must_fail": ["action_match_add", "no_match_only_key_assigned"],
        "factor_id": "F6.2",
    },
    {
        "name": "attrs_assign_not_match",
        "description": 'ATTRS{idVendor}="1d6b" — attribute match confused with assign.',
        "mutation": _attrs_assign_not_match,
        "must_fail": ["idvendor_match_1d6b", "no_match_only_key_assigned"],
        "factor_id": "F6.2",
    },
    {
        "name": "tag_plain_equal",
        "description": 'TAG="systemd" — plain = overwrites existing tags; + on boot, on reload, etc. gone.',
        "mutation": _tag_plain_equal,
        "must_fail": ["tag_systemd_append_assign"],
        "factor_id": "F6.2",
    },
    {
        "name": "tag_double_equal",
        "description": 'TAG=="systemd" — match operator on assign key. Tag is not set; systemd handoff broken.',
        "mutation": _tag_double_equal,
        "must_fail": ["tag_systemd_append_assign"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_systemd_tag",
        "description": "Remove TAG+=\"systemd\" — udev does not hand off to systemd; SYSTEMD_WANTS has no effect.",
        "mutation": _drop_systemd_tag,
        "must_fail": ["tag_directive_present", "tag_systemd_append_assign"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_systemd_wants",
        "description": "Remove ENV{SYSTEMD_WANTS} — hotplug has no effect; service not restarted.",
        "mutation": _drop_systemd_wants,
        "must_fail": [
            "systemd_wants_env_present",
            "systemd_wants_env_set_to_service",
        ],
        "factor_id": "F6.1",
    },
    {
        "name": "systemd_wants_double_eq",
        "description": 'ENV{SYSTEMD_WANTS}=="..." — match instead of assign. Env var not set; service not triggered.',
        "mutation": _systemd_wants_double_eq,
        "must_fail": ["systemd_wants_env_set_to_service"],
        "factor_id": "F6.2",
    },
    {
        "name": "wrong_vendor_id",
        "description": "Vendor ID 0x2222 — rule never matches the intended device.",
        "mutation": _wrong_vendor_id,
        "must_fail": ["idvendor_match_1d6b"],
        "factor_id": "F6.2",
    },
    {
        "name": "wrong_product_id",
        "description": "Product ID 0x9999 — rule never matches.",
        "mutation": _wrong_product_id,
        "must_fail": ["idproduct_match_0002"],
        "factor_id": "F6.2",
    },
    {
        "name": "run_systemctl_antipattern",
        "description": 'RUN+="/bin/systemctl restart ..." — legacy shell-out anti-pattern. Spawns a shell inside udev event handler; race against systemd\'s own device-unit handling.',
        "mutation": _run_systemctl_antipattern,
        "must_fail": [
            "no_run_systemctl_antipattern",
            "systemd_wants_env_set_to_service",
        ],
        "factor_id": "F6.2",
    },
    {
        "name": "action_wrong_value",
        "description": 'ACTION=="change" — fires on device-changed events, not plug-in.',
        "mutation": _action_wrong_value,
        "must_fail": ["action_match_add"],
        "factor_id": "F6.2",
    },
]
