#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#include <linux/spi/spidev.h>

int main(void)
{
	int fd;
	int ret = 1;
	uint8_t mode = SPI_MODE_0;
	uint8_t bpw = 8;
	uint32_t speed = 1000000;
	uint8_t tx[4] = {0xAA, 0xBB, 0xCC, 0xDD};
	uint8_t rx[4] = {0};
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)tx,
		.rx_buf = (unsigned long)rx,
		.len = 4,
		.speed_hz = 1000000,
		.bits_per_word = 8,
	};

	fd = open("/dev/spidev0.0", O_RDWR);
	if (fd < 0) {
		perror("open /dev/spidev0.0");
		return 1;
	}

	if (ioctl(fd, SPI_IOC_WR_MODE, &mode) < 0) {
		perror("SPI_IOC_WR_MODE");
		goto out_close;
	}
	if (ioctl(fd, SPI_IOC_WR_BITS_PER_WORD, &bpw) < 0) {
		perror("SPI_IOC_WR_BITS_PER_WORD");
		goto out_close;
	}
	if (ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed) < 0) {
		perror("SPI_IOC_WR_MAX_SPEED_HZ");
		goto out_close;
	}

	if (ioctl(fd, SPI_IOC_MESSAGE(1), &tr) < 0) {
		perror("SPI_IOC_MESSAGE");
		goto out_close;
	}

	printf("rx: %02x %02x %02x %02x\n", rx[0], rx[1], rx[2], rx[3]);
	ret = 0;

out_close:
	close(fd);
	return ret;
}
