/*
 * Zephyr producer-consumer example using a bounded message queue.
 *
 * The producer thread pushes incrementing integers into the queue, the
 * consumer thread pops them and prints them. The producer runs at a higher
 * scheduling priority (numerically lower value) than the consumer, so it
 * keeps the queue fed and only yields the CPU while sleeping or when the
 * queue is full.
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

/* Message carried through the queue. */
struct data_msg {
	int value;
};

/* Queue geometry and thread configuration. */
#define MSGQ_DEPTH        10
#define STACK_SIZE        1024
#define PRODUCER_PRIORITY 4 /* higher priority: lower number */
#define CONSUMER_PRIORITY 6
#define PRODUCE_DELAY_MS  100

/* Bounded message queue, statically allocated and word aligned. */
K_MSGQ_DEFINE(data_msgq, sizeof(struct data_msg), MSGQ_DEPTH, 4);

static void producer_thread(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	struct data_msg msg = {.value = 0};

	while (1) {
		/* Block if the queue is full so no value is ever dropped. */
		int ret = k_msgq_put(&data_msgq, &msg, K_FOREVER);

		if (ret == 0) {
			printk("Producer: sent %d\n", msg.value);
			msg.value++;
		} else {
			printk("Producer: put failed (%d)\n", ret);
		}

		k_sleep(K_MSEC(PRODUCE_DELAY_MS));
	}
}

static void consumer_thread(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	struct data_msg msg;

	while (1) {
		int ret = k_msgq_get(&data_msgq, &msg, K_FOREVER);

		if (ret == 0) {
			printk("Consumer: received %d\n", msg.value);
		} else {
			printk("Consumer: get failed (%d)\n", ret);
		}
	}
}

/* Statically defined threads; they start as soon as the kernel is up. */
K_THREAD_DEFINE(producer_tid, STACK_SIZE, producer_thread, NULL, NULL, NULL,
		PRODUCER_PRIORITY, 0, 0);

K_THREAD_DEFINE(consumer_tid, STACK_SIZE, consumer_thread, NULL, NULL, NULL,
		CONSUMER_PRIORITY, 0, 0);

int main(void)
{
	printk("Producer-consumer demo started\n");

	/* Nothing to do here: let the producer and consumer threads run. */
	while (1) {
		k_sleep(K_FOREVER);
	}

	return 0;
}
