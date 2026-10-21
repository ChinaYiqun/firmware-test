#include <zephyr/kernel.h>

/* Mutex with priority inheritance built-in */
K_MUTEX_DEFINE(resource_mutex);

#define LOW_PRIO 10
#define MED_PRIO 7
#define HIGH_PRIO 4

void low_prio_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_mutex_lock(&resource_mutex, K_FOREVER);
	printk("Low: holding mutex\n");
	k_msleep(300);
	printk("Low: releasing mutex\n");
	k_mutex_unlock(&resource_mutex);
}

void med_prio_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_msleep(50);
	printk("Med: running (should not preempt low)\n");

	while (1) {
		k_msleep(100);
	}
}

void high_prio_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_msleep(100);
	k_mutex_lock(&resource_mutex, K_FOREVER);
	printk("High: acquired mutex\n");
	k_mutex_unlock(&resource_mutex);
}

K_THREAD_DEFINE(low_prio_thread, 1024, low_prio_entry, NULL, NULL, NULL,
		LOW_PRIO, 0, 0);

K_THREAD_DEFINE(med_prio_thread, 1024, med_prio_entry, NULL, NULL, NULL,
		MED_PRIO, 0, 0);

K_THREAD_DEFINE(high_prio_thread, 1024, high_prio_entry, NULL, NULL, NULL,
		HIGH_PRIO, 0, 0);

int main(void)
{
	k_sleep(K_FOREVER);
	return 0;
}
