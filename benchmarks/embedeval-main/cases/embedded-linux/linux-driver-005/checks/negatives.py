"""Negative tests for Sysfs Attribute Interface.

Reference: cases/linux-driver-005/reference/main.c
Checks:    cases/linux-driver-005/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_module_header",
        "description": "Remove #include <linux/module.h>.",
        "mutation": lambda code: code.replace('#include <linux/module.h>\n', ''),
        "must_fail": ["module_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_sysfs_header",
        "description": "Remove #include <linux/sysfs.h>.",
        "mutation": lambda code: code.replace('#include <linux/sysfs.h>\n', ''),
        "must_fail": ["sysfs_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_module_license",
        "description": "Remove MODULE_LICENSE — kernel refuses module load without license tag.",
        "mutation": lambda code: code.replace('MODULE_LICENSE("GPL");\n', ''),
        "must_fail": ["module_license"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_device_attr_rw",
        "description": "Replace DEVICE_ATTR_RW with fictitious DEVICE_ATTR_RX — macro doesn't exist.",
        "mutation": lambda code: code.replace('DEVICE_ATTR_RW', 'DEVICE_ATTR_RX'),
        "must_fail": ["device_attr_rw_macro"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_show_suffix",
        "description": "Rename *_show to *_read — sysfs subsystem won't wire up the show callback.",
        "mutation": lambda code: code.replace('_show', '_read'),
        "must_fail": ["show_function"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_store_suffix",
        "description": "Rename *_store to *_write — sysfs subsystem won't wire up the store callback.",
        "mutation": lambda code: code.replace('_store', '_write'),
        "must_fail": ["store_function"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_attribute_group",
        "description": "Rename attribute_group struct to attr_set — sysfs API no longer matches; unwires attribute registration.",
        "mutation": lambda code: code.replace('attribute_group', 'attr_set'),
        "must_fail": ["attribute_group_defined", "attr_group_used_in_create"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_sysfs_create_group",
        "description": "Use fictitious sysfs_make_group — attributes never created under /sys/.",
        "mutation": lambda code: code.replace(
            'sysfs_create_group', 'sysfs_make_group'
        ),
        "must_fail": ["sysfs_create_group_called"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_sysfs_remove_group",
        "description": "Remove sysfs_remove_group in .remove — attributes leak across module unload.",
        "mutation": lambda code: code.replace(
            '\tsysfs_remove_group(&pdev->dev.kobj, &mydev_attr_group);\n', ''
        ),
        "must_fail": ["sysfs_remove_group_in_remove"],
        "factor_id": "F4.1",
    },
    {
        "name": "sysfs_emit_to_sprintf",
        "description": "Use raw sprintf instead of sysfs_emit — no PAGE_SIZE bounds check, buffer overflow possible.",
        "mutation": lambda code: code.replace('sysfs_emit', 'sprintf'),
        "must_fail": ["sysfs_emit_in_show"],
        "factor_id": "F5.2",
    },
    {
        "name": "kstrtoint_to_sscanf",
        "description": "Use sscanf instead of kstrtoint — ignores parse errors, accepts malformed input.",
        "mutation": lambda code: code.replace('kstrtoint', 'sscanf'),
        "must_fail": ["kstrtoint_in_store"],
        "factor_id": "F5.2",
    },
    {
        "name": "store_returns_zero",
        "description": "Return 0 instead of count — userspace write() loops forever (0 bytes consumed).",
        "mutation": lambda code: code.replace('return count;', 'return 0;'),
        "must_fail": ["store_returns_count"],
        "factor_id": "F2.2",
    },
    {
        "name": "strip_newlines",
        "description": "Remove all backslash-n from strings — sysfs convention violated (no trailing newline on read).",
        "mutation": lambda code: code.replace('\\n', ''),
        "must_fail": ["show_newline_terminated"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_create_group_error_check",
        "description": "Drop 'if (ret) return ret;' after sysfs_create_group and rename store's ret→err — failure silently ignored.",
        "mutation": lambda code: code.replace(
            '\tif (ret)\n\t\treturn ret;\n', ''
        ).replace(
            'int val;\n\tint ret;\n\n\tret = kstrtoint',
            'int val;\n\tint err;\n\n\terr = kstrtoint',
        ).replace(
            'if (ret)\n\t\treturn -EINVAL;',
            'if (err)\n\t\treturn -EINVAL;',
        ),
        "must_fail": ["sysfs_create_group_error_handled"],
        "factor_id": "F4.1",
    },
    {
        "name": "inject_zephyr_k_sleep",
        "description": "Inject Zephyr k_sleep — cross-RTOS contamination in Linux sysfs driver.",
        "mutation": lambda code: code.replace(
            'dev_info(&pdev->dev, "mydev: sysfs group created\\n");',
            'k_sleep(K_MSEC(1));\n\tdev_info(&pdev->dev, "mydev: sysfs group created\\n");',
        ),
        "must_fail": ["no_zephyr_apis"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_stm32_hal_gpio",
        "description": "Inject STM32 HAL_GPIO_WritePin — cross-platform contamination in Linux sysfs driver.",
        "mutation": lambda code: code.replace(
            'return 0;\n}\n\nstatic int mydev_remove',
            'HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_SET);\n\treturn 0;\n}\n\nstatic int mydev_remove',
        ),
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F5.1",
    },
]
