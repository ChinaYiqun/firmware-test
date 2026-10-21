#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

static const struct device *const led_dev = DEVICE_DT_GET(DT_ALIAS(led0));
static const struct device *const btn_dev = DEVICE_DT_GET(DT_ALIAS(sw0));

static struct gpio_callback btn_cb_data;

static void btn_isr(struct gpio_callback *cb, uint32_t pins)
{
	(void)cb;
	(void)pins;

	gpio_pin_toggle_dt(led_dev, DT_GPIO_PIN(DT_ALIAS(led0)));
}

int main(void)
{
	gpio_pin_configure_dt(led_dev, DT_GPIO_PIN(DT_ALIAS(led0)),
			      GPIO_OUTPUT_INACTIVE);

	gpio_pin_configure_dt(btn_dev, DT_GPIO_PIN(DT_ALIAS(sw0)),
			      GPIO_INPUT | GPIO_PULL_UP);

	gpio_init_callback(&btn_cb_data, btn_isr,
			   BIT(DT_GPIO_PIN(DT_ALIAS(sw0))));

	gpio_add_callback_dt(btn_dev, &btn_cb_data);

	gpio_pin_interrupt_configure_dt(btn_dev, DT_GPIO_PIN(DT_ALIAS(sw0)),
					GPIO_INT_EDGE_BOTH);

	k_sleep(K_FOREVER);

	return 0;
}
