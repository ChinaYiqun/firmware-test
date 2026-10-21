"""Negative tests for Interrupt-Driven Character Device.

Reference: cases/linux-driver-004/reference/main.c
Checks:    cases/linux-driver-004/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_module_header",
        "description": "Remove #include <linux/module.h> — module macros undefined.",
        "mutation": lambda code: code.replace('#include <linux/module.h>\n', ''),
        "must_fail": ["module_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_interrupt_header",
        "description": "Remove #include <linux/interrupt.h> — IRQ types/request_irq undefined.",
        "mutation": lambda code: code.replace('#include <linux/interrupt.h>\n', ''),
        "must_fail": ["interrupt_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_wait_header",
        "description": "Remove #include <linux/wait.h> — waitqueue primitives undefined.",
        "mutation": lambda code: code.replace('#include <linux/wait.h>\n', ''),
        "must_fail": ["wait_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_spinlock_header",
        "description": "Remove #include <linux/spinlock.h> — spin_lock primitives undefined.",
        "mutation": lambda code: code.replace('#include <linux/spinlock.h>\n', ''),
        "must_fail": ["spinlock_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_request_irq",
        "description": "Use claim_irq() instead of request_irq() — fictitious API, kernel has no IRQ registered.",
        "mutation": lambda code: code.replace('request_irq', 'claim_irq'),
        "must_fail": ["request_irq_called"],
        "factor_id": "F3.1",
    },
    {
        "name": "irqreturn_t_to_int",
        "description": "Use int instead of irqreturn_t as IRQ handler return type — violates kernel IRQ contract.",
        "mutation": lambda code: code.replace('irqreturn_t', 'int'),
        "must_fail": ["irq_handler_defined"],
        "factor_id": "F3.1",
    },
    {
        "name": "mangle_waitqueue_decl",
        "description": "Rename DECLARE_WAIT_QUEUE_HEAD/init_waitqueue_head to non-kernel macros — waitqueue never initialized.",
        "mutation": lambda code: code.replace(
            'DECLARE_WAIT_QUEUE_HEAD', 'DECLARE_WQ_HEAD'
        ).replace('init_waitqueue_head', 'init_wq_head'),
        "must_fail": ["wait_queue_declared"],
        "factor_id": "F3.1",
    },
    {
        "name": "drop_free_irq",
        "description": "Remove free_irq() call in module_exit — IRQ handler leaks across module unload.",
        "mutation": lambda code: code.replace(
            '\tif (irq_num > 0)\n\t\tfree_irq(irq_num, &data_wq);\n\n',
            '',
        ),
        "must_fail": ["free_irq_in_exit"],
        "factor_id": "F4.1",
    },
    {
        "name": "spin_to_mutex_in_irq",
        "description": "Replace spinlock with mutex — mutex can sleep, fatal inside IRQ context (classic Linux bug).",
        "mutation": lambda code: code.replace(
            'spin_lock_irqsave', 'mutex_lock_irqsave'
        ).replace('spin_unlock_irqrestore', 'mutex_unlock_irqrestore')
        .replace('spin_lock_init', 'mutex_init')
        .replace('DEFINE_SPINLOCK', 'DEFINE_MUTEX'),
        "must_fail": ["spinlock_in_irq_handler"],
        "factor_id": "F2.1",
    },
    {
        "name": "wait_event_to_timeout",
        "description": "Use wait_event_timeout instead of wait_event_interruptible — different blocking semantics.",
        "mutation": lambda code: code.replace(
            'wait_event_interruptible', 'wait_event_timeout'
        ),
        "must_fail": ["wait_event_interruptible_in_read"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_wake_up",
        "description": "Replace wake_up_interruptible with wake_up_anyone — fictitious API; reader never unblocks.",
        "mutation": lambda code: code.replace(
            'wake_up_interruptible', 'wake_up_anyone'
        ),
        "must_fail": ["wake_up_interruptible_in_handler"],
        "factor_id": "F3.1",
    },
    {
        "name": "irq_handled_to_none",
        "description": "Return IRQ_NONE instead of IRQ_HANDLED — kernel thinks IRQ was spurious, may disable line.",
        "mutation": lambda code: code.replace(
            'return IRQ_HANDLED;', 'return IRQ_NONE;'
        ),
        "must_fail": ["irq_handled_returned"],
        "factor_id": "F2.2",
    },
    {
        "name": "copy_to_user_to_memcpy",
        "description": "Use memcpy() instead of copy_to_user() for kernel→user transfer — security bug (bypasses access checks).",
        "mutation": lambda code: code.replace('copy_to_user', 'memcpy'),
        "must_fail": ["copy_to_user_in_read"],
        "factor_id": "F5.2",
    },
    {
        "name": "remove_init_error_cleanup",
        "description": "Drop cleanup calls from both init error-return paths — resource leaks when probe fails mid-init.",
        "mutation": lambda code: code.replace(
            '\tif (ret < 0) {\n\t\tunregister_chrdev_region(dev_num, 1);\n\t\treturn ret;\n\t}',
            '\tif (ret < 0)\n\t\treturn ret;',
        ).replace(
            '\t\tif (ret < 0) {\n\t\t\tcdev_del(&my_cdev);\n\t\t\tunregister_chrdev_region(dev_num, 1);\n\t\t\treturn ret;\n\t\t}',
            '\t\tif (ret < 0)\n\t\t\treturn ret;',
        ),
        "must_fail": ["init_error_path_cleanup"],
        "factor_id": "F4.1",
    },
    {
        "name": "inject_zephyr_k_sleep",
        "description": "Inject Zephyr k_sleep() call — cross-RTOS contamination in Linux kernel driver.",
        "mutation": lambda code: code.replace(
            'wake_up_interruptible(&data_wq);',
            'k_sleep(K_MSEC(1));\n\twake_up_interruptible(&data_wq);',
        ),
        "must_fail": ["no_zephyr_apis"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_stm32_hal_gpio",
        "description": "Inject STM32 HAL_GPIO_WritePin — cross-platform contamination in Linux kernel driver.",
        "mutation": lambda code: code.replace(
            'return IRQ_HANDLED;',
            'HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_SET);\n\treturn IRQ_HANDLED;',
        ),
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F5.1",
    },
]
