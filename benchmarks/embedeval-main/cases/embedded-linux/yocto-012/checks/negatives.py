"""Negative tests for yocto-012 (PACKAGECONFIG discipline)."""

import re


def _swap_default_to_include_examples(code: str) -> str:
    return code.replace(
        'PACKAGECONFIG ??= "ssl"',
        'PACKAGECONFIG ??= "ssl examples"',
    )


def _swap_default_weak_to_hard(code: str) -> str:
    """Use = instead of ??= — user can't override in local.conf."""
    return code.replace(
        'PACKAGECONFIG ??= "ssl"',
        'PACKAGECONFIG = "ssl"',
    )


def _drop_packageconfig_default(code: str) -> str:
    return code.replace('PACKAGECONFIG ??= "ssl"\n\n', "")


def _ssl_wrong_autoconf_flag(code: str) -> str:
    return code.replace(
        '"--with-ssl,--without-ssl,openssl,openssl-bin,"',
        '"--enable-ssl,--disable-ssl,openssl,openssl-bin,"',
    )


def _ssl_4_fields_only(code: str) -> str:
    """Drop the 5th (RCONFLICTS) field from PACKAGECONFIG[ssl].

    BitBake parses the tuple by comma count and rejects 4-field
    entries. Regex-based so trailing-whitespace or field-value variance
    in the reference still triggers the mutation."""
    return re.sub(
        r'(PACKAGECONFIG\[ssl\]\s*=\s*")([^,"]*,[^,"]*,[^,"]*,[^,"]*),[^"]*(")',
        r"\1\2\3",
        code,
        count=1,
    )


def _ssl_missing_rdepends(code: str) -> str:
    return code.replace(
        '"--with-ssl,--without-ssl,openssl,openssl-bin,"',
        '"--with-ssl,--without-ssl,openssl,,"',
    )


def _ssl_missing_depends(code: str) -> str:
    return code.replace(
        '"--with-ssl,--without-ssl,openssl,openssl-bin,"',
        '"--with-ssl,--without-ssl,,openssl-bin,"',
    )


def _examples_wrong_autoconf_flag(code: str) -> str:
    return code.replace(
        '"--enable-examples,--disable-examples,,,"',
        '"--with-examples,--without-examples,,,"',
    )


def _examples_injects_deps(code: str) -> str:
    return code.replace(
        '"--enable-examples,--disable-examples,,,"',
        '"--enable-examples,--disable-examples,glibc,glibc,"',
    )


def _drop_extra_oeconf_confargs(code: str) -> str:
    return code.replace(
        '\nEXTRA_OECONF += "${PACKAGECONFIG_CONFARGS}"\n', "\n"
    )


def _drop_inherit_autotools(code: str) -> str:
    return code.replace("inherit autotools\n\n", "")


def _drop_ssl_entry_entirely(code: str) -> str:
    return code.replace(
        'PACKAGECONFIG[ssl] = "--with-ssl,--without-ssl,openssl,openssl-bin,"\n',
        "",
    )


NEGATIVES = [
    {
        "name": "default_includes_examples",
        "description": "Default includes examples — violates the ssl-only default contract.",
        "mutation": _swap_default_to_include_examples,
        "must_fail": ["packageconfig_default_ssl_only"],
        "factor_id": "F6.2",
    },
    {
        "name": "default_uses_hard_assign",
        "description": "Use = instead of ??= for default — local.conf can't override.",
        "mutation": _swap_default_weak_to_hard,
        "must_fail": ["packageconfig_default_ssl_only"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_default",
        "description": "No PACKAGECONFIG default — user must opt in manually.",
        "mutation": _drop_packageconfig_default,
        "must_fail": ["packageconfig_default_ssl_only"],
        "factor_id": "F6.1",
    },
    {
        "name": "ssl_wrong_autoconf_toggle",
        "description": "ssl uses --enable-ssl instead of --with-ssl — wrong autoconf convention for an optional dependency.",
        "mutation": _ssl_wrong_autoconf_flag,
        "must_fail": ["ssl_autoconf_flags_correct"],
        "factor_id": "F6.2",
    },
    {
        "name": "ssl_4_fields_not_5",
        "description": "ssl PACKAGECONFIG tuple has only 4 fields — bitbake rejects.",
        "mutation": _ssl_4_fields_only,
        "must_fail": ["ssl_packageconfig_5_fields"],
        "factor_id": "F6.2",
    },
    {
        "name": "ssl_missing_rdepends",
        "description": "ssl PACKAGECONFIG missing RDEPENDS openssl-bin — runtime tool absent on target.",
        "mutation": _ssl_missing_rdepends,
        "must_fail": ["ssl_runtime_depends_openssl_bin"],
        "factor_id": "F6.2",
    },
    {
        "name": "ssl_missing_depends",
        "description": "ssl PACKAGECONFIG missing DEPENDS openssl — build fails (missing headers).",
        "mutation": _ssl_missing_depends,
        "must_fail": ["ssl_build_depends_openssl"],
        "factor_id": "F6.2",
    },
    {
        "name": "examples_wrong_autoconf_toggle",
        "description": "examples uses --with-examples instead of --enable-examples — wrong autoconf convention for a feature flag.",
        "mutation": _examples_wrong_autoconf_flag,
        "must_fail": ["examples_autoconf_flags_correct"],
        "factor_id": "F6.2",
    },
    {
        "name": "examples_injects_deps",
        "description": "examples PACKAGECONFIG injects glibc as DEPENDS/RDEPENDS — unnecessary, contradicts the empty-deps contract.",
        "mutation": _examples_injects_deps,
        "must_fail": ["examples_dep_fields_empty"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_extra_oeconf_confargs",
        "description": "EXTRA_OECONF missing ${PACKAGECONFIG_CONFARGS} — flags never reach configure.",
        "mutation": _drop_extra_oeconf_confargs,
        "must_fail": ["extra_oeconf_uses_packageconfig_confargs"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_inherit_autotools",
        "description": "Drop inherit autotools — recipe doesn't run configure at all.",
        "mutation": _drop_inherit_autotools,
        "must_fail": ["autotools_inherited"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_ssl_entry",
        "description": "Remove PACKAGECONFIG[ssl] entry — default references undefined flag.",
        "mutation": _drop_ssl_entry_entirely,
        "must_fail": [
            "ssl_packageconfig_5_fields",
            "ssl_autoconf_flags_correct",
        ],
        "factor_id": "F6.1",
    },
]
