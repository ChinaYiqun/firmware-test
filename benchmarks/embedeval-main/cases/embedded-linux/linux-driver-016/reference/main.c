#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/mod_devicetable.h>
#include <linux/clk.h>
#include <linux/reset.h>
#include <linux/interrupt.h>
#include <linux/io.h>
#include <linux/ioport.h>
#include <linux/slab.h>
#include <linux/err.h>

#define DRIVER_NAME "vendor-example-ctl"

struct example_ctl {
	struct clk *clk;
	struct reset_control *rst;
	void __iomem *regs;
	int irq;
};

static irqreturn_t example_ctl_isr(int irq, void *data)
{
	(void)irq;
	(void)data;
	return IRQ_HANDLED;
}

static int example_ctl_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct example_ctl *priv;
	struct resource *res;
	int ret;

	priv = kzalloc(sizeof(*priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	priv->clk = clk_get(dev, "pclk");
	if (IS_ERR(priv->clk)) {
		ret = PTR_ERR(priv->clk);
		goto err_free;
	}

	priv->rst = reset_control_get(dev, "rst");
	if (IS_ERR(priv->rst)) {
		ret = PTR_ERR(priv->rst);
		goto err_clk;
	}

	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	if (!res) {
		ret = -ENODEV;
		goto err_rst;
	}
	priv->regs = ioremap(res->start, resource_size(res));
	if (!priv->regs) {
		ret = -ENOMEM;
		goto err_rst;
	}

	priv->irq = platform_get_irq(pdev, 0);
	if (priv->irq < 0) {
		ret = priv->irq;
		goto err_iomap;
	}

	ret = request_irq(priv->irq, example_ctl_isr, 0, DRIVER_NAME, priv);
	if (ret)
		goto err_iomap;

	platform_set_drvdata(pdev, priv);
	return 0;

err_iomap:
	iounmap(priv->regs);
err_rst:
	reset_control_put(priv->rst);
err_clk:
	clk_put(priv->clk);
err_free:
	kfree(priv);
	return ret;
}

static int example_ctl_remove(struct platform_device *pdev)
{
	struct example_ctl *priv = platform_get_drvdata(pdev);

	free_irq(priv->irq, priv);
	iounmap(priv->regs);
	reset_control_put(priv->rst);
	clk_put(priv->clk);
	kfree(priv);
	return 0;
}

static const struct of_device_id example_ctl_of_match[] = {
	{ .compatible = "vendor,example-ctl" },
	{},
};
MODULE_DEVICE_TABLE(of, example_ctl_of_match);

static struct platform_driver example_ctl_driver = {
	.probe  = example_ctl_probe,
	.remove = example_ctl_remove,
	.driver = {
		.name           = DRIVER_NAME,
		.of_match_table = example_ctl_of_match,
	},
};
module_platform_driver(example_ctl_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Platform driver demonstrating mixed error-return conventions");
