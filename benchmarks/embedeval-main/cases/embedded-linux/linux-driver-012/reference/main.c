#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/mod_devicetable.h>
#include <linux/interrupt.h>
#include <linux/io.h>
#include <linux/ioport.h>
#include <linux/slab.h>
#include <linux/ktime.h>
#include <linux/delay.h>

#define DRIVER_NAME "vendor-example-button"
#define DEBOUNCE_MS 5

struct example_button {
	void __iomem *regs;
	int irq;
	ktime_t last_press;
	struct device *dev;
};

static irqreturn_t example_button_primary(int irq, void *dev_id)
{
	struct example_button *b = dev_id;

	b->last_press = ktime_get();
	return IRQ_WAKE_THREAD;
}

static irqreturn_t example_button_thread(int irq, void *dev_id)
{
	struct example_button *b = dev_id;

	msleep(DEBOUNCE_MS);
	dev_info(b->dev, "%s: press at %lld ns\n", DRIVER_NAME,
		 ktime_to_ns(b->last_press));
	return IRQ_HANDLED;
}

static int example_button_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct example_button *b;
	struct resource *res;
	int ret;

	b = kzalloc(sizeof(*b), GFP_KERNEL);
	if (!b)
		return -ENOMEM;
	b->dev = dev;

	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	if (!res) {
		ret = -ENODEV;
		goto err_free;
	}
	b->regs = ioremap(res->start, resource_size(res));
	if (!b->regs) {
		ret = -ENOMEM;
		goto err_free;
	}

	b->irq = platform_get_irq(pdev, 0);
	if (b->irq < 0) {
		ret = b->irq;
		goto err_iomap;
	}

	ret = request_threaded_irq(b->irq,
				   example_button_primary,
				   example_button_thread,
				   IRQF_ONESHOT | IRQF_TRIGGER_RISING,
				   DRIVER_NAME, b);
	if (ret)
		goto err_iomap;

	platform_set_drvdata(pdev, b);
	dev_info(dev, "%s: probed irq=%d\n", DRIVER_NAME, b->irq);
	return 0;

err_iomap:
	iounmap(b->regs);
err_free:
	kfree(b);
	return ret;
}

static int example_button_remove(struct platform_device *pdev)
{
	struct example_button *b = platform_get_drvdata(pdev);

	free_irq(b->irq, b);
	iounmap(b->regs);
	kfree(b);
	return 0;
}

static const struct of_device_id example_button_of_match[] = {
	{ .compatible = "vendor,example-button" },
	{},
};
MODULE_DEVICE_TABLE(of, example_button_of_match);

static struct platform_driver example_button_driver = {
	.probe  = example_button_probe,
	.remove = example_button_remove,
	.driver = {
		.name           = DRIVER_NAME,
		.of_match_table = example_button_of_match,
	},
};
module_platform_driver(example_button_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("GPIO button with request_threaded_irq primary/thread split");
