/*
 * GPIO button interrupt toggles an LED.
 *
 * Requires the board devicetree to provide the "led0" and "sw0" aliases.
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

#define LED0_NODE DT_ALIAS(led0)
#define SW0_NODE  DT_ALIAS(sw0)

#if !DT_NODE_HAS_STATUS(LED0_NODE, okay)
#error "Unsupported board: devicetree alias led0 is not defined"
#endif

#if !DT_NODE_HAS_STATUS(SW0_NODE, okay)
#error "Unsupported board: devicetree alias sw0 is not defined"
#endif

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(SW0_NODE, gpios);

static struct gpio_callback button_cb_data;

static void button_pressed(const struct device *dev, struct gpio_callback *cb,
			   uint32_t pins)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(cb);
	ARG_UNUSED(pins);

	(void)gpio_pin_toggle_dt(&led);
}

int main(void)
{
	int ret;

	if (!gpio_is_ready_dt(&led)) {
		printk("Error: LED device %s is not ready\n", led.port->name);
		return -ENODEV;
	}

	if (!gpio_is_ready_dt(&button)) {
		printk("Error: button device %s is not ready\n", button.port->name);
		return -ENODEV;
	}

	/* LED as output, initially off. */
	ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	if (ret != 0) {
		printk("Error %d: failed to configure LED pin %d\n", ret, led.pin);
		return ret;
	}

	/* Button as input with internal pull-up. */
	ret = gpio_pin_configure_dt(&button, GPIO_INPUT | GPIO_PULL_UP);
	if (ret != 0) {
		printk("Error %d: failed to configure button pin %d\n", ret, button.pin);
		return ret;
	}

	/* Edge-triggered interrupt on both edges. */
	ret = gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_BOTH);
	if (ret != 0) {
		printk("Error %d: failed to configure interrupt on pin %d\n", ret,
		       button.pin);
		return ret;
	}

	gpio_init_callback(&button_cb_data, button_pressed, BIT(button.pin));

	ret = gpio_add_callback_dt(&button, &button_cb_data);
	if (ret != 0) {
		printk("Error %d: failed to add button callback\n", ret);
		return ret;
	}

	printk("Press the button on %s pin %d to toggle the LED\n",
	       button.port->name, button.pin);

	k_sleep(K_FOREVER);

	return 0;
}
