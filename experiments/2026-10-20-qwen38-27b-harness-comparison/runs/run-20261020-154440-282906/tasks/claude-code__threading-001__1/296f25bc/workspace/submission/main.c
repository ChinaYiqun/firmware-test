/*
 * Producer-consumer demo using a bounded Zephyr message queue.
 *
 * - A producer thread (higher priority) puts incrementing values
 *   into the queue with a short delay between sends.
 * - A consumer thread (lower priority) blocks on the queue and
 *   prints each value as it arrives.
 *
 * Both threads and the queue are statically defined.
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

/* 1. Message struct carrying an integer value */
struct message {
	int32_t value;
};

/* Bounded queue: holds up to 8 messages, aligned to 1 word. */
#define MSGQ_MAX_MESSAGES	8
K_MSGQ_DEFINE(msgq, sizeof(struct message), MSGQ_MAX_MESSAGES, 1);

/* 5. Producer runs at a higher priority (lower number) than the consumer. */
#define PRODUCER_PRIORITY	5
#define CONSUMER_PRIORITY	7

#define PRODUCER_DELAY_MS	200

/* 6. Producer thread (statically defined) */
static void producer_main(void *arg1, void *arg2, void *arg3)
{
	struct message msg;
	k_timeout_t timeout = K_FOREVER;
	int value = 0;

	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	while (true) {
		msg.value = value++;

		/* Retry with a bounded timeout if the queue is full. */
		while (k_msgq_put(&msgq, &msg, timeout) != 0) {
			if (timeout == K_FOREVER) {
				timeout = K_MSEC(10);
			}
		}
		timeout = K_FOREVER;

		LOG_INF("Produced: %d", msg.value);

		/* 3. Short delay between sends. */
		k_sleep(K_MSEC(PRODUCER_DELAY_MS));
	}
}

static K_THREAD_STACK_DEFINE(producer_stack, 1024);
K_THREAD_DEFINE(producer_id, sizeof(producer_stack), producer_main,
		NULL, NULL, NULL,
		PRODUCER_PRIORITY, 0, 0, NULL);

/* Consumer thread (statically defined) */
static void consumer_main(void *arg1, void *arg2, void *arg3)
{
	struct message msg;

	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	while (true) {
		/* Block until a message is available. */
		if (k_msgq_get(&msgq, &msg, K_FOREVER) == 0) {
			LOG_INF("Consumed: %d", msg.value);
		}
	}
}

static K_THREAD_STACK_DEFINE(consumer_stack, 1024);
K_THREAD_DEFINE(consumer_id, sizeof(consumer_stack), consumer_main,
		NULL, NULL, NULL,
		CONSUMER_PRIORITY, 0, 0, NULL);

int main(void)
{
	LOG_INF("Producer-consumer demo started");

	/* 7. Sleep forever; both threads keep running. */
	while (true) {
		k_sleep(K_SECONDS(1));
	}

	return 0;
}
