#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

struct message {
	int value;
};

#define QUEUE_MAX_MESSAGES 10

K_MSGQ_DEFINE(msg_queue, sizeof(struct message), QUEUE_MAX_MESSAGES, 1);

#define PRODUCER_PRIORITY 5
#define CONSUMER_PRIORITY 10

static void producer_thread(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	int value = 0;
	struct message msg;

	while (true) {
		msg.value = value++;

		k_msgq_put(&msg_queue, &msg, K_FOREVER);
		printk("Producer sent: %d\n", msg.value);

		k_msleep(100);
	}
}

static void consumer_thread(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	struct message msg;

	while (true) {
		k_msgq_get(&msg_queue, &msg, K_FOREVER);
		printk("Consumer received: %d\n", msg.value);
	}
}

K_THREAD_DEFINE(producer_thread_id, 1024, producer_thread, NULL, NULL, NULL,
		PRODUCER_PRIORITY, 0, 0, 0);

K_THREAD_DEFINE(consumer_thread_id, 1024, consumer_thread, NULL, NULL, NULL,
		CONSUMER_PRIORITY, 0, 0, 0);

int main(void)
{
	printk("Producer-consumer application started\n");

	while (true) {
		k_sleep(K_FOREVER);
	}

	return 0;
}
