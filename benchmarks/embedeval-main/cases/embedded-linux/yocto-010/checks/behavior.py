"""Behavioral checks for yocto-010 (colon-form override discipline)."""

import re

from embedeval.check_utils import (
    strip_yocto_comments,
    yocto_has_legacy_override,
    yocto_has_override,
)
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    body = strip_yocto_comments(generated_code)

    # 1. FILESEXTRAPATHS:prepend — colon form.
    uses_colon_filesextra = yocto_has_override(
        generated_code, "FILESEXTRAPATHS", "prepend"
    )
    uses_legacy_filesextra = yocto_has_legacy_override(
        generated_code, "FILESEXTRAPATHS", "prepend"
    )
    details.append(
        CheckDetail(
            check_name="filesextrapaths_colon_prepend",
            passed=uses_colon_filesextra,
            expected='FILESEXTRAPATHS:prepend := "${THISDIR}/files:"',
            actual="colon form" if uses_colon_filesextra else "missing colon form",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="no_legacy_filesextrapaths_prepend",
            passed=not uses_legacy_filesextra,
            expected="Do NOT use FILESEXTRAPATHS_prepend (legacy underscore)",
            actual="clean" if not uses_legacy_filesextra else "legacy _prepend used",
            check_type="constraint",
        )
    )

    # 2. SRC_URI:append — colon form, with file://sshd_config_harden.
    uses_colon_srcuri = yocto_has_override(generated_code, "SRC_URI", "append")
    has_harden_file = "file://sshd_config_harden" in body
    details.append(
        CheckDetail(
            check_name="src_uri_colon_append_with_file",
            passed=uses_colon_srcuri and has_harden_file,
            expected='SRC_URI:append = " file://sshd_config_harden"',
            actual=f"colon={uses_colon_srcuri}, file={has_harden_file}",
            check_type="constraint",
        )
    )

    # 3. No legacy SRC_URI_append.
    uses_legacy_srcuri = yocto_has_legacy_override(
        generated_code, "SRC_URI", "append"
    )
    details.append(
        CheckDetail(
            check_name="no_legacy_src_uri_append",
            passed=not uses_legacy_srcuri,
            expected="Do NOT use SRC_URI_append (legacy)",
            actual="clean" if not uses_legacy_srcuri else "legacy underscore used",
            check_type="constraint",
        )
    )

    # 4. RDEPENDS:${PN}:append with audit.
    # The helper handles ``VAR:override`` but RDEPENDS has a variable
    # expansion `${PN}` interposed. Check explicitly.
    rdepends_colon_pat = re.compile(
        r"RDEPENDS:\$\{PN\}:append\s*[:+?]?=", re.MULTILINE
    )
    has_rdepends_colon = bool(rdepends_colon_pat.search(body))
    has_audit = re.search(r"RDEPENDS:\$\{PN\}:append[^\"]*\"[^\"]*audit", body)
    details.append(
        CheckDetail(
            check_name="rdepends_colon_append_audit",
            passed=has_rdepends_colon and bool(has_audit),
            expected='RDEPENDS:${PN}:append = " audit"',
            actual=f"colon={has_rdepends_colon}, audit={bool(has_audit)}",
            check_type="constraint",
        )
    )

    # 5. No legacy RDEPENDS_${PN}_append.
    has_legacy_rdepends = bool(
        re.search(r"RDEPENDS_\$\{PN\}_append\b", body)
    )
    details.append(
        CheckDetail(
            check_name="no_legacy_rdepends_append",
            passed=not has_legacy_rdepends,
            expected="Do NOT use RDEPENDS_${PN}_append (legacy)",
            actual="clean" if not has_legacy_rdepends else "legacy used",
            check_type="constraint",
        )
    )

    # 6. do_install:append function body — colon form.
    has_do_install_append = bool(
        re.search(r"do_install:append\s*\(\s*\)\s*\{", body)
    )
    details.append(
        CheckDetail(
            check_name="do_install_colon_append",
            passed=has_do_install_append,
            expected="do_install:append() { ... } function body",
            actual="present" if has_do_install_append else "missing",
            check_type="constraint",
        )
    )

    # 7. install -m 0644 directive for the hardened config.
    has_install_0644 = bool(re.search(r"install\s+-m\s+0644", body))
    details.append(
        CheckDetail(
            check_name="install_mode_0644",
            passed=has_install_0644,
            expected="install -m 0644 for sshd config (text file, not executable)",
            actual="present" if has_install_0644 else "missing",
            check_type="constraint",
        )
    )

    return details
