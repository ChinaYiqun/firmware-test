Write a Linux 5.15 character device driver module that exposes a ring
buffer shared between a hardware IRQ handler (which writes) and a
blocking read() syscall (which reads and sleeps when empty).

Scenario:
- A hardware peripheral raises an IRQ with a single byte of data.
- The IRQ top-half handler runs in hard-interrupt context on the CPU
  that received the interrupt; other CPUs may be running user tasks
  that could call read() on this chrdev at the same moment.
- The ring buffer head/tail indices and the buffer contents are
  shared between the IRQ handler and read().
- read() blocks when the buffer is empty and must be woken by the
  IRQ handler after it pushes a byte.

Requirements:
1. Include headers for module metadata, char device, file operations,
   interrupt handling, spinlocks, wait queues, user access, and
   platform device infrastructure.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Match DT compatible string "vendor,example-ring" and register with
   MODULE_DEVICE_TABLE(of, ...).
4. Define a per-device state struct that holds:
   - A 256-byte ring buffer.
   - head and tail indices (appropriately qualified for concurrent access).
   - A lock that is safe to acquire from both process context (read())
     and hard-IRQ context (handler).
   - A wait queue head for blocking readers.
   - The irq number.
5. Implement the IRQ hardirq handler:
   - Reads one byte from an MMIO data register.
   - Takes the lock, pushes the byte to the ring, releases the lock.
   - Wakes waiting readers.
   - Returns IRQ_HANDLED.
6. Implement file_operations.read(file, ubuf, count, off):
   - Sleeps (interruptibly) while the ring is empty.
   - Once woken, takes the lock, pops one byte, releases the lock, and
     copies it to userspace.
   - Returns the number of bytes copied.
7. probe() registers the chrdev, maps registers, requests the IRQ, and
   attaches state. remove() reverses probe. Use non-devm (traditional)
   lifecycle so you control the locking / IRQ ordering explicitly.

Critical correctness property: a read()er running on one CPU and the
IRQ handler running on another must not race on the buffer. The lock
you pick must disable interrupts locally AND save prior IRQ state so
nested locking does not re-enable them prematurely.

Output ONLY the complete C source file.
