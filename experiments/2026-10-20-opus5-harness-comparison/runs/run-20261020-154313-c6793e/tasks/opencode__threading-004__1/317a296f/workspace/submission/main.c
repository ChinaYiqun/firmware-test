#include <zephyr/kernel.h>

/* Define mutex with priority inheritance */
K_MUTEX_DEFINE(my_mutex);

/* Low priority thread entry function */
void low_prio_entry(void *p1, void *p2, void *p3)
{
	k_mutex_lock(&my_mutex, K_FOREVER);
	printk("Low: holding mutex\n");
	k_sleep(K_MSEC(300));
	printk("Low: releasing mutex\n");
	k_mutex_unlock(&my_mutex);
}

/* Medium priority thread entry function */
void med_prio_entry(void *p1, void *p2, void *p3)
{
	k_sleep(K_MSEC(50));
	printk("Med: running (should not preempt low)\n");
	while (1) {
		k_sleep(K_MSEC(100));
	}
}

/* High priority thread entry function */
void high_prio_entry(void *p1, void *p2, void *p3)
{
	k_sleep(K_MSEC(100));
	k_mutex_lock(&my_mutex, K_FOREVER);
	printk("High: acquired mutex\n");
	k_mutex_unlock(&my_mutex);
}

/* Define three threads with different priorities */
K_THREAD_DEFINE(low_prio_thread, 1024, low_prio_entry, NULL, NULL, NULL, 10, 0, 0);
K_THREAD_DEFINE(med_prio_thread, 1024, med_prio_entry, NULL, NULL, NULL, 7, 0, 0);
K_THREAD_DEFINE(high_prio_thread, 1024, high_prio_entry, NULL, NULL, NULL, 4, 0, 0);

/* Main function */
int main(void)
{
	k_sleep(K_FOREVER);
	return 0;
}
