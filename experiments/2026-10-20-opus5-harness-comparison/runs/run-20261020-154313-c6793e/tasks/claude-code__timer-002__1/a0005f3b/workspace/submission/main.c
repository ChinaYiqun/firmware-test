/*
 * One-shot kernel timer that submits work to the system work queue.
 */

#include <zephyr/kernel.h>

static struct k_work work;

/* Runs in the system work queue thread context. */
static void work_handler(struct k_work *item)
{
	ARG_UNUSED(item);

	printk("Work executed\n");
}

/* Runs in ISR context; defer the real work to the system work queue. */
static void timer_expiry(struct k_timer *timer)
{
	ARG_UNUSED(timer);

	k_work_submit(&work);
}

K_TIMER_DEFINE(one_shot_timer, timer_expiry, NULL);

int main(void)
{
	k_work_init(&work, work_handler);

	/* Duration 1s, period K_NO_WAIT -> fires exactly once. */
	k_timer_start(&one_shot_timer, K_MSEC(1000), K_NO_WAIT);

	k_sleep(K_MSEC(3000));

	printk("Done\n");

	return 0;
}
