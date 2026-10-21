"""Behavioral checks for yocto-012 (PACKAGECONFIG flag semantics)."""

import re

from embedeval.check_utils import strip_yocto_comments
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    body = strip_yocto_comments(generated_code)

    # 1. PACKAGECONFIG default uses ??= (weak assignment so the user
    # can override) and sets ssl as default (no examples).
    default_pat = re.search(
        r'PACKAGECONFIG\s*\?\?=\s*"([^"]*)"', body
    )
    has_default = bool(default_pat)
    default_value = default_pat.group(1) if default_pat else ""
    default_ssl_only = (
        has_default
        and "ssl" in default_value
        and "examples" not in default_value
    )
    details.append(
        CheckDetail(
            check_name="packageconfig_default_ssl_only",
            passed=default_ssl_only,
            expected='PACKAGECONFIG ??= "ssl" (examples disabled by default)',
            actual=f"value={default_value!r}",
            check_type="constraint",
        )
    )

    # 2. PACKAGECONFIG[ssl] tuple present with 5 comma-separated fields.
    ssl_pat = re.search(
        r'PACKAGECONFIG\[ssl\]\s*=\s*"([^"]*)"', body
    )
    ssl_fields = (ssl_pat.group(1).split(",") if ssl_pat else []) if ssl_pat else []
    ssl_has_5 = len(ssl_fields) == 5
    details.append(
        CheckDetail(
            check_name="ssl_packageconfig_5_fields",
            passed=ssl_has_5,
            expected="PACKAGECONFIG[ssl] has 5 comma-separated fields",
            actual=f"fields={len(ssl_fields)}",
            check_type="constraint",
        )
    )

    # 3. ssl enable/disable flags are --with-ssl / --without-ssl.
    ssl_enable_ok = (
        ssl_has_5
        and "--with-ssl" in ssl_fields[0]
        and "--without-ssl" in ssl_fields[1]
    )
    details.append(
        CheckDetail(
            check_name="ssl_autoconf_flags_correct",
            passed=ssl_enable_ok,
            expected="--with-ssl / --without-ssl",
            actual=(
                f"enable={ssl_fields[0] if ssl_has_5 else ''}, "
                f"disable={ssl_fields[1] if ssl_has_5 else ''}"
            ),
            check_type="constraint",
        )
    )

    # 4. ssl DEPENDS includes openssl.
    ssl_depends_ok = ssl_has_5 and "openssl" in ssl_fields[2]
    details.append(
        CheckDetail(
            check_name="ssl_build_depends_openssl",
            passed=ssl_depends_ok,
            expected="ssl PACKAGECONFIG DEPENDS on openssl",
            actual=f"field={ssl_fields[2] if ssl_has_5 else ''}",
            check_type="constraint",
        )
    )

    # 5. ssl RDEPENDS includes openssl-bin.
    ssl_rdepends_ok = ssl_has_5 and "openssl-bin" in ssl_fields[3]
    details.append(
        CheckDetail(
            check_name="ssl_runtime_depends_openssl_bin",
            passed=ssl_rdepends_ok,
            expected="ssl PACKAGECONFIG RDEPENDS on openssl-bin",
            actual=f"field={ssl_fields[3] if ssl_has_5 else ''}",
            check_type="constraint",
        )
    )

    # 6. PACKAGECONFIG[examples] tuple present with 5 fields.
    ex_pat = re.search(
        r'PACKAGECONFIG\[examples\]\s*=\s*"([^"]*)"', body
    )
    ex_fields = (ex_pat.group(1).split(",") if ex_pat else []) if ex_pat else []
    ex_has_5 = len(ex_fields) == 5
    details.append(
        CheckDetail(
            check_name="examples_packageconfig_5_fields",
            passed=ex_has_5,
            expected="PACKAGECONFIG[examples] has 5 comma-separated fields",
            actual=f"fields={len(ex_fields)}",
            check_type="constraint",
        )
    )

    # 7. examples enable flag is --enable-examples.
    ex_enable_ok = (
        ex_has_5
        and "--enable-examples" in ex_fields[0]
        and "--disable-examples" in ex_fields[1]
    )
    details.append(
        CheckDetail(
            check_name="examples_autoconf_flags_correct",
            passed=ex_enable_ok,
            expected="--enable-examples / --disable-examples",
            actual=(
                f"enable={ex_fields[0] if ex_has_5 else ''}, "
                f"disable={ex_fields[1] if ex_has_5 else ''}"
            ),
            check_type="constraint",
        )
    )

    # 8. examples dep fields are empty (no DEPENDS / RDEPENDS changes).
    ex_deps_empty = (
        ex_has_5
        and ex_fields[2].strip() == ""
        and ex_fields[3].strip() == ""
    )
    details.append(
        CheckDetail(
            check_name="examples_dep_fields_empty",
            passed=ex_deps_empty,
            expected="examples PACKAGECONFIG DEPENDS/RDEPENDS empty",
            actual=(
                f"DEPENDS={ex_fields[2]!r}, RDEPENDS={ex_fields[3]!r}"
                if ex_has_5
                else "missing fields"
            ),
            check_type="constraint",
        )
    )

    # 9. EXTRA_OECONF picks up ${PACKAGECONFIG_CONFARGS} — must appear
    # INSIDE an EXTRA_OECONF assignment, not anywhere in the recipe.
    confargs_in_extra_oeconf = bool(
        re.search(
            r'EXTRA_OECONF\s*[+?]?=\s*"[^"]*\$\{PACKAGECONFIG_CONFARGS\}',
            body,
        )
    )
    details.append(
        CheckDetail(
            check_name="extra_oeconf_uses_packageconfig_confargs",
            passed=confargs_in_extra_oeconf,
            expected='EXTRA_OECONF assignment references ${PACKAGECONFIG_CONFARGS}',
            actual=(
                "present"
                if confargs_in_extra_oeconf
                else "missing or not scoped to EXTRA_OECONF"
            ),
            check_type="constraint",
        )
    )

    return details
