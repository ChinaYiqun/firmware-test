#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>

#define SENSOR_I2C_ADDR 0x68
#define WHO_AM_I_REG 0x75

int main(void)
{
	const struct device *i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));
	uint8_t reg_value;

	if (!device_is_ready(i2c_dev)) {
		printk("I2C device %s not ready\n", i2c_dev->name);
		return -ENODEV;
	}

	int err = i2c_reg_read_byte(i2c_dev, SENSOR_I2C_ADDR, WHO_AM_I_REG, &reg_value);

	if (err < 0) {
		printk("Failed to read WHO_AM_I register: %d\n", err);
		return err;
	}

	printk("WHO_AM_I register value: 0x%02x\n", reg_value);
	return 0;
}
