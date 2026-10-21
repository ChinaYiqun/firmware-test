"""Negative tests for IIO ADC Driver Skeleton.

Reference: cases/linux-driver-003/reference/main.c
Checks:    cases/linux-driver-003/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_module_header",
        "description": "Remove #include <linux/module.h> — module macros undefined at build.",
        "mutation": lambda code: code.replace('#include <linux/module.h>\n', ''),
        "must_fail": ["module_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_iio_header",
        "description": "Remove #include <linux/iio/iio.h> — all IIO types/macros undefined.",
        "mutation": lambda code: code.replace('#include <linux/iio/iio.h>\n', ''),
        "must_fail": ["iio_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_module_license",
        "description": "Remove MODULE_LICENSE — kernel refuses to load without license tag.",
        "mutation": lambda code: code.replace('MODULE_LICENSE("GPL");\n', ''),
        "must_fail": ["module_license"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_iio_chan_spec",
        "description": "Rename struct iio_chan_spec to iio_chan_desc — type no longer recognized by IIO core.",
        "mutation": lambda code: code.replace('iio_chan_spec', 'iio_chan_desc'),
        "must_fail": ["iio_chan_spec_defined"],
        "factor_id": "F3.1",
    },
    {
        "name": "iio_voltage_to_current",
        "description": "Change IIO_VOLTAGE channel type to IIO_CURRENT — misclassifies sensor.",
        "mutation": lambda code: code.replace('IIO_VOLTAGE', 'IIO_CURRENT'),
        "must_fail": ["iio_voltage_type"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_read_raw_callback",
        "description": "Rename read_raw callback to read_data — IIO core never invokes it for sysfs reads.",
        "mutation": lambda code: code.replace('read_raw', 'read_data'),
        "must_fail": ["read_raw_callback"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_iio_info_struct",
        "description": "Rename struct iio_info type to iio_ops — ops struct no longer matches IIO driver contract.",
        "mutation": lambda code: code.replace('iio_info', 'iio_ops'),
        "must_fail": ["iio_info_struct"],
        "factor_id": "F3.1",
    },
    {
        "name": "replace_iio_val_int_with_0",
        "description": "Return raw 0 instead of IIO_VAL_INT — sysfs shows empty value to userspace.",
        "mutation": lambda code: code.replace('return IIO_VAL_INT;', 'return 0;'),
        "must_fail": ["read_raw_returns_iio_val_int"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_chan_info_raw_to_offset",
        "description": "Handle IIO_CHAN_INFO_OFFSET instead of _RAW — sysfs 'in_voltage0_raw' attribute never answered.",
        "mutation": lambda code: code.replace('IIO_CHAN_INFO_RAW', 'IIO_CHAN_INFO_OFFSET'),
        "must_fail": ["iio_chan_info_raw_handled"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_devm_prefix_on_alloc",
        "description": "Use iio_device_alloc instead of devm_iio_device_alloc — leaks on probe failure, no devres cleanup.",
        "mutation": lambda code: code.replace(
            'devm_iio_device_alloc', 'iio_device_alloc'
        ),
        "must_fail": ["devm_iio_device_alloc_used"],
        "factor_id": "F4.1",
    },
    {
        "name": "rename_register_to_setup",
        "description": "Rename iio_device_register family to iio_device_setup — device never registered with IIO core.",
        "mutation": lambda code: code.replace(
            'iio_device_register', 'iio_device_setup'
        ),
        "must_fail": ["iio_device_registered"],
        "factor_id": "F3.1",
    },
    {
        "name": "replace_arrow_info_with_priv",
        "description": "Assign iio_info struct to indio_dev->priv instead of ->info — read_raw never invoked by core.",
        "mutation": lambda code: code.replace(
            'indio_dev->info', 'indio_dev->priv'
        ).replace('.info_mask_separate', '.mask_separate'),
        "must_fail": ["iio_info_assigned"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_num_channels_assign",
        "description": "Remove num_channels assignment — IIO exports 0 channels, sysfs attributes missing.",
        "mutation": lambda code: code.replace(
            '\tindio_dev->num_channels = ARRAY_SIZE(myadc_channels);\n', ''
        ),
        "must_fail": ["num_channels_set"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_enomem_check_block",
        "description": "Remove the allocation failure check — NULL pointer deref if alloc fails.",
        "mutation": lambda code: code.replace(
            '\tif (!indio_dev)\n\t\treturn -ENOMEM;\n\n', ''
        ),
        "must_fail": ["allocation_failure_handled"],
        "factor_id": "F2.3",
    },
    {
        "name": "inject_zephyr_k_sleep",
        "description": "Inject Zephyr k_sleep() call — cross-RTOS contamination in Linux kernel driver.",
        "mutation": lambda code: code.replace(
            'indio_dev = devm_iio_device_alloc',
            'k_sleep(K_MSEC(10));\n\tindio_dev = devm_iio_device_alloc',
        ),
        "must_fail": ["no_zephyr_apis"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_stm32_hal_gpio",
        "description": "Inject STM32 HAL_GPIO_WritePin — cross-platform contamination in Linux driver.",
        "mutation": lambda code: code.replace(
            'return IIO_VAL_INT;',
            'HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_SET);\n\t\treturn IIO_VAL_INT;',
        ),
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F5.1",
    },
]
