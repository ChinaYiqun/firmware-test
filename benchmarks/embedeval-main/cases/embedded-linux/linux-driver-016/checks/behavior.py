"""Behavioral checks for linux-driver-016.

Tests that the LLM distinguishes error-return conventions:

- clk_get / reset_control_get return ERR_PTR → MUST be guarded with IS_ERR
- ioremap returns NULL → MUST be guarded with !ptr (NOT IS_ERR, which would
  accept NULL as success and later dereference it)
- platform_get_irq returns int<0 → MUST be guarded with `< 0`

Failure mode: LLM uses NULL check on ERR_PTR APIs or IS_ERR on NULL APIs.
"""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    has_is_err_guard,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def _init_has_plain_null_check(body: str, var: str) -> bool:
    """Whether ``if (!<var>)`` or ``if (<var> == NULL)`` appears in body."""
    return bool(
        re.search(rf"if\s*\(\s*!\s*{re.escape(var)}\s*\)", body)
        or re.search(rf"if\s*\(\s*{re.escape(var)}\s*==\s*NULL\s*\)", body)
    )


def _init_has_is_err_on_var(body: str, var: str) -> bool:
    return bool(
        re.search(rf"IS_ERR(?:_OR_NULL)?\s*\(\s*{re.escape(var)}\s*\)", body)
    )


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    init_body = extract_module_init_body(generated_code) or ""
    exit_body = extract_module_exit_body(generated_code) or ""
    stripped = strip_comments(generated_code)

    # 1. clk_get used (traditional, non-devm).
    uses_clk_get = has_api_call(init_body, "clk_get") and not has_api_call(
        init_body, "devm_clk_get"
    )
    details.append(
        CheckDetail(
            check_name="uses_traditional_clk_get",
            passed=uses_clk_get,
            expected="probe() uses clk_get (non-devm)",
            actual="present" if uses_clk_get else "missing or devm variant used",
            check_type="constraint",
        )
    )

    # 2. IS_ERR guards clk_get result (per-API call guard check).
    clk_guarded = has_is_err_guard(init_body, "clk_get")
    details.append(
        CheckDetail(
            check_name="is_err_guards_clk_get",
            passed=clk_guarded,
            expected="clk_get return value guarded with IS_ERR",
            actual="guarded" if clk_guarded else "MISSING IS_ERR guard (ERR_PTR not detected!)",
            check_type="constraint",
        )
    )

    # 3. reset_control_get used + IS_ERR-guarded.
    uses_reset_get = has_api_call(init_body, "reset_control_get")
    reset_guarded = has_is_err_guard(init_body, "reset_control_get")
    details.append(
        CheckDetail(
            check_name="is_err_guards_reset_control_get",
            passed=uses_reset_get and reset_guarded,
            expected="reset_control_get + IS_ERR guard",
            actual=f"used={uses_reset_get}, guarded={reset_guarded}",
            check_type="constraint",
        )
    )

    # 4. ioremap used AND guarded with NULL check (NOT IS_ERR).
    uses_ioremap = has_api_call(init_body, "ioremap")
    # Find the variable assigned from ioremap.
    regs_match = re.search(
        r"([A-Za-z_]\w*(?:(?:\s*->\s*|\s*\.\s*)\w+)*)\s*=\s*ioremap\s*\([^;]*\)\s*;",
        init_body,
    )
    regs_var = re.sub(r"\s+", "", regs_match.group(1)) if regs_match else ""
    # Normalize body whitespace for the check.
    norm_body = re.sub(r"\s+", "", init_body)
    regs_null_checked = bool(regs_var) and (
        f"if(!{regs_var})" in norm_body or f"if({regs_var}==NULL)" in norm_body
    )
    details.append(
        CheckDetail(
            check_name="null_check_on_ioremap",
            passed=uses_ioremap and regs_null_checked,
            expected="ioremap result guarded with NULL check (ioremap returns NULL on fail, not ERR_PTR)",
            actual=f"used={uses_ioremap}, null-checked={regs_null_checked}",
            check_type="constraint",
        )
    )

    # 5. Must NOT use IS_ERR on ioremap result — that is a category error.
    regs_wrongly_is_err = bool(regs_var) and re.search(
        rf"IS_ERR(?:_OR_NULL)?\s*\(\s*{re.escape(regs_var)}\s*\)",
        re.sub(r"\s+", "", init_body),
    )
    # The regex above is already normalized; reuse norm_body path.
    regs_wrongly_is_err = bool(regs_var) and (
        f"IS_ERR({regs_var})" in norm_body or f"IS_ERR_OR_NULL({regs_var})" in norm_body
    )
    details.append(
        CheckDetail(
            check_name="no_is_err_on_ioremap",
            passed=not regs_wrongly_is_err,
            expected="ioremap result NOT wrapped in IS_ERR (category error)",
            actual="clean" if not regs_wrongly_is_err else "WRONG: IS_ERR on NULL-returning API",
            check_type="constraint",
        )
    )

    # 6. platform_get_irq used AND guarded with int<0 check.
    uses_get_irq = has_api_call(init_body, "platform_get_irq")
    # Grab the int result var.
    irq_match = re.search(
        r"([A-Za-z_]\w*(?:(?:\s*->\s*|\s*\.\s*)\w+)*)\s*=\s*platform_get_irq\s*\([^;]*\)\s*;",
        init_body,
    )
    irq_var = re.sub(r"\s+", "", irq_match.group(1)) if irq_match else ""
    irq_neg_checked = bool(irq_var) and (
        f"if({irq_var}<0)" in norm_body
        or f"{irq_var}<0)" in norm_body
    )
    details.append(
        CheckDetail(
            check_name="neg_check_on_platform_get_irq",
            passed=uses_get_irq and irq_neg_checked,
            expected="platform_get_irq result guarded with `< 0` (int return, not ERR_PTR)",
            actual=f"used={uses_get_irq}, neg-checked={irq_neg_checked}",
            check_type="constraint",
        )
    )

    # 7. Must NOT use IS_ERR on platform_get_irq — it returns int, not ERR_PTR.
    # Include IS_ERR_VALUE in the bad-pattern list: it's a third guard
    # variant that silently accepts small-positive irq numbers as error.
    irq_wrongly_is_err = bool(irq_var) and (
        f"IS_ERR({irq_var})" in norm_body
        or f"IS_ERR_OR_NULL({irq_var})" in norm_body
        or f"IS_ERR_VALUE({irq_var})" in norm_body
    )
    details.append(
        CheckDetail(
            check_name="no_is_err_on_platform_get_irq",
            passed=not irq_wrongly_is_err,
            expected="platform_get_irq result NOT wrapped in IS_ERR (int return)",
            actual="clean" if not irq_wrongly_is_err else "WRONG: IS_ERR on int-returning API",
            check_type="constraint",
        )
    )

    # 8. kzalloc used and guarded with plain NULL check (kzalloc returns NULL).
    uses_kzalloc = has_api_call(init_body, "kzalloc") and not has_api_call(
        init_body, "devm_kzalloc"
    )
    priv_match = re.search(
        r"([A-Za-z_]\w*)\s*=\s*kzalloc\s*\([^;]*\)\s*;", init_body
    )
    priv_var = priv_match.group(1) if priv_match else ""
    priv_null_checked = bool(priv_var) and _init_has_plain_null_check(init_body, priv_var)
    details.append(
        CheckDetail(
            check_name="null_check_on_kzalloc",
            passed=uses_kzalloc and priv_null_checked,
            expected="kzalloc result guarded with NULL check",
            actual=f"used={uses_kzalloc}, null-checked={priv_null_checked}",
            check_type="constraint",
        )
    )

    # 9. PTR_ERR used for error propagation on ERR_PTR paths.
    has_ptr_err = scoped_contains(generated_code, "PTR_ERR(", scope="code_only")
    details.append(
        CheckDetail(
            check_name="ptr_err_propagated",
            passed=has_ptr_err,
            expected="PTR_ERR() propagates the actual errno from ERR_PTR APIs",
            actual="present" if has_ptr_err else "missing — hardcoded errno likely",
            check_type="constraint",
        )
    )

    # 10. goto-style reverse cleanup: remove() must release every resource
    # probe acquired (clk_put, reset_control_put, iounmap, free_irq, kfree).
    remove_releases = {
        "free_irq": has_api_call(exit_body, "free_irq"),
        "iounmap": has_api_call(exit_body, "iounmap"),
        "reset_control_put": has_api_call(exit_body, "reset_control_put"),
        "clk_put": has_api_call(exit_body, "clk_put"),
        "kfree": has_api_call(exit_body, "kfree"),
    }
    missing_release = [k for k, v in remove_releases.items() if not v]
    details.append(
        CheckDetail(
            check_name="remove_releases_all_resources",
            passed=len(missing_release) == 0,
            expected="remove() calls free_irq, iounmap, reset_control_put, clk_put, kfree",
            actual="all present" if not missing_release else f"missing: {missing_release}",
            check_type="constraint",
        )
    )

    # 11. No cross-platform API contamination.
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

    # 12. No devm_* usage — this TC specifically asks for traditional APIs
    # to exercise manual lifecycle + error discipline. Match any devm_*
    # identifier with a function-call shape, not a fixed enumeration —
    # devm_ioremap_resource / devm_reset_control_get / devm_gpiod_get_optional
    # etc. all count.
    devm_calls = re.findall(r"\bdevm_\w+\s*\(", stripped)
    details.append(
        CheckDetail(
            check_name="no_devm_apis_used",
            passed=len(devm_calls) == 0,
            expected="non-devm (traditional) APIs only per prompt",
            actual="clean"
            if not devm_calls
            else f"devm_* found: {sorted(set(devm_calls))}",
            check_type="constraint",
        )
    )

    return details
