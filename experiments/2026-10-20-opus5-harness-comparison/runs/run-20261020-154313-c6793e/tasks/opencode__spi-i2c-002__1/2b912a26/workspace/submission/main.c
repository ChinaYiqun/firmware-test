/*
 * SPI loopback test application.
 *
 * Sends a known 8-byte pattern on spi0 and verifies that the same bytes
 * are received back. Requires MOSI and MISO to be tied together (either
 * physically or via the controller's internal loopback mode).
 */

#include <string.h>

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/spi.h>

#define SPI_XFER_LEN 8U

static const struct device *const spi_dev = DEVICE_DT_GET(DT_NODELABEL(spi0));

int main(void)
{
	static uint8_t tx_buffer[SPI_XFER_LEN] = {
		0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08
	};
	static uint8_t rx_buffer[SPI_XFER_LEN];

	struct spi_config config = {
		.frequency = 1000000U,
		.operation = SPI_OP_MODE_MASTER | SPI_WORD_SET(8),
		.slave = 0U,
		.cs = {0},
	};

	const struct spi_buf tx_buf = {
		.buf = tx_buffer,
		.len = SPI_XFER_LEN,
	};
	const struct spi_buf rx_buf = {
		.buf = rx_buffer,
		.len = SPI_XFER_LEN,
	};
	const struct spi_buf_set tx_bufs = {
		.buffers = &tx_buf,
		.count = 1U,
	};
	const struct spi_buf_set rx_bufs = {
		.buffers = &rx_buf,
		.count = 1U,
	};

	int ret;

	memset(rx_buffer, 0, sizeof(rx_buffer));

	if (!device_is_ready(spi_dev)) {
		printk("SPI device %s is not ready\n",
		       spi_dev != NULL ? spi_dev->name : "spi0");
		return -ENODEV;
	}

	ret = spi_transceive(spi_dev, &config, &tx_bufs, &rx_bufs);
	if (ret < 0) {
		printk("spi_transceive() failed: %d\n", ret);
		return ret;
	}

	for (size_t i = 0U; i < SPI_XFER_LEN; i++) {
		if (tx_buffer[i] != rx_buffer[i]) {
			printk("Mismatch at byte %u: tx 0x%02x != rx 0x%02x\n",
			       (unsigned int)i, tx_buffer[i], rx_buffer[i]);
			printk("SPI loopback mismatch\n");
			return -EIO;
		}
	}

	printk("SPI loopback successful\n");

	return 0;
}
