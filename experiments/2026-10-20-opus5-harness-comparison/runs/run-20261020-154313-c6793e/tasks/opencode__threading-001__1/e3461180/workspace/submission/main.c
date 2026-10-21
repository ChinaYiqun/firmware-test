/*
 * Zephyr RTOS producer-consumer example using a bounded message queue.
 *
 * - Producer thread pushes incrementing integers into the queue.
 * - Consumer thread pops values and prints them.
 * - Producer runs at a higher priority (numerically lower) than the consumer.
 * - Both threads are defined statically via K_THREAD_DEFINE.
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

/* Requirement 1: message struct carrying an integer value */
struct msg_item {
	int value;
};

/* Requirement 2: bounded message queue (10 slots, 4-byte alignment) */
#define MSGQ_DEPTH 10
K_MSGQ_DEFINE(data_msgq, sizeof(struct msg_item), MSGQ_DEPTH, 4);

#define STACK_SIZE 1024

/* Requirement 5: lower number == higher priority in Zephyr */
#define PRODUCER_PRIORITY 4
#define CONSUMER_PRIORITY 6

#define PRODUCE_DELAY_MS 100

/* Requirement 3: producer sends incrementing values with a short delay */
static void producer_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	struct msg_item msg;
	int counter = 0;

	printk("producer: started (prio %d)\n", PRODUCER_PRIORITY);

	while (1) {
		msg.value = counter;

		/* Block if the queue is full so no value is lost. */
		if (k_msgq_put(&data_msgq, &msg, K_FOREVER) == 0) {
			printk("producer: sent %d\n", msg.value);
			counter++;
		}

		k_msleep(PRODUCE_DELAY_MS);
	}
}

/* Requirement 4: consumer receives and prints values */
static void consumer_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	struct msg_item msg;

	printk("consumer: started (prio %d)\n", CONSUMER_PRIORITY);

	while (1) {
		if (k_msgq_get(&data_msgq, &msg, K_FOREVER) == 0) {
			printk("consumer: received %d\n", msg.value);
		}
	}
}

/* Requirement 6: statically defined threads, started at boot (delay 0) */
K_THREAD_DEFINE(producer_tid, STACK_SIZE,
		producer_entry, NULL, NULL, NULL,
		PRODUCER_PRIORITY, 0, 0);

K_THREAD_DEFINE(consumer_tid, STACK_SIZE,
		consumer_entry, NULL, NULL, NULL,
		CONSUMER_PRIORITY, 0, 0);

/* Requirement 7: main sleeps indefinitely while the threads run */
int main(void)
{
	printk("producer-consumer demo: queue depth %d\n", MSGQ_DEPTH);

	k_sleep(K_FOREVER);

	return 0;
}
