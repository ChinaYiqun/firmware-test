#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/mod_devicetable.h>
#include <linux/cdev.h>
#include <linux/fs.h>
#include <linux/interrupt.h>
#include <linux/spinlock.h>
#include <linux/wait.h>
#include <linux/sched.h>
#include <linux/uaccess.h>
#include <linux/io.h>
#include <linux/ioport.h>
#include <linux/slab.h>
#include <linux/err.h>

#define DRIVER_NAME "vendor-example-ring"
#define RING_SIZE   256
#define DATA_REG    0x00

struct example_ring {
	u8 buf[RING_SIZE];
	unsigned int head;
	unsigned int tail;
	spinlock_t lock;
	wait_queue_head_t wq;
	void __iomem *regs;
	int irq;
	dev_t devno;
	struct cdev cdev;
};

static struct example_ring *g_ring;

static irqreturn_t example_ring_isr(int irq, void *data)
{
	struct example_ring *r = data;
	unsigned long flags;
	u8 b;
	unsigned int next;

	b = readb(r->regs + DATA_REG);

	spin_lock_irqsave(&r->lock, flags);
	next = (r->head + 1) % RING_SIZE;
	if (next != r->tail) {
		r->buf[r->head] = b;
		r->head = next;
	}
	spin_unlock_irqrestore(&r->lock, flags);

	wake_up_interruptible(&r->wq);
	return IRQ_HANDLED;
}

static ssize_t example_ring_read(struct file *file, char __user *ubuf,
				 size_t count, loff_t *off)
{
	struct example_ring *r = g_ring;
	unsigned long flags;
	u8 b;
	int ret;

	(void)file;
	(void)off;
	if (count < 1)
		return 0;

	ret = wait_event_interruptible(r->wq, r->head != r->tail);
	if (ret)
		return ret;

	spin_lock_irqsave(&r->lock, flags);
	b = r->buf[r->tail];
	r->tail = (r->tail + 1) % RING_SIZE;
	spin_unlock_irqrestore(&r->lock, flags);

	if (copy_to_user(ubuf, &b, 1))
		return -EFAULT;
	return 1;
}

static const struct file_operations example_ring_fops = {
	.owner = THIS_MODULE,
	.read  = example_ring_read,
};

static int example_ring_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct example_ring *r;
	struct resource *res;
	int ret;

	r = kzalloc(sizeof(*r), GFP_KERNEL);
	if (!r)
		return -ENOMEM;

	spin_lock_init(&r->lock);
	init_waitqueue_head(&r->wq);

	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	if (!res) {
		ret = -ENODEV;
		goto err_free;
	}
	r->regs = ioremap(res->start, resource_size(res));
	if (!r->regs) {
		ret = -ENOMEM;
		goto err_free;
	}

	r->irq = platform_get_irq(pdev, 0);
	if (r->irq < 0) {
		ret = r->irq;
		goto err_iomap;
	}

	ret = alloc_chrdev_region(&r->devno, 0, 1, DRIVER_NAME);
	if (ret < 0)
		goto err_iomap;

	cdev_init(&r->cdev, &example_ring_fops);
	r->cdev.owner = THIS_MODULE;
	ret = cdev_add(&r->cdev, r->devno, 1);
	if (ret)
		goto err_chrdev;

	ret = request_irq(r->irq, example_ring_isr, 0, DRIVER_NAME, r);
	if (ret)
		goto err_cdev;

	g_ring = r;
	platform_set_drvdata(pdev, r);
	dev_info(dev, "%s: probed irq=%d\n", DRIVER_NAME, r->irq);
	return 0;

err_cdev:
	cdev_del(&r->cdev);
err_chrdev:
	unregister_chrdev_region(r->devno, 1);
err_iomap:
	iounmap(r->regs);
err_free:
	kfree(r);
	return ret;
}

static int example_ring_remove(struct platform_device *pdev)
{
	struct example_ring *r = platform_get_drvdata(pdev);

	free_irq(r->irq, r);
	cdev_del(&r->cdev);
	unregister_chrdev_region(r->devno, 1);
	iounmap(r->regs);
	kfree(r);
	g_ring = NULL;
	return 0;
}

static const struct of_device_id example_ring_of_match[] = {
	{ .compatible = "vendor,example-ring" },
	{},
};
MODULE_DEVICE_TABLE(of, example_ring_of_match);

static struct platform_driver example_ring_driver = {
	.probe  = example_ring_probe,
	.remove = example_ring_remove,
	.driver = {
		.name           = DRIVER_NAME,
		.of_match_table = example_ring_of_match,
	},
};
module_platform_driver(example_ring_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Char device demonstrating IRQ-safe spinlock discipline");
