"""Tests for Linux networking-kernel helpers in check_utils (Phase C-2).

These helpers back the cases/embedded-linux/networking-kernel-001..005 TC
family added by PLAN-linux-networking-kernel-phase-c. Each test class pins
a specific false-positive trap called out in the PLAN's helper design
notes so regressions surface here rather than as silent check drift in
per-TC oracles.

Coverage target: >=3 tests per helper (happy + false-positive trap +
API-variant acceptance). Current count: 4 helpers x 4 tests = 16 tests.
"""

from embedeval.check_utils import (
    has_genl_family_struct,
    has_netlink_kernel_api,
    has_nf_hook_ops_struct,
    has_nf_register_call,
)


class TestHasNfHookOpsStruct:
    """Netfilter hook-ops struct declaration detection."""

    def test_scalar_declaration(self) -> None:
        code = (
            "static struct nf_hook_ops ops = {\n"
            "    .hook = my_hookfn,\n"
            "    .hooknum = NF_INET_PRE_ROUTING,\n"
            "};\n"
        )
        assert has_nf_hook_ops_struct(code)

    def test_array_declaration(self) -> None:
        code = (
            "static struct nf_hook_ops ops[] = {\n"
            "    { .hook = my_hookfn, .hooknum = NF_INET_PRE_ROUTING },\n"
            "};\n"
        )
        assert has_nf_hook_ops_struct(code)

    def test_header_include_alone_is_not_match(self) -> None:
        # A bare include without a declaration must not false-positive.
        code = "#include <linux/netfilter.h>\n#include <linux/netfilter_ipv4.h>\n"
        assert not has_nf_hook_ops_struct(code)

    def test_comment_containing_identifier_is_ignored(self) -> None:
        code = "/* struct nf_hook_ops is the registration type */\n"
        assert not has_nf_hook_ops_struct(code)


class TestHasNfRegisterCall:
    """Netfilter registration call detection — both plural and singular."""

    def test_plural_form(self) -> None:
        code = "nf_register_net_hooks(&init_net, &ops, 1);"
        assert has_nf_register_call(code)

    def test_singular_form(self) -> None:
        code = "nf_register_net_hook(&init_net, &ops);"
        assert has_nf_register_call(code)

    def test_legacy_non_net_form(self) -> None:
        # Pre-namespace variant some older-style modules use.
        code = "nf_register_hook(&ops);"
        assert has_nf_register_call(code)

    def test_unregister_is_not_register(self) -> None:
        code = "nf_unregister_net_hooks(&init_net, &ops, 1);"
        assert not has_nf_register_call(code)


class TestHasNetlinkKernelApi:
    """Netlink kernel-side API enumeration."""

    def test_kernel_create_and_release(self) -> None:
        code = (
            "nl_sk = netlink_kernel_create(&init_net, 31, &cfg);\n"
            "if (nl_sk) netlink_kernel_release(nl_sk);\n"
        )
        apis = has_netlink_kernel_api(code)
        assert "netlink_kernel_create" in apis
        assert "netlink_kernel_release" in apis

    def test_attribute_accessors(self) -> None:
        code = (
            "nla_put_u32(skb, MY_ATTR, 42);\nnla_put_string(skb, MY_ATTR_NAME, name);\n"
        )
        apis = has_netlink_kernel_api(code)
        assert "nla_put_u32" in apis
        assert "nla_put_string" in apis

    def test_no_false_positive_on_struct_field(self) -> None:
        # A struct field named .input or .cfg must NOT pull in non-API
        # matches — the helper requires "name(" form.
        code = "struct netlink_kernel_cfg cfg = { .input = my_cb };\n"
        apis = has_netlink_kernel_api(code)
        assert apis == []

    def test_preserves_first_appearance_order(self) -> None:
        code = (
            "nlmsg_hdr(skb);\n"
            "netlink_kernel_create(&init_net, 31, &cfg);\n"
            "nlmsg_hdr(skb2);\n"  # duplicate; should not appear twice
        )
        apis = has_netlink_kernel_api(code)
        assert apis.index("nlmsg_hdr") < apis.index("netlink_kernel_create")
        assert apis.count("nlmsg_hdr") == 1


class TestHasGenlFamilyStruct:
    """Generic netlink family struct — 5.15 form required."""

    def test_modern_form_with_n_ops(self) -> None:
        code = (
            "static struct genl_family my_family = {\n"
            '    .name = "embedeval_ex",\n'
            "    .version = 1,\n"
            "    .module = THIS_MODULE,\n"
            "    .ops = my_ops,\n"
            "    .n_ops = ARRAY_SIZE(my_ops),\n"
            "    .maxattr = MY_ATTR_MAX,\n"
            "};\n"
        )
        assert has_genl_family_struct(code)

    def test_modern_form_with_small_ops(self) -> None:
        code = (
            "static struct genl_family f = {\n"
            '    .name = "ex",\n'
            "    .small_ops = my_ops,\n"
            "    .n_small_ops = 1,\n"
            "};\n"
        )
        assert has_genl_family_struct(code)

    def test_forward_declaration_without_ops_is_rejected(self) -> None:
        # Without any .ops / .n_ops / .small_ops, the declaration could
        # be the pre-4.10 form and doesn't count.
        code = 'static struct genl_family f = { .name = "ex" };\n'
        assert not has_genl_family_struct(code)

    def test_ops_on_separate_line_from_brace(self) -> None:
        # Common formatting: brace on previous line, .ops several lines
        # into the body — the helper must not require lexical adjacency.
        code = (
            "static struct genl_family f =\n"
            "{\n"
            '\t.name = "ex",\n'
            "\t.version = 1,\n"
            "\n"
            "\t.ops = my_ops,\n"
            "\t.n_ops = 1,\n"
            "};\n"
        )
        assert has_genl_family_struct(code)
