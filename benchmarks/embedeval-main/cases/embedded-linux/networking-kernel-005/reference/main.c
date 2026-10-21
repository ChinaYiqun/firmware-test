#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/netdevice.h>
#include <linux/notifier.h>

static int embedeval_netdev_event(struct notifier_block *nb,
				  unsigned long event, void *ptr)
{
	struct net_device *dev = netdev_notifier_info_to_dev(ptr);

	switch (event) {
	case NETDEV_UP:
		pr_info("embedeval netdev: %s UP\n", dev->name);
		break;
	case NETDEV_DOWN:
		pr_info("embedeval netdev: %s DOWN\n", dev->name);
		break;
	default:
		break;
	}

	return NOTIFY_OK;
}

static struct notifier_block embedeval_netdev_nb = {
	.notifier_call = embedeval_netdev_event,
};

static int __init embedeval_netdev_init(void)
{
	int ret;

	ret = register_netdevice_notifier(&embedeval_netdev_nb);
	if (ret) {
		pr_err("embedeval netdev: register failed: %d\n", ret);
		return ret;
	}

	pr_info("embedeval netdev: notifier registered\n");
	return 0;
}

static void __exit embedeval_netdev_exit(void)
{
	unregister_netdevice_notifier(&embedeval_netdev_nb);
	pr_info("embedeval netdev: notifier unregistered\n");
}

module_init(embedeval_netdev_init);
module_exit(embedeval_netdev_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Netdevice UP/DOWN notifier tracer");
