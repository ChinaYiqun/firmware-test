"""Behavioral checks for yocto-011 (kernel config fragment .bbappend)."""

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

    # 1. Colon FILESEXTRAPATHS:prepend.
    colon_filesextra = yocto_has_override(
        generated_code, "FILESEXTRAPATHS", "prepend"
    )
    details.append(
        CheckDetail(
            check_name="filesextrapaths_colon_prepend",
            passed=colon_filesextra,
            expected='FILESEXTRAPATHS:prepend := "${THISDIR}/files:"',
            actual="present" if colon_filesextra else "missing",
            check_type="constraint",
        )
    )

    # 2. No underscore-form FILESEXTRAPATHS.
    legacy_filesextra = yocto_has_legacy_override(
        generated_code, "FILESEXTRAPATHS", "prepend"
    )
    details.append(
        CheckDetail(
            check_name="no_legacy_filesextrapaths",
            passed=not legacy_filesextra,
            expected="No FILESEXTRAPATHS_prepend (legacy form)",
            actual="clean" if not legacy_filesextra else "legacy underscore used",
            check_type="constraint",
        )
    )

    # 3. Colon SRC_URI:append with file://debug.cfg.
    colon_srcuri = yocto_has_override(generated_code, "SRC_URI", "append")
    has_debug_cfg = "file://debug.cfg" in body
    details.append(
        CheckDetail(
            check_name="src_uri_colon_append_debug_cfg",
            passed=colon_srcuri and has_debug_cfg,
            expected='SRC_URI:append = " file://debug.cfg"',
            actual=f"colon={colon_srcuri}, cfg={has_debug_cfg}",
            check_type="constraint",
        )
    )

    # 4. No inherit module / do_compile / do_install (wrong type of
    # extension for a kernel config fragment).
    has_inherit_module = bool(re.search(r"inherit\s+module\b", body))
    has_do_compile = bool(re.search(r"do_compile\s*\(", body))
    has_do_install = bool(re.search(r"do_install\s*\(", body))
    details.append(
        CheckDetail(
            check_name="no_inherit_module",
            passed=not has_inherit_module,
            expected="No ``inherit module`` — this is not a module recipe",
            actual="clean" if not has_inherit_module else "WRONG: inherit module",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="no_do_compile",
            passed=not has_do_compile,
            expected="No do_compile — kernel recipe handles compile",
            actual="clean" if not has_do_compile else "WRONG: do_compile",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="no_do_install",
            passed=not has_do_install,
            expected="No do_install — kernel recipe handles install",
            actual="clean" if not has_do_install else "WRONG: do_install",
            check_type="constraint",
        )
    )

    # 5. SRC_URI append does NOT use the legacy underscore form.
    legacy_srcuri = yocto_has_legacy_override(generated_code, "SRC_URI", "append")
    details.append(
        CheckDetail(
            check_name="no_legacy_src_uri_append",
            passed=not legacy_srcuri,
            expected="No SRC_URI_append (legacy form)",
            actual="clean" if not legacy_srcuri else "legacy underscore used",
            check_type="constraint",
        )
    )

    # 6. No SUMMARY / LICENSE declared in bbappend — inherited from
    # base recipe. Authoring them in a bbappend is style-wrong.
    has_summary = bool(re.search(r"^SUMMARY\s*=", body, re.MULTILINE))
    details.append(
        CheckDetail(
            check_name="no_summary_redeclared",
            passed=not has_summary,
            expected="No SUMMARY redeclared (inherited from base recipe)",
            actual="clean" if not has_summary else "redeclared",
            check_type="constraint",
        )
    )

    # 7. .cfg suffix (not .scc — that's the kernel-yocto metadata
    # dialect which is a different code path).
    has_correct_suffix = "file://debug.cfg" in body
    details.append(
        CheckDetail(
            check_name="cfg_suffix_not_scc",
            passed=has_correct_suffix and ".scc" not in body,
            expected="Fragment suffix is .cfg (plain kconfig), not .scc",
            actual=f"has_cfg={has_correct_suffix}, has_scc={'.scc' in body}",
            check_type="constraint",
        )
    )

    return details
