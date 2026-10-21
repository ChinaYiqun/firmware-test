"""Negative tests for linux-userspace-006 (spidev ioctl UAPI)."""

import re


def _tx_cast_to_uintptr(code: str) -> str:
    """Cast tx_buf via (uintptr_t) — compiles but relies on pointer size
    matching __u64 and trips on 32-bit userspace."""
    return code.replace(
        ".tx_buf = (unsigned long)tx,", ".tx_buf = (uintptr_t)tx,"
    )


def _tx_bare_pointer(code: str) -> str:
    """No cast at all — compiler warning; on some toolchains silent
    truncation from 64-bit __u64 to 32-bit pointer."""
    return code.replace(
        ".tx_buf = (unsigned long)tx,", ".tx_buf = tx,"
    )


def _swap_wr_mode_to_rd_mode(code: str) -> str:
    return code.replace("SPI_IOC_WR_MODE", "SPI_IOC_RD_MODE")


def _drop_wr_mode_ioctl(code: str) -> str:
    return re.sub(
        r"\n\s*if\s*\(ioctl\(fd, SPI_IOC_WR_MODE[^}]+\}",
        "",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_wr_speed_ioctl(code: str) -> str:
    return re.sub(
        r"\n\s*if\s*\(ioctl\(fd, SPI_IOC_WR_MAX_SPEED_HZ[^}]+\}",
        "",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _message_count_zero(code: str) -> str:
    return code.replace("SPI_IOC_MESSAGE(1)", "SPI_IOC_MESSAGE(0)")


def _drop_close(code: str) -> str:
    return code.replace("close(fd);\n", "")


def _write_read_fallback(code: str) -> str:
    """Remove the ioctl transfer and substitute write()+read() half-duplex."""
    return code.replace(
        'if (ioctl(fd, SPI_IOC_MESSAGE(1), &tr) < 0) {\n'
        '\t\tperror("SPI_IOC_MESSAGE");\n'
        '\t\tgoto out_close;\n'
        '\t}',
        'if (write(fd, tx, 4) != 4) { perror("write"); goto out_close; }\n'
        '\tif (read(fd, rx, 4) != 4) { perror("read"); goto out_close; }',
    )


def _arduino_spi_api(code: str) -> str:
    """Inject Arduino-style SPI.transfer()."""
    return code.replace(
        'printf("rx: ', 'SPI.transfer(tx, rx, 4);\n\tprintf("rx: '
    )


def _speed_wrong_value(code: str) -> str:
    return code.replace("speed = 1000000", "speed = 25000").replace(
        ".speed_hz = 1000000,", ".speed_hz = 25000,"
    )


def _open_without_rdwr(code: str) -> str:
    return code.replace('O_RDWR', 'O_RDONLY')


def _drop_perror(code: str) -> str:
    return re.sub(r'perror\("[^"]+"\);', "/* err */", code)


NEGATIVES = [
    {
        "name": "tx_buf_cast_to_uintptr",
        "description": "Cast tx_buf via (uintptr_t) — kernel field is __u64; on 32-bit userspace the upper word is implementation-defined.",
        "mutation": _tx_cast_to_uintptr,
        "must_fail": ["tx_rx_buf_cast_to_unsigned_long"],
        "factor_id": "A8.1",
    },
    {
        "name": "tx_buf_bare_pointer_no_cast",
        "description": "No cast — compiler may warn or silently truncate pointer-to-__u64 conversion.",
        "mutation": _tx_bare_pointer,
        "must_fail": ["tx_rx_buf_cast_to_unsigned_long"],
        "factor_id": "A8.1",
    },
    {
        "name": "swap_wr_mode_to_rd_mode",
        "description": "Use SPI_IOC_RD_MODE (read) where SPI_IOC_WR_MODE (write) is needed. Mode never programmed.",
        "mutation": _swap_wr_mode_to_rd_mode,
        "must_fail": ["spi_ioc_wr_mode_used"],
        "factor_id": "A8.2",
    },
    {
        "name": "drop_wr_mode_ioctl",
        "description": "Skip SPI_IOC_WR_MODE entirely — mode is whatever the kernel defaults to, likely wrong.",
        "mutation": _drop_wr_mode_ioctl,
        "must_fail": ["spi_ioc_wr_mode_used"],
        "factor_id": "A2.1",
    },
    {
        "name": "drop_wr_speed_ioctl",
        "description": "Skip SPI_IOC_WR_MAX_SPEED_HZ — bus runs at default speed; may be too fast or too slow for peripheral.",
        "mutation": _drop_wr_speed_ioctl,
        "must_fail": ["spi_ioc_wr_max_speed_hz_used"],
        "factor_id": "A2.1",
    },
    {
        "name": "message_count_zero",
        "description": "SPI_IOC_MESSAGE(0) — 0 transfer structs; ioctl is a no-op. TX never sent.",
        "mutation": _message_count_zero,
        "must_fail": ["spi_ioc_message_nonzero_count"],
        "factor_id": "F1.1",
    },
    {
        "name": "drop_close",
        "description": "Omit close(fd) — FD leaks across program lifetime; long-running use eventually exhausts FD table.",
        "mutation": _drop_close,
        "must_fail": ["close_called"],
        "factor_id": "E3.1",
    },
    {
        "name": "write_read_fallback",
        "description": "Use write(fd,tx,4)+read(fd,rx,4) instead of SPI_IOC_MESSAGE — half-duplex; most SPI peripherals need simultaneous TX+RX for register-read transactions.",
        "mutation": _write_read_fallback,
        "must_fail": ["no_write_read_fallback"],
        "factor_id": "A8.1",
    },
    {
        "name": "arduino_spi_api",
        "description": "Inject SPI.transfer(tx, rx, 4) — Arduino API, not Linux userspace.",
        "mutation": _arduino_spi_api,
        "must_fail": ["no_arduino_spi_api"],
        "factor_id": "F2.1",
    },
    {
        "name": "speed_wrong_value",
        "description": "Speed set to 25kHz instead of 1MHz — far too slow; violates prompt.",
        "mutation": _speed_wrong_value,
        "must_fail": ["speed_1mhz_configured"],
        "factor_id": "A3.1",
    },
    {
        "name": "open_read_only",
        "description": "open(..., O_RDONLY) — ioctl writes to the device fail with EBADF.",
        "mutation": _open_without_rdwr,
        "must_fail": ["open_spidev0_0_rdwr"],
        "factor_id": "F1.1",
    },
    {
        "name": "drop_perror_on_failure",
        "description": "Replace perror() with a silent comment — failures go undiagnosed.",
        "mutation": _drop_perror,
        "must_fail": ["perror_on_failure"],
        "factor_id": "E2.1",
    },
]
