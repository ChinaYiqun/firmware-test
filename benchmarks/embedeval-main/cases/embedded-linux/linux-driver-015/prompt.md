Write a Linux 5.15 platform driver module that uses the kernel's
register-map abstraction to access registers instead of raw I/O
accessors, so that the same driver code can later be re-backed over
a different transport without rewriting the access-site logic.

Scenario:
- The peripheral has a 32-bit memory-mapped register bank reaching
  address 0xFF (so max register is 0xFF, access width 32 bits).
- The register bank is used for a CONTROL register at offset 0x00
  (enable bit, bit 0) and a STATUS register at offset 0x04.
- A future hardware revision will expose the same registers over SPI;
  the driver should therefore access registers through an abstraction
  that can be re-backed without rewriting the driver logic.
- probe() maps the MMIO resource, wraps it with the kernel's register
  abstraction, then exercises CONTROL and STATUS through that
  abstraction.
- All resources in probe are acquired through device-managed
  equivalents so cleanup is automatic on device detach — the driver
  keeps only the abstraction handle in state and does not need to
  maintain the raw mapping separately.

Requirements:
1. Include headers for module metadata, platform_device, of_device_id,
   the register abstraction, I/O memory, and error-coded pointers.
2. MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Match DT compatible "vendor,example-regmap" + MODULE_DEVICE_TABLE.
4. Provide the abstraction's config struct (instance of the standard
   config type) with reg_bits, val_bits, reg_stride, and max_register
   set to the values above.
5. Per-device state holds a pointer to the abstraction instance and
   nothing else.
6. probe():
   - Allocates per-device state via the kernel's device-managed
     zero-allocator so release is automatic on detach.
   - Maps the register bank via the kernel's device-managed
     platform-resource I/O mapping helper.
   - Initialises the abstraction with the device-managed MMIO variant
     so its lifetime is tied to the device.
   - Guards every ERR_PTR return correctly — NULL checks are wrong
     for error-coded pointers.
   - Writes 0x1 to the CONTROL register and reads the STATUS register
     — both through the abstraction, not raw I/O.
   - platform_set_drvdata.
7. remove(): return 0.
8. The driver MUST NOT call readl / writel / ioread32 / iowrite32 on
   the mapped pointer — the abstraction is the authoritative accessor.

Output ONLY the complete C source file.
