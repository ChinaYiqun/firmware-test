Write a Linux 5.15 platform driver module for a GPIO-backed button that
splits interrupt handling into two phases: a fast primary handler that
timestamps the event, and a slower secondary handler that debounces
the bounce window by sleeping before emitting a press event.

Scenario:
- The button signals via a GPIO-backed IRQ on every level change.
- Hardware bounce means multiple physical edges within ~5 ms must be
  collapsed into a single logical press.
- Timestamping must be precise — it belongs in the fast path where
  jitter is minimal.
- Debouncing requires sleeping, which is illegal in hard-interrupt
  context — it belongs in the slow (sleepable) handler.
- The interrupt line must stay masked from the moment the primary
  handler hands off to the slow handler until the slow handler
  returns; otherwise the same physical bounce re-triggers the primary
  handler mid-debounce and the deferral collapses.

Requirements:
1. Include headers for module metadata, platform_device, of_device_id,
   interrupts, slab, time (ktime), and delay.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Match DT compatible "vendor,example-button" with MODULE_DEVICE_TABLE.
4. Per-device state holds: the register base, the IRQ number, and a
   last-press ktime_t timestamp.
5. Implement the PRIMARY (hardirq) handler:
   - Reads the current ktime and stores it in the state.
   - Returns the value that tells the kernel to wake the slow handler.
   - Does NOT sleep, log, or access slow peripherals.
6. Implement the SLOW (sleepable) handler:
   - Sleeps for ~5 ms to let the bounce window pass.
   - Emits a dev_info trace with the stored timestamp.
   - Returns IRQ_HANDLED.
7. probe():
   - Allocates state.
   - Maps registers.
   - Retrieves the IRQ.
   - Registers BOTH handlers together via the single kernel call that
     accepts a primary and a slow function in one invocation, with a
     flag that keeps the line masked while the slow handler runs (so
     spurious re-entries during debounce are suppressed).
   - platform_set_drvdata.
8. remove():
   - Frees the IRQ.
   - Releases registers and state.

Output ONLY the complete C source file.
