#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/mod_devicetable.h>
#include <linux/interrupt.h>
#include <linux/spinlock.h>
#include <linux/list.h>
#include <linux/slab.h>
#include <linux/io.h>
#include <linux/ioport.h>
#include <linux/err.h>

#define DRIVER_NAME "vendor-example-gfp"
#define DATA_REG    0x00

struct example_rec {
	struct list_head node;
	u32 data;
};

struct example_drv {
	void __iomem *regs;
	int irq;
	spinlock_t lock;
	struct list_head head;
};

static irqreturn_t example_gfp_isr(int irq, void *dev_id)
{
	struct example_drv *d = dev_id;
	struct example_rec *r;
	unsigned long flags;
	u32 val;

	val = readl(d->regs + DATA_REG);

	r = kmalloc(sizeof(*r), GFP_ATOMIC);
	if (!r)
		return IRQ_NONE;

	r->data = val;
	spin_lock_irqsave(&d->lock, flags);
	list_add_tail(&r->node, &d->head);
	spin_unlock_irqrestore(&d->lock, flags);

	return IRQ_HANDLED;
}

static int example_gfp_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct example_drv *d;
	struct resource *res;
	int ret;

	d = kzalloc(sizeof(*d), GFP_KERNEL);
	if (!d)
		return -ENOMEM;

	spin_lock_init(&d->lock);
	INIT_LIST_HEAD(&d->head);

	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	if (!res) {
		ret = -ENODEV;
		goto err_free;
	}
	d->regs = ioremap(res->start, resource_size(res));
	if (!d->regs) {
		ret = -ENOMEM;
		goto err_free;
	}

	d->irq = platform_get_irq(pdev, 0);
	if (d->irq < 0) {
		ret = d->irq;
		goto err_iomap;
	}

	ret = request_irq(d->irq, example_gfp_isr, 0, DRIVER_NAME, d);
	if (ret)
		goto err_iomap;

	platform_set_drvdata(pdev, d);
	dev_info(dev, "%s: probed\n", DRIVER_NAME);
	return 0;

err_iomap:
	iounmap(d->regs);
err_free:
	kfree(d);
	return ret;
}

static int example_gfp_remove(struct platform_device *pdev)
{
	struct example_drv *d = platform_get_drvdata(pdev);
	struct example_rec *r, *tmp;
	unsigned long flags;

	free_irq(d->irq, d);

	spin_lock_irqsave(&d->lock, flags);
	list_for_each_entry_safe(r, tmp, &d->head, node) {
		list_del(&r->node);
		kfree(r);
	}
	spin_unlock_irqrestore(&d->lock, flags);

	iounmap(d->regs);
	kfree(d);
	return 0;
}

static const struct of_device_id example_gfp_of_match[] = {
	{ .compatible = "vendor,example-gfp" },
	{},
};
MODULE_DEVICE_TABLE(of, example_gfp_of_match);

static struct platform_driver example_gfp_driver = {
	.probe  = example_gfp_probe,
	.remove = example_gfp_remove,
	.driver = {
		.name           = DRIVER_NAME,
		.of_match_table = example_gfp_of_match,
	},
};
module_platform_driver(example_gfp_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Platform driver demonstrating GFP_KERNEL vs GFP_ATOMIC discipline");
