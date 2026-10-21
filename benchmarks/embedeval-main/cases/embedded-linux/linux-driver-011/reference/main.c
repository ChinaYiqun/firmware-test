#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/mod_devicetable.h>
#include <linux/workqueue.h>
#include <linux/interrupt.h>
#include <linux/spinlock.h>
#include <linux/io.h>
#include <linux/ioport.h>
#include <linux/slab.h>
#include <linux/err.h>

#define DRIVER_NAME  "vendor-example-frame"
#define STATUS_REG   0x00
#define FRAME_REG    0x04

struct example_frame {
	struct work_struct work;
	void __iomem *regs;
	int irq;
	spinlock_t lock;
	struct platform_device *pdev;
};

static void example_frame_worker(struct work_struct *work)
{
	struct example_frame *f = container_of(work, struct example_frame, work);
	u32 frame;

	frame = readl(f->regs + FRAME_REG);
	dev_info(&f->pdev->dev, "%s: frame=0x%08x\n", DRIVER_NAME, frame);
}

static irqreturn_t example_frame_isr(int irq, void *data)
{
	struct example_frame *f = data;

	writel(0x1, f->regs + STATUS_REG);  /* ack */
	schedule_work(&f->work);
	return IRQ_HANDLED;
}

static int example_frame_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct example_frame *f;
	struct resource *res;
	int ret;

	f = kzalloc(sizeof(*f), GFP_KERNEL);
	if (!f)
		return -ENOMEM;

	spin_lock_init(&f->lock);
	INIT_WORK(&f->work, example_frame_worker);
	f->pdev = pdev;

	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	if (!res) {
		ret = -ENODEV;
		goto err_free;
	}
	f->regs = ioremap(res->start, resource_size(res));
	if (!f->regs) {
		ret = -ENOMEM;
		goto err_free;
	}

	f->irq = platform_get_irq(pdev, 0);
	if (f->irq < 0) {
		ret = f->irq;
		goto err_iomap;
	}

	ret = request_irq(f->irq, example_frame_isr, 0, DRIVER_NAME, f);
	if (ret)
		goto err_iomap;

	platform_set_drvdata(pdev, f);
	dev_info(dev, "%s: probed irq=%d\n", DRIVER_NAME, f->irq);
	return 0;

err_iomap:
	iounmap(f->regs);
err_free:
	kfree(f);
	return ret;
}

static int example_frame_remove(struct platform_device *pdev)
{
	struct example_frame *f = platform_get_drvdata(pdev);

	free_irq(f->irq, f);
	cancel_work_sync(&f->work);
	iounmap(f->regs);
	kfree(f);
	return 0;
}

static const struct of_device_id example_frame_of_match[] = {
	{ .compatible = "vendor,example-frame" },
	{},
};
MODULE_DEVICE_TABLE(of, example_frame_of_match);

static struct platform_driver example_frame_driver = {
	.probe  = example_frame_probe,
	.remove = example_frame_remove,
	.driver = {
		.name           = DRIVER_NAME,
		.of_match_table = example_frame_of_match,
	},
};
module_platform_driver(example_frame_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Platform driver deferring IRQ work to a workqueue");
