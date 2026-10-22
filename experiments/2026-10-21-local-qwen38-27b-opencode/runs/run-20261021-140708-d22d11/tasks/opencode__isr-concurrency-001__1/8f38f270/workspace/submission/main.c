/*
 * ringbuf - ISR-safe, lock-free single-producer / single-consumer ring buffer
 * for Zephyr RTOS.
 *
 * Design
 * ------
 *   Producer : ISR context  (writes, advances `head`)
 *   Consumer : thread context (reads,  advances `tail`)
 *
 *   Only one context ever writes `head` and only one ever writes `tail`,
 *   so no compare-and-swap loop and no mutex is needed.  Correctness comes
 *   from the release/acquire ordering that Zephyr's atomic_set()/atomic_get()
 *   provide:
 *
 *     producer:  buf[head % size] = byte;      (plain store)
 *                atomic_set(&head, head + 1);  (release)
 *     consumer:  head = atomic_get(&head);     (acquire)
 *                byte = buf[head % size];      (plain load)
 *
 *   The release on `head` guarantees the consumer sees the byte store before
 *   it observes the new head value, and the acquire on `tail` gives the
 *   producer the same guarantee in the other direction.
 *
 *   `head` and `tail` are monotonically increasing counters (not wrapped
 *   indices).  A byte's slot is `counter % size`.  Because the buffer is
 *   declared full as soon as `head - tail == size`, the write slot and the
 *   read slot can never alias, so an in-flight write can never clobber a
 *   byte the consumer is about to read.  Unsigned subtraction makes the
 *   occupancy test correct even after the 32-bit counters wrap around.
 *
 *   FIFO order is preserved trivially: the producer fills slots in increasing
 *   `head` order and the consumer drains them in increasing `tail` order.
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/sys/printk.h>

#include <errno.h>
#include <stdint.h>
#include <stdbool.h>

/* ==========================================================================
 *  ringbuf.h  (public interface)
 * ========================================================================== */

struct ringbuf {
	uint8_t  *buf;     /* underlying storage                      */
	size_t   size;     /* capacity in bytes (must be > 0)         */
	atomic_t  head;     /* next slot the producer will write (mono)*/
	atomic_t  tail;     /* next slot the consumer will read  (mono)*/
};

/*
 * Initialise a ring buffer backed by the caller-provided storage.
 * Safe to call from thread context before any producer/consumer starts.
 */
void ringbuf_init(struct ringbuf *rb, uint8_t *buf, size_t size);

/*
 * Static-allocation convenience.  Declares the storage and the ring buffer.
 * Static storage is zero-initialised, so head == tail == 0 on boot.
 */
#define RINGBUF_DEFINE(name, size)                             \
	static uint8_t name ## _storage[(size)];                  \
	static struct ringbuf name = {                            \
		.buf  = name ## _storage,                             \
		.size = (size),                                       \
	}

/*
 * Producer (ISR context): enqueue one byte.
 *   Returns 0 on success, -ENOSPC if the buffer is full.
 */
int ringbuf_put(struct ringbuf *rb, uint8_t byte);

/*
 * Consumer (thread context): dequeue one byte.
 *   Returns 0 on success, -ENOBUFS if the buffer is empty.
 */
int ringbuf_get(struct ringbuf *rb, uint8_t *byte);

/*
 * Bulk variants: copy as many bytes as fit / are available.
 *   Returns the number of bytes actually transferred (may be < len).
 */
size_t ringbuf_put_buf(struct ringbuf *rb, const uint8_t *data, size_t len);
size_t ringbuf_get_buf(struct ringbuf *rb, uint8_t *data, size_t len);

/* Occupancy queries (safe from either context). */
size_t ringbuf_count(const struct ringbuf *rb);
bool   ringbuf_is_full(const struct ringbuf *rb);
bool   ringbuf_is_empty(const struct ringbuf *rb);

/* ==========================================================================
 *  ringbuf.c  (implementation)
 * ========================================================================== */

void ringbuf_init(struct ringbuf *rb, uint8_t *buf, size_t size)
{
	rb->buf  = buf;
	rb->size = size;
	atomic_set(&rb->head, 0);
	atomic_set(&rb->tail, 0);
}

int ringbuf_put(struct ringbuf *rb, uint8_t byte)
{
	uint32_t head = (uint32_t)atomic_get(&rb->head);
	uint32_t tail = (uint32_t)atomic_get(&rb->tail);

	if ((head - tail) >= (uint32_t)rb->size) {
		return -ENOSPC;		/* full: no slot available */
	}

	rb->buf[head % rb->size] = byte;	/* store the byte first ... */
	atomic_set(&rb->head, head + 1);	/* ... then publish it (release) */

	return 0;
}

int ringbuf_get(struct ringbuf *rb, uint8_t *byte)
{
	uint32_t tail = (uint32_t)atomic_get(&rb->tail);
	uint32_t head = (uint32_t)atomic_get(&rb->head);

	if (tail >= head) {
		return -ENOBUFS;		/* empty: nothing to read */
	}

	*byte = rb->buf[tail % rb->size];	/* acquire of head happened above */
	atomic_set(&rb->tail, tail + 1);	/* release: slot is now free */

	return 0;
}

size_t ringbuf_put_buf(struct ringbuf *rb, const uint8_t *data, size_t len)
{
	size_t n = 0;

	while (n < len && ringbuf_put(rb, data[n]) == 0) {
		n++;
	}
	return n;
}

size_t ringbuf_get_buf(struct ringbuf *rb, uint8_t *data, size_t len)
{
	size_t n = 0;

	while (n < len && ringbuf_get(rb, &data[n]) == 0) {
		n++;
	}
	return n;
}

size_t ringbuf_count(const struct ringbuf *rb)
{
	uint32_t head = (uint32_t)atomic_get(&rb->head);
	uint32_t tail = (uint32_t)atomic_get(&rb->tail);

	return (size_t)(head - tail);
}

bool ringbuf_is_full(const struct ringbuf *rb)
{
	return ringbuf_count(rb) >= rb->size;
}

bool ringbuf_is_empty(const struct ringbuf *rb)
{
	return ringbuf_count(rb) == 0;
}

/* ==========================================================================
 *  Demonstration: ISR producer -> thread consumer
 * ========================================================================== */

RINGBUF_DEFINE(app_ring, 64);

/* ---- consumer (thread context) ------------------------------------------ */

static void consumer_thread(void *arg1, void *arg2, void *arg3)
{
	uint8_t byte;

	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	while (true) {
		if (ringbuf_get(&app_ring, &byte) == 0) {
			printk("consumer: got %u (in buf: %u)\n",
			       byte, ringbuf_count(&app_ring));
		} else {
			k_sleep(K_MSEC(1));	/* idle while empty */
		}
	}
}

K_THREAD_STACK_DEFINE(consumer_stack, 1024);
static struct k_thread consumer_thread_data;

/* ---- producer (ISR context) --------------------------------------------- */

#if DT_NODE_EXISTS(DT_ALIAS(sw0))
/*
 * Real ISR producer: every edge on the sw0 button pushes a byte into the
 * ring buffer.  This is genuine interrupt context, so ringbuf_put() must
 * (and does) use only atomics -- no sleeping, no mutexes.
 */
static const struct device *const sw0_dev = DEVICE_DT_GET(DT_ALIAS(sw0));
static const gpio_pin_t sw0_pin = DT_GPIO_PIN(DT_ALIAS(sw0));
static uint8_t prod_seq;

static void sw0_isr(const struct device *dev)
{
	(void)dev;

	(void)ringbuf_put(&app_ring, prod_seq++);

	/* Edge-triggered GPIO IRQs latch off after firing; re-arm so the
	 * next press is also delivered from ISR context.
	 */
	gpio_pin_interrupt_configure_dt(dev, sw0_pin, GPIO_INT_EDGE_BOTH);
}

static void producer_isr_init(void)
{
	gpio_pin_configure_dt(sw0_dev,
			      GPIO_INPUT | GPIO_ACTIVE_LOW | GPIO_PULL_UP);
	gpio_pin_interrupt_configure_dt(sw0_dev, sw0_pin, GPIO_INT_EDGE_BOTH);
}
#else
/*
 * Fallback when the board has no sw0 alias: a thread stands in for the ISR.
 * It exercises the exact same ringbuf_put() path, so the lock-free logic is
 * exercised identically; only the calling context differs.
 */
static void producer_thread(void *arg1, void *arg2, void *arg3)
{
	uint8_t seq = 0;

	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	while (true) {
		if (ringbuf_put(&app_ring, seq) == 0) {
			seq++;
		}
		k_sleep(K_MSEC(100));
	}
}

K_THREAD_STACK_DEFINE(producer_stack, 1024);
static struct k_thread producer_thread_data;
#endif /* DT_NODE_EXISTS(DT_ALIAS(sw0)) */

int main(void)
{
	/* Re-initialise explicitly so the demo does not rely on static
	 * zero-init (and so it works for heap/stack buffers too).
	 */
	ringbuf_init(&app_ring, app_ring_storage, sizeof(app_ring_storage));

	k_thread_create(&consumer_thread_data, consumer_stack,
			K_THREAD_STACK_SIZEOF(consumer_stack),
			consumer_thread, NULL, NULL, NULL,
			K_PRIO_COOP(5), 0, K_NO_WAIT);
	k_thread_name_set(&consumer_thread_data, "ringbuf-consumer");

#if DT_NODE_EXISTS(DT_ALIAS(sw0))
	producer_isr_init();
	printk("producer: GPIO sw0 ISR\n");
#else
	k_thread_create(&producer_thread_data, producer_stack,
			K_THREAD_STACK_SIZEOF(producer_stack),
			producer_thread, NULL, NULL, NULL,
			K_PRIO_COOP(7), 0, K_NO_WAIT);
	k_thread_name_set(&producer_thread_data, "ringbuf-producer");
	printk("producer: fallback thread (no sw0 alias)\n");
#endif

	return 0;
}
