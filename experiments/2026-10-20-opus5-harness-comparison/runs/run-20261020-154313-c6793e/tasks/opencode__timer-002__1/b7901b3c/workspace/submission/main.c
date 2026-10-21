#include <zephyr/kernel.h>

/* Work item submitted from the timer expiry function */
static struct k_work work_item;

/* Worker function executed in the system work queue context */
static void worker_function(struct k_work *work)
{
	ARG_UNUSED(work);

	printk("Work executed\n");
}

/* Timer expiry function runs in interrupt context, so it only
 * submits the work item rather than doing the printing itself.
 */
static void timer_expiry_function(struct k_timer *timer)
{
	ARG_UNUSED(timer);

	k_work_submit(&work_item);
}

/* One-shot timer: expiry function only, no stop function */
K_TIMER_DEFINE(one_shot_timer, timer_expiry_function, NULL);

int main(void)
{
	k_work_init(&work_item, worker_function);

	/* Start as one-shot: 1 second initial duration, K_NO_WAIT period
	 * means the timer does not repeat.
	 */
	k_timer_start(&one_shot_timer, K_MSEC(1000), K_NO_WAIT);

	k_sleep(K_MSEC(3000));

	printk("Done\n");

	return 0;
}
