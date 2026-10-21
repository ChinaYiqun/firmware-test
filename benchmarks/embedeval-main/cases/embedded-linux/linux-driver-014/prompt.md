Write a Linux 5.15 platform driver module that runs a long-lived
background execution context polling a hardware register, and that
cooperates with the standard kernel unload protocol so the background
context exits promptly when the module is unbound.

Scenario:
- The peripheral exposes a 32-bit status register.
- A background flow must poll this register every 100 ms and stash the
  most recent value into per-device state.
- When the module unloads, the background flow must exit promptly —
  not hours later. The driver must cooperate with the kernel
  subsystem's standard stop protocol: on unload, the caller signals
  "please stop" and then blocks until the background flow observes the
  signal and returns.
- Choose the kernel facility designed for long-lived in-kernel
  schedulable execution contexts (distinct from deferred-task
  facilities, which are one-shot) — the handle returned on creation
  uses the kernel's error-coded-pointer convention on failure, so the
  correct guard shape must be used.

Requirements:
1. Include headers for module metadata, platform_device, of_device_id,
   the background-execution facility, delay (for sleeping in the poll
   loop), I/O memory, slab, and the error-coded-pointer macros.
2. MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Match DT compatible "vendor,example-poll" + MODULE_DEVICE_TABLE.
4. Per-device state holds: the register base, a handle to the
   background execution context, and the most-recent reading.
5. Implement the background function (signature: ``int fn(void *data)``):
   - Loops. On each iteration: reads the status register, caches it,
     then sleeps for ~100 ms in a way that cooperates with the stop
     protocol (uninterruptible sleep would delay shutdown; use an
     interruptible variant).
   - Uses the standard cooperative predicate to decide when to exit.
   - Returns 0.
6. probe():
   - Allocates state.
   - Maps registers.
   - Starts the background context using the kernel helper that both
     creates and wakes it. Guard the returned handle correctly for the
     error-coded-pointer convention and propagate the subsystem errno
     on failure.
   - platform_set_drvdata.
7. remove():
   - Stops the background context using the standard API that blocks
     until the context has exited.
   - Releases registers and state.

Critical: if the background flow ignores the stop signal, the stop
call never returns and the module unload hangs.

Output ONLY the complete C source file.
