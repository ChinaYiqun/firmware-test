#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>

#define TASK_COMM_LEN 16

struct unlink_event {
	__u32 pid;
	char comm[TASK_COMM_LEN];
};

struct {
	__uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, 4096);
} events SEC(".maps");

SEC("kprobe/do_unlinkat")
int BPF_KPROBE(trace_unlink, int dfd, struct filename *name)
{
	struct unlink_event *e;
	struct task_struct *task;

	(void)dfd;
	(void)name;

	e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
	if (!e)
		return 0;

	e->pid = bpf_get_current_pid_tgid() >> 32;

	task = (struct task_struct *)bpf_get_current_task();
	BPF_CORE_READ_STR_INTO(&e->comm, task, comm);

	bpf_ringbuf_submit(e, 0);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
