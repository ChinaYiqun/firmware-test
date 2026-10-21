Write a Linux 5.15 platform driver module for an i.MX8M Plus board that
binds to a device-tree node and acquires four probe-time resources.

Scenario:
- The device tree describes a peripheral with a memory-mapped register
  bank, an optional input clock, a reset GPIO, and an interrupt line.
- The driver runs on a long-lived production board; probe may be
  attempted, deferred, and retried many times over the device lifetime.
- Probe may fail at any step after partial resource acquisition.
- When the device is later unbound, every resource acquired during a
  successful probe must be released exactly once — no leaks, no
  double releases.

Requirements:
1. Include the headers needed for: module metadata, platform_device,
   of_device_id / MODULE_DEVICE_TABLE, clock framework, GPIO consumer
   interface, interrupts, I/O memory, slab allocation, and error-coded
   pointers.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Define an of_device_id table matching compatible string
   "vendor,example-sensor", followed by MODULE_DEVICE_TABLE(of, ...).
4. Define a per-device state struct that holds:
   - pointer to the mapped register bank (__iomem)
   - the input clock handle
   - the reset GPIO descriptor
   - the IRQ number
5. Implement probe(struct platform_device *pdev) that, in order:
   - Allocates the per-device state.
   - Maps the register bank from the platform resource.
   - Gets the optional input clock (may be absent in DT).
   - Gets the reset GPIO descriptor, asserted low on request.
   - Registers a threaded IRQ handler for the interrupt line.
   - Attaches the per-device state to the device.
   - Any step failing must return the appropriate negative errno without
     leaving any previously-acquired resource dangling.
6. Implement remove(struct platform_device *pdev) that returns 0.
   Whatever cleanup is needed must be consistent with the acquisition
   strategy used in probe — the driver must neither leak nor double-free
   when the device is unbound.
7. Define the platform_driver with .probe, .remove, .driver.name =
   "vendor-example-sensor", and .driver.of_match_table.
8. Register with module_platform_driver().

The IRQ thread handler body is out of scope — provide a stub that returns
IRQ_HANDLED.

Output ONLY the complete C source file.
