#include <zephyr/kernel.h>

/*
 * Priority inheritance demo.
 *
 * k_mutex (unlike k_sem) implements priority inheritance: when a
 * high-priority thread blocks on a mutex held by a low-priority thread,
 * the low-priority thread temporarily inherits the high priority, so it
 * finishes its critical section as soon as possible and the
 * high-priority thread is not starved behind medium-priority threads.
 */

/* Mutex with priority inheritance built in */
K_MUTEX_DEFINE(work_mutex, K_MUTEX_DEFAULT);

/* Lowest priority thread (priority 10): acquires the mutex first and
 * holds it while simulating work. */
static void low_prio_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_mutex_lock(&work_mutex, K_FOREVER);
	printk("Low: holding mutex\n");
	k_sleep(K_MSEC(300));
	printk("Low: releasing mutex\n");
	k_mutex_unlock(&work_mutex);
}

/* Medium priority thread (priority 7): starts after low holds the
 * mutex. It cannot run the critical section, but on its own it would
 * preempt the low-priority thread. */
static void med_prio_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sleep(K_MSEC(50));
	printk("Med: running (should not preempt low)\n");

	while (true) {
		k_sleep(K_MSEC(100));
	}
}

/* Highest priority thread (priority 4): starts after low has the
 * mutex. Its attempt to lock blocks until low releases; while blocked,
 * low inherits priority 4 and finishes its work without being
 * preempted by med. */
static void high_prio_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	k_sleep(K_MSEC(100));
	k_mutex_lock(&work_mutex, K_FOREVER);
	printk("High: acquired mutex\n");
	k_mutex_unlock(&work_mutex);
}

K_THREAD_DEFINE(low_prio_thread, 1024, K_THREAD_STACK_SECTION_DEFAULT, 10,
		low_prio_entry, NULL, NULL, NULL, K_NO_WAIT, 0, NULL);

K_THREAD_DEFINE(med_prio_thread, 1024, K_THREAD_STACK_SECTION_DEFAULT, 7,
		med_prio_entry, NULL, NULL, NULL, K_NO_WAIT, 0, NULL);

K_THREAD_DEFINE(high_prio_thread, 1024, K_THREAD_STACK_SECTION_DEFAULT, 4,
		high_prio_entry, NULL, NULL, NULL, K_NO_WAIT, 0, NULL);

int main(void)
{
	k_sleep(K_FOREVER);
	return 0;
}
