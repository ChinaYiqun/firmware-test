/*
 * One-shot kernel timer demo.
 *
 * A one-shot kernel timer fires after 1 second; its expiry function
 * submits a work item to the system work queue, whose thread then
 * runs the worker function and prints "Work executed".
 */

#include <zephyr/kernel.h>

static struct k_work my_work;

/* Worker function executed by the system work queue thread. */
static void worker_fn(struct k_work *work)
{
	ARG_UNUSED(work);

	printk("Work executed\n");
}

/* Expiry function for the one-shot timer. */
static void timer_expiry_fn(struct k_timer *timer)
{
	ARG_UNUSED(timer);

	k_work_submit(&my_work);
}

/* One-shot kernel timer (no sync callback needed). */
K_TIMER_DEFINE(my_timer, timer_expiry_fn, NULL);

int main(void)
{
	k_work_init(&my_work, worker_fn);

	/* Fire once after 1 second; K_NO_WAIT means no periodic repeat. */
	k_timer_start(&my_timer, K_MSEC(1000), K_NO_WAIT);

	/* Give the system work queue time to execute the work item. */
	k_sleep(K_MSEC(3000));

	printk("Done\n");

	return 0;
}
