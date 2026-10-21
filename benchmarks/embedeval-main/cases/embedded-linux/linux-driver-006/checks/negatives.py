"""Negative tests for Input Validation in ioctl Handler.

Reference: cases/linux-driver-006/reference/main.c
Checks:    cases/linux-driver-006/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_ioctl_header",
        "description": "Remove #include <linux/ioctl.h> — _IOW/_IOR macros undefined.",
        "mutation": lambda code: code.replace('#include <linux/ioctl.h>\n', ''),
        "must_fail": ["ioctl_header_included"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_uaccess_header",
        "description": "Remove #include <linux/uaccess.h> — copy_from_user/copy_to_user undefined.",
        "mutation": lambda code: code.replace('#include <linux/uaccess.h>\n', ''),
        "must_fail": ["uaccess_header_included"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_iow_ior_macros",
        "description": "Rename _IOW/_IOR to fictitious _IOA — ioctl command encoding broken.",
        "mutation": lambda code: code.replace('_IOW(', '_IOA(').replace(
            '_IOR(', '_IOA('
        ),
        "must_fail": ["ioctl_command_defined"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_unlocked_ioctl",
        "description": "Use deprecated .ioctl instead of .unlocked_ioctl — kernel BKL removed long ago, handler never invoked.",
        "mutation": lambda code: code.replace('unlocked_ioctl', 'ioctl'),
        "must_fail": ["unlocked_ioctl_in_fops"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_module_license",
        "description": "Remove MODULE_LICENSE — kernel refuses to load module without license tag.",
        "mutation": lambda code: code.replace('MODULE_LICENSE("GPL");\n', ''),
        "must_fail": ["module_license"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_ioc_type_check",
        "description": "Remove _IOC_TYPE validation — driver accepts commands from unrelated drivers (security bug).",
        "mutation": lambda code: code.replace(
            '\tif (_IOC_TYPE(cmd) != IOCTL_MAGIC)\n\t\treturn -ENOTTY;\n\n',
            '',
        ),
        "must_fail": ["ioc_type_validated"],
        "factor_id": "F5.2",
    },
    {
        "name": "drop_ioc_nr_check",
        "description": "Remove _IOC_NR range check — unbounded command numbers accepted.",
        "mutation": lambda code: code.replace(
            '\tif (_IOC_NR(cmd) >= IOCTL_MAX_NR)\n\t\treturn -ENOTTY;\n\n',
            '',
        ),
        "must_fail": ["ioc_nr_range_checked"],
        "factor_id": "F5.2",
    },
    {
        "name": "copy_from_user_to_memcpy",
        "description": "Use memcpy() instead of copy_from_user() — bypasses user pointer validation (kernel oops or security bug).",
        "mutation": lambda code: code.replace('copy_from_user', 'memcpy'),
        "must_fail": ["copy_from_user_for_ioctl_arg"],
        "factor_id": "F5.2",
    },
    {
        "name": "enotty_to_einval",
        "description": "Return -EINVAL instead of -ENOTTY for unknown commands — wrong errno convention, tools misinterpret.",
        "mutation": lambda code: code.replace('ENOTTY', 'EINVAL'),
        "must_fail": ["enotty_for_invalid_cmd"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_raw_user_deref",
        "description": "Introduce a raw dereference of the user-space arg pointer — classic kernel security flaw.",
        "mutation": lambda code: code.replace(
            'stored_arg = karg;',
            'stored_arg = *(struct ioctl_arg *)arg;',
        ),
        "must_fail": ["no_raw_user_pointer_deref"],
        "factor_id": "F5.2",
    },
    {
        "name": "efault_to_eio",
        "description": "Return -EIO instead of -EFAULT on copy failure — wrong errno for user-space copy error.",
        "mutation": lambda code: code.replace('EFAULT', 'EIO'),
        "must_fail": ["efault_on_copy_failure"],
        "factor_id": "F3.2",
    },
    {
        "name": "remove_init_error_cleanup",
        "description": "Drop cleanup calls from both init error paths — resource leaks on probe failure.",
        "mutation": lambda code: code.replace(
            '\tif (ret < 0) {\n\t\tunregister_chrdev_region(dev_num, 1);\n\t\treturn ret;\n\t}',
            '\tif (ret < 0)\n\t\treturn ret;',
        ).replace(
            '\tif (IS_ERR(dev_class)) {\n\t\tcdev_del(&my_cdev);\n\t\tunregister_chrdev_region(dev_num, 1);\n\t\treturn PTR_ERR(dev_class);\n\t}',
            '\tif (IS_ERR(dev_class))\n\t\treturn PTR_ERR(dev_class);',
        ),
        "must_fail": ["init_error_path_cleanup"],
        "factor_id": "F4.1",
    },
    {
        "name": "inject_zephyr_k_sleep",
        "description": "Inject Zephyr k_sleep — cross-RTOS contamination in Linux ioctl driver.",
        "mutation": lambda code: code.replace(
            'stored_arg = karg;',
            'k_sleep(K_MSEC(1));\n\t\tstored_arg = karg;',
        ),
        "must_fail": ["no_zephyr_apis"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_stm32_hal_gpio",
        "description": "Inject STM32 HAL_GPIO_WritePin — cross-platform contamination in Linux ioctl driver.",
        "mutation": lambda code: code.replace(
            'return 0;\n}\n\nstatic const struct file_operations fops',
            'HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_SET);\n\treturn 0;\n}\n\nstatic const struct file_operations fops',
        ),
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F5.1",
    },
]
