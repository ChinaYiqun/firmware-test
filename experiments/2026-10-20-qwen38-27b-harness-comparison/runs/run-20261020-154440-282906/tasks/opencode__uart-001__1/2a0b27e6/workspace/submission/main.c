#include <zephyr/kernel.h>
#include <zephyr/drivers/uart.h>

static const struct device *const uart_dev = DEVICE_DT_GET(DT_ALIAS(uart0));

int main(void)
{
	uint8_t rx_byte;

	if (!device_is_ready(uart_dev)) {
		return -ENODEV;
	}

	while (true) {
		if (uart_poll_in(uart_dev, &rx_byte) == 0) {
			uart_poll_out(uart_dev, rx_byte);
		}
	}

	return 0;
}
