#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/skbuff.h>
#include <net/genetlink.h>

#define REPLY_STRING "embedeval-echo"

enum {
	EMBEDEVAL_CMD_UNSPEC,
	EMBEDEVAL_CMD_ECHO,
	__EMBEDEVAL_CMD_MAX,
};
#define EMBEDEVAL_CMD_MAX (__EMBEDEVAL_CMD_MAX - 1)

enum {
	EMBEDEVAL_ATTR_UNSPEC,
	EMBEDEVAL_ATTR_MSG,
	__EMBEDEVAL_ATTR_MAX,
};
#define EMBEDEVAL_ATTR_MAX (__EMBEDEVAL_ATTR_MAX - 1)

static const struct nla_policy embedeval_genl_policy[EMBEDEVAL_ATTR_MAX + 1] = {
	[EMBEDEVAL_ATTR_MSG] = { .type = NLA_STRING },
};

/* Forward declare the family so genlmsg_put_reply can reference it. */
static struct genl_family embedeval_genl_family;

static int embedeval_cmd_echo(struct sk_buff *skb, struct genl_info *info)
{
	struct sk_buff *reply;
	void *hdr;
	int ret;

	reply = genlmsg_new(NLMSG_DEFAULT_SIZE, GFP_KERNEL);
	if (!reply)
		return -ENOMEM;

	hdr = genlmsg_put_reply(reply, info, &embedeval_genl_family, 0,
				EMBEDEVAL_CMD_ECHO);
	if (!hdr) {
		nlmsg_free(reply);
		return -EMSGSIZE;
	}

	ret = nla_put_string(reply, EMBEDEVAL_ATTR_MSG, REPLY_STRING);
	if (ret) {
		genlmsg_cancel(reply, hdr);
		nlmsg_free(reply);
		return ret;
	}

	genlmsg_end(reply, hdr);

	return genlmsg_reply(reply, info);
}

static const struct genl_ops embedeval_genl_ops[] = {
	{
		.cmd    = EMBEDEVAL_CMD_ECHO,
		.flags  = 0,
		.doit   = embedeval_cmd_echo,
	},
};

static struct genl_family embedeval_genl_family = {
	.name     = "embedeval_genl",
	.version  = 1,
	.module   = THIS_MODULE,
	.ops      = embedeval_genl_ops,
	.n_ops    = ARRAY_SIZE(embedeval_genl_ops),
	.maxattr  = EMBEDEVAL_ATTR_MAX,
	.policy   = embedeval_genl_policy,
};

static int __init embedeval_genl_init(void)
{
	int ret;

	ret = genl_register_family(&embedeval_genl_family);
	if (ret) {
		pr_err("embedeval genl: register failed: %d\n", ret);
		return ret;
	}

	pr_info("embedeval genl: family registered\n");
	return 0;
}

static void __exit embedeval_genl_exit(void)
{
	genl_unregister_family(&embedeval_genl_family);
	pr_info("embedeval genl: family unregistered\n");
}

module_init(embedeval_genl_init);
module_exit(embedeval_genl_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Generic netlink family with a single echo operation");
