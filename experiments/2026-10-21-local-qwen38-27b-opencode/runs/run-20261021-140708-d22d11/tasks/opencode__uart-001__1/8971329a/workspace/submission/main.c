#include <zephyr/kernel.h>
#include <zephyr/drivers/uart.h>

int main(void)
{
	const struct device *const uart = DEVICE_DT_GET(DT_ALIAS(uart0));

	if (!device_is_ready(uart)) {
		return -ENODEV;
	}

	uint8_t byte;

	while (true) {
		if (uart_poll_in(uart, &byte) == 0) {
			uart_poll_out(uart, byte);
		}
	}

	return 0;
}
