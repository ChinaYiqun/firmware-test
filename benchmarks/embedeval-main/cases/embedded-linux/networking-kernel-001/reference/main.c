#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/net.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/workqueue.h>
#include <linux/atomic.h>
#include <linux/slab.h>
#include <linux/skbuff.h>
#include <net/net_namespace.h>

static atomic_t pkt_count = ATOMIC_INIT(0);
static struct work_struct stats_work;

static void stats_worker(struct work_struct *work)
{
	int count = atomic_read(&pkt_count);

	pr_info("embedeval netfilter: observed %d packets\n", count);
}

static unsigned int
embedeval_nf_hookfn(void *priv, struct sk_buff *skb,
		    const struct nf_hook_state *state)
{
	atomic_inc(&pkt_count);
	schedule_work(&stats_work);
	return NF_ACCEPT;
}

static struct nf_hook_ops nf_ops = {
	.hook     = embedeval_nf_hookfn,
	.hooknum  = NF_INET_PRE_ROUTING,
	.pf       = PF_INET,
	.priority = NF_IP_PRI_FIRST,
};

static int __init embedeval_netfilter_init(void)
{
	int ret;

	INIT_WORK(&stats_work, stats_worker);

	ret = nf_register_net_hook(&init_net, &nf_ops);
	if (ret) {
		pr_err("embedeval netfilter: register failed: %d\n", ret);
		return ret;
	}

	pr_info("embedeval netfilter: hook registered\n");
	return 0;
}

static void __exit embedeval_netfilter_exit(void)
{
	nf_unregister_net_hook(&init_net, &nf_ops);
	cancel_work_sync(&stats_work);
	pr_info("embedeval netfilter: hook unregistered\n");
}

module_init(embedeval_netfilter_init);
module_exit(embedeval_netfilter_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Netfilter PRE_ROUTING hook with softirq-safe body and deferred logging");
