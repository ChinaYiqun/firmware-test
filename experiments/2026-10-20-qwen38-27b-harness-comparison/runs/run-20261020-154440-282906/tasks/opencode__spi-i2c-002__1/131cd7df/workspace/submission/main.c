#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/spi.h>
#include <string.h>
#include <stdio.h>

#define SPI_TEST_LEN 8

int main(void)
{
	const struct device *const spi_dev = DEVICE_DT_GET(DT_NODELABEL(spi0));

	if (!device_is_ready(spi_dev)) {
		printf("SPI device not ready\n");
		return -1;
	}

	uint8_t tx_data[SPI_TEST_LEN] = {0x01, 0x02, 0x03, 0x04,
					    0x05, 0x06, 0x07, 0x08};
	uint8_t rx_data[SPI_TEST_LEN] = {0};

	struct spi_config spi_cfg = {
		.frequency = 1000000,
		.operation = SPI_OP_MODE_MASTER | SPI_WORD_SET(8),
	};

	struct spi_buf tx_buf = {
		.buf = tx_data,
		.len = SPI_TEST_LEN,
	};

	struct spi_buf rx_buf = {
		.buf = rx_data,
		.len = SPI_TEST_LEN,
	};

	struct spi_buf_set tx_bufs = {
		.buffers = &tx_buf,
		.count = 1,
	};

	struct spi_buf_set rx_bufs = {
		.buffers = &rx_buf,
		.count = 1,
	};

	int rc = spi_transceive(spi_dev, &spi_cfg, &tx_bufs, &rx_bufs);

	if (rc != 0) {
		printf("spi_transceive failed: %d\n", rc);
		return rc;
	}

	for (int i = 0; i < SPI_TEST_LEN; i++) {
		if (tx_data[i] != rx_data[i]) {
			printf("SPI loopback mismatch\n");
			return -1;
		}
	}

	printf("SPI loopback successful\n");
	return 0;
}