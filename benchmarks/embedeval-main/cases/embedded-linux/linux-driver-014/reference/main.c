#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/mod_devicetable.h>
#include <linux/kthread.h>
#include <linux/delay.h>
#include <linux/io.h>
#include <linux/ioport.h>
#include <linux/slab.h>
#include <linux/err.h>
#include <linux/sched.h>

#define DRIVER_NAME "vendor-example-poll"
#define STATUS_REG  0x00
#define POLL_MS     100

struct example_poll {
	void __iomem *regs;
	struct task_struct *task;
	u32 last_reading;
};

static int example_poll_thread(void *data)
{
	struct example_poll *p = data;

	while (!kthread_should_stop()) {
		p->last_reading = readl(p->regs + STATUS_REG);
		msleep_interruptible(POLL_MS);
	}
	return 0;
}

static int example_poll_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct example_poll *p;
	struct resource *res;
	int ret;

	p = kzalloc(sizeof(*p), GFP_KERNEL);
	if (!p)
		return -ENOMEM;

	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	if (!res) {
		ret = -ENODEV;
		goto err_free;
	}
	p->regs = ioremap(res->start, resource_size(res));
	if (!p->regs) {
		ret = -ENOMEM;
		goto err_free;
	}

	p->task = kthread_run(example_poll_thread, p, "%s-poll", DRIVER_NAME);
	if (IS_ERR(p->task)) {
		ret = PTR_ERR(p->task);
		goto err_iomap;
	}

	platform_set_drvdata(pdev, p);
	dev_info(dev, "%s: probed\n", DRIVER_NAME);
	return 0;

err_iomap:
	iounmap(p->regs);
err_free:
	kfree(p);
	return ret;
}

static int example_poll_remove(struct platform_device *pdev)
{
	struct example_poll *p = platform_get_drvdata(pdev);

	kthread_stop(p->task);
	iounmap(p->regs);
	kfree(p);
	return 0;
}

static const struct of_device_id example_poll_of_match[] = {
	{ .compatible = "vendor,example-poll" },
	{},
};
MODULE_DEVICE_TABLE(of, example_poll_of_match);

static struct platform_driver example_poll_driver = {
	.probe  = example_poll_probe,
	.remove = example_poll_remove,
	.driver = {
		.name           = DRIVER_NAME,
		.of_match_table = example_poll_of_match,
	},
};
module_platform_driver(example_poll_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Platform driver with cooperative kthread polling loop");
