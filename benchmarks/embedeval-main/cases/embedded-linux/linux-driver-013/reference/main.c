#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/mod_devicetable.h>
#include <linux/clk.h>
#include <linux/gpio/consumer.h>
#include <linux/interrupt.h>
#include <linux/io.h>
#include <linux/slab.h>
#include <linux/err.h>

#define DRIVER_NAME "vendor-example-sensor"

struct example_sensor {
	void __iomem *regs;
	struct clk *clk;
	struct gpio_desc *reset;
	int irq;
};

static irqreturn_t example_sensor_thread(int irq, void *data)
{
	(void)irq;
	(void)data;
	return IRQ_HANDLED;
}

static int example_sensor_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct example_sensor *priv;
	int ret;

	priv = devm_kzalloc(dev, sizeof(*priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	priv->regs = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(priv->regs))
		return PTR_ERR(priv->regs);

	priv->clk = devm_clk_get_optional(dev, NULL);
	if (IS_ERR(priv->clk))
		return PTR_ERR(priv->clk);

	priv->reset = devm_gpiod_get(dev, "reset", GPIOD_OUT_LOW);
	if (IS_ERR(priv->reset))
		return PTR_ERR(priv->reset);

	priv->irq = platform_get_irq(pdev, 0);
	if (priv->irq < 0)
		return priv->irq;

	ret = devm_request_threaded_irq(dev, priv->irq, NULL,
					example_sensor_thread,
					IRQF_ONESHOT, DRIVER_NAME, priv);
	if (ret)
		return ret;

	platform_set_drvdata(pdev, priv);
	return 0;
}

static int example_sensor_remove(struct platform_device *pdev)
{
	(void)pdev;
	return 0;
}

static const struct of_device_id example_sensor_of_match[] = {
	{ .compatible = "vendor,example-sensor" },
	{},
};
MODULE_DEVICE_TABLE(of, example_sensor_of_match);

static struct platform_driver example_sensor_driver = {
	.probe  = example_sensor_probe,
	.remove = example_sensor_remove,
	.driver = {
		.name           = DRIVER_NAME,
		.of_match_table = example_sensor_of_match,
	},
};
module_platform_driver(example_sensor_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Example platform driver with managed resources");
