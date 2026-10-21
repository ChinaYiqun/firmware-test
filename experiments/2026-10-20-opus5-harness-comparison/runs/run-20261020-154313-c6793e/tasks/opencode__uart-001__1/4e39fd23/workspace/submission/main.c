#include <zephyr/kernel.h>
#include <zephyr/drivers/uart.h>

int main(void)
{
	const struct device *uart_dev = DEVICE_DT_GET(DT_ALIAS(uart0));
	unsigned char byte;
	int ret;

	if (!device_is_ready(uart_dev)) {
		return -1;
	}

	while (1) {
		ret = uart_poll_in(uart_dev, &byte);
		if (ret == 0) {
			uart_poll_out(uart_dev, byte);
		}
	}

	return 0;
}
