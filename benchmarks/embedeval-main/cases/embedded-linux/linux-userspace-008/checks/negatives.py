"""Negative tests for linux-userspace-008 (eBPF CO-RE kprobe)."""

import re


def _drop_vmlinux_h(code: str) -> str:
    return code.replace('#include "vmlinux.h"\n', "")


def _drop_license_section(code: str) -> str:
    return re.sub(r'\nchar LICENSE\[\][^;]+;\n', "\n", code, count=1)


def _license_non_gpl(code: str) -> str:
    return code.replace('"GPL"', '"Proprietary"')


def _drop_kprobe_sec(code: str) -> str:
    return re.sub(r'SEC\(\s*"kprobe[^"]*"\s*\)\s*\n', "", code, count=1)


def _swap_ringbuf_to_hash_map(code: str) -> str:
    return code.replace(
        "BPF_MAP_TYPE_RINGBUF", "BPF_MAP_TYPE_HASH"
    )


def _raw_task_comm_deref(code: str) -> str:
    """Replace CO-RE read with direct task->comm dereference —
    non-portable, defeats CO-RE."""
    return re.sub(
        r"BPF_CORE_READ_STR_INTO\s*\([^)]+\);",
        "__builtin_memcpy(e->comm, task->comm, TASK_COMM_LEN);",
        code,
        count=1,
    )


def _drop_bpf_kprobe_macro(code: str) -> str:
    """Use a raw function signature with struct pt_regs* — works but
    loses the macro's ergonomics and doesn't match the prompt-required
    BPF_KPROBE macro style."""
    return code.replace(
        "int BPF_KPROBE(trace_unlink, int dfd, struct filename *name)",
        "int trace_unlink(struct pt_regs *ctx)",
    )


def _drop_null_check_on_reserve(code: str) -> str:
    return re.sub(
        r"\n\s*if\s*\(\s*!\s*e\s*\)\s*\n\s*return\s+0;\s*\n",
        "\n",
        code,
        count=1,
    )


def _drop_ringbuf_submit(code: str) -> str:
    return re.sub(
        r"\n\s*bpf_ringbuf_submit\([^;]+;", "", code, count=1
    )


def _drop_bpf_core_read_include(code: str) -> str:
    return code.replace("#include <bpf/bpf_core_read.h>\n", "")


def _comm_oversized(code: str) -> str:
    return code.replace("#define TASK_COMM_LEN 16", "#define TASK_COMM_LEN 64")


def _use_legacy_trace_printk(code: str) -> str:
    """Inject a bpf_trace_printk call — the legacy discouraged helper."""
    return code.replace(
        "bpf_ringbuf_submit(e, 0);",
        'bpf_trace_printk("unlink\\n", 8);\n\tbpf_ringbuf_submit(e, 0);',
    )


NEGATIVES = [
    {
        "name": "drop_vmlinux_h",
        "description": 'Remove #include "vmlinux.h" — struct task_struct / struct filename unresolved; CO-RE field accesses fail to compile.',
        "mutation": _drop_vmlinux_h,
        "must_fail": ["vmlinux_h_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "drop_license_section",
        "description": 'Remove SEC("license") = "GPL" — verifier refuses to load the program (required for GPL-only kernel helpers).',
        "mutation": _drop_license_section,
        "must_fail": ["license_section_gpl_compatible"],
        "factor_id": "F6.1",
    },
    {
        "name": "license_proprietary",
        "description": 'SEC("license") = "Proprietary" — non-GPL-compatible; verifier blocks GPL-only helpers (bpf_get_current_task, bpf_ringbuf_*).',
        "mutation": _license_non_gpl,
        "must_fail": ["license_section_gpl_compatible"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_kprobe_sec",
        "description": 'Remove SEC("kprobe/do_unlinkat") — program has no attachment point; libbpf load skips it.',
        "mutation": _drop_kprobe_sec,
        "must_fail": ["sec_kprobe_macro_used"],
        "factor_id": "F6.1",
    },
    {
        "name": "swap_ringbuf_to_hash_map",
        "description": "BPF_MAP_TYPE_HASH instead of BPF_MAP_TYPE_RINGBUF — wrong map type; reserve/submit don't work on hash maps.",
        "mutation": _swap_ringbuf_to_hash_map,
        "must_fail": ["ringbuf_map_type_declared"],
        "factor_id": "F2.1",
    },
    {
        "name": "raw_task_comm_deref",
        "description": "task->comm direct dereference — compiles for the currently-running kernel but NOT portable across kernel versions (defeats the CO-RE model).",
        "mutation": _raw_task_comm_deref,
        "must_fail": ["bpf_core_read_used", "no_raw_task_struct_deref"],
        "factor_id": "A7.1",
    },
    {
        "name": "drop_bpf_kprobe_macro",
        "description": "Raw signature with struct pt_regs* — skips the BPF_KPROBE macro that unpacks registers into typed args.",
        "mutation": _drop_bpf_kprobe_macro,
        "must_fail": ["bpf_kprobe_signature_macro"],
        "factor_id": "F1.1",
    },
    {
        "name": "drop_null_check_on_reserve",
        "description": "Remove if (!e) check — verifier rejects the load: ringbuf_reserve return value may be NULL; subsequent deref is a load-time verifier failure.",
        "mutation": _drop_null_check_on_reserve,
        "must_fail": ["ringbuf_reserve_null_checked"],
        "factor_id": "E6.1",
    },
    {
        "name": "drop_ringbuf_submit",
        "description": "Drop bpf_ringbuf_submit — reserved slot never published; memory is leaked inside the ringbuf.",
        "mutation": _drop_ringbuf_submit,
        "must_fail": ["ringbuf_reserve_and_submit_paired"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_bpf_core_read_h",
        "description": "Remove bpf_core_read.h include — BPF_CORE_READ* macros unresolved.",
        "mutation": _drop_bpf_core_read_include,
        "must_fail": ["bpf_core_read_h_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "comm_oversized_array",
        "description": "TASK_COMM_LEN redefined to 64 — larger than kernel's 16-byte comm field; reading past the end returns uninitialised stack bytes.",
        "mutation": _comm_oversized,
        "must_fail": ["comm_array_size_16_bytes"],
        "factor_id": "A7.1",
    },
    {
        "name": "use_legacy_trace_printk",
        "description": "Inject bpf_trace_printk — legacy trace_pipe helper; global-shared debug channel, doesn't scale, discouraged in production BPF.",
        "mutation": _use_legacy_trace_printk,
        "must_fail": ["no_bcc_legacy_markers"],
        "factor_id": "F4.2",
    },
]
