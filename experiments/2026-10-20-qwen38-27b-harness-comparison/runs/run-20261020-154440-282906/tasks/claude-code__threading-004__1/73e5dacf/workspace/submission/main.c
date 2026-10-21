/*
 * Priority Inheritance demo using a Zephyr mutex.
 *
 * k_mutex provides priority inheritance: when the highest-priority
 * waiter blocks on the mutex, the current holder is temporarily
 * boosted to the waiter's priority so that a medium-priority thread
 * cannot starve the low-priority holder.
 */

#include <zephyr/kernel.h>

/* Mutex with priority inheritance built-in (do NOT use k_sem here). */
K_MUTEX_DEFINE(pi_mutex);

/* Priority 10 - lowest priority; runs first and holds the mutex. */
void low_prio_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* Lock the mutex with K_FOREVER */
	k_mutex_lock(&pi_mutex, K_FOREVER);

	printk("Low: holding mutex\n");

	/* Simulate work while holding the mutex */
	k_msleep(300);

	printk("Low: releasing mutex\n");

	/* Unlock the mutex */
	k_mutex_unlock(&pi_mutex);
}

/* Priority 7 - medium priority; should NOT preempt low while it
 * holds the mutex (low is boosted to priority 4 by inheritance).
 */
void med_prio_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* Start after low acquires the mutex */
	k_msleep(50);

	printk("Med: running (should not preempt low)\n");

	/* Loop forever */
	while (true) {
		k_msleep(100);
	}
}

/* Priority 4 - highest priority; tries to acquire the mutex,
 * triggering priority inheritance on the holder.
 */
void high_prio_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* Start after low has the mutex */
	k_msleep(100);

	/* Try to lock the mutex with K_FOREVER. Low's priority is
	 * inherited (boosted to 4) until it releases the mutex.
	 */
	k_mutex_lock(&pi_mutex, K_FOREVER);

	printk("High: acquired mutex\n");

	/* Unlock the mutex immediately */
	k_mutex_unlock(&pi_mutex);
}

/* Stack 1024 bytes, priority 10 (lowest priority). */
K_THREAD_DEFINE(low_prio_thread, 1024, low_prio_entry,
		NULL, NULL, NULL,
		10, 0, 0);

/* Stack 1024 bytes, priority 7 (medium priority). */
K_THREAD_DEFINE(med_prio_thread, 1024, med_prio_entry,
		NULL, NULL, NULL,
		7, 0, 0);

/* Stack 1024 bytes, priority 4 (highest priority). */
K_THREAD_DEFINE(high_prio_thread, 1024, high_prio_entry,
		NULL, NULL, NULL,
		4, 0, 0);

int main(void)
{
	/* Threads defined above start automatically; main just idles. */
	k_sleep(K_FOREVER);

	return 0;
}
