"""Tests for Linux userspace helpers in check_utils (Phase B).

Backs the linux-userspace-001..008 TC family. Each test class pins a
specific false-positive trap or API-variant acceptance rule so
regressions surface here rather than as silent check drift in
per-TC oracles.
"""

import pytest

from embedeval.check_utils import (
    has_bpf_core_read,
    has_bpf_sec_macro,
    has_libdbus_api,
    has_libgpiod_v1_api,
    has_libgpiod_v2_api,
    has_sd_bus_api,
    strip_systemd_comments,
    systemd_unit_section_has,
    udev_match_key_used_as_assign,
    udev_rule_assigns,
    udev_rule_matches,
)


class TestSystemdUnitSectionHas:
    """Directive-within-section extraction."""

    def test_service_type_notify(self) -> None:
        unit = (
            "[Unit]\nDescription=Test\n"
            "[Service]\nType=notify\nExecStart=/usr/bin/foo\nWatchdogSec=30\n"
            "[Install]\nWantedBy=multi-user.target\n"
        )
        assert systemd_unit_section_has(unit, "Service", "Type") == "notify"
        assert systemd_unit_section_has(unit, "Service", "WatchdogSec") == "30"

    def test_directive_in_wrong_section_not_found(self) -> None:
        unit = (
            "[Unit]\nType=notify\n"  # wrong section — Type belongs in [Service]
            "[Service]\nExecStart=/usr/bin/foo\n"
        )
        # Looking for Type in [Service] — should be None, not pick up [Unit]'s Type
        assert systemd_unit_section_has(unit, "Service", "Type") is None

    def test_directive_absent(self) -> None:
        unit = "[Service]\nExecStart=/usr/bin/foo\n"
        assert systemd_unit_section_has(unit, "Service", "WatchdogSec") is None

    def test_last_occurrence_wins(self) -> None:
        """systemd's precedence: later directive overrides earlier."""
        unit = "[Service]\nRestart=no\nRestart=on-failure\n"
        assert systemd_unit_section_has(unit, "Service", "Restart") == "on-failure"

    def test_comment_stripped(self) -> None:
        unit = "[Service]\n# Type=simple (old)\nType=notify\n"
        assert systemd_unit_section_has(unit, "Service", "Type") == "notify"


class TestUdevRuleMatchers:
    """udev match-vs-assign discipline."""

    def test_match_with_double_eq(self) -> None:
        rule = 'SUBSYSTEM=="usb", ACTION=="add"\n'
        assert udev_rule_matches(rule, "SUBSYSTEM") == "usb"
        assert udev_rule_matches(rule, "ACTION") == "add"

    def test_attrs_subkey(self) -> None:
        rule = 'ATTRS{idVendor}=="1d6b", ATTRS{idProduct}=="0002"\n'
        assert udev_rule_matches(rule, "ATTRS") == "1d6b"  # first subkey

    def test_assign_detected(self) -> None:
        rule = 'SYMLINK+="custom-name", MODE="0660"\n'
        assert udev_rule_assigns(rule, "SYMLINK") == ("+=", "custom-name")
        assert udev_rule_assigns(rule, "MODE") == ("=", "0660")

    def test_match_only_key_used_as_assign_flagged(self) -> None:
        """Classic bug: SUBSYSTEM="usb" is assign; correct is SUBSYSTEM=="usb"."""
        rule = 'SUBSYSTEM="usb", ACTION=="add"\n'
        offenders = udev_match_key_used_as_assign(rule)
        assert "SUBSYSTEM" in offenders

    def test_match_only_clean_when_double_eq(self) -> None:
        rule = 'SUBSYSTEM=="usb", KERNEL=="ttyUSB*"\n'
        assert udev_match_key_used_as_assign(rule) == []

    def test_plus_eq_on_assign_key_is_fine(self) -> None:
        """+= on SYMLINK/TAG/RUN is legal; only bare = on match-only keys is bad."""
        rule = 'TAG+="systemd", RUN+="/bin/true"\n'
        assert udev_match_key_used_as_assign(rule) == []

    def test_attr_dual_use_assignment_not_flagged(self) -> None:
        """ATTR{key}=value is a VALID udev assignment (writes to sysfs).
        Must not be flagged as a match-only-key-used-as-assign bug.
        Regression for /review fix C1."""
        rule = 'ACTION=="add", SUBSYSTEM=="backlight", ATTR{brightness}="200"\n'
        offenders = udev_match_key_used_as_assign(rule)
        assert "ATTR" not in offenders

    def test_attrs_plural_still_match_only(self) -> None:
        """ATTRS (plural, walks parent chain) stays strictly match-only —
        the kernel cannot write to a parent device attribute."""
        rule = 'ATTRS{idVendor}="1d6b"\n'
        assert "ATTRS" in udev_match_key_used_as_assign(rule)


class TestSystemdLineContinuation:
    """Regression for /review fix N1 — multi-line directive values."""

    def test_single_line_continuation_folded(self) -> None:
        unit = "[Service]\nExecStart=/usr/bin/foo \\\n    --arg1 --arg2\n"
        rhs = systemd_unit_section_has(unit, "Service", "ExecStart")
        assert rhs is not None
        assert "/usr/bin/foo" in rhs
        assert "--arg1" in rhs
        assert "--arg2" in rhs

    def test_multi_line_continuation_folded(self) -> None:
        unit = (
            "[Service]\n"
            "ExecStart=/usr/bin/foo \\\n"
            "    --arg1 \\\n"
            "    --arg2 \\\n"
            "    --arg3\n"
        )
        rhs = systemd_unit_section_has(unit, "Service", "ExecStart")
        assert rhs is not None
        for tok in ("/usr/bin/foo", "--arg1", "--arg2", "--arg3"):
            assert tok in rhs


class TestLibgpiodVersionDetection:
    """libgpiod v1 vs v2 symbol disambiguation."""

    def test_v1_exclusive_symbol_detected(self) -> None:
        code = "line = gpiod_chip_get_line(chip, 17);\n"
        assert "gpiod_chip_get_line" in has_libgpiod_v1_api(code)

    def test_v2_exclusive_symbol_detected(self) -> None:
        code = "settings = gpiod_line_settings_new();\n"
        assert "gpiod_line_settings_new" in has_libgpiod_v2_api(code)

    def test_v1_not_flagged_for_v2_code(self) -> None:
        code = (
            "settings = gpiod_line_settings_new();\n"
            "gpiod_line_settings_set_direction(settings,\n"
            "    GPIOD_LINE_DIRECTION_OUTPUT);\n"
        )
        assert has_libgpiod_v1_api(code) == []
        assert "gpiod_line_settings_new" in has_libgpiod_v2_api(code)

    def test_v2_not_flagged_for_v1_code(self) -> None:
        code = (
            "line = gpiod_chip_get_line(chip, 17);\n"
            'gpiod_line_request_output(line, "consumer", 0);\n'
        )
        assert has_libgpiod_v2_api(code) == []
        assert set(has_libgpiod_v1_api(code)) >= {
            "gpiod_chip_get_line",
            "gpiod_line_request_output",
        }

    def test_shared_symbol_not_in_either_exclusive(self) -> None:
        """``gpiod_chip_open`` exists in both v1 and v2 — must not appear
        in either exclusive list."""
        code = 'chip = gpiod_chip_open("/dev/gpiochip0");\n'
        assert has_libgpiod_v1_api(code) == []
        assert has_libgpiod_v2_api(code) == []


class TestSdBusVsLibdbus:
    """sd-bus vs libdbus spelling disambiguation."""

    def test_sd_bus_symbols_detected(self) -> None:
        code = "sd_bus_open_system(&bus);\nsd_bus_request_name(bus, name, 0);\n"
        found = has_sd_bus_api(code)
        assert "sd_bus_open_system" in found
        assert "sd_bus_request_name" in found

    def test_libdbus_symbols_detected(self) -> None:
        code = (
            "dbus_bus_get(DBUS_BUS_SYSTEM, &err);\n"
            "dbus_bus_request_name(conn, name, 0, &err);\n"
        )
        found = has_libdbus_api(code)
        assert "dbus_bus_get" in found
        assert "dbus_bus_request_name" in found

    def test_sd_bus_not_flagged_as_libdbus(self) -> None:
        """``sd_bus_foo`` must not match ``dbus_foo`` due to word boundary."""
        code = 'sd_bus_open_system(&bus);\nsd_bus_message_append(m, "s", x);\n'
        assert has_libdbus_api(code) == []

    def test_libdbus_not_flagged_as_sd_bus(self) -> None:
        code = "dbus_message_new_method_call(NULL, NULL, NULL, NULL);\n"
        assert has_sd_bus_api(code) == []


class TestBpfSecMacros:
    """BPF SEC() macro detection."""

    def test_kprobe_detected(self) -> None:
        code = 'SEC("kprobe/do_unlinkat") int trace(void *ctx) { return 0; }\n'
        assert "kprobe" in has_bpf_sec_macro(code)

    def test_tracepoint_variants(self) -> None:
        code = (
            'SEC("tp/sched/sched_switch") int t1(void *ctx) { return 0; }\n'
            'SEC("tracepoint/raw_syscalls/sys_enter") int t2(void *ctx) { return 0; }\n'
        )
        found = has_bpf_sec_macro(code)
        assert "tp" in found
        assert "tracepoint" in found

    def test_license_and_maps_sections(self) -> None:
        code = (
            'char LICENSE[] SEC("license") = "GPL";\n'
            'struct { int dummy; } events SEC(".maps");\n'
        )
        found = has_bpf_sec_macro(code)
        assert "license" in found
        assert ".maps" in found

    def test_unknown_sec_not_in_program_list(self) -> None:
        """A plain `SEC("weird")` shouldn't flag any program-type attachment."""
        code = 'int x SEC("weird_section");\n'
        assert has_bpf_sec_macro(code) == []


class TestBpfCoreRead:
    def test_basic_core_read(self) -> None:
        code = "pid = BPF_CORE_READ(task, tgid);\n"
        assert has_bpf_core_read(code)

    def test_str_into_variant(self) -> None:
        code = "BPF_CORE_READ_STR_INTO(&buf, task, comm);\n"
        assert has_bpf_core_read(code)

    def test_no_core_read_detected(self) -> None:
        code = "pid = task->tgid;\n"  # direct deref, not CO-RE
        assert not has_bpf_core_read(code)


class TestStripSystemdComments:
    def test_alias_identity(self) -> None:
        """strip_systemd_comments must be the same function as strip_yocto_comments."""
        from embedeval.check_utils import strip_yocto_comments

        assert strip_systemd_comments is strip_yocto_comments

    def test_hash_line_comment_dropped(self) -> None:
        text = "# leading\n[Service]\nType=notify  # trailing\n"
        out = strip_systemd_comments(text)
        assert "leading" not in out
        assert "trailing" not in out
        assert "Type=notify" in out

    def test_uri_not_stripped(self) -> None:
        text = "ExecStart=/usr/bin/curl https://example.com/file\n"
        out = strip_systemd_comments(text)
        assert "https://example.com/file" in out


@pytest.mark.parametrize(
    "symbol",
    sorted(
        set(
            [  # v1 exclusives must all be detected by has_libgpiod_v1_api
                "gpiod_chip_get_line",
                "gpiod_line_request_output",
                "gpiod_line_event_wait",
                "gpiod_line_set_value",
                "gpiod_line_release",
            ]
        )
    ),
)
def test_libgpiod_v1_constant_coverage(symbol: str) -> None:
    code = f"{symbol}(arg1, arg2);\n"
    assert symbol in has_libgpiod_v1_api(code)


@pytest.mark.parametrize(
    "symbol",
    sorted(
        set(
            [  # v2 exclusives must all be detected by has_libgpiod_v2_api
                "gpiod_line_settings_new",
                "gpiod_chip_request_lines",
                "gpiod_line_request_get_value",
                "gpiod_edge_event_buffer_new",
                "gpiod_request_config_new",
            ]
        )
    ),
)
def test_libgpiod_v2_constant_coverage(symbol: str) -> None:
    code = f"{symbol}(arg1, arg2);\n"
    assert symbol in has_libgpiod_v2_api(code)
