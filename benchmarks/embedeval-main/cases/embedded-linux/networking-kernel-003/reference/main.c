#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/skbuff.h>
#include <linux/netlink.h>
#include <net/netlink.h>
#include <net/net_namespace.h>
#include <net/sock.h>

#define EMBEDEVAL_NETLINK_PROTO 31
#define REPLY_PAYLOAD "embedeval-ack"

static struct sock *nl_sk;

static void embedeval_netlink_input(struct sk_buff *skb)
{
	struct nlmsghdr *nlh;
	struct sk_buff *reply;
	struct nlmsghdr *rnlh;
	int pid;
	int ret;

	nlh = nlmsg_hdr(skb);
	if (!nlh)
		return;

	pid = nlh->nlmsg_pid;

	reply = nlmsg_new(sizeof(REPLY_PAYLOAD), GFP_KERNEL);
	if (!reply)
		return;

	rnlh = nlmsg_put(reply, 0, 0, NLMSG_DONE, sizeof(REPLY_PAYLOAD), 0);
	if (!rnlh) {
		nlmsg_free(reply);
		return;
	}

	memcpy(nlmsg_data(rnlh), REPLY_PAYLOAD, sizeof(REPLY_PAYLOAD));

	ret = netlink_unicast(nl_sk, reply, pid, 0);
	if (ret < 0)
		pr_warn("embedeval netlink: unicast failed: %d\n", ret);
}

static int __init embedeval_netlink_init(void)
{
	struct netlink_kernel_cfg cfg = {
		.input = embedeval_netlink_input,
	};

	nl_sk = netlink_kernel_create(&init_net, EMBEDEVAL_NETLINK_PROTO, &cfg);
	if (!nl_sk) {
		pr_err("embedeval netlink: create failed\n");
		return -ENOMEM;
	}

	pr_info("embedeval netlink: listening on proto %d\n",
		EMBEDEVAL_NETLINK_PROTO);
	return 0;
}

static void __exit embedeval_netlink_exit(void)
{
	if (nl_sk)
		netlink_kernel_release(nl_sk);
	pr_info("embedeval netlink: released\n");
}

module_init(embedeval_netlink_init);
module_exit(embedeval_netlink_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Netlink kernel endpoint with input callback and unicast echo");
