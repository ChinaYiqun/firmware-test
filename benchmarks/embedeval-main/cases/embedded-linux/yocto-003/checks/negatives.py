"""Negative tests for Yocto Recipe with Systemd Service.

Reference: cases/yocto-003/reference/main.c (BitBake .bb recipe)
Checks:    cases/yocto-003/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_summary",
        "description": "Remove SUMMARY line — recipe lacks required metadata.",
        "mutation": lambda code: code.replace(
            'SUMMARY = "Application with systemd service integration"\n', ''
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
        "name": "remove_inherit_systemd",
        "description": "Drop 'inherit systemd' — SYSTEMD_SERVICE has no effect, service never installed.",
        "mutation": lambda code: code.replace('inherit systemd\n\n', ''),
        "must_fail": ["inherit_systemd", "inherits_systemd_class"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_systemd_service_var",
        "description": "Remove SYSTEMD_SERVICE:${PN} — systemd class has nothing to install/enable.",
        "mutation": lambda code: code.replace(
            'SYSTEMD_SERVICE:${PN} = "myapp.service"\n', ''
        ),
        "must_fail": ["systemd_service_var"],
        "factor_id": "F3.2",
    },
    {
        "name": "dotservice_to_dotsvc",
        "description": "Rename .service to .svc everywhere — service unit file invisible to systemd.",
        "mutation": lambda code: code.replace('.service', '.svc'),
        "must_fail": ["service_in_src_uri", "service_file_in_src_uri"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_do_install_block",
        "description": "Remove entire do_install() block — recipe produces no installable artifacts.",
        "mutation": lambda code: code.replace(
            'do_install() {\n'
            '    install -d ${D}${bindir}\n'
            '    install -m 0755 myapp ${D}${bindir}/myapp\n\n'
            '    install -d ${D}${systemd_unitdir}/system/\n'
            '    install -m 0644 ${WORKDIR}/myapp.service ${D}${systemd_unitdir}/system/myapp.service\n'
            '}\n',
            '',
        ),
        "must_fail": ["do_install_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "underscore_override_systemd_service",
        "description": "Use deprecated SYSTEMD_SERVICE_${PN} underscore syntax instead of :${PN}.",
        "mutation": lambda code: code.replace(
            'SYSTEMD_SERVICE:${PN}', 'SYSTEMD_SERVICE_${PN}'
        ),
        "must_fail": ["systemd_service_has_pn_suffix", "colon_override_syntax"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_auto_enable",
        "description": "Remove SYSTEMD_AUTO_ENABLE — service installed but not enabled at boot.",
        "mutation": lambda code: code.replace(
            'SYSTEMD_AUTO_ENABLE:${PN} = "enable"\n', ''
        ),
        "must_fail": ["systemd_auto_enable_set"],
        "factor_id": "F3.2",
    },
    {
        "name": "hardcode_systemd_unitdir",
        "description": "Replace ${systemd_unitdir} with hardcoded /lib/systemd — not portable, breaks usrmerge.",
        "mutation": lambda code: code.replace('${systemd_unitdir}', '/lib/systemd'),
        "must_fail": ["service_installed_to_systemd_unitdir"],
        "factor_id": "F3.2",
    },
    {
        "name": "strip_d_prefix",
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
        "name": "hardcode_bindir",
        "description": "Replace ${bindir} with hardcoded /usr/bin — not multilib-safe.",
        "mutation": lambda code: code.replace('${bindir}', '/usr/bin'),
        "must_fail": ["no_hardcoded_paths"],
        "factor_id": "F3.2",
    },
    {
        "name": "add_git_without_srcrev",
        "description": "Convert file://myapp.c to git:// source without providing SRCREV — build fetcher error.",
        "mutation": lambda code: code.replace(
            'file://myapp.c',
            'git://github.com/example/src.git;protocol=https;branch=main',
        ),
        "must_fail": ["git_src_uri_has_srcrev"],
        "factor_id": "F3.2",
    },
]
