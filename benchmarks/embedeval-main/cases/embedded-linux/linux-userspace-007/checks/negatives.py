"""Negative tests for linux-userspace-007 (sd-bus service)."""

import re


def _swap_sd_bus_for_libdbus(code: str) -> str:
    """Wholesale replace sd-bus core calls with libdbus stubs — LLM
    default bias."""
    code = code.replace(
        "sd_bus_open_system(&bus)",
        "dbus_bus_get(DBUS_BUS_SYSTEM, &err)",
    )
    code = code.replace(
        "sd_bus_request_name(bus, ",
        "dbus_bus_request_name(bus, ",
    )
    code = code.replace("sd_bus_process", "dbus_connection_read_write_dispatch")
    code = code.replace("sd_bus_wait", "dbus_connection_read_write")
    return code


def _drop_vtable_start(code: str) -> str:
    return code.replace("SD_BUS_VTABLE_START(0),\n\t", "")


def _drop_vtable_end(code: str) -> str:
    return code.replace(",\n\tSD_BUS_VTABLE_END,", ",")


def _swap_ping_signature_si(code: str) -> str:
    return code.replace(
        'SD_BUS_METHOD("Ping", "s", "s"', 'SD_BUS_METHOD("Ping", "si", "s"'
    )


def _drop_request_name(code: str) -> str:
    return re.sub(
        r"\n\s*r\s*=\s*sd_bus_request_name[^;]+;\s*\n"
        r"\s*if\s*\(r\s*<\s*0\)\s*\{[^}]+\}\s*\n",
        "\n",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_process_wait_loop(code: str) -> str:
    return re.sub(
        r"\n\s*for\s*\(;;\)\s*\{[^}]+\}\s*\n",
        "\n",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_unref(code: str) -> str:
    return code.replace("bus = sd_bus_unref(bus);\n", "")


def _wrong_object_path(code: str) -> str:
    return code.replace('"/com/embedeval/Example"', '"/org/example/Other"')


def _wrong_interface(code: str) -> str:
    return code.replace(
        'sd_bus_add_object_vtable(bus, &slot, "/com/embedeval/Example",\n'
        '\t\t\t\t     "com.embedeval.Example"',
        'sd_bus_add_object_vtable(bus, &slot, "/com/embedeval/Example",\n'
        '\t\t\t\t     "org.wrong.Interface"',
    )


def _open_user_instead_of_system(code: str) -> str:
    return code.replace("sd_bus_open_system", "sd_bus_open_user")


def _drop_error_check(code: str) -> str:
    """Remove the if (r < 0) check specifically after sd_bus_open_system.

    Targets only that call's error block to leave the other sd_bus_*
    error checks intact — the point is to show open_system unchecked,
    not to break the whole error-handling chain.
    """
    return re.sub(
        r"(r\s*=\s*sd_bus_open_system\s*\([^;]+;)\s*\n"
        r"\s*if\s*\(r\s*<\s*0\)\s*\{[^}]+\}\s*\n",
        r"\1\n",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_ping_method_entry(code: str) -> str:
    """Drop the SD_BUS_METHOD line — vtable becomes empty."""
    return re.sub(
        r"\n\s*SD_BUS_METHOD\([^)]+\),", "", code, count=1
    )


NEGATIVES = [
    {
        "name": "use_libdbus_instead_of_sd_bus",
        "description": "Swap sd-bus core calls for libdbus equivalents. LLM default bias — but libdbus is explicitly discouraged for Linux-only embedded daemons.",
        "mutation": _swap_sd_bus_for_libdbus,
        "must_fail": ["sd_bus_api_used", "no_libdbus_api"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_vtable_start",
        "description": "Remove SD_BUS_VTABLE_START — compiler errors on missing vtable preamble.",
        "mutation": _drop_vtable_start,
        "must_fail": ["vtable_start_and_end_markers"],
        "factor_id": "F5.2",
    },
    {
        "name": "drop_vtable_end",
        "description": "Remove SD_BUS_VTABLE_END — vtable array unterminated; runtime reads into adjacent memory.",
        "mutation": _drop_vtable_end,
        "must_fail": ["vtable_start_and_end_markers"],
        "factor_id": "F5.2",
    },
    {
        "name": "wrong_ping_signature",
        "description": 'SD_BUS_METHOD("Ping", "si", "s") — two args where one is specified. Contract violation; D-Bus introspection disagrees with implementation.',
        "mutation": _swap_ping_signature_si,
        "must_fail": ["ping_method_registered"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_request_name",
        "description": "Skip sd_bus_request_name — no well-known name; clients cannot find the service.",
        "mutation": _drop_request_name,
        "must_fail": ["sd_bus_api_used", "bus_name_is_com_embedeval_example"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_process_wait_loop",
        "description": "No main loop — service registers its vtable and immediately exits. Never serves a request.",
        "mutation": _drop_process_wait_loop,
        "must_fail": ["process_wait_loop_present", "sd_bus_api_used"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_bus_unref",
        "description": "Skip sd_bus_unref — bus connection leaks; D-Bus ref kept until process exits. For a long-running service this is a real leak when main exits via error path.",
        "mutation": _drop_unref,
        "must_fail": ["bus_unref_on_exit", "sd_bus_api_used"],
        "factor_id": "E3.1",
    },
    {
        "name": "wrong_object_path",
        "description": "Object path is /org/example/Other — mismatches documented /com/embedeval/Example; clients cannot find the object.",
        "mutation": _wrong_object_path,
        "must_fail": ["object_path_set"],
        "factor_id": "F6.2",
    },
    {
        "name": "wrong_interface_name",
        "description": "Interface renamed to org.wrong.Interface — mismatches bus name; clients calling com.embedeval.Example.Ping see InterfaceNotFound.",
        "mutation": _wrong_interface,
        "must_fail": ["interface_name_correct"],
        "factor_id": "F6.2",
    },
    {
        "name": "use_user_bus_instead_of_system",
        "description": "sd_bus_open_user — system service registered on per-session bus; only works inside a logged-in user session, not in the systemd system scope.",
        "mutation": _open_user_instead_of_system,
        "must_fail": ["sd_bus_api_used"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_error_check_on_open",
        "description": "No r<0 check after sd_bus_open_system — continues into add_object_vtable with a NULL bus.",
        "mutation": _drop_error_check,
        "must_fail": ["error_propagation_r_lt_0"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_ping_method_entry",
        "description": "Vtable has no SD_BUS_METHOD entry — Ping is introspected as missing; client sees UnknownMethod.",
        "mutation": _drop_ping_method_entry,
        "must_fail": ["ping_method_registered"],
        "factor_id": "F6.2",
    },
]
