"""Negative tests for Yocto Recipe with Build and Runtime Dependencies.

Reference: cases/yocto-004/reference/main.c (BitBake .bb recipe)
Checks:    cases/yocto-004/checks/static.py, behavior.py

Authored: 2026-04-19 via /negatives command
"""


NEGATIVES = [
    {
        "name": "drop_summary",
        "description": "Remove SUMMARY line — recipe lacks required metadata.",
        "mutation": lambda code: code.replace(
            'SUMMARY = "Application with build-time and runtime dependencies"\n',
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
        "name": "strip_all_depends",
        "description": "Rename DEPENDS→DEPS everywhere (both build-time DEPENDS and runtime RDEPENDS) — no dependencies declared; build fails, package ships without runtime libs.",
        "mutation": lambda code: code.replace('DEPENDS', 'DEPS'),
        "must_fail": [
            "depends_defined",
            "rdepends_defined",
            "both_depends_and_rdepends_present",
        ],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_do_compile",
        "description": "Remove do_compile() block — recipe has no build step.",
        "mutation": lambda code: code.replace(
            'do_compile() {\n    ${CC} ${CFLAGS} ${LDFLAGS} -lssl -lcrypto -o myapp ${S}/myapp.c\n}\n\n',
            '',
        ),
        "must_fail": ["do_compile_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_do_install_block",
        "description": "Remove do_install() block — recipe produces no installable artifacts.",
        "mutation": lambda code: code.replace(
            'do_install() {\n    install -d ${D}${bindir}\n    install -m 0755 myapp ${D}${bindir}/myapp\n}\n',
            '',
        ),
        "must_fail": ["do_install_defined"],
        "factor_id": "F3.2",
    },
    {
        "name": "underscore_override_rdepends",
        "description": "Use deprecated RDEPENDS_${PN} underscore syntax instead of :${PN}.",
        "mutation": lambda code: code.replace(
            'RDEPENDS:${PN}', 'RDEPENDS_${PN}'
        ),
        "must_fail": ["rdepends_has_pn_suffix", "colon_override_syntax"],
        "factor_id": "F3.2",
    },
    {
        "name": "drop_lic_chksum_hash",
        "description": "Corrupt LIC_FILES_CHKSUM by stripping md5= tag — recipe parse fails.",
        "mutation": lambda code: code.replace(
            'md5=838c366f69b72c5df05c96dff79b35f2', 'todo'
        ),
        "must_fail": ["lic_chksum_has_hash"],
        "factor_id": "F3.2",
    },
    {
        "name": "hardcode_cc_to_gcc",
        "description": "Replace ${CC} with hardcoded gcc — breaks cross-compilation, uses host toolchain.",
        "mutation": lambda code: code.replace('${CC}', 'gcc'),
        "must_fail": ["uses_cc_variable"],
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
        "name": "hardcode_bindir",
        "description": "Replace ${bindir} with hardcoded /usr/bin — not multilib-safe.",
        "mutation": lambda code: code.replace('${bindir}', '/usr/bin'),
        "must_fail": ["uses_bindir_variable"],
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
        "name": "inject_hardcoded_libdir",
        "description": "Inject FILES:${PN} with hardcoded /usr/lib path instead of ${libdir}.",
        "mutation": lambda code: code.replace(
            'RDEPENDS:${PN} = "libssl"\n',
            'RDEPENDS:${PN} = "libssl"\nFILES:${PN} += "/usr/lib/myapp.so"\n',
        ),
        "must_fail": ["no_hardcoded_libdir"],
        "factor_id": "F3.2",
    },
    {
        "name": "add_git_without_srcrev",
        "description": "Convert file://myapp.c to git:// without providing SRCREV — build fetcher error.",
        "mutation": lambda code: code.replace(
            'file://myapp.c',
            'git://github.com/example/myapp.git;protocol=https;branch=main',
        ),
        "must_fail": ["git_src_uri_has_srcrev"],
        "factor_id": "F3.2",
    },
]
