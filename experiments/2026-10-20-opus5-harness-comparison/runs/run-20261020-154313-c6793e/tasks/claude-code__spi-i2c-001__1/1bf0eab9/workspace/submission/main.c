/*
 * Minimal Zephyr application: read the WHO_AM_I register of an I2C sensor.
 *
 * The sensor is assumed to sit on the bus described by the "i2c0" devicetree
 * node label, at 7-bit address 0x68 (e.g. an MPU-6050 / ICM-20xxx class part).
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>

/* 7-bit I2C address of the sensor. */
#define SENSOR_I2C_ADDR 0x68

/* WHO_AM_I identification register. */
#define REG_WHO_AM_I 0x75

/* I2C controller the sensor is wired to. */
static const struct device *const i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));

int main(void)
{
	uint8_t who_am_i = 0U;
	int ret;

	/* DEVICE_DT_GET() resolves at build time but does not guarantee that the
	 * driver initialised successfully, so check readiness before any transfer.
	 */
	if (!device_is_ready(i2c_dev)) {
		printk("Error: I2C device %s is not ready\n",
		       i2c_dev != NULL ? i2c_dev->name : "(null)");
		return -ENODEV;
	}

	ret = i2c_reg_read_byte(i2c_dev, SENSOR_I2C_ADDR, REG_WHO_AM_I,
				&who_am_i);
	if (ret < 0) {
		printk("Error: failed to read WHO_AM_I (reg 0x%02x) from "
		       "device 0x%02x: %d\n",
		       REG_WHO_AM_I, SENSOR_I2C_ADDR, ret);
		return ret;
	}

	printk("WHO_AM_I (reg 0x%02x) = 0x%02x\n", REG_WHO_AM_I, who_am_i);

	return 0;
}
