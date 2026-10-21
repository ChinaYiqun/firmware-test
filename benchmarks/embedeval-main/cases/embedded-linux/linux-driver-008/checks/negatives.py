"""Negative tests for Proc/Sysfs File for Driver Debug Info.

Reference: cases/linux-driver-008/reference/main.c
Checks:    cases/linux-driver-008/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_proc_fs_header",
        "description": "Remove #include <linux/proc_fs.h> — proc API undefined.",
        "mutation": lambda code: code.replace('#include <linux/proc_fs.h>\n', ''),
        "must_fail": ["proc_fs_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_seq_file_header",
        "description": "Remove #include <linux/seq_file.h> — seq_file API undefined.",
        "mutation": lambda code: code.replace('#include <linux/seq_file.h>\n', ''),
        "must_fail": ["seq_file_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_proc_ops_to_file_ops",
        "description": "Use file_operations instead of proc_ops — legacy API removed in kernel 5.6+.",
        "mutation": lambda code: code.replace('proc_ops', 'file_ops'),
        "must_fail": ["proc_ops_struct_used"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_proc_create",
        "description": "Use fictitious proc_make instead of proc_create — /proc entry never created.",
        "mutation": lambda code: code.replace('proc_create', 'proc_make'),
        "must_fail": ["proc_create_called"],
        "factor_id": "F3.1",
    },
    {
        "name": "seq_printf_to_sprintf",
        "description": "Use sprintf instead of seq_printf — no seq_file buffer growth, output truncated to PAGE_SIZE.",
        "mutation": lambda code: code.replace('seq_printf', 'sprintf'),
        "must_fail": ["seq_printf_used", "seq_printf_not_raw_sprintf"],
        "factor_id": "F5.2",
    },
    {
        "name": "rename_remove_proc_entry",
        "description": "Use fictitious remove_proc instead of remove_proc_entry — /proc entry leaks across module unload.",
        "mutation": lambda code: code.replace(
            'remove_proc_entry', 'remove_proc'
        ),
        "must_fail": ["proc_removed_on_exit"],
        "factor_id": "F4.1",
    },
    {
        "name": "rename_single_open",
        "description": "Use simple_open instead of single_open — incompatible with seq_read.",
        "mutation": lambda code: code.replace('single_open', 'simple_open'),
        "must_fail": ["single_open_used"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_seq_read",
        "description": "Assign file_read (fictitious) instead of seq_read to proc_read — proc output never formatted through seq_file.",
        "mutation": lambda code: code.replace('seq_read', 'file_read'),
        "must_fail": ["seq_read_in_proc_ops"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_proc_create_null_check_block",
        "description": "Remove the if(!entry){...} block after proc_create — NULL return silently ignored; init returns 0 on failure.",
        "mutation": lambda code: code.replace(
            '\tif (!entry) {\n\t\tpr_err("Failed to create /proc/%s\\n", PROC_NAME);\n\t\treturn -ENOMEM;\n\t}\n\n',
            '',
        ),
        "must_fail": [
            "proc_create_result_checked",
            "proc_create_failure_returns_error",
        ],
        "factor_id": "F4.1",
    },
    {
        "name": "rename_seq_file_type",
        "description": "Rename struct seq_file to sq_file — show callback signature broken, kernel rejects proc_ops.",
        "mutation": lambda code: code.replace('seq_file', 'sq_file'),
        "must_fail": ["show_function_uses_seq_file"],
        "factor_id": "F3.1",
    },
    {
        "name": "inject_zephyr_k_sleep",
        "description": "Inject Zephyr k_sleep — cross-RTOS contamination in Linux proc driver.",
        "mutation": lambda code: code.replace(
            'call_count++;',
            'k_sleep(K_MSEC(1));\n\tcall_count++;',
        ),
        "must_fail": ["no_zephyr_apis"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_stm32_hal_gpio",
        "description": "Inject STM32 HAL_GPIO_WritePin — cross-platform contamination in Linux proc driver.",
        "mutation": lambda code: code.replace(
            'return 0;\n}\n\nstatic int my_open',
            'HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_SET);\n\treturn 0;\n}\n\nstatic int my_open',
        ),
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F5.1",
    },
]
