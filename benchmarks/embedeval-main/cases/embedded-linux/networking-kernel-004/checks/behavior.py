"""Behavioral checks for networking-kernel-004 (generic netlink family).

Validates:
  - struct genl_family declared with the 5.15 form (.ops / .n_ops /
    .maxattr / .module = THIS_MODULE).
  - genl_register_family called from init; genl_unregister_family
    called from exit.
  - struct genl_ops array declared with at least .cmd + .doit.
  - Deprecated genl_register_family_with_ops NOT used.
  - Handler exercises genlmsg_new / genlmsg_put_reply / genlmsg_end /
    genlmsg_reply.
"""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    has_genl_family_struct,
    strip_comments,
)
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)
    init_body = extract_module_init_body(generated_code) or ""
    exit_body = extract_module_exit_body(generated_code) or ""

    # 1. struct genl_family declared in the 5.15 form.
    has_family = has_genl_family_struct(generated_code)
    details.append(
        CheckDetail(
            check_name="genl_family_struct_declared",
            passed=has_family,
            expected="struct genl_family with .ops / .n_ops / .small_ops",
            actual="present" if has_family else "missing",
            check_type="constraint",
        )
    )

    # Scope the per-field membership checks (2..6, 13) to the
    # genl_family initializer body so a separate genl_ops array with
    # similarly-named fields can't satisfy them spuriously.
    fam_init_m = re.search(
        r"\bstruct\s+genl_family\s+\w+\s*=\s*\{([^}]*)\}",
        stripped,
        flags=re.DOTALL,
    )
    fam_body = fam_init_m.group(1) if fam_init_m else ""

    # 2. .name field populated.
    has_name = bool(re.search(r"\.name\s*=\s*\"[^\"]+\"", fam_body))
    details.append(
        CheckDetail(
            check_name="genl_family_has_name_field",
            passed=has_name,
            expected=".name = \"<string>\"",
            actual="present" if has_name else "missing",
            check_type="constraint",
        )
    )

    # 3. .module = THIS_MODULE.
    has_this_module = bool(re.search(r"\.module\s*=\s*THIS_MODULE\b", fam_body))
    details.append(
        CheckDetail(
            check_name="genl_family_has_module_this_module",
            passed=has_this_module,
            expected=".module = THIS_MODULE",
            actual="present" if has_this_module else "missing",
            check_type="constraint",
        )
    )

    # 4. .ops pointer set.
    has_ops = bool(re.search(r"\.ops\s*=\s*\w+", fam_body))
    details.append(
        CheckDetail(
            check_name="genl_family_has_ops_field",
            passed=has_ops,
            expected=".ops = <array>",
            actual="present" if has_ops else "missing",
            check_type="constraint",
        )
    )

    # 5. .n_ops field set.
    has_n_ops = bool(re.search(r"\.n_ops\s*=\s*\w+", fam_body))
    details.append(
        CheckDetail(
            check_name="genl_family_has_n_ops",
            passed=has_n_ops,
            expected=".n_ops = ARRAY_SIZE(ops)",
            actual="present" if has_n_ops else "missing",
            check_type="constraint",
        )
    )

    # 6. .maxattr field set.
    has_maxattr = bool(re.search(r"\.maxattr\s*=\s*\w+", fam_body))
    details.append(
        CheckDetail(
            check_name="genl_family_has_maxattr",
            passed=has_maxattr,
            expected=".maxattr = <MAX>",
            actual="present" if has_maxattr else "missing",
            check_type="constraint",
        )
    )

    # 7. struct genl_ops array declared with .cmd and .doit.
    has_ops_array = bool(
        re.search(
            r"\bstruct\s+genl_ops\s+\w+\s*\[\s*\][^{]*\{",
            stripped,
        )
    )
    has_cmd = bool(re.search(r"\.cmd\s*=\s*\w+", stripped))
    has_doit = bool(re.search(r"\.doit\s*=\s*\w+", stripped))
    details.append(
        CheckDetail(
            check_name="genl_ops_array_with_cmd_and_doit",
            passed=has_ops_array and has_cmd and has_doit,
            expected="static const struct genl_ops arr[] = { { .cmd=..., .doit=... } }",
            actual=(
                f"array={has_ops_array}, cmd={has_cmd}, doit={has_doit}"
            ),
            check_type="constraint",
        )
    )

    # 8. genl_register_family called from init.
    register_in_init = has_api_call(init_body, "genl_register_family")
    details.append(
        CheckDetail(
            check_name="genl_register_family_in_init",
            passed=register_in_init,
            expected="genl_register_family(&family) in init",
            actual="present" if register_in_init else "missing",
            check_type="constraint",
        )
    )

    # 9. genl_unregister_family called from exit.
    unregister_in_exit = has_api_call(exit_body, "genl_unregister_family")
    details.append(
        CheckDetail(
            check_name="genl_unregister_family_in_exit",
            passed=unregister_in_exit,
            expected="genl_unregister_family(&family) in exit",
            actual="present" if unregister_in_exit else "missing",
            check_type="constraint",
        )
    )

    # 10. Deprecated API NOT used.
    has_deprecated = bool(
        re.search(r"\bgenl_register_family_with_ops\s*\(", stripped)
    )
    details.append(
        CheckDetail(
            check_name="no_deprecated_genl_register_family_with_ops",
            passed=not has_deprecated,
            expected="genl_register_family_with_ops absent (removed in 4.10)",
            actual="clean" if not has_deprecated else "deprecated API used",
            check_type="constraint",
        )
    )

    # 11. Handler uses the genlmsg_* reply builder family.
    handler_builds_reply = all(
        re.search(rf"\b{api}\s*\(", stripped)
        for api in ("genlmsg_new", "genlmsg_end", "genlmsg_reply")
    )
    details.append(
        CheckDetail(
            check_name="handler_uses_genlmsg_reply_builder",
            passed=handler_builds_reply,
            expected="genlmsg_new + genlmsg_end + genlmsg_reply all present",
            actual="present" if handler_builds_reply else "missing one or more",
            check_type="constraint",
        )
    )

    # 12. Neutral family name — no vendor prefix.
    has_qcells = bool(re.search(r"\"qcells", stripped, flags=re.IGNORECASE))
    details.append(
        CheckDetail(
            check_name="family_name_is_neutral_not_qcells",
            passed=not has_qcells,
            expected="family name free of vendor prefix (qcells / nxp / imx)",
            actual="clean" if not has_qcells else "vendor prefix present",
            check_type="constraint",
        )
    )

    # 12b. NLA policy array bound to the family — enables kernel-side
    # attribute-type validation. Without a policy array, maxattr alone
    # does not prevent malformed payloads. The check also scopes to
    # the genl_family initializer so an unrelated policy array in the
    # file does not count.
    has_policy = bool(re.search(r"\.policy\s*=\s*\w+", fam_body))
    has_policy_decl = bool(
        re.search(
            r"\bstruct\s+nla_policy\s+\w+\s*\[[^\]]*\]\s*=\s*\{",
            stripped,
        )
    )
    details.append(
        CheckDetail(
            check_name="genl_family_has_policy_array",
            passed=has_policy and has_policy_decl,
            expected=".policy = <nla_policy[]> declared + bound to family",
            actual=(
                "bound"
                if has_policy and has_policy_decl
                else "missing policy declaration or .policy field"
            ),
            check_type="constraint",
        )
    )

    # 13. No cross-platform APIs.
    cross_plat = check_no_cross_platform_apis(
        generated_code, skip_platforms=["Linux_Userspace", "POSIX"]
    )
    details.append(
        CheckDetail(
            check_name="no_cross_platform_apis",
            passed=len(cross_plat) == 0,
            expected="No FreeRTOS / Zephyr / Arduino / STM32 HAL APIs",
            actual="clean" if not cross_plat else f"found: {[a for a, _ in cross_plat]}",
            check_type="constraint",
        )
    )

    return details
