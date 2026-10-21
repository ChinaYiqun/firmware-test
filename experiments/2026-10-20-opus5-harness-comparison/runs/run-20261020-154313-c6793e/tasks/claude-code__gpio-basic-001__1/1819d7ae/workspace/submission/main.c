#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

/* Get LED and button devices from devicetree */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(DT_ALIAS(sw0), gpios);

/* GPIO callback structure */
static struct gpio_callback button_cb_data;

/* Button interrupt callback function */
void button_pressed(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
	gpio_pin_toggle_dt(&led);
}

void main(void)
{
	int ret;

	/* Check if LED device is ready */
	if (!gpio_is_ready_dt(&led)) {
		return;
	}

	/* Check if button device is ready */
	if (!gpio_is_ready_dt(&button)) {
		return;
	}

	/* Configure LED pin as output (initially off) */
	ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	if (ret < 0) {
		return;
	}

	/* Configure button pin as input with pull-up */
	ret = gpio_pin_configure_dt(&button, GPIO_INPUT | GPIO_PULL_UP);
	if (ret < 0) {
		return;
	}

	/* Configure button interrupt (falling edge) */
	ret = gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_FALLING);
	if (ret < 0) {
		return;
	}

	/* Initialize GPIO callback */
	gpio_init_callback(&button_cb_data, button_pressed, BIT(button.pin));

	/* Add the callback */
	ret = gpio_add_callback_dt(&button, &button_cb_data);
	if (ret < 0) {
		return;
	}

	/* Sleep forever */
	k_sleep(K_FOREVER);
}
