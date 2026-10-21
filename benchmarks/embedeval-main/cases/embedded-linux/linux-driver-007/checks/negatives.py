"""Negative tests for DMA-Coherent Buffer Allocation.

Reference: cases/linux-driver-007/reference/main.c
Checks:    cases/linux-driver-007/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_dma_mapping_header",
        "description": "Remove #include <linux/dma-mapping.h> — DMA API undefined.",
        "mutation": lambda code: code.replace(
            '#include <linux/dma-mapping.h>\n', ''
        ),
        "must_fail": ["dma_mapping_header"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_dma_addr_t",
        "description": "Use phys_addr_t (wrong for DMA handle) instead of dma_addr_t — wrong type on 32-bit/64-bit systems with different DMA address widths.",
        "mutation": lambda code: code.replace('dma_addr_t', 'phys_addr_t'),
        "must_fail": ["dma_addr_t_used"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_dma_alloc_coherent",
        "description": "Rename dma_alloc_coherent to fictitious dma_alloc_chr — buffer never allocated.",
        "mutation": lambda code: code.replace(
            'dma_alloc_coherent', 'dma_alloc_chr'
        ),
        "must_fail": ["dma_alloc_coherent_used", "dma_alloc_free_balanced"],
        "factor_id": "F3.1",
    },
    {
        "name": "rename_dma_free_coherent",
        "description": "Rename dma_free_coherent to fictitious dma_release — DMA memory leaks on module unload.",
        "mutation": lambda code: code.replace(
            'dma_free_coherent', 'dma_release'
        ),
        "must_fail": ["dma_free_coherent_in_cleanup"],
        "factor_id": "F4.1",
    },
    {
        "name": "gfp_kernel_to_atomic",
        "description": "Use GFP_ATOMIC instead of GFP_KERNEL — inappropriate for probe path (may exhaust atomic pool).",
        "mutation": lambda code: code.replace('GFP_KERNEL', 'GFP_ATOMIC'),
        "must_fail": ["gfp_kernel_flags"],
        "factor_id": "F2.1",
    },
    {
        "name": "use_userspace_malloc",
        "description": "Replace dma_alloc_coherent with userspace malloc() — hallucination, malloc() doesn't exist in kernel.",
        "mutation": lambda code: code.replace('dma_alloc_coherent', 'malloc'),
        "must_fail": ["no_userspace_malloc"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_vmalloc_for_dma",
        "description": "Add vmalloc() call for DMA buffer — vmalloc memory is not physically contiguous, unsafe for DMA.",
        "mutation": lambda code: code.replace(
            'dev->size = DMA_BUF_SIZE;',
            'dev->size = DMA_BUF_SIZE;\n\tvoid *extra_buf = vmalloc(DMA_BUF_SIZE);',
        ),
        "must_fail": ["no_vmalloc_for_dma"],
        "factor_id": "F2.1",
    },
    {
        "name": "kmalloc_instead_of_dma_alloc",
        "description": "Use kmalloc() instead of dma_alloc_coherent (and purge the API name from pr_err) — not DMA-coherent, cache sync required manually.",
        "mutation": lambda code: code.replace(
            'dma_alloc_coherent(&pdev->dev, dev->size,\n\t\t\t\t\t    &dev->dma_handle, GFP_KERNEL)',
            'kmalloc(dev->size, GFP_KERNEL)',
        ).replace('dma_alloc_coherent failed', 'kmalloc failed'),
        "must_fail": ["no_kmalloc_instead_of_dma_alloc"],
        "factor_id": "F2.1",
    },
    {
        "name": "enomem_to_eio",
        "description": "Return -EIO instead of -ENOMEM on allocation failure — wrong errno for OOM.",
        "mutation": lambda code: code.replace('ENOMEM', 'EIO'),
        "must_fail": ["enomem_on_alloc_failure"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_drvdata_and_devm",
        "description": "Remove dev_set_drvdata and drop devm_ prefix on kzalloc — no per-device state; leaks on probe failure.",
        "mutation": lambda code: code.replace(
            '\tdev_set_drvdata(&pdev->dev, dev);\n', ''
        ).replace(
            'devm_kzalloc(&pdev->dev, sizeof(*dev), GFP_KERNEL)',
            'kzalloc(sizeof(*dev), GFP_KERNEL)',
        ),
        "must_fail": ["per_device_data_stored"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_dma_alloc_error_check",
        "description": "Remove the !virt_addr error-return block after dma_alloc_coherent — driver uses NULL pointer on allocation failure.",
        "mutation": lambda code: code.replace(
            '\tif (!dev->virt_addr) {\n\t\tpr_err("%s: dma_alloc_coherent failed\\n", DRIVER_NAME);\n\t\treturn -ENOMEM;\n\t}\n\n',
            '',
        ),
        "must_fail": ["dma_alloc_error_handled"],
        "factor_id": "F4.1",
    },
    {
        "name": "inject_zephyr_k_sleep",
        "description": "Inject Zephyr k_sleep — cross-RTOS contamination in Linux DMA driver.",
        "mutation": lambda code: code.replace(
            'dev_set_drvdata(&pdev->dev, dev);',
            'k_sleep(K_MSEC(1));\n\tdev_set_drvdata(&pdev->dev, dev);',
        ),
        "must_fail": ["no_zephyr_apis"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_stm32_hal_gpio",
        "description": "Inject STM32 HAL_GPIO_WritePin — cross-platform contamination in Linux DMA driver.",
        "mutation": lambda code: code.replace(
            'return 0;\n}\n\nstatic int dmabuf_remove',
            'HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_SET);\n\treturn 0;\n}\n\nstatic int dmabuf_remove',
        ),
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F5.1",
    },
]
