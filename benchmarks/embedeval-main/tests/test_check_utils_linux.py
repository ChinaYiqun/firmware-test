"""Tests for Linux kernel 5.15+ and Yocto kirkstone helpers in check_utils.

These helpers back the linux-driver-009..016 and yocto-009..012 TC families
added by PLAN-linux-tc-expansion-phase-a. Each test class pins a specific
false-positive trap from CLAUDE.md corrections so regressions surface here
rather than as silent check drift in per-TC oracles.
"""

import pytest

from embedeval.check_utils import (
    _DEVM_TO_MANUAL_FREE,
    _ERR_PTR_RETURNING_APIS,
    extract_module_exit_body,
    extract_module_init_body,
    has_is_err_guard,
    has_manual_free_paired_with_devm,
    returns_err_ptr,
    sleepable_calls_in_atomic_ctx,
    strip_yocto_comments,
    yocto_contains,
    yocto_has_legacy_override,
    yocto_has_override,
)


class TestExtractModuleInitBody:
    """probe() / __init function body extraction."""

    def test_platform_probe(self) -> None:
        code = (
            "static int mydrv_probe(struct platform_device *pdev)\n"
            "{\n"
            "    int ret = 0;\n"
            "    return ret;\n"
            "}\n"
        )
        body = extract_module_init_body(code)
        assert body is not None
        assert "int ret = 0;" in body
        assert "return ret;" in body

    def test_module_init_annotated(self) -> None:
        code = (
            "static int __init mydrv_init(void)\n"
            "{\n"
            "    platform_driver_register(&drv);\n"
            "    return 0;\n"
            "}\n"
        )
        body = extract_module_init_body(code)
        assert body is not None
        assert "platform_driver_register" in body

    def test_no_init_returns_none(self) -> None:
        assert extract_module_init_body("void helper(void) { return; }") is None

    def test_scopes_away_from_exit_body(self) -> None:
        """init body must not leak the __exit function's body — the
        PLAN-remaining-blindspots linux-001 regression that motivated
        scope discipline."""
        code = (
            "static int mydrv_probe(struct platform_device *pdev) { return 0; }\n"
            "static int mydrv_remove(struct platform_device *pdev) {\n"
            "    unregister_chrdev_region(devno, 1);\n"
            "    return 0;\n"
            "}\n"
        )
        body = extract_module_init_body(code)
        assert body is not None
        assert "unregister_chrdev_region" not in body


class TestExtractModuleExitBody:
    """remove() / __exit function body extraction."""

    def test_platform_remove(self) -> None:
        code = (
            "static int mydrv_remove(struct platform_device *pdev)\n"
            "{\n"
            "    free_irq(irq, dev);\n"
            "    return 0;\n"
            "}\n"
        )
        body = extract_module_exit_body(code)
        assert body is not None
        assert "free_irq" in body

    def test_module_exit_annotated(self) -> None:
        code = (
            "static void __exit mydrv_exit(void)\n"
            "{\n"
            "    platform_driver_unregister(&drv);\n"
            "}\n"
        )
        body = extract_module_exit_body(code)
        assert body is not None
        assert "platform_driver_unregister" in body

    def test_no_exit_returns_none(self) -> None:
        assert extract_module_exit_body("int foo(void) { return 0; }") is None


class TestManualFreePairedWithDevm:
    """CVE-2026-23068 double-free detector."""

    def test_devm_with_manual_free_flagged(self) -> None:
        code = (
            "clk = devm_clk_get(&pdev->dev, NULL);\n"
            "if (IS_ERR(clk)) return PTR_ERR(clk);\n"
            "clk_put(clk);  /* BUG: devm will also put this */\n"
        )
        pairs = has_manual_free_paired_with_devm(code)
        assert ("devm_clk_get", "clk_put") in pairs

    def test_devm_only_no_bug(self) -> None:
        code = (
            "buf = devm_kzalloc(&pdev->dev, 256, GFP_KERNEL);\n"
            "if (!buf) return -ENOMEM;\n"
        )
        assert has_manual_free_paired_with_devm(code) == []

    def test_manual_only_no_bug(self) -> None:
        """Plain kzalloc + kfree is correct; only devm+manual is the CVE."""
        code = (
            "buf = kzalloc(256, GFP_KERNEL);\n"
            "if (!buf) return -ENOMEM;\n"
            "/* ... */\n"
            "kfree(buf);\n"
        )
        assert has_manual_free_paired_with_devm(code) == []

    def test_substring_alias_trap(self) -> None:
        """``kfree_rcu`` must not match ``kfree`` (word-boundary regression)."""
        code = (
            "buf = devm_kzalloc(&pdev->dev, 256, GFP_KERNEL);\nkfree_rcu(buf, rcu);\n"
        )
        # kfree_rcu is a distinct API; devm_kzalloc should NOT pair with it
        pairs = has_manual_free_paired_with_devm(code)
        assert ("devm_kzalloc", "kfree") not in pairs


class TestReturnsErrPtr:
    def test_known_err_ptr_api(self) -> None:
        assert returns_err_ptr("devm_clk_get")
        assert returns_err_ptr("devm_platform_ioremap_resource")

    def test_non_err_ptr_api(self) -> None:
        assert not returns_err_ptr("kmalloc")
        assert not returns_err_ptr("some_made_up_api")

    @pytest.mark.parametrize("api", sorted(_ERR_PTR_RETURNING_APIS))
    def test_every_declared_api_detected(self, api: str) -> None:
        """Every entry in the declared ERR_PTR-returning API set must be
        recognized by returns_err_ptr. Pins the constant against drift."""
        assert returns_err_ptr(api)


class TestDevmManualFreePairingConstant:
    """Every entry in _DEVM_TO_MANUAL_FREE must round-trip through the
    detector. Parametrized so a new devm_* → manual_free pair added to
    the constant is forced to have at least one detection test."""

    @pytest.mark.parametrize(
        "devm_api,manual_free",
        [(devm, m) for devm, manuals in _DEVM_TO_MANUAL_FREE.items() for m in manuals],
    )
    def test_detects_pair(self, devm_api: str, manual_free: str) -> None:
        code = f"x = {devm_api}(dev, 16, GFP_KERNEL);\n/* ... */\n{manual_free}(x);\n"
        pairs = has_manual_free_paired_with_devm(code)
        assert (devm_api, manual_free) in pairs

    @pytest.mark.parametrize("devm_api", sorted(_DEVM_TO_MANUAL_FREE.keys()))
    def test_devm_alone_is_clean(self, devm_api: str) -> None:
        """devm_* call with no matching manual free anywhere must not trip."""
        code = f"x = {devm_api}(dev, 16, GFP_KERNEL);\n"
        assert has_manual_free_paired_with_devm(code) == []


class TestHasIsErrGuard:
    def test_is_err_guards_assignment(self) -> None:
        code = (
            "clk = devm_clk_get(&pdev->dev, NULL);\n"
            "if (IS_ERR(clk)) return PTR_ERR(clk);\n"
        )
        assert has_is_err_guard(code, "devm_clk_get")

    def test_plain_null_check_rejected(self) -> None:
        """NULL check is a bug for ERR_PTR-returning APIs — non-NULL
        error-coded pointers silently pass ``if (!x)``."""
        code = "clk = devm_clk_get(&pdev->dev, NULL);\nif (!clk) return -ENODEV;\n"
        assert not has_is_err_guard(code, "devm_clk_get")

    def test_is_err_or_null_accepted(self) -> None:
        code = (
            'node = of_find_node_by_name(NULL, "foo");\n'
            "if (IS_ERR_OR_NULL(node)) return -ENODEV;\n"
        )
        assert has_is_err_guard(code, "of_find_node_by_name")

    def test_no_call_returns_false(self) -> None:
        assert not has_is_err_guard("/* no call */", "devm_clk_get")

    def test_struct_member_lhs_accepted(self) -> None:
        """Drivers idiomatically store resources in a per-device struct;
        ``priv->regs = devm_...`` + ``if (IS_ERR(priv->regs))`` must match."""
        code = (
            "priv->regs = devm_platform_ioremap_resource(pdev, 0);\n"
            "if (IS_ERR(priv->regs))\n"
            "    return PTR_ERR(priv->regs);\n"
        )
        assert has_is_err_guard(code, "devm_platform_ioremap_resource")


class TestSleepableCallsInAtomicCtx:
    def test_msleep_in_spinlock_flagged(self) -> None:
        body = "msleep(10);\nreadl(regs);\n"
        assert "msleep" in sleepable_calls_in_atomic_ctx(body)

    def test_copy_to_user_in_irq_flagged(self) -> None:
        body = "if (copy_to_user(ubuf, kbuf, n))\n    return -EFAULT;\n"
        assert "copy_to_user" in sleepable_calls_in_atomic_ctx(body)

    def test_clean_body_empty_list(self) -> None:
        body = "writel(val, regs);\nspin_unlock_irqrestore(&lock, flags);\n"
        assert sleepable_calls_in_atomic_ctx(body) == []


class TestYoctoHelpers:
    def test_strip_yocto_comments_preserves_uri(self) -> None:
        text = (
            "# leading comment\n"
            'SRC_URI = "file://foo.patch \\\n'
            '           git://example.com/repo.git;branch=main"\n'
        )
        out = strip_yocto_comments(text)
        assert "leading comment" not in out
        assert "file://foo.patch" in out
        assert "git://example.com" in out

    def test_yocto_contains_ignores_commented_line(self) -> None:
        text = '# RDEPENDS:${PN} += "foo"\nRDEPENDS:${PN} += "bar"\n'
        assert yocto_contains(text, "bar")
        # commented-out foo should not count
        assert not yocto_contains(text, 'RDEPENDS:${PN} += "foo"')

    def test_yocto_has_override_colon_form(self) -> None:
        text = 'FILESEXTRAPATHS:prepend := "${THISDIR}/files:"\n'
        assert yocto_has_override(text, "FILESEXTRAPATHS", "prepend")
        assert not yocto_has_legacy_override(text, "FILESEXTRAPATHS", "prepend")

    def test_yocto_has_legacy_override_underscore_form(self) -> None:
        text = 'FILESEXTRAPATHS_prepend := "${THISDIR}/files:"\n'
        assert yocto_has_legacy_override(text, "FILESEXTRAPATHS", "prepend")
        assert not yocto_has_override(text, "FILESEXTRAPATHS", "prepend")

    def test_yocto_has_override_rejects_mismatched_name(self) -> None:
        text = 'FILESEXTRAPATHS:append := "foo"\n'
        assert not yocto_has_override(text, "FILESEXTRAPATHS", "prepend")
        assert yocto_has_override(text, "FILESEXTRAPATHS", "append")
