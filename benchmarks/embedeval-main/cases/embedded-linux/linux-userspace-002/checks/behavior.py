"""Behavioral checks for linux-userspace-002 (libgpiod v2 edge monitor)."""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    has_api_call,
    has_libgpiod_v1_api,
    has_libgpiod_v2_api,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)

    # 1. v2-exclusive edge-event API present.
    v2_found = set(has_libgpiod_v2_api(generated_code))
    required_v2 = {
        "gpiod_line_settings_new",
        "gpiod_line_settings_set_edge_detection",
        "gpiod_edge_event_buffer_new",
        "gpiod_line_request_wait_edge_events",
        "gpiod_line_request_read_edge_events",
    }
    missing = required_v2 - v2_found
    details.append(
        CheckDetail(
            check_name="libgpiod_v2_edge_api_used",
            passed=not missing,
            expected="v2 edge-event API: settings_set_edge_detection + edge_event_buffer_new + request_wait/read_edge_events",
            actual=f"found: {sorted(v2_found)}; missing: {sorted(missing)}",
            check_type="constraint",
        )
    )

    # 2. v1 event helpers must NOT appear.
    v1_event = [
        api
        for api in has_libgpiod_v1_api(generated_code)
        if "event" in api or "request" in api
    ]
    details.append(
        CheckDetail(
            check_name="no_libgpiod_v1_event_api",
            passed=len(v1_event) == 0,
            expected="No v1 event helpers (gpiod_line_event_wait, gpiod_line_event_read, ...)",
            actual="clean" if not v1_event else f"v1 found: {v1_event}",
            check_type="constraint",
        )
    )

    # 3. GPIOD_LINE_EDGE_RISING configured.
    has_rising = scoped_contains(
        generated_code, "GPIOD_LINE_EDGE_RISING", scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="rising_edge_detection_configured",
            passed=has_rising,
            expected="gpiod_line_settings_set_edge_detection(..., GPIOD_LINE_EDGE_RISING)",
            actual="present" if has_rising else "missing",
            check_type="constraint",
        )
    )

    # 4. Line direction is INPUT (not OUTPUT — edge detection on output is
    # a nonsense configuration).
    has_input_direction = scoped_contains(
        generated_code, "GPIOD_LINE_DIRECTION_INPUT", scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="direction_set_input",
            passed=has_input_direction,
            expected="GPIOD_LINE_DIRECTION_INPUT set for edge monitoring",
            actual="present" if has_input_direction else "missing",
            check_type="constraint",
        )
    )

    # 5. Wait has a FINITE timeout — NOT -1 (wait forever).
    # Match the wait call's second argument; reject the constant -1 as the
    # sole call. Also resolve simple ``#define NAME -...`` macros since
    # the argument may be a symbol.
    wait_calls = re.findall(
        r"gpiod_line_request_wait_edge_events\s*\([^,]+,\s*([^)]+)\)",
        stripped,
    )
    # Pre-scan negative-value #define macros so we can flag symbolic
    # forever markers (e.g. WAIT_NS defined as -1LL).
    forever_macros = set(
        re.findall(r"#define\s+(\w+)\s+-\d+[uUlL]*", stripped)
    )
    forever_literals = {"-1", "-1LL", "-1L", "-1LL"}

    def _is_forever(arg: str) -> bool:
        s = arg.strip()
        return s in forever_literals or s in forever_macros

    all_finite = bool(wait_calls) and all(not _is_forever(a) for a in wait_calls)
    details.append(
        CheckDetail(
            check_name="wait_has_finite_timeout",
            passed=all_finite,
            expected="Wait timeout is a finite positive value (≤ 1 second = 1_000_000_000 ns)",
            actual=(
                f"wait calls: {wait_calls}; forever_macros: {sorted(forever_macros)}"
                if wait_calls
                else "wait call missing"
            ),
            check_type="constraint",
        )
    )

    # 6. SIGTERM handler registered via signal() or sigaction().
    sigterm_registered = bool(
        re.search(r"(?:signal|sigaction)\s*\(\s*SIGTERM\b", stripped)
    )
    details.append(
        CheckDetail(
            check_name="sigterm_handler_registered",
            passed=sigterm_registered,
            expected="SIGTERM handler registered (signal() or sigaction())",
            actual="present" if sigterm_registered else "missing",
            check_type="constraint",
        )
    )

    # 7. Exit flag is volatile sig_atomic_t.
    has_sig_atomic = bool(
        re.search(r"volatile\s+sig_atomic_t\s+\w+", stripped)
    )
    details.append(
        CheckDetail(
            check_name="exit_flag_is_sig_atomic_volatile",
            passed=has_sig_atomic,
            expected="exit flag declared ``volatile sig_atomic_t``",
            actual="present" if has_sig_atomic else "missing",
            check_type="constraint",
        )
    )

    # 8. Main loop checks the exit flag.
    # Extract the flag name via the sig_atomic_t declaration, then look
    # for ``while (!flag)`` or ``while (flag == 0)``.
    flag_match = re.search(
        r"volatile\s+sig_atomic_t\s+(\w+)", stripped
    )
    flag_name = flag_match.group(1) if flag_match else ""
    loop_checks = False
    if flag_name:
        loop_checks = bool(
            re.search(rf"while\s*\(\s*!\s*{re.escape(flag_name)}\s*\)", stripped)
            or re.search(
                rf"while\s*\(\s*{re.escape(flag_name)}\s*==\s*0\s*\)", stripped
            )
        )
    details.append(
        CheckDetail(
            check_name="main_loop_checks_exit_flag",
            passed=loop_checks,
            expected="main loop predicate is ``!exit_flag`` or equivalent",
            actual="present" if loop_checks else "missing",
            check_type="constraint",
        )
    )

    # 9. All resources released on exit.
    cleanup_apis = [
        "gpiod_edge_event_buffer_free",
        "gpiod_line_request_release",
        "gpiod_line_settings_free",
        "gpiod_line_config_free",
        "gpiod_request_config_free",
        "gpiod_chip_close",
    ]
    missing_cleanup = [api for api in cleanup_apis if not has_api_call(stripped, api)]
    details.append(
        CheckDetail(
            check_name="all_resources_released",
            passed=len(missing_cleanup) == 0,
            expected="all buffer / request / configs / settings / chip released",
            actual="complete" if not missing_cleanup else f"missing: {missing_cleanup}",
            check_type="constraint",
        )
    )

    # 10. Event-read call in the events-available branch.
    has_read_events = has_api_call(stripped, "gpiod_line_request_read_edge_events")
    details.append(
        CheckDetail(
            check_name="events_read_on_wait_success",
            passed=has_read_events,
            expected="gpiod_line_request_read_edge_events called after successful wait",
            actual="present" if has_read_events else "missing",
            check_type="constraint",
        )
    )

    # 11. No cross-platform APIs.
    cross_plat = check_no_cross_platform_apis(
        generated_code, skip_platforms=["Linux_Userspace", "POSIX"]
    )
    details.append(
        CheckDetail(
            check_name="no_cross_platform_apis",
            passed=len(cross_plat) == 0,
            expected="No FreeRTOS / Zephyr / Arduino / STM32 HAL APIs",
            actual="clean" if not cross_plat else f"found: {[a for a, _ in cross_plat]}",
            check_type="constraint",
        )
    )

    return details
