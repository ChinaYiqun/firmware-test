"""Behavioral checks for linux-userspace-005 (udev match/assign discipline)."""

from embedeval.check_utils import (
    scoped_contains,
    udev_match_key_used_as_assign,
    udev_rule_assigns,
    udev_rule_matches,
)
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    # 1. SUBSYSTEM=="usb" (match).
    subsystem = udev_rule_matches(generated_code, "SUBSYSTEM")
    details.append(
        CheckDetail(
            check_name="subsystem_match_usb",
            passed=subsystem == "usb",
            expected='SUBSYSTEM=="usb" (double-eq match)',
            actual=f"SUBSYSTEM=={subsystem!r}" if subsystem else "missing or wrong op",
            check_type="constraint",
        )
    )

    # 2. ACTION=="add" (match).
    action = udev_rule_matches(generated_code, "ACTION")
    details.append(
        CheckDetail(
            check_name="action_match_add",
            passed=action == "add",
            expected='ACTION=="add" (double-eq match)',
            actual=f"ACTION=={action!r}" if action else "missing or wrong op",
            check_type="constraint",
        )
    )

    # 3. idVendor match (hex 1d6b — Linux Foundation public VID).
    vendor = udev_rule_matches(generated_code, "ATTRS")
    # udev_rule_matches returns first ATTRS{*} — may be either; check both.
    has_vendor = scoped_contains(generated_code, "1d6b", scope="raw") and (
        scoped_contains(generated_code, 'ATTRS{idVendor}=="1d6b"', scope="raw")
        or scoped_contains(generated_code, 'ATTRS{idVendor} == "1d6b"', scope="raw")
    )
    details.append(
        CheckDetail(
            check_name="idvendor_match_1d6b",
            passed=has_vendor,
            expected='ATTRS{idVendor}=="1d6b"',
            actual="present" if has_vendor else f"first ATTRS matched: {vendor!r}",
            check_type="constraint",
        )
    )

    # 4. idProduct match (hex 0002).
    has_product = scoped_contains(
        generated_code, 'ATTRS{idProduct}=="0002"', scope="raw"
    ) or scoped_contains(generated_code, 'ATTRS{idProduct} == "0002"', scope="raw")
    details.append(
        CheckDetail(
            check_name="idproduct_match_0002",
            passed=has_product,
            expected='ATTRS{idProduct}=="0002"',
            actual="present" if has_product else "missing",
            check_type="constraint",
        )
    )

    # 5. TAG+="systemd" (append-assign; must not be ==, must not be =).
    tag_assign = udev_rule_assigns(generated_code, "TAG")
    tag_systemd = tag_assign is not None and tag_assign[1] == "systemd"
    tag_plus_eq = tag_assign is not None and tag_assign[0] == "+="
    details.append(
        CheckDetail(
            check_name="tag_systemd_append_assign",
            passed=tag_systemd and tag_plus_eq,
            expected='TAG+="systemd" (append-assign)',
            actual=(
                f"TAG{tag_assign[0]}{tag_assign[1]!r}" if tag_assign else "missing"
            ),
            check_type="constraint",
        )
    )

    # 6. ENV{SYSTEMD_WANTS}="<service name>" — coupling between udev and
    # systemd that replaces old-style RUN+="/bin/systemctl ...".
    has_systemd_wants = scoped_contains(
        generated_code,
        'ENV{SYSTEMD_WANTS}="vendor-example-daemon.service"',
        scope="raw",
    ) or scoped_contains(
        generated_code,
        'ENV{SYSTEMD_WANTS} = "vendor-example-daemon.service"',
        scope="raw",
    )
    details.append(
        CheckDetail(
            check_name="systemd_wants_env_set_to_service",
            passed=has_systemd_wants,
            expected='ENV{SYSTEMD_WANTS}="vendor-example-daemon.service"',
            actual="present" if has_systemd_wants else "missing or wrong service",
            check_type="constraint",
        )
    )

    # 7. No match-only key used with plain ``=`` (classic udev bug).
    offenders = udev_match_key_used_as_assign(generated_code)
    details.append(
        CheckDetail(
            check_name="no_match_only_key_assigned",
            passed=len(offenders) == 0,
            expected="Match-only keys (SUBSYSTEM, ACTION, ATTRS, KERNEL, ...) use ==, not =",
            actual="clean"
            if not offenders
            else f"assigned instead of matched: {offenders}",
            check_type="constraint",
        )
    )

    # 8. No legacy RUN+="/bin/systemctl ..." pattern. Modern udev should
    # use SYSTEMD_WANTS not shell-out. Reject RUN entirely here because
    # it's the anti-pattern being tested.
    has_run_systemctl = scoped_contains(
        generated_code, "RUN", scope="raw"
    ) and scoped_contains(generated_code, "systemctl", scope="raw")
    details.append(
        CheckDetail(
            check_name="no_run_systemctl_antipattern",
            passed=not has_run_systemctl,
            expected="No RUN+=/bin/systemctl — use SYSTEMD_WANTS instead",
            actual=("WRONG: RUN with systemctl" if has_run_systemctl else "clean"),
            check_type="constraint",
        )
    )

    return details
