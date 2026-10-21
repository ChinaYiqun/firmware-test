Write a Linux userspace C program that opens ``/dev/spidev0.0``,
configures SPI bus parameters, and performs one full-duplex 4-byte
transaction using the kernel's spidev UAPI ioctl interface.

Scenario:
- Target: NXP i.MX8M Plus, Linux 5.15 userspace.
- SPI bus parameters: mode 0 (CPOL=0, CPHA=0), 8 bits per word,
  1 MHz clock.
- Transaction: simultaneously transmit 4 bytes
  ``{0xAA, 0xBB, 0xCC, 0xDD}`` and read 4 bytes into a response
  buffer.
- On any ioctl failure, perror and exit non-zero.
- The SPI device node may be owned by root; program is expected
  to run as root or via the spi group. Do NOT attempt privilege
  escalation — just fail gracefully on permission errors.

Requirements:
1. Include the relevant headers: ``unistd.h``, ``fcntl.h``,
   ``sys/ioctl.h``, ``linux/spi/spidev.h``, ``stdio.h``,
   ``stdlib.h``, ``string.h``.
2. ``open("/dev/spidev0.0", O_RDWR)``; bail with perror on failure.
3. Configure mode: write mode byte via the SPI_IOC_WR_MODE ioctl.
4. Configure bits-per-word: write 8 via SPI_IOC_WR_BITS_PER_WORD.
5. Configure max speed: write 1_000_000 via SPI_IOC_WR_MAX_SPEED_HZ.
6. Populate ``struct spi_ioc_transfer`` with:
   - tx_buf cast to ``(unsigned long)`` — NOT ``(uintptr_t)``,
     NOT bare pointer. The kernel UAPI declares these fields as
     ``__u64`` regardless of build word size; the canonical
     userspace idiom casts through ``unsigned long``.
   - rx_buf cast to ``(unsigned long)`` too.
   - len = 4.
   - speed_hz and bits_per_word fields set consistently.
7. Execute the transfer via ``ioctl(fd, SPI_IOC_MESSAGE(1), &tr)``
   (1 = number of transfer structs in this ioctl invocation).
8. Close the fd on both success and error paths.
9. Do NOT use Arduino-style ``SPI.transfer()`` or ``SPI.begin()``
   — that is not a Linux userspace API.
10. Do NOT use the write(2) / read(2) fallback — use the ioctl
    transaction API so TX+RX happen simultaneously.

Output ONLY the complete C source file.
