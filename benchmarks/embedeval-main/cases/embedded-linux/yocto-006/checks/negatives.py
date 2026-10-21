"""Negative tests for Yocto Recipe with Patch Application.

Reference: cases/yocto-006/reference/main.c (BitBake .bb recipe)
Checks:    cases/yocto-006/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_patch_from_src_uri",
        "description": "Remove file://fix-build.patch from SRC_URI — patch never fetched, no patch applied by do_patch.",
        "mutation": lambda code: code.replace(
            '           file://fix-build.patch \\\n', ''
        ),
        "must_fail": ["patch_file_in_src_uri", "patch_uses_file_scheme"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_filesextrapaths",
        "description": "Remove FILESEXTRAPATHS:prepend — BitBake cannot locate the patch file in ${THISDIR}/files.",
        "mutation": lambda code: code.replace(
            'FILESEXTRAPATHS:prepend := "${THISDIR}/files:"\n\n', ''
        ),
        "must_fail": ["filesextrapaths_set", "filesextrapaths_prepend_syntax"],
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
        "name": "drop_lic_files_chksum",
        "description": "Remove LIC_FILES_CHKSUM — recipe parse fails; hash check also drops.",
        "mutation": lambda code: code.replace(
            'LIC_FILES_CHKSUM = "file://COPYING;md5=b234ee4d69f5fce4486a80fdaf4a4263"\n',
            '',
        ),
        "must_fail": ["lic_files_chksum_defined", "lic_chksum_has_hash"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_do_install_block",
        "description": "Remove entire do_install() block — recipe produces no installable artifacts.",
        "mutation": lambda code: code.replace(
            'do_install() {\n    install -d ${D}${bindir}\n    install -m 0755 myapp ${D}${bindir}/myapp\n}\n',
            '',
        ),
        "must_fail": ["do_install_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "inject_manual_git_apply",
        "description": "Add 'git apply' command inside do_compile — hallucination; Yocto auto-applies patches via do_patch.",
        "mutation": lambda code: code.replace(
            'do_compile() {\n    ${CC}',
            'do_compile() {\n    git apply ${WORKDIR}/fix-build.patch\n    ${CC}',
        ),
        "must_fail": ["no_manual_patch_in_do_compile"],
        "factor_id": "F5.1",
    },
    {
        "name": "hardcode_bindir_path",
        "description": "Replace ${D}${bindir} with hardcoded /usr/bin — not multilib-safe, wrong install path.",
        "mutation": lambda code: code.replace('${D}${bindir}', '/usr/bin'),
        "must_fail": ["d_bindir_in_install"],
        "factor_id": "F3.2",
    },
    {
        "name": "hardcode_cc_to_gcc",
        "description": "Replace ${CC} with hardcoded gcc — breaks cross-compilation.",
        "mutation": lambda code: code.replace('${CC}', 'gcc'),
        "must_fail": ["cc_variable_used"],
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
            'SRCREV = "abc1234def5678901234567890abcdef12345678"\n',
            'SRCREV = "abc1234def5678901234567890abcdef12345678"\nFILES_${PN} += "${bindir}/myapp"\n',
        ),
        "must_fail": ["colon_override_syntax"],
        "factor_id": "F3.2",
    },
    {
        "name": "filesextrapaths_late_assign",
        "description": "Use '=' instead of ':=' for FILESEXTRAPATHS:prepend — late binding causes wrong ${THISDIR} resolution.",
        "mutation": lambda code: code.replace(
            'FILESEXTRAPATHS:prepend := ',
            'FILESEXTRAPATHS:prepend = ',
        ),
        "must_fail": ["filesextrapaths_immediate_assignment"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_install_d",
        "description": "Remove 'install -d' — 'install -m' runs without creating target directory.",
        "mutation": lambda code: code.replace(
            '    install -d ${D}${bindir}\n', ''
        ),
        "must_fail": ["install_d_before_install_m"],
        "factor_id": "F3.2",
    },
]
