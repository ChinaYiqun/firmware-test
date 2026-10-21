#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/skbuff.h>
#include <linux/workqueue.h>
#include <linux/slab.h>

static struct sk_buff_head skb_q;
static struct work_struct drain_work;

static void drain_worker(struct work_struct *work)
{
	struct sk_buff *skb;

	while ((skb = skb_dequeue(&skb_q)) != NULL) {
		pr_info("embedeval skbq: consuming skb len=%u\n", skb->len);
		consume_skb(skb);
	}
}

void embedeval_enqueue_skb(struct sk_buff *skb)
{
	struct sk_buff *clone;

	if (!skb)
		return;

	clone = skb_clone(skb, GFP_ATOMIC);
	if (!clone)
		return;

	skb_queue_tail(&skb_q, clone);
	schedule_work(&drain_work);
}
EXPORT_SYMBOL(embedeval_enqueue_skb);

static int __init embedeval_skbq_init(void)
{
	skb_queue_head_init(&skb_q);
	INIT_WORK(&drain_work, drain_worker);
	pr_info("embedeval skbq: initialised\n");
	return 0;
}

static void __exit embedeval_skbq_exit(void)
{
	cancel_work_sync(&drain_work);
	skb_queue_purge(&skb_q);
	pr_info("embedeval skbq: exited\n");
}

module_init(embedeval_skbq_init);
module_exit(embedeval_skbq_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("sk_buff clone + queue + drain worker lifecycle example");
