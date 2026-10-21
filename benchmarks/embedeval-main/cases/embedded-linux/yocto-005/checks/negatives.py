"""Negative tests for Yocto Out-of-Tree Kernel Module Recipe.

Reference: cases/yocto-005/reference/main.c (BitBake .bb recipe)
Checks:    cases/yocto-005/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_summary",
        "description": "Remove SUMMARY line — recipe lacks required metadata.",
        "mutation": lambda code: code.replace(
            'SUMMARY = "Out-of-tree kernel module recipe"\n', ''
        ),
        "must_fail": ["summary_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_license_line",
        "description": "Remove LICENSE declaration — recipe parse fails on missing mandatory variable.",
        "mutation": lambda code: code.replace(
            'LICENSE = "GPL-2.0-only"\n', ''
        ),
        "must_fail": ["license_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "remove_inherit_module",
        "description": "Drop 'inherit module' — recipe has no kbuild wiring, module never builds against kernel.",
        "mutation": lambda code: code.replace('inherit module\n\n', ''),
        "must_fail": ["inherit_module", "inherits_module_class"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_src_uri_block",
        "description": "Remove entire SRC_URI block — nothing to fetch; Makefile and .c source both removed.",
        "mutation": lambda code: code.replace(
            'SRC_URI = "file://mymodule.c \\\n           file://Makefile \\\n           file://COPYING \\\n           "\n\n',
            '',
        ),
        "must_fail": ["src_uri_defined", "source_files_in_src_uri"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_autoload",
        "description": "Remove KERNEL_MODULE_AUTOLOAD — module installed but not loaded at boot.",
        "mutation": lambda code: code.replace(
            'KERNEL_MODULE_AUTOLOAD += "mymodule"\n', ''
        ),
        "must_fail": ["kernel_module_autoload", "kernel_module_autoload_set"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_lic_files_chksum",
        "description": "Remove LIC_FILES_CHKSUM — recipe parse fails; hash check also drops.",
        "mutation": lambda code: code.replace(
            'LIC_FILES_CHKSUM = "file://COPYING;md5=b234ee4d69f5fce4486a80fdaf4a4263"\n',
            '',
        ),
        "must_fail": ["lic_files_chksum", "lic_chksum_has_hash"],
        "factor_id": "F3.2",
    },
    {
        "name": "replace_gpl_with_mit",
        "description": "Change LICENSE from GPL-2.0-only to MIT — kernel module loaded with MIT license taints kernel.",
        "mutation": lambda code: code.replace(
            'LICENSE = "GPL-2.0-only"', 'LICENSE = "MIT"'
        ),
        "must_fail": ["gpl_license_used"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_custom_do_compile",
        "description": "Add a custom do_compile() that bypasses module class kbuild — breaks cross-kernel integration.",
        "mutation": lambda code: code.replace(
            'KERNEL_MODULE_AUTOLOAD += "mymodule"\n',
            'KERNEL_MODULE_AUTOLOAD += "mymodule"\n\ndo_compile() {\n    make\n}\n',
        ),
        "must_fail": ["no_custom_do_compile"],
        "factor_id": "F3.2",
    },
    {
        "name": "legacy_license_name",
        "description": "Use pre-SPDX license identifier 'GPLv2' instead of SPDX 'GPL-2.0-only'.",
        "mutation": lambda code: code.replace(
            'LICENSE = "GPL-2.0-only"', 'LICENSE = "GPLv2"'
        ),
        "must_fail": ["spdx_license_format"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_deprecated_underscore_override",
        "description": "Inject FILES_${PN} underscore-override — pre-Yocto-4.0 syntax.",
        "mutation": lambda code: code.replace(
            'KERNEL_MODULE_AUTOLOAD += "mymodule"',
            'KERNEL_MODULE_AUTOLOAD += "mymodule"\nFILES_${PN} += "/lib/modules"',
        ),
        "must_fail": ["colon_override_syntax"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_hardcoded_libdir",
        "description": "Inject FILES:${PN} with hardcoded /usr/lib path — not multilib-safe.",
        "mutation": lambda code: code.replace(
            'KERNEL_MODULE_AUTOLOAD += "mymodule"',
            'KERNEL_MODULE_AUTOLOAD += "mymodule"\nFILES:${PN} += "/usr/lib/modules/myfoo.so"',
        ),
        "must_fail": ["no_hardcoded_paths"],
        "factor_id": "F3.2",
    },
    {
        "name": "require_instead_of_inherit",
        "description": "Use 'require module' instead of 'inherit module' — require is for recipe files, not classes; module class never applied.",
        "mutation": lambda code: code.replace(
            'inherit module', 'require module'
        ),
        "must_fail": ["inherit_not_require_for_class"],
        "factor_id": "F3.2",
    },
]
