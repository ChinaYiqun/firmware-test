"""Negative tests for Yocto Recipe with CMake Build System.

Reference: cases/yocto-002/reference/main.c (BitBake .bb recipe)
Checks:    cases/yocto-002/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_srcrev_with_git_src",
        "description": "Remove SRCREV while keeping git:// SRC_URI — Yocto build fails without SRCREV for git fetcher.",
        "mutation": lambda code: code.replace(
            'SRCREV = "abc123def456abc123def456abc123def456abc1"\n\n', ''
        ),
        "must_fail": ["srcrev_present_for_git", "srcrev_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "strip_d_prefix_from_install",
        "description": "Drop all ${D} prefixes — installs land in final rootfs path instead of staging.",
        "mutation": lambda code: code.replace('${D}', ''),
        "must_fail": ["install_uses_d_prefix"],
        "factor_id": "F3.2",
    },
    {
        "name": "legacy_license_name",
        "description": "Use pre-SPDX license identifier 'GPLv2' instead of SPDX 'GPL-2.0-only'.",
        "mutation": lambda code: code.replace(
            'LICENSE = "MIT"', 'LICENSE = "GPLv2"'
        ),
        "must_fail": ["spdx_license_format"],
        "factor_id": "F3.2",
    },
    {
        "name": "deprecated_underscore_override",
        "description": "Inject RDEPENDS_${PN} using pre-Yocto-4.0 underscore override syntax.",
        "mutation": lambda code: code.replace(
            'EXTRA_OECMAKE = "-DBUILD_TESTS=OFF"\n',
            'EXTRA_OECMAKE = "-DBUILD_TESTS=OFF"\nRDEPENDS_${PN} = "bash"\n',
        ),
        "must_fail": ["colon_override_syntax"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_install_d",
        "description": "Remove 'install -d' — 'install -m' runs without creating the target directory.",
        "mutation": lambda code: code.replace(
            '    install -d ${D}${bindir}\n', ''
        ),
        "must_fail": ["install_d_before_install_m"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_summary",
        "description": "Remove SUMMARY line — recipe lacks required metadata.",
        "mutation": lambda code: code.replace(
            'SUMMARY = "CMake-based application built with Yocto cmake class"\n',
            '',
        ),
        "must_fail": ["summary_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_license_line",
        "description": "Remove LICENSE declaration — recipe parse fails on missing mandatory variable.",
        "mutation": lambda code: code.replace('LICENSE = "MIT"\n', ''),
        "must_fail": ["license_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_lic_files_chksum",
        "description": "Remove LIC_FILES_CHKSUM — recipe parse fails; also strips the md5=/sha256= hash.",
        "mutation": lambda code: code.replace(
            'LIC_FILES_CHKSUM = "file://COPYING;md5=838c366f69b72c5df05c96dff79b35f2"\n',
            '',
        ),
        "must_fail": ["lic_files_chksum", "lic_chksum_has_hash"],
        "factor_id": "F3.2",
    },
    {
        "name": "replace_inherit_with_manual_build",
        "description": "Replace 'inherit cmake' with manual do_compile() running cmake by hand — bypasses class.",
        "mutation": lambda code: code.replace(
            'inherit cmake',
            'do_compile() {\n    cmake ${S} -DBUILD_TESTS=OFF\n    make\n}',
        ),
        "must_fail": ["inherit_cmake", "inherits_cmake_class"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_src_uri",
        "description": "Remove SRC_URI — recipe has nothing to fetch.",
        "mutation": lambda code: code.replace(
            'SRC_URI = "git://github.com/example/myapp.git;protocol=https;branch=main"\n\n',
            '',
        ),
        "must_fail": ["src_uri_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_s_variable",
        "description": "Remove S assignment — Yocto defaults to ${WORKDIR}/${BPN}-${PV} which will not match git fetch layout.",
        "mutation": lambda code: code.replace('S = "${WORKDIR}/git"\n\n', ''),
        "must_fail": ["s_variable_set"],
        "factor_id": "F3.2",
    },
    {
        "name": "hardcode_bindir",
        "description": "Replace ${bindir} with hardcoded /usr/bin — not multilib-safe.",
        "mutation": lambda code: code.replace('${bindir}', '/usr/bin'),
        "must_fail": ["uses_bindir_variable"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_do_install_block",
        "description": "Remove entire do_install() block — recipe produces no installable artifacts.",
        "mutation": lambda code: code.replace(
            'do_install() {\n    install -d ${D}${bindir}\n    install -m 0755 ${B}/myapp ${D}${bindir}/myapp\n}\n',
            '',
        ),
        "must_fail": ["do_install_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_hardcoded_libdir",
        "description": "Inject FILES:${PN} with hardcoded /usr/lib path instead of ${libdir} — not multilib-safe.",
        "mutation": lambda code: code.replace(
            'EXTRA_OECMAKE = "-DBUILD_TESTS=OFF"\n',
            'EXTRA_OECMAKE = "-DBUILD_TESTS=OFF"\nFILES:${PN} = "/usr/lib/myapp.so"\n',
        ),
        "must_fail": ["no_hardcoded_libdir"],
        "factor_id": "F3.2",
    },
]
