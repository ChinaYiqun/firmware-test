"""Negative tests for yocto-011 (kernel config fragment .bbappend)."""


def _swap_filesextra_to_underscore(code: str) -> str:
    return code.replace("FILESEXTRAPATHS:prepend", "FILESEXTRAPATHS_prepend")


def _swap_srcuri_to_underscore(code: str) -> str:
    return code.replace("SRC_URI:append", "SRC_URI_append")


def _drop_filesextra(code: str) -> str:
    return code.replace(
        'FILESEXTRAPATHS:prepend := "${THISDIR}/files:"\n\n', ""
    )


def _drop_srcuri_append(code: str) -> str:
    return code.replace('SRC_URI:append = " file://debug.cfg"\n', "")


def _inject_inherit_module(code: str) -> str:
    return "inherit module\n" + code


def _inject_do_compile(code: str) -> str:
    return code + "\ndo_compile() {\n    echo override\n}\n"


def _inject_do_install(code: str) -> str:
    return code + "\ndo_install() {\n    :\n}\n"


def _drop_cfg_file(code: str) -> str:
    return code.replace("file://debug.cfg", "")


def _swap_cfg_to_scc(code: str) -> str:
    return code.replace("debug.cfg", "debug.scc")


def _inject_summary_redeclaration(code: str) -> str:
    return 'SUMMARY = "override"\n' + code


def _swap_prepend_to_append_on_filesextrapaths(code: str) -> str:
    """FILESEXTRAPATHS must prepend; :append comes too late and
    files aren't found."""
    return code.replace(
        "FILESEXTRAPATHS:prepend", "FILESEXTRAPATHS:append"
    )


def _drop_both_colons(code: str) -> str:
    """Replace both colon overrides with plain assignment — no
    layering happens at all."""
    return code.replace(
        "FILESEXTRAPATHS:prepend", "FILESEXTRAPATHS"
    ).replace("SRC_URI:append", "SRC_URI")


NEGATIVES = [
    {
        "name": "filesextra_underscore_override",
        "description": "Use FILESEXTRAPATHS_prepend (legacy underscore form).",
        "mutation": _swap_filesextra_to_underscore,
        "must_fail": ["filesextrapaths_colon_prepend", "no_legacy_filesextrapaths"],
        "factor_id": "F4.1",
    },
    {
        "name": "srcuri_underscore_override",
        "description": "Use SRC_URI_append (legacy underscore form).",
        "mutation": _swap_srcuri_to_underscore,
        "must_fail": ["src_uri_colon_append_debug_cfg", "no_legacy_src_uri_append"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_filesextrapaths",
        "description": "Remove FILESEXTRAPATHS — .cfg not discoverable in files/ subdir.",
        "mutation": _drop_filesextra,
        "must_fail": ["filesextrapaths_colon_prepend"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_srcuri_append",
        "description": "Remove SRC_URI append — fragment never added to kernel config merge.",
        "mutation": _drop_srcuri_append,
        "must_fail": ["src_uri_colon_append_debug_cfg", "debug_cfg_referenced"],
        "factor_id": "F6.1",
    },
    {
        "name": "inject_inherit_module",
        "description": "Inherit the module class — wrong recipe type, builds as a module not a kernel extension.",
        "mutation": _inject_inherit_module,
        "must_fail": ["no_inherit_module"],
        "factor_id": "F6.2",
    },
    {
        "name": "inject_do_compile",
        "description": "Add do_compile — overrides the kernel recipe's build step and breaks the build.",
        "mutation": _inject_do_compile,
        "must_fail": ["no_do_compile"],
        "factor_id": "F6.2",
    },
    {
        "name": "inject_do_install",
        "description": "Add do_install — overrides the kernel recipe's install step.",
        "mutation": _inject_do_install,
        "must_fail": ["no_do_install"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_cfg_file_uri",
        "description": "Strip debug.cfg reference from SRC_URI — fragment gone.",
        "mutation": _drop_cfg_file,
        "must_fail": [
            "src_uri_colon_append_debug_cfg",
            "debug_cfg_referenced",
            "cfg_suffix_not_scc",
        ],
        "factor_id": "F6.1",
    },
    {
        "name": "cfg_suffix_changed_to_scc",
        "description": "Rename debug.cfg to debug.scc — scc is kernel-yocto metadata, different code path.",
        "mutation": _swap_cfg_to_scc,
        "must_fail": ["cfg_suffix_not_scc", "debug_cfg_referenced"],
        "factor_id": "F4.2",
    },
    {
        "name": "redeclare_summary",
        "description": "Redeclare SUMMARY — shadows the base recipe's metadata unnecessarily.",
        "mutation": _inject_summary_redeclaration,
        "must_fail": ["no_summary_redeclared"],
        "factor_id": "F6.2",
    },
    {
        "name": "filesextra_append_not_prepend",
        "description": "FILESEXTRAPATHS:append — files searched AFTER upstream paths; if the same name exists upstream, the wrong file wins.",
        "mutation": _swap_prepend_to_append_on_filesextrapaths,
        "must_fail": ["filesextrapaths_colon_prepend"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_colon_overrides",
        "description": "Use plain assignment instead of colon overrides — clobbers upstream values instead of layering.",
        "mutation": _drop_both_colons,
        "must_fail": [
            "filesextrapaths_colon_prepend",
            "src_uri_colon_append_debug_cfg",
        ],
        "factor_id": "F6.2",
    },
]
