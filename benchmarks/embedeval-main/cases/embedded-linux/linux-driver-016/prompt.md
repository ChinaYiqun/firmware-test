Write a Linux 5.15 platform driver module for an i.MX8M Plus board that
uses traditional (non-managed) resource acquisition and demonstrates
correct error-return handling for four APIs with three different
return-value conventions.

Scenario:
- The peripheral is described in the device tree.
- The probe must acquire four resources: a clock, a reset line, a
  memory-mapped register bank, and an interrupt. Use the traditional,
  non-managed kernel APIs for each.
- Each of the four APIs has a different failure convention. Your code
  must pick the correct guard for each — an incorrect guard accepts a
  non-NULL error-coded value as success, or treats a valid NULL-on-absent
  return as failure.
- On failure at any step, release every already-acquired resource in
  reverse order using labeled goto statements.
- On remove, release everything in reverse order.

Requirements:
1. Include headers for module metadata, platform_device, of_device_id,
   clock framework, reset framework, I/O memory, interrupts, and
   error-coded pointers.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Provide an of_device_id table matching compatible "vendor,example-ctl"
   and call MODULE_DEVICE_TABLE(of, ...).
4. Define a per-device state struct holding the clock, reset line,
   register base, and irq number.
5. Implement probe(struct platform_device *pdev) that, in order:
   - Allocates per-device state with kzalloc (not devm).
   - Retrieves a clock named "pclk" using the traditional clock API
     that returns an error-coded pointer on failure.
   - Retrieves a reset line named "rst" using the traditional reset
     framework API that returns an error-coded pointer on failure.
   - Maps the register bank using the traditional iomap API that
     returns NULL on failure (not an error-coded pointer).
   - Retrieves the IRQ number using the traditional API that returns
     a negative errno on failure.
   - Requests the interrupt with a plain (non-threaded) handler stub
     that returns IRQ_HANDLED.
   - Attaches the state to the device.
   - On any failure, propagate the correct errno to the caller —
     do NOT return a hardcoded -EIO or -ENODEV if the API already
     supplied an errno.
6. Implement remove(struct platform_device *pdev) that releases every
   resource probe acquired, in reverse order of acquisition.
7. Define the platform_driver with .probe, .remove, .driver.name =
   "vendor-example-ctl", .driver.of_match_table. Register with
   module_platform_driver().

Output ONLY the complete C source file.
