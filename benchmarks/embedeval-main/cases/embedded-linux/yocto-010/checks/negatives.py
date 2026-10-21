"""Negative tests for yocto-010 (colon-form override discipline)."""


def _swap_colon_filesextra_to_underscore(code: str) -> str:
    return code.replace(
        "FILESEXTRAPATHS:prepend", "FILESEXTRAPATHS_prepend"
    )


def _swap_colon_srcuri_to_underscore(code: str) -> str:
    return code.replace("SRC_URI:append", "SRC_URI_append")


def _swap_colon_rdepends_to_underscore(code: str) -> str:
    return code.replace(
        "RDEPENDS:${PN}:append", "RDEPENDS_${PN}_append"
    )


def _swap_colon_do_install_to_underscore(code: str) -> str:
    return code.replace("do_install:append", "do_install_append")


def _drop_filesextrapaths(code: str) -> str:
    return code.replace(
        'FILESEXTRAPATHS:prepend := "${THISDIR}/files:"\n\n', ""
    )


def _drop_src_uri_append(code: str) -> str:
    return code.replace(
        'SRC_URI:append = " file://sshd_config_harden"\n\n', ""
    )


def _drop_rdepends_append(code: str) -> str:
    return code.replace(
        'RDEPENDS:${PN}:append = " audit"\n\n', ""
    )


def _drop_do_install_append(code: str) -> str:
    return code.replace(
        'do_install:append() {\n'
        '    install -d ${D}${sysconfdir}/ssh/sshd_config.d\n'
        '    install -m 0644 ${WORKDIR}/sshd_config_harden \\\n'
        '        ${D}${sysconfdir}/ssh/sshd_config.d/50-harden.conf\n'
        '}\n',
        "",
    )


def _drop_harden_file_from_src_uri(code: str) -> str:
    return code.replace(
        "file://sshd_config_harden", "file://README"
    )


def _swap_install_mode_to_executable(code: str) -> str:
    return code.replace("install -m 0644", "install -m 0755")


def _remove_audit_from_rdepends(code: str) -> str:
    return code.replace(
        'RDEPENDS:${PN}:append = " audit"',
        'RDEPENDS:${PN}:append = " lsb"',
    )


def _drop_rdepends_colon_pn(code: str) -> str:
    """Miss the :${PN}: segment — appends apply to the wrong package set."""
    return code.replace(
        "RDEPENDS:${PN}:append", "RDEPENDS:append"
    )


NEGATIVES = [
    {
        "name": "filesextrapaths_underscore_override",
        "description": "Use the legacy FILESEXTRAPATHS_prepend — kirkstone accepts it but it's the older, non-canonical form.",
        "mutation": _swap_colon_filesextra_to_underscore,
        "must_fail": [
            "filesextrapaths_colon_prepend",
            "no_legacy_filesextrapaths_prepend",
        ],
        "factor_id": "F4.1",
    },
    {
        "name": "src_uri_underscore_override",
        "description": "Use legacy SRC_URI_append — deprecated since kirkstone.",
        "mutation": _swap_colon_srcuri_to_underscore,
        "must_fail": [
            "src_uri_colon_append_with_file",
            "no_legacy_src_uri_append",
        ],
        "factor_id": "F4.1",
    },
    {
        "name": "rdepends_underscore_override",
        "description": "Use legacy RDEPENDS_${PN}_append — deprecated.",
        "mutation": _swap_colon_rdepends_to_underscore,
        "must_fail": [
            "rdepends_colon_append_audit",
            "no_legacy_rdepends_append",
        ],
        "factor_id": "F4.1",
    },
    {
        "name": "do_install_underscore_override",
        "description": "Use legacy do_install_append — deprecated.",
        "mutation": _swap_colon_do_install_to_underscore,
        "must_fail": ["do_install_colon_append"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_filesextrapaths",
        "description": "Remove FILESEXTRAPATHS — new config file becomes unreachable.",
        "mutation": _drop_filesextrapaths,
        "must_fail": ["filesextrapaths_colon_prepend"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_src_uri_append",
        "description": "Remove SRC_URI append — new config file never fetched.",
        "mutation": _drop_src_uri_append,
        "must_fail": ["src_uri_colon_append_with_file"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_rdepends_append",
        "description": "Remove RDEPENDS append — audit runtime dependency missing.",
        "mutation": _drop_rdepends_append,
        "must_fail": ["rdepends_colon_append_audit"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_do_install_append",
        "description": "Remove do_install:append — config file not installed into rootfs.",
        "mutation": _drop_do_install_append,
        "must_fail": ["do_install_colon_append", "install_mode_0644"],
        "factor_id": "F6.1",
    },
    {
        "name": "rename_harden_file_to_readme",
        "description": "Source a README instead of sshd_config_harden — wrong file fetched.",
        "mutation": _drop_harden_file_from_src_uri,
        "must_fail": ["src_uri_colon_append_with_file"],
        "factor_id": "F6.2",
    },
    {
        "name": "install_mode_executable",
        "description": "install -m 0755 for a sshd config file — wrong permission (executable, not plain data).",
        "mutation": _swap_install_mode_to_executable,
        "must_fail": ["install_mode_0644"],
        "factor_id": "F6.2",
    },
    {
        "name": "rdepends_wrong_package",
        "description": "Depend on lsb instead of audit — wrong runtime contract.",
        "mutation": _remove_audit_from_rdepends,
        "must_fail": ["rdepends_colon_append_audit"],
        "factor_id": "F6.2",
    },
    {
        "name": "rdepends_missing_pn_scope",
        "description": "Drop :${PN}: — override targets wrong package set.",
        "mutation": _drop_rdepends_colon_pn,
        "must_fail": ["rdepends_colon_append_audit"],
        "factor_id": "F6.2",
    },
]
