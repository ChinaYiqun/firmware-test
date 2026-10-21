Write an eBPF kernel-side program in C that traces file unlink
operations via a kprobe and reports events to a userspace consumer
via a ringbuf map. This is the BPF program only (``.bpf.c`` style) —
the userspace loader is out of scope for this task.

Target: NXP i.MX8M Plus, kernel linux-imx 5.15 with BTF enabled
(``CONFIG_DEBUG_INFO_BTF=y``), libbpf 1.x, CO-RE.

Scenario:
- Attach to the kernel function ``do_unlinkat`` via kprobe.
- Each invocation: record the calling PID and the process comm
  (a short identifier string; reading past the end is incorrect).
- Push an event struct (containing the PID and the comm) to a
  ringbuf map for a userspace consumer to drain.

Requirements:
1. Include the canonical BPF-side triad of headers:
   - ``"vmlinux.h"`` (auto-generated kernel type definitions).
   - ``<bpf/bpf_helpers.h>`` (SEC, __uint, bpf_printk, etc.).
   - ``<bpf/bpf_core_read.h>`` (BPF_CORE_READ macros).
   - ``<bpf/bpf_tracing.h>`` (BPF_KPROBE macro).
2. Declare the license string: ``char LICENSE[] SEC("license") = "GPL";``
   (or ``"Dual BSD/GPL"`` / ``"LGPL"`` — any GPL-compatible string).
   Without this, the verifier rejects the load.
3. Declare a ringbuf map:
   - Map name: ``events``.
   - ``type`` = ``BPF_MAP_TYPE_RINGBUF``.
   - ``max_entries`` = 4096.
   - Mark with ``SEC(".maps")``.
4. Declare an event struct with fields for pid (u32) and comm (char
   array). Use a comm array sized TASK_COMM_LEN (16 bytes); DO NOT
   hand-pick a larger size that would read past the kernel struct.
5. Program declaration:
   - ``SEC("kprobe/do_unlinkat")`` section macro.
   - Function signature via ``BPF_KPROBE(name, arg types...)`` —
     this is the macro that abstracts CPU-register reads and gives
     you normal C arguments.
6. Inside the program body:
   - Reserve an event slot via ``bpf_ringbuf_reserve(&events, ...)``.
   - Read PID via ``bpf_get_current_pid_tgid()``.
   - Read the current task's ``comm`` field via ``BPF_CORE_READ`` —
     do NOT dereference ``task->comm`` directly; that is correct C
     but defeats the whole CO-RE portability model.
   - Submit with ``bpf_ringbuf_submit(e, 0)``.
   - Return 0.
7. Do NOT use BCC-style helpers (``bpf_get_current_task_btf``
   without vmlinux.h, bcc Python annotations, etc.).

Output ONLY the complete BPF C source file.
