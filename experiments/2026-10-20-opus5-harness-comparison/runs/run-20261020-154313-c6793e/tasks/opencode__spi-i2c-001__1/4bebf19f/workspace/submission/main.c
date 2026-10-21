/*
 * Copyright (c) 2026
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>

/* Sensor I2C address (7-bit) */
#define SENSOR_I2C_ADDR 0x68

/* WHO_AM_I register address */
#define WHO_AM_I_REG 0x75

int main(void)
{
	const struct device *i2c_dev;
	uint8_t who_am_i;
	int ret;

	/* Get the I2C bus device from devicetree */
	i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));

	/* Verify the device is initialized and ready before use */
	if (!device_is_ready(i2c_dev)) {
		printk("Error: I2C device %s is not ready\n",
		       i2c_dev ? i2c_dev->name : "i2c0");
		return -ENODEV;
	}

	/* Read one byte from the WHO_AM_I register */
	ret = i2c_reg_read_byte(i2c_dev, SENSOR_I2C_ADDR, WHO_AM_I_REG,
				&who_am_i);
	if (ret < 0) {
		printk("Error: failed to read WHO_AM_I (reg 0x%02X) from "
		       "device 0x%02X: %d\n",
		       WHO_AM_I_REG, SENSOR_I2C_ADDR, ret);
		return ret;
	}

	printk("WHO_AM_I (reg 0x%02X) = 0x%02X\n", WHO_AM_I_REG, who_am_i);

	return 0;
}
