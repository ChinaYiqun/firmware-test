"""Behavioral checks for linux-userspace-001 (libgpiod v2 discipline).

Enforces the v1→v2 boundary: LLM must use the post-2020 character-device
config composition pattern, not the deprecated 2017-era single-call
request helpers.
"""

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

    # 1. v2-exclusive symbols must appear (at least the config composition
    # trio: line_settings_new, line_config_new, request_config_new, and
    # the terminal chip_request_lines call).
    v2_found = has_libgpiod_v2_api(generated_code)
    required_v2 = {
        "gpiod_line_settings_new",
        "gpiod_line_config_new",
        "gpiod_request_config_new",
        "gpiod_chip_request_lines",
    }
    v2_present_core = required_v2.issubset(set(v2_found))
    details.append(
        CheckDetail(
            check_name="libgpiod_v2_config_composition_used",
            passed=v2_present_core,
            expected="v2 config composition: line_settings_new + line_config_new + request_config_new + chip_request_lines",
            actual=f"found v2 symbols: {sorted(v2_found)}",
            check_type="constraint",
        )
    )

    # 2. v1-exclusive symbols must NOT appear.
    v1_found = has_libgpiod_v1_api(generated_code)
    details.append(
        CheckDetail(
            check_name="no_libgpiod_v1_api",
            passed=len(v1_found) == 0,
            expected="No deprecated v1 symbols (gpiod_chip_get_line, gpiod_line_request_output, ...)",
            actual="clean" if not v1_found else f"v1 symbols used: {v1_found}",
            check_type="constraint",
        )
    )

    # 3. No sysfs gpio fallback (/sys/class/gpio/export path).
    has_sysfs = scoped_contains(
        generated_code, "/sys/class/gpio", scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="no_sysfs_gpio_fallback",
            passed=not has_sysfs,
            expected="No /sys/class/gpio references — that interface is deprecated",
            actual="clean" if not has_sysfs else "WRONG: sysfs gpio fallback",
            check_type="constraint",
        )
    )

    # 4. gpiod_chip_open called (works in both v1 and v2 — common entry).
    has_chip_open = has_api_call(stripped, "gpiod_chip_open")
    details.append(
        CheckDetail(
            check_name="chip_opened",
            passed=has_chip_open,
            expected="gpiod_chip_open(path) called",
            actual="present" if has_chip_open else "missing",
            check_type="constraint",
        )
    )

    # 5. Consumer string set on request-config.
    has_set_consumer = has_api_call(stripped, "gpiod_request_config_set_consumer")
    details.append(
        CheckDetail(
            check_name="request_consumer_set",
            passed=has_set_consumer,
            expected="gpiod_request_config_set_consumer(...) — consumer label for kernel-side tracking",
            actual="present" if has_set_consumer else "missing",
            check_type="constraint",
        )
    )

    # 6. Direction set to OUTPUT.
    has_output_direction = scoped_contains(
        generated_code, "GPIOD_LINE_DIRECTION_OUTPUT", scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="direction_set_output",
            passed=has_output_direction,
            expected="gpiod_line_settings_set_direction(..., GPIOD_LINE_DIRECTION_OUTPUT)",
            actual="present" if has_output_direction else "missing",
            check_type="constraint",
        )
    )

    # 7. Argc count validated against 4 (program name + 3 args).
    argc_check = bool(re.search(r"argc\s*!=\s*4", stripped))
    details.append(
        CheckDetail(
            check_name="argc_validated",
            passed=argc_check,
            expected="argc != 4 validated and usage printed on mismatch",
            actual="present" if argc_check else "missing",
            check_type="constraint",
        )
    )

    # 8. Resource release: chip_close, request_release, both configs free,
    # settings free — all present.
    cleanup_apis = [
        "gpiod_chip_close",
        "gpiod_line_request_release",
        "gpiod_line_settings_free",
        "gpiod_line_config_free",
        "gpiod_request_config_free",
    ]
    missing_cleanup = [api for api in cleanup_apis if not has_api_call(stripped, api)]
    details.append(
        CheckDetail(
            check_name="all_resources_released",
            passed=len(missing_cleanup) == 0,
            expected="chip_close + request_release + line_settings_free + line_config_free + request_config_free",
            actual="complete" if not missing_cleanup else f"missing: {missing_cleanup}",
            check_type="constraint",
        )
    )

    # 9. Exit code non-zero on error — at least one ``return 1;`` or
    # ``return <nonzero>;``.
    nonzero_return = bool(re.search(r"return\s+[1-9]\d*\s*;", stripped))
    details.append(
        CheckDetail(
            check_name="nonzero_exit_on_error",
            passed=nonzero_return,
            expected="return non-zero on error (return 1; or similar)",
            actual="present" if nonzero_return else "missing",
            check_type="constraint",
        )
    )

    # 10. perror / fprintf(stderr, ...) on failure paths.
    has_perror = has_api_call(stripped, "perror") or bool(
        re.search(r"fprintf\s*\(\s*stderr", stripped)
    )
    details.append(
        CheckDetail(
            check_name="error_reported_to_stderr",
            passed=has_perror,
            expected="perror() or fprintf(stderr, ...) used on failure",
            actual="present" if has_perror else "missing",
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
