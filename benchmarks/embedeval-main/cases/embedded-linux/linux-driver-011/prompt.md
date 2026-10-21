Write a Linux 5.15 platform driver module that fields an interrupt and
defers the heavy-weight post-processing (register I/O that may sleep,
logging) into a sleepable execution context — scheduled and owned by
the kernel, distinct from the interrupt context itself.

Scenario:
- A hardware peripheral raises an IRQ when a data frame is ready.
- Reading the full frame requires multiple register accesses that the
  driver's parent bus layer serializes with a mutex — so the read
  cannot happen in hard-interrupt context.
- The IRQ top half must merely ack the interrupt and hand the
  post-processing off; the post-processing itself belongs in a
  sleepable context owned and scheduled by the kernel independently
  of the interrupt path. Pick the kernel facility designed for this
  decoupling — a named per-device deferred-task descriptor submitted
  to a shared execution pool, so that queued work runs even if more
  interrupts fire before the previous task completes.
- When the module is unbound, any pending or in-flight deferred work
  must finish (or be cancelled) before the per-device state is freed,
  so the worker never dereferences freed memory.

Requirements:
1. Include headers for module metadata, platform_device, of_device_id,
   the deferred-task facility, interrupt handling, I/O memory,
   spinlocks, and slab.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Match DT compatible "vendor,example-frame" with MODULE_DEVICE_TABLE.
4. Define a per-device state struct that holds:
   - A deferred-task descriptor appropriate for the chosen facility.
   - The register base.
   - The IRQ number.
   - A lock suitable for IRQ / deferred-task synchronisation.
5. Implement the IRQ hardirq handler:
   - Acks the interrupt by writing to a status register.
   - Submits the deferred task to the shared execution pool.
   - Returns IRQ_HANDLED.
   - Performs NO register read of the frame itself, NO printk, NO sleep.
6. Implement the deferred-task function:
   - Reads the frame register(s).
   - Emits a dev_info / pr_info trace.
7. probe():
   - Allocates per-device state.
   - Initialises the deferred-task descriptor to point at the handler
     function.
   - Maps registers.
   - Requests the IRQ (traditional, non-devm).
   - Attaches state with platform_set_drvdata.
8. remove():
   - Disables further interrupts.
   - Guarantees no pending or in-flight deferred-task handler
     dereferences state after this function returns, before any other
     cleanup touches the state fields. Use the synchronous cancel
     primitive.
   - Releases registers, the IRQ, and the per-device state.

Output ONLY the complete C source file.
