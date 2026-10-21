"""Behavioral checks for linux-userspace-008 (eBPF CO-RE discipline)."""

import re

from embedeval.check_utils import (
    has_api_call,
    has_bpf_core_read,
    has_bpf_sec_macro,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)

    # 1. SEC("kprobe/...") program section present.
    sec_found = has_bpf_sec_macro(generated_code)
    has_kprobe_sec = "kprobe" in sec_found
    details.append(
        CheckDetail(
            check_name="sec_kprobe_macro_used",
            passed=has_kprobe_sec,
            expected='SEC("kprobe/<function>") attachment declaration',
            actual=f"SEC flavours found: {sec_found}",
            check_type="constraint",
        )
    )

    # 2. SEC("license") + GPL-compatible license string.
    has_license_sec = "license" in sec_found
    has_gpl_compat = bool(
        re.search(
            r'SEC\(\s*"license"\s*\)\s*=\s*"(?:GPL|Dual BSD/GPL|LGPL)"',
            stripped,
        )
    )
    details.append(
        CheckDetail(
            check_name="license_section_gpl_compatible",
            passed=has_license_sec and has_gpl_compat,
            expected='char LICENSE[] SEC("license") = "GPL" (or Dual BSD/GPL / LGPL)',
            actual=f"sec_license={has_license_sec}, gpl_compat={has_gpl_compat}",
            check_type="constraint",
        )
    )

    # 3. .maps section for ringbuf declaration.
    has_maps_sec = ".maps" in sec_found
    details.append(
        CheckDetail(
            check_name="maps_section_declared",
            passed=has_maps_sec,
            expected='SEC(".maps") on a ringbuf map declaration',
            actual="present" if has_maps_sec else "missing",
            check_type="constraint",
        )
    )

    # 4. Ringbuf map type.
    has_ringbuf_type = "BPF_MAP_TYPE_RINGBUF" in stripped
    details.append(
        CheckDetail(
            check_name="ringbuf_map_type_declared",
            passed=has_ringbuf_type,
            expected="BPF_MAP_TYPE_RINGBUF",
            actual="present" if has_ringbuf_type else "missing",
            check_type="constraint",
        )
    )

    # 5. BPF_KPROBE macro for the program signature.
    has_bpf_kprobe = bool(re.search(r"\bBPF_KPROBE\s*\(", stripped))
    details.append(
        CheckDetail(
            check_name="bpf_kprobe_signature_macro",
            passed=has_bpf_kprobe,
            expected="int BPF_KPROBE(name, ...) signature",
            actual="present" if has_bpf_kprobe else "missing",
            check_type="constraint",
        )
    )

    # 6. CO-RE read macro used — NOT a raw pointer dereference like
    # task->comm.
    has_core = has_bpf_core_read(generated_code)
    details.append(
        CheckDetail(
            check_name="bpf_core_read_used",
            passed=has_core,
            expected="BPF_CORE_READ* macro used for kernel struct fields",
            actual="present" if has_core else "missing",
            check_type="constraint",
        )
    )

    # 7. No raw deref of the task_struct pointer. Extract the LHS of the
    # ``<lhs> = (struct task_struct *)bpf_get_current_task()`` assignment —
    # variable name is NOT hardcoded (may be ``task``, ``t``, ``ts``,
    # ``cur``, ``tsk``, …). Then verify no ``<lhs>->`` deref exists
    # outside BPF_CORE_READ* macros.
    without_core_calls = re.sub(
        r"BPF_CORE_READ(?:_\w+)?\([^)]*\)", "", stripped
    )
    task_lhs_match = re.search(
        r"(\w+)\s*=\s*(?:\(\s*struct\s+task_struct\s*\*\s*\))?\s*"
        r"bpf_get_current_task(?:_btf)?\s*\(\s*\)",
        stripped,
    )
    task_var = task_lhs_match.group(1) if task_lhs_match else ""
    has_raw_task_deref = bool(task_var) and bool(
        re.search(rf"\b{re.escape(task_var)}\s*->\s*\w+", without_core_calls)
    )
    details.append(
        CheckDetail(
            check_name="no_raw_task_struct_deref",
            passed=not has_raw_task_deref,
            expected="No raw <task_ptr>-> deref outside BPF_CORE_READ",
            actual="clean"
            if not has_raw_task_deref
            else f"raw {task_var}->  deref found; must use BPF_CORE_READ",
            check_type="constraint",
        )
    )

    # 8. Ringbuf reserve/submit pair.
    has_reserve = has_api_call(stripped, "bpf_ringbuf_reserve")
    has_submit = has_api_call(stripped, "bpf_ringbuf_submit") or has_api_call(
        stripped, "bpf_ringbuf_discard"
    )
    details.append(
        CheckDetail(
            check_name="ringbuf_reserve_and_submit_paired",
            passed=has_reserve and has_submit,
            expected="bpf_ringbuf_reserve + bpf_ringbuf_submit / _discard paired",
            actual=f"reserve={has_reserve}, submit={has_submit}",
            check_type="constraint",
        )
    )

    # 9. NULL-check the reserve return — variable name NOT hardcoded
    # (accepts e, event, evt, ep, …). Extract the LHS from
    # ``<lhs> = bpf_ringbuf_reserve(...)`` then verify the next few
    # statements contain ``if (!<lhs>)`` or ``if (<lhs> == NULL)``.
    reserve_lhs = re.search(
        r"(\w+)\s*=\s*bpf_ringbuf_reserve\s*\([^;]+\)\s*;", stripped
    )
    reserve_var = reserve_lhs.group(1) if reserve_lhs else ""
    has_null_check = bool(reserve_var) and bool(
        re.search(
            rf"(\w+)\s*=\s*bpf_ringbuf_reserve[^;]+;\s*"
            rf"(?:/\*.*?\*/\s*)?\s*"
            rf"if\s*\(\s*(?:!\s*{re.escape(reserve_var)}|"
            rf"{re.escape(reserve_var)}\s*==\s*NULL)\s*\)",
            stripped,
            re.DOTALL,
        )
    )
    details.append(
        CheckDetail(
            check_name="ringbuf_reserve_null_checked",
            passed=has_null_check,
            expected="``if (!<lhs>)`` / ``if (<lhs> == NULL)`` after bpf_ringbuf_reserve (any variable name)",
            actual=(
                f"null-checked {reserve_var!r}"
                if has_null_check
                else f"reserve LHS={reserve_var!r}; null-check missing or mismatched"
            ),
            check_type="constraint",
        )
    )

    # 9a. Event struct declares BOTH a pid field AND a comm field —
    # closes the gap where an LLM could declare a struct with only one
    # of the two, silently losing the required field content.
    # Look for ``struct <name> { ... }`` block(s) reachable from the
    # ringbuf reserve path; within those, require both pid and comm.
    struct_bodies = re.findall(
        r"struct\s+\w+\s*\{([^}]+)\}\s*;", stripped, re.DOTALL
    )
    has_pid_field = any(
        re.search(r"\b(?:__u32|u32|uint32_t|int)\s+pid\b", body)
        for body in struct_bodies
    )
    has_comm_field = any(
        re.search(r"\bchar\s+comm\s*\[", body) for body in struct_bodies
    )
    details.append(
        CheckDetail(
            check_name="event_struct_has_pid_and_comm_fields",
            passed=has_pid_field and has_comm_field,
            expected="event struct declares both a pid field and a comm[] field",
            actual=f"pid_field={has_pid_field}, comm_field={has_comm_field}",
            check_type="constraint",
        )
    )

    # 10. bpf_get_current_pid_tgid used for PID.
    has_pid_tgid = has_api_call(stripped, "bpf_get_current_pid_tgid")
    details.append(
        CheckDetail(
            check_name="current_pid_tgid_used",
            passed=has_pid_tgid,
            expected="bpf_get_current_pid_tgid() for PID extraction",
            actual="present" if has_pid_tgid else "missing",
            check_type="constraint",
        )
    )

    # 11. TASK_COMM_LEN (16) used as comm array size — not a custom larger
    # value that would read past the kernel struct.
    # Accept: #define TASK_COMM_LEN 16, or literal char comm[16].
    comm_16 = bool(
        re.search(r"#define\s+TASK_COMM_LEN\s+16\b", stripped)
    ) or bool(re.search(r"char\s+comm\s*\[\s*16\s*\]", stripped))
    comm_oversized = bool(
        re.search(r"char\s+comm\s*\[\s*(?:32|64|128|256|512|1024)\s*\]", stripped)
    )
    details.append(
        CheckDetail(
            check_name="comm_array_size_16_bytes",
            passed=comm_16 and not comm_oversized,
            expected="comm array sized TASK_COMM_LEN (16 bytes)",
            actual=(
                "present"
                if comm_16 and not comm_oversized
                else f"comm_16={comm_16}, oversized={comm_oversized}"
            ),
            check_type="constraint",
        )
    )

    # 12. No BCC legacy hints — no Python markers, no bpf_trace_printk
    # (discouraged). Accept bpf_printk (the libbpf CO-RE equivalent).
    has_python_markers = bool(
        re.search(r'#pragma\s+(?:BCC|bcc)|from\s+bcc\s+import', stripped)
    )
    has_legacy_trace_printk = bool(
        re.search(r"\bbpf_trace_printk\s*\(", stripped)
    )
    details.append(
        CheckDetail(
            check_name="no_bcc_legacy_markers",
            passed=not has_python_markers and not has_legacy_trace_printk,
            expected="No BCC Python markers or bpf_trace_printk",
            actual=(
                "clean"
                if not (has_python_markers or has_legacy_trace_printk)
                else f"bcc={has_python_markers}, legacy_printk={has_legacy_trace_printk}"
            ),
            check_type="constraint",
        )
    )

    return details
