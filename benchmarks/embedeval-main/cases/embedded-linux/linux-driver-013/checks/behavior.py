"""Behavioral checks for linux-driver-013.

Validates that the driver uses devm_* managed resources end-to-end, never
pairs a devm_* acquisition with a manual free (CVE-2026-23068 pattern), and
guards every ERR_PTR-returning API with IS_ERR.
"""

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    has_is_err_guard,
    has_manual_free_paired_with_devm,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)

    init_body = extract_module_init_body(generated_code) or ""
    exit_body = extract_module_exit_body(generated_code) or ""

    # 1. devm_kzalloc used for per-device state
    uses_devm_kzalloc = has_api_call(init_body, "devm_kzalloc")
    details.append(
        CheckDetail(
            check_name="devm_kzalloc_used_in_probe",
            passed=uses_devm_kzalloc,
            expected="probe() allocates per-device state with devm_kzalloc",
            actual="present" if uses_devm_kzalloc else "missing",
            check_type="constraint",
        )
    )

    # 2. Register bank mapped via devm_platform_ioremap_resource
    uses_devm_ioremap = has_api_call(
        init_body, "devm_platform_ioremap_resource"
    ) or has_api_call(init_body, "devm_ioremap_resource")
    details.append(
        CheckDetail(
            check_name="devm_ioremap_used",
            passed=uses_devm_ioremap,
            expected="probe() maps registers via devm_platform_ioremap_resource",
            actual="present" if uses_devm_ioremap else "missing",
            check_type="constraint",
        )
    )

    # 3. Optional clock acquired via devm_clk_get_optional (or devm_clk_get)
    uses_devm_clk = has_api_call(init_body, "devm_clk_get_optional") or has_api_call(
        init_body, "devm_clk_get"
    )
    details.append(
        CheckDetail(
            check_name="devm_clk_get_used",
            passed=uses_devm_clk,
            expected="probe() acquires clock via devm_clk_get_optional",
            actual="present" if uses_devm_clk else "missing",
            check_type="constraint",
        )
    )

    # 4. GPIO descriptor acquired via devm_gpiod_get (or _optional variant).
    # Per CLAUDE.md rule on API variants: accept both spellings. Note that
    # for a *reset* GPIO the mandatory form is preferred — _optional would
    # allow the pin to be absent, which is semantically weak for reset —
    # but we do not enforce that distinction at the check level.
    uses_devm_gpiod = has_api_call(init_body, "devm_gpiod_get") or has_api_call(
        init_body, "devm_gpiod_get_optional"
    )
    details.append(
        CheckDetail(
            check_name="devm_gpiod_get_used",
            passed=uses_devm_gpiod,
            expected="probe() acquires GPIO via devm_gpiod_get / devm_gpiod_get_optional",
            actual="present" if uses_devm_gpiod else "missing",
            check_type="constraint",
        )
    )

    # 5. Threaded IRQ registered via devm_request_threaded_irq
    uses_devm_irq = has_api_call(init_body, "devm_request_threaded_irq")
    details.append(
        CheckDetail(
            check_name="devm_threaded_irq_used",
            passed=uses_devm_irq,
            expected="probe() registers IRQ with devm_request_threaded_irq",
            actual="present" if uses_devm_irq else "missing",
            check_type="constraint",
        )
    )

    # 6. IS_ERR guards every ERR_PTR-returning API used in probe
    # (devm_clk_get_optional, devm_gpiod_get, devm_ioremap_resource,
    #  devm_platform_ioremap_resource)
    err_ptr_apis = [
        "devm_clk_get_optional",
        "devm_clk_get",
        "devm_gpiod_get",
        "devm_gpiod_get_optional",
        "devm_platform_ioremap_resource",
        "devm_ioremap_resource",
    ]
    missing_guards: list[str] = []
    for api in err_ptr_apis:
        if has_api_call(init_body, api) and not has_is_err_guard(init_body, api):
            missing_guards.append(api)
    details.append(
        CheckDetail(
            check_name="is_err_guards_err_ptr_apis",
            passed=len(missing_guards) == 0,
            expected="IS_ERR guards every ERR_PTR-returning API result",
            actual="all guarded"
            if not missing_guards
            else f"unguarded: {missing_guards}",
            check_type="constraint",
        )
    )

    # 7. No manual free paired with any devm_* (CVE-2026-23068 pattern).
    # Checked across the whole source, not just probe/remove, because the
    # bug surfaces wherever the manual free lives.
    double_free_pairs = has_manual_free_paired_with_devm(generated_code)
    details.append(
        CheckDetail(
            check_name="no_manual_free_for_devm_resource",
            passed=len(double_free_pairs) == 0,
            expected="No manual free paired with a devm_* managed resource",
            actual="clean"
            if not double_free_pairs
            else f"double-free risk: {double_free_pairs}",
            check_type="constraint",
        )
    )

    # 8. remove() body is effectively empty-of-cleanup. Allow dev_info /
    # platform_set_drvdata(NULL) / return statements; reject actual
    # release calls the devm layer already performs.
    forbidden_in_remove = [
        "free_irq",
        "iounmap",
        "clk_put",
        "gpiod_put",
        "kfree",
        "devm_kfree",  # redundant — devm frees on detach
    ]
    remove_violations = [
        api for api in forbidden_in_remove if has_api_call(exit_body, api)
    ]
    details.append(
        CheckDetail(
            check_name="remove_does_not_double_free",
            passed=len(remove_violations) == 0,
            expected="remove() does not manually release devm-managed resources",
            actual="clean"
            if not remove_violations
            else f"forbidden release calls in remove: {remove_violations}",
            check_type="constraint",
        )
    )

    # 9. Probe returns PTR_ERR on error-pointer failure paths
    # (error propagation, not -EIO or hardcoded errno).
    has_ptr_err = scoped_contains(generated_code, "PTR_ERR(", scope="code_only")
    details.append(
        CheckDetail(
            check_name="ptr_err_used_for_error_propagation",
            passed=has_ptr_err,
            expected="PTR_ERR() propagates the actual error code from ERR_PTR APIs",
            actual="present" if has_ptr_err else "missing",
            check_type="constraint",
        )
    )

    # 10. No plain kzalloc/kmalloc for the per-device state (would be
    # correct C but leaks on probe failure path without goto cleanup).
    # scoped_contains(..., scope='code_only') per CLAUDE.md 2026-04-19:
    # strip both comments AND string literals so pr_err("use kzalloc")
    # doesn't false-positive this check.
    has_plain_kzalloc_for_state = scoped_contains(
        generated_code, "kzalloc(", scope="code_only"
    ) and not scoped_contains(generated_code, "devm_kzalloc", scope="code_only")
    details.append(
        CheckDetail(
            check_name="no_plain_kzalloc_for_device_state",
            passed=not has_plain_kzalloc_for_state,
            expected="per-device state uses devm_kzalloc, not plain kzalloc",
            actual="clean"
            if not has_plain_kzalloc_for_state
            else "plain kzalloc found (would leak on probe failure)",
            check_type="constraint",
        )
    )

    # 11. No cross-platform API contamination
    cross_plat = check_no_cross_platform_apis(
        generated_code, skip_platforms=["Linux_Userspace", "POSIX"]
    )
    details.append(
        CheckDetail(
            check_name="no_cross_platform_apis",
            passed=len(cross_plat) == 0,
            expected="No FreeRTOS / Zephyr / Arduino / STM32 HAL APIs",
            actual="clean"
            if not cross_plat
            else f"found: {[a for a, _ in cross_plat]}",
            check_type="constraint",
        )
    )

    return details
