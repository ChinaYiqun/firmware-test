/*
 * I2C WHO_AM_I register reader
 *
 * Reads the WHO_AM_I register from an I2C sensor attached to the i2c0
 * bus and prints the result to the console.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>

/* 7-bit I2C address of the sensor on the bus */
#define SENSOR_I2C_ADDRESS	0x68

/* Address of the WHO_AM_I register */
#define WHO_AM_I_REG		0x75

int main(void)
{
	const struct device *const i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));
	uint8_t who_am_i;
	int err;

	/* Verify the I2C bus device is initialized and ready before use */
	if (!device_is_ready(i2c_dev)) {
		printk("I2C bus device i2c0 is not ready\n");
		return -ENODEV;
	}

	/* Read one byte from the WHO_AM_I register */
	err = i2c_reg_read_byte(i2c_dev, SENSOR_I2C_ADDRESS, WHO_AM_I_REG,
				&who_am_i);
	if (err != 0) {
		printk("Failed to read WHO_AM_I register: %d\n", err);
		return err;
	}

	printk("WHO_AM_I register value: 0x%02x\n", who_am_i);

	return 0;
}
