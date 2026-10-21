"""Negative tests for linux-userspace-001 (libgpiod v2 CLI)."""

import re


def _swap_v2_settings_to_v1_output_request(code: str) -> str:
    """Rewrite to the v1 pattern: chip_get_line + line_request_output.
    Drops v2 config composition entirely."""
    return code.replace(
        "settings = gpiod_line_settings_new();",
        "line = gpiod_chip_get_line(chip, offset);",
    ).replace(
        "gpiod_line_settings_new", "gpiod_chip_get_line_v1_stub"
    ).replace(
        "gpiod_chip_request_lines",
        "gpiod_line_request_output",
    )


def _drop_line_settings_new(code: str) -> str:
    return re.sub(
        r"\n\s*settings\s*=\s*gpiod_line_settings_new\(\);[^\n]*\n"
        r"\s*if\s*\(!settings\).*?goto [^\n]*\n",
        "\n",
        code,
        flags=re.DOTALL,
        count=1,
    )


def _drop_line_config_new(code: str) -> str:
    return re.sub(
        r"\n\s*line_cfg\s*=\s*gpiod_line_config_new\(\);[^\n]*\n"
        r"\s*if\s*\(!line_cfg\).*?goto [^\n]*\n",
        "\n",
        code,
        flags=re.DOTALL,
        count=1,
    )


def _drop_request_config_new(code: str) -> str:
    return re.sub(
        r"\n\s*req_cfg\s*=\s*gpiod_request_config_new\(\);[^\n]*\n"
        r"\s*if\s*\(!req_cfg\).*?goto [^\n]*\n",
        "\n",
        code,
        flags=re.DOTALL,
        count=1,
    )


def _drop_chip_request_lines(code: str) -> str:
    return re.sub(
        r"\n\s*request\s*=\s*gpiod_chip_request_lines[^;]*;", "", code, count=1
    )


def _drop_settings_free(code: str) -> str:
    return code.replace("gpiod_line_settings_free(settings);\n", "")


def _drop_line_config_free(code: str) -> str:
    return code.replace("gpiod_line_config_free(line_cfg);\n", "")


def _drop_request_release(code: str) -> str:
    return code.replace("gpiod_line_request_release(request);\n", "")


def _drop_chip_close(code: str) -> str:
    return code.replace("gpiod_chip_close(chip);\n", "")


def _sysfs_gpio_fallback(code: str) -> str:
    """Inject a sysfs-gpio write path — the deprecated interface."""
    return code.replace(
        "chip = gpiod_chip_open(argv[1]);",
        (
            'FILE *exp = fopen("/sys/class/gpio/export", "w");\n'
            '\tif (exp) { fprintf(exp, "%d", offset); fclose(exp); }\n'
            '\tchip = gpiod_chip_open(argv[1]);'
        ),
    )


def _drop_argc_validation(code: str) -> str:
    return re.sub(
        r"if\s*\(argc\s*!=\s*4\)\s*\{[^}]*\}\n", "", code, count=1
    )


def _drop_direction_output(code: str) -> str:
    return code.replace(
        "GPIOD_LINE_DIRECTION_OUTPUT", "GPIOD_LINE_DIRECTION_INPUT"
    )


NEGATIVES = [
    {
        "name": "use_v1_api_instead_of_v2",
        "description": "Swap v2 config composition for v1 chip_get_line + line_request_output — the deprecated 2017-era API.",
        "mutation": _swap_v2_settings_to_v1_output_request,
        "must_fail": [
            "libgpiod_v2_config_composition_used",
            "no_libgpiod_v1_api",
        ],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_line_settings_new",
        "description": "Remove gpiod_line_settings_new — the settings handle is never allocated; subsequent set_direction / set_output_value calls dereference NULL.",
        "mutation": _drop_line_settings_new,
        "must_fail": ["libgpiod_v2_config_composition_used"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_line_config_new",
        "description": "Remove gpiod_line_config_new — cannot bind settings to line offset.",
        "mutation": _drop_line_config_new,
        "must_fail": ["libgpiod_v2_config_composition_used"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_request_config_new",
        "description": "Remove gpiod_request_config_new — the req_cfg handle is NULL at chip_request_lines time.",
        "mutation": _drop_request_config_new,
        "must_fail": ["libgpiod_v2_config_composition_used"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_chip_request_lines",
        "description": "Remove gpiod_chip_request_lines — line never actually requested.",
        "mutation": _drop_chip_request_lines,
        "must_fail": ["libgpiod_v2_config_composition_used"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_settings_free",
        "description": "Omit gpiod_line_settings_free — settings object leak.",
        "mutation": _drop_settings_free,
        "must_fail": ["all_resources_released"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_line_config_free",
        "description": "Omit gpiod_line_config_free — config object leak.",
        "mutation": _drop_line_config_free,
        "must_fail": ["all_resources_released"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_request_release",
        "description": "Omit gpiod_line_request_release — request stays pinned until process exits; other processes cannot request the line.",
        "mutation": _drop_request_release,
        "must_fail": ["all_resources_released"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_chip_close",
        "description": "Omit gpiod_chip_close — chip FD leaks.",
        "mutation": _drop_chip_close,
        "must_fail": ["all_resources_released"],
        "factor_id": "E3.1",
    },
    {
        "name": "sysfs_gpio_fallback",
        "description": "Inject /sys/class/gpio/export fallback — the deprecated pre-2016 interface. Should be entirely absent on kernel 5.15 without CONFIG_GPIO_SYSFS.",
        "mutation": _sysfs_gpio_fallback,
        "must_fail": ["no_sysfs_gpio_fallback"],
        "factor_id": "F4.2",
    },
    {
        "name": "drop_argc_validation",
        "description": "Skip argc sanity check — program segfaults on missing args.",
        "mutation": _drop_argc_validation,
        "must_fail": ["argc_validated"],
        "factor_id": "E6.1",
    },
    {
        "name": "direction_input_not_output",
        "description": "Direction set to INPUT instead of OUTPUT — write-intent request but read-only line.",
        "mutation": _drop_direction_output,
        "must_fail": ["direction_set_output"],
        "factor_id": "A1.1",
    },
]
