Write a Linux 5.15 platform driver module that allocates memory in two
different execution contexts and must pick the correct GFP flag for
each.

Scenario:
- A hardware peripheral raises an IRQ with a 32-bit data word.
- On every interrupt the driver allocates a small record struct and
  pushes it to a linked list protected by a spinlock. Userspace (or a
  later worker, out of scope here) drains the list.
- probe() allocates the per-device state.
- Both allocations use kmalloc (or kzalloc), but the *context* they
  run in is different. The GFP flag chosen must be appropriate — an
  allocation that may sleep in hardirq context will BUG the kernel.

Requirements:
1. Include headers for module metadata, platform_device, of_device_id,
   interrupts, spinlocks, linked lists, slab allocation, and I/O memory.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Match DT compatible "vendor,example-gfp" with MODULE_DEVICE_TABLE.
4. Define:
   - struct example_rec — a record with a struct list_head and the
     32-bit data word.
   - struct example_drv — per-device state with the register base,
     IRQ number, a spinlock, and a list_head.
5. Implement the IRQ hardirq handler:
   - Reads the 32-bit data word.
   - Allocates a new record struct. Pick the GFP flag correctly for
     hardirq context.
   - If allocation fails, returns IRQ_NONE.
   - Otherwise populates the record, takes the spinlock, appends to
     the list, releases the spinlock, and returns IRQ_HANDLED.
6. Implement probe():
   - Allocates the per-device state. Pick the GFP flag correctly for
     process context.
   - Initialises the list and the spinlock.
   - Maps registers and retrieves the IRQ.
   - Registers the IRQ handler (traditional request_irq).
7. Implement remove():
   - Frees the IRQ.
   - Drains the list with list_for_each_entry_safe + list_del + kfree
     under lock.
   - Releases the register mapping and per-device state.

Output ONLY the complete C source file.
