#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

static struct gpio_callback led_cb_data;

static void button_toggle(struct gpio_callback *cb, uint32_t pins)
{
	ARG_UNUSED(cb);
	ARG_UNUSED(pins);

	gpio_pin_toggle_dt(DEVICE_DT_GET(DT_ALIAS(led0)),
			DT_GPIO_PIN(DT_ALIAS(led0)));
}

int main(void)
{
	const struct device *led_dev = DEVICE_DT_GET(DT_ALIAS(led0));
	const struct device *btn_dev = DEVICE_DT_GET(DT_ALIAS(sw0));

	if (!device_is_ready(led_dev) || !device_is_ready(btn_dev)) {
		return -ENODEV;
	}

	gpio_pin_configure_dt(led_dev, GPIO_PIN_OUTPUT_INACTIVE);

	gpio_pin_configure_dt(btn_dev, GPIO_INPUT | GPIO_PULL_UP);

	gpio_init_callback(&led_cb_data, button_toggle,
			BIT(DT_GPIO_PIN(DT_ALIAS(sw0))));
	gpio_add_callback_dt(btn_dev, &led_cb_data);

	gpio_pin_interrupt_configure_dt(btn_dev, GPIO_INT_EDGE_BOTH);

	k_sleep(K_FOREVER);

	return 0;
}
