"""Negative tests for Yocto Custom Image Recipe.

Reference: cases/yocto-007/reference/main.c (BitBake .bb image recipe)
Checks:    cases/yocto-007/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "wrong_inherit_class",
        "description": "Use 'inherit recipe-package' instead of 'inherit core-image' — not an image recipe.",
        "mutation": lambda code: code.replace(
            'inherit core-image', 'inherit recipe-package'
        ),
        "must_fail": ["inherits_core_image", "inherits_correct_image_class"],
        "factor_id": "F3.2",
    },
    {
        "name": "rename_image_install",
        "description": "Rename IMAGE_INSTALL to IMG_INSTALL — fictitious variable; no packages installed to image.",
        "mutation": lambda code: code.replace('IMAGE_INSTALL', 'IMG_INSTALL'),
        "must_fail": ["image_install_defined", "image_install_uses_append"],
        "factor_id": "F3.2",
    },
    {
        "name": "rename_image_features",
        "description": "Rename IMAGE_FEATURES to IMG_FEATURES — fictitious variable; ssh/debug-tweaks features not applied.",
        "mutation": lambda code: code.replace(
            'IMAGE_FEATURES', 'IMG_FEATURES'
        ),
        "must_fail": ["image_features_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_summary",
        "description": "Remove SUMMARY line — image lacks required metadata.",
        "mutation": lambda code: code.replace(
            'SUMMARY = "Custom embedded Linux image"\n', ''
        ),
        "must_fail": ["summary_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_do_compile",
        "description": "Add do_compile() block to image recipe — image recipes do not compile anything; build warnings.",
        "mutation": lambda code: code.replace(
            'IMAGE_ROOTFS_SIZE ?= "65536"\n',
            'IMAGE_ROOTFS_SIZE ?= "65536"\n\ndo_compile() {\n    true\n}\n',
        ),
        "must_fail": ["no_do_compile_in_image_recipe"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_do_install",
        "description": "Add do_install() block to image recipe — image recipes do not install like packages.",
        "mutation": lambda code: code.replace(
            'IMAGE_ROOTFS_SIZE ?= "65536"\n',
            'IMAGE_ROOTFS_SIZE ?= "65536"\n\ndo_install() {\n    true\n}\n',
        ),
        "must_fail": ["no_do_install_in_image_recipe"],
        "factor_id": "F5.1",
    },
    {
        "name": "strip_all_packages",
        "description": "Replace IMAGE_INSTALL package list and scrub 'openssh' from IMAGE_FEATURES — no identifiable packages in image.",
        "mutation": lambda code: code.replace(
            'IMAGE_INSTALL += " \\\n    packagegroup-core-boot \\\n    busybox \\\n    openssh \\\n    openssh-sftp-server \\\n    "\n',
            'IMAGE_INSTALL += " foo bar baz "\n',
        ).replace(
            'IMAGE_FEATURES += "ssh-server-openssh debug-tweaks"',
            'IMAGE_FEATURES += "ssh-server debug-tweaks"',
        ),
        "must_fail": ["packages_listed"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_legacy_license_name",
        "description": "Add LICENSE = 'GPLv2' using pre-SPDX identifier — should be GPL-2.0-only under SPDX rules.",
        "mutation": lambda code: code.replace(
            'SUMMARY = ', 'LICENSE = "GPLv2"\nSUMMARY = '
        ),
        "must_fail": ["spdx_license_format"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_deprecated_append_override",
        "description": "Add IMAGE_INSTALL_append (underscore syntax) — deprecated since Yocto 4.0.",
        "mutation": lambda code: code.replace(
            'IMAGE_ROOTFS_SIZE ?= "65536"\n',
            'IMAGE_ROOTFS_SIZE ?= "65536"\nIMAGE_INSTALL_append = " extra-pkg"\n',
        ),
        "must_fail": ["colon_override_syntax"],
        "factor_id": "F3.2",
    },
    {
        "name": "require_instead_of_inherit",
        "description": "Use 'require core-image' instead of 'inherit core-image' — require is for recipes, class never applied.",
        "mutation": lambda code: code.replace(
            'inherit core-image', 'require core-image'
        ),
        "must_fail": ["inherit_not_require_for_class"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_hardcoded_usr_path",
        "description": "Mention /usr/bin path in DESCRIPTION — hardcoded path in image recipe (should use package names).",
        "mutation": lambda code: code.replace(
            'DESCRIPTION = "Minimal embedded image with SSH and development tools"',
            'DESCRIPTION = "Minimal image, /usr/bin tools included"',
        ),
        "must_fail": ["no_hardcoded_paths_in_image"],
        "factor_id": "F3.2",
    },
    {
        "name": "rootfs_size_hard_assign",
        "description": "Change IMAGE_ROOTFS_SIZE ?= to IMAGE_ROOTFS_SIZE = (hard assign) — overrides board-specific value.",
        "mutation": lambda code: code.replace(
            'IMAGE_ROOTFS_SIZE ?= "65536"',
            'IMAGE_ROOTFS_SIZE = "65536"',
        ),
        "must_fail": ["rootfs_size_uses_weak_assignment"],
        "factor_id": "F3.2",
    },
]
