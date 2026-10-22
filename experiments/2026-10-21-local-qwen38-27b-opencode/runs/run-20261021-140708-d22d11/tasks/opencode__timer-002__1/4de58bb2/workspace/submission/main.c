#include <zephyr/kernel.h>

static struct k_work work;

static void worker_fn(struct k_work *item)
{
	printk("Work executed\n");
}

static void timer_expiry(struct k_timer *timer)
{
	k_work_submit(&work);
}

K_TIMER_DEFINE(my_timer, timer_expiry);

int main(void)
{
	k_work_init(&work, worker_fn);
	k_timer_start(&my_timer, K_MSEC(1000));
	k_sleep(K_MSEC(3000));
	printk("Done\n");
	return 0;
}
