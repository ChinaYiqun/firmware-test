"""Negative tests for linux-userspace-002 (libgpiod v2 edge monitor)."""

import re


def _wait_forever(code: str) -> str:
    return code.replace(
        "gpiod_line_request_wait_edge_events(request, WAIT_NS)",
        "gpiod_line_request_wait_edge_events(request, -1)",
    )


def _wait_forever_literal(code: str) -> str:
    return code.replace("#define WAIT_NS 1000000000LL", "#define WAIT_NS -1LL")


def _drop_sigterm_handler(code: str) -> str:
    return re.sub(
        r"sigaction\(SIGTERM[^;]+;\n", "", code, count=1
    )


def _swap_edge_rising_to_falling(code: str) -> str:
    return code.replace("GPIOD_LINE_EDGE_RISING", "GPIOD_LINE_EDGE_FALLING")


def _drop_edge_detection(code: str) -> str:
    return re.sub(
        r"\n\s*gpiod_line_settings_set_edge_detection\([^;]+;", "", code, count=1
    )


def _use_output_direction(code: str) -> str:
    return code.replace(
        "GPIOD_LINE_DIRECTION_INPUT", "GPIOD_LINE_DIRECTION_OUTPUT"
    )


def _swap_volatile_to_plain_int(code: str) -> str:
    return code.replace(
        "static volatile sig_atomic_t exit_flag = 0;",
        "static int exit_flag = 0;",
    )


def _use_v1_event_api(code: str) -> str:
    """Swap the v2 wait/read for v1 line_event_wait/read helpers."""
    return code.replace(
        "int n = gpiod_line_request_wait_edge_events(request, WAIT_NS);",
        "int n = gpiod_line_event_wait(request, NULL);",
    ).replace(
        "int got = gpiod_line_request_read_edge_events(request, buf, BUF_CAP);",
        "int got = gpiod_line_event_read(request, NULL);",
    )


def _drop_buffer_free(code: str) -> str:
    return re.sub(
        r"\n\s*gpiod_edge_event_buffer_free\([^)]+\);",
        "",
        code,
        count=1,
    )


def _drop_request_release(code: str) -> str:
    return code.replace("gpiod_line_request_release(request);\n", "")


def _main_loop_ignores_exit_flag(code: str) -> str:
    return code.replace("while (!exit_flag)", "while (1)")


def _drop_event_read(code: str) -> str:
    return re.sub(
        r"\n\s*int got\s*=\s*gpiod_line_request_read_edge_events[^;]+;",
        "\n\t\tint got = 0;",
        code,
        count=1,
    )


NEGATIVES = [
    {
        "name": "wait_forever_literal_minus_one",
        "description": "Pass -1 as timeout to wait_edge_events — blocks indefinitely; SIGTERM interrupts only via EINTR which many implementations handle silently.",
        "mutation": _wait_forever,
        "must_fail": ["wait_has_finite_timeout"],
        "factor_id": "B3.1",
    },
    {
        "name": "wait_forever_macro_redefined",
        "description": "Redefine WAIT_NS to -1LL — same semantic: infinite blocking.",
        "mutation": _wait_forever_literal,
        "must_fail": ["wait_has_finite_timeout"],
        "factor_id": "B3.1",
    },
    {
        "name": "drop_sigterm_handler",
        "description": "Remove sigaction(SIGTERM, ...) — daemon cannot be shut down gracefully; systemd stop sends SIGTERM then SIGKILL 90s later.",
        "mutation": _drop_sigterm_handler,
        "must_fail": ["sigterm_handler_registered"],
        "factor_id": "E4.1",
    },
    {
        "name": "edge_falling_instead_of_rising",
        "description": "GPIOD_LINE_EDGE_FALLING — monitors opposite transition.",
        "mutation": _swap_edge_rising_to_falling,
        "must_fail": ["rising_edge_detection_configured"],
        "factor_id": "A1.1",
    },
    {
        "name": "drop_edge_detection_config",
        "description": "Omit set_edge_detection call — line configured as plain input; wait never resolves.",
        "mutation": _drop_edge_detection,
        "must_fail": ["libgpiod_v2_edge_api_used"],
        "factor_id": "F4.1",
    },
    {
        "name": "direction_output_not_input",
        "description": "GPIOD_LINE_DIRECTION_OUTPUT for an edge monitor — nonsense configuration; kernel rejects.",
        "mutation": _use_output_direction,
        "must_fail": ["direction_set_input"],
        "factor_id": "A1.1",
    },
    {
        "name": "exit_flag_not_sig_atomic_volatile",
        "description": "Plain ``int exit_flag`` instead of volatile sig_atomic_t — race between signal handler write and main-loop read.",
        "mutation": _swap_volatile_to_plain_int,
        "must_fail": ["exit_flag_is_sig_atomic_volatile"],
        "factor_id": "D1.1",
    },
    {
        "name": "use_v1_event_api",
        "description": "Replace v2 wait/read with v1 line_event_wait/read — deprecated, absent on libgpiod 2.x builds.",
        "mutation": _use_v1_event_api,
        "must_fail": ["libgpiod_v2_edge_api_used", "no_libgpiod_v1_event_api"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_edge_buffer_free",
        "description": "Omit buffer free — leak on exit.",
        "mutation": _drop_buffer_free,
        "must_fail": ["all_resources_released"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_request_release",
        "description": "Omit request release — line remains reserved.",
        "mutation": _drop_request_release,
        "must_fail": ["all_resources_released"],
        "factor_id": "E3.1",
    },
    {
        "name": "main_loop_ignores_exit_flag",
        "description": "while (1) — signal handler flips flag but loop never reads it; SIGTERM ignored.",
        "mutation": _main_loop_ignores_exit_flag,
        "must_fail": ["main_loop_checks_exit_flag"],
        "factor_id": "E4.1",
    },
    {
        "name": "drop_event_read",
        "description": "Skip read_edge_events after successful wait — events stay queued, kernel buffer fills, eventually lost.",
        "mutation": _drop_event_read,
        "must_fail": ["libgpiod_v2_edge_api_used", "events_read_on_wait_success"],
        "factor_id": "E2.1",
    },
]
