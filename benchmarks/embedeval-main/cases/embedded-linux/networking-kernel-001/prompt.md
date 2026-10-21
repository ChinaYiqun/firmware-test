Write a Linux 5.15 kernel module that registers a netfilter hook on the
IPv4 pre-routing chain of the initial network namespace. The hook
inspects every incoming IPv4 packet, bumps a per-module counter, and
defers any heavy-weight reporting to a sleepable execution context.

Scenario:
- The hook runs inside the receive path of the kernel network stack —
  the context is NOT a plain process, NOT a hardirq, but the third
  kernel execution context that packet-forwarding traverses.
- Because of that context, the hook body MUST NOT sleep, MUST NOT
  allocate with the default sleep-allowed memory flag, and MUST NOT
  grab a mutex. All heavy work — dev_info / pr_info tracing — moves
  out into a worker scheduled on the shared execution pool.
- Registration is per-netns. Use the initial network namespace.
- Module init registers the hook LAST (after the worker descriptor is
  initialised). If registration fails, no cleanup is needed because
  nothing was acquired; but if a later init step fails after
  registration succeeded, the hook must be unregistered before the
  init returns its error.
- Module exit unregisters the hook, then flushes any still-scheduled
  deferred work, then tears down anything else.

Requirements:
1. Include the kernel headers for: module metadata, network namespace
   access, the netfilter registration interface, the netfilter IPv4
   chain enums, the deferred-task facility, atomics, and slab.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Declare `struct nf_hook_ops` with these fields populated:
   - `.hook` — the hook callback you implement.
   - `.hooknum` — the IPv4 pre-routing chain enum value.
   - `.pf` — the protocol family for IPv4.
   - `.priority` — any first-in-chain netfilter priority constant.
4. Declare an `atomic_t` module-scope packet counter, and a
   `struct work_struct` for deferred logging. Initialise the worker
   descriptor in module init, pointing it at your worker function
   using the standard kernel work-initialisation macro.
5. The hook callback:
   - Increments the atomic counter.
   - Submits the worker to the shared execution pool.
   - Returns the verdict constant that lets the packet continue up
     the stack.
6. The worker callback:
   - Reads the current counter value.
   - Emits a `pr_info` trace containing the count.
7. Module init:
   - Initialises the worker descriptor.
   - Registers the netfilter hook against the initial netns with the
     appropriate kernel API.
   - On any failure path: does not leave a half-registered hook.
   - Returns 0 on success, negative errno on failure.
8. Module exit:
   - Unregisters the netfilter hook.
   - Cancels any pending deferred work (synchronous cancel).
9. For any allocation on the packet path use the memory allocation
   flag that is safe in softirq / interrupt context (not the default
   sleep-allowed flag). Do NOT sleep, take a mutex, allocate with
   sleep-allowed memory flags, or copy to / from user space from
   inside the hook.

Output ONLY the complete C source file.
