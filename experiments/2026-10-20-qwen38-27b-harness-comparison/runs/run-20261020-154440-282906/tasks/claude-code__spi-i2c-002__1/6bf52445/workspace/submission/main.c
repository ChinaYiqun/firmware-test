/*
 * SPI loopback test for Zephyr RTOS.
 *
 * Drives a known 8-byte pattern out the SPI bus in master mode and verifies
 * that the same pattern is read back (wired loopback between MOSI and MISO).
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/spi.h>
#include <string.h>
#include <errno.h>

#define SPI_TEST_LEN		8
#define SPI_TEST_FREQ		1000000

int main(void)
{
	/* 1. Get the SPI bus device from the devicetree. */
	const struct device *const spi_dev = DEVICE_DT_GET(DT_NODELABEL(spi0));

	/* 2. Verify the device is initialized and ready before use. */
	if (!device_is_ready(spi_dev)) {
		PRINTK("SPI device not ready\n");
		return -ENODEV;
	}

	/* 3. Transmit buffer: 8 bytes with a known pattern (0x01 through 0x08). */
	uint8_t tx_data[SPI_TEST_LEN] = {
		0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08
	};

	/* 4. Receive buffer: 8 bytes, initialized to zero. */
	uint8_t rx_data[SPI_TEST_LEN] = {0};

	/* 5. SPI configuration: 1 MHz, master mode, 8-bit words. */
	const struct spi_config spi_cfg = {
		.frequency = SPI_TEST_FREQ,
		.operation = SPI_OP_MODE_MASTER | SPI_WORD_SET(8),
	};

	/* 6. One SPI buffer descriptor for transmit. */
	struct spi_buf tx_buf = {
		.buf = tx_data,
		.len = SPI_TEST_LEN,
	};

	/* 6. One SPI buffer descriptor for receive. */
	struct spi_buf rx_buf = {
		.buf = rx_data,
		.len = SPI_TEST_LEN,
	};

	/* 7. Buffer set: a single buffer for transmit. */
	const struct spi_buf_set tx_bufs = {
		.buffers = &tx_buf,
		.count = 1,
	};

	/* 7. Buffer set: a single buffer for receive. */
	const struct spi_buf_set rx_bufs = {
		.buffers = &rx_buf,
		.count = 1,
	};

	/* 8. Perform the SPI transceive. */
	int rc = spi_transceive(spi_dev, &spi_cfg, &tx_bufs, &rx_bufs);

	/* 9. Check the return value for errors. */
	if (rc < 0) {
		PRINTK("SPI transceive failed: %d\n", rc);
		return rc;
	}

	/* 10. Compare transmit and receive buffers byte-by-byte to verify loopback. */
	int status = 0;

	for (size_t i = 0; i < SPI_TEST_LEN; i++) {
		if (tx_data[i] != rx_data[i]) {
			status = -EIO;
			break;
		}
	}

	/* 11. Report the result. */
	if (status == 0) {
		PRINTK("SPI loopback successful\n");
	} else {
		PRINTK("SPI loopback mismatch\n");
	}

	return status;
}