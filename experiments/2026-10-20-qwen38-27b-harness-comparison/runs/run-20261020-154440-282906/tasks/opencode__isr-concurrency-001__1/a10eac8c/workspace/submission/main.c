/*
 * isr_ring_buffer -- ISR-safe lock-free SPSC ring buffer for Zephyr RTOS
 * =====================================================================
 *
 * Submitted as a single file (submission/main.c) containing:
 *   Part 1: public API     (what would live in isr_ring_buffer.h)
 *   Part 2: implementation (what would live in isr_ring_buffer.c)
 *   Part 3: demo main()    (ISR producer via k_timer expiry, thread consumer)
 *
 * Design
 * ------
 * Classic single-producer / single-consumer (SPSC) lock-free ring buffer:
 *
 *   - head : monotonically increasing next-write index,
 *            written ONLY by the producer (ISR context)
 *   - tail : monotonically increasing next-read index,
 *            written ONLY by the consumer (thread context)
 *
 * Each side snapshots the other's index with atomic_get() and publishes
 * its own index update with atomic_set(). Zephyr's atomic_get()/atomic_set()
 * carry the required compiler + memory fences, so:
 *
 *   producer:  storage[head] = x;    atomic_set(&head, head + 1);
 *   consumer:  h = atomic_get(&head); ...read storage[tail]...
 *              atomic_set(&tail, tail + 1);
 *
 * guarantees that item data is globally visible before the index that
 * advertises it, and that the consumer never reads a slot the producer
 * could rewrite (the invariant head - tail <= capacity is maintained
 * because the producer refuses to write while full).
 *
 * No mutexes, no spinlocks, no critical sections: the ISR path never
 * blocks and the thread path never waits on the ISR.
 *
 * Semantics
 * ---------
 *   - Buffer full  : ring_buf_write() returns false and the item is
 *                    dropped (bulk variant returns the number stored).
 *   - Buffer empty : ring_buf_read() returns false; the caller polls or
 *                    blocks elsewhere (e.g. on a k_sem signalled from the
 *                    ISR) -- the buffer itself stays lock-free.
 *   - FIFO order   : items are always consumed in the order written.
 *   - Capacity     : all `size` slots are usable (monotonic counters
 *                    avoid the "wasted slot" trick).
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* ==========================================================================
 * Part 1: public API   (header: isr_ring_buffer.h)
 * ========================================================================== */

typedef struct {
	uint8_t *storage; /* backing array; must outlive the buffer  */
	size_t   size;    /* capacity in bytes (must be > 0)         */
	atomic_t head;    /* next write index, monotonic, producer-owned */
	atomic_t tail;    /* next read index, monotonic, consumer-owned  */
} ring_buf_t;

/* Initialize an empty ring buffer. Call once before first use. */
void ring_buf_init(ring_buf_t *rb, uint8_t *storage, size_t size);

/*
 * Producer API -- safe to call from ISR context (never blocks).
 *
 * @return true if the byte was stored, false if the buffer is full
 *         (the byte is dropped).
 */
bool ring_buf_write(ring_buf_t *rb, uint8_t data);

/* Bulk producer variant, ISR context safe.
 * Stores up to `len` bytes, returns the number actually stored. */
size_t ring_buf_write_buf(ring_buf_t *rb, const uint8_t *data, size_t len);

/*
 * Consumer API -- intended for thread context (never blocks).
 *
 * @return true and stores one byte in *data, or false if the buffer
 *         is empty.
 */
bool ring_buf_read(ring_buf_t *rb, uint8_t *data);

/* Bulk consumer variant.
 * Reads up to `len` bytes, returns the number actually read. */
size_t ring_buf_read_buf(ring_buf_t *rb, uint8_t *data, size_t len);

/* Status queries -- may be called from either context. */
bool   ring_buf_is_empty(const ring_buf_t *rb);
bool   ring_buf_is_full(const ring_buf_t *rb);
size_t ring_buf_count(const ring_buf_t *rb);       /* bytes in buffer      */
size_t ring_buf_free_space(const ring_buf_t *rb);  /* bytes that fit       */

/* ==========================================================================
 * Part 2: implementation   (source: isr_ring_buffer.c)
 * ========================================================================== */

#define RINGBUF_MIN(a, b) (((a) < (b)) ? (a) : (b))

void ring_buf_init(ring_buf_t *rb, uint8_t *storage, size_t size)
{
	rb->storage = storage;
	rb->size = size;
	atomic_set(&rb->head, 0);
	atomic_set(&rb->tail, 0);
}

bool ring_buf_write(ring_buf_t *rb, uint8_t data)
{
	uint32_t head = (uint32_t)atomic_get(&rb->head);
	uint32_t tail = (uint32_t)atomic_get(&rb->tail);

	/* Full once head has lapped tail by a whole capacity.
	 * Unsigned wraparound keeps the check correct indefinitely. */
	if ((head - tail) >= (uint32_t)rb->size) {
		return false; /* buffer full: drop the item */
	}

	/* Store the item, then publish the new head. The fence inside
	 * atomic_set() makes the data write globally visible before the
	 * index update, so the consumer can never see a head that points
	 * at unwritten data. */
	rb->storage[head % rb->size] = data;
	atomic_set(&rb->head, head + 1U);

	return true;
}

bool ring_buf_read(ring_buf_t *rb, uint8_t *data)
{
	uint32_t tail = (uint32_t)atomic_get(&rb->tail);
	uint32_t head = (uint32_t)atomic_get(&rb->head);

	if (head == tail) {
		return false; /* buffer empty */
	}

	/* head > tail (mod 2^32) implies the producer already wrote this
	 * slot, and the full condition prevents it rewriting the slot until
	 * tail advances, so no concurrent writer can touch it. */
	*data = rb->storage[tail % rb->size];

	/* The fence makes the data read complete before the new tail is
	 * published, so the producer cannot treat this slot as free until
	 * we are done with it. */
	atomic_set(&rb->tail, tail + 1U);

	return true;
}

size_t ring_buf_write_buf(ring_buf_t *rb, const uint8_t *data, size_t len)
{
	uint32_t head = (uint32_t)atomic_get(&rb->head);
	uint32_t tail = (uint32_t)atomic_get(&rb->tail);
	size_t free_space = rb->size - (size_t)(head - tail);
	size_t n = RINGBUF_MIN(len, free_space);
	size_t first_chunk = RINGBUF_MIN(n, rb->size - (head % rb->size));

	/* Copy in at most two contiguous chunks to handle the wrap. */
	if (n > 0U) {
		memcpy(&rb->storage[head % rb->size], data, first_chunk);
		if (n > first_chunk) {
			memcpy(&rb->storage[0], &data[first_chunk],
			       n - first_chunk);
		}
	}

	atomic_set(&rb->head, head + (uint32_t)n);
	return n;
}

size_t ring_buf_read_buf(ring_buf_t *rb, uint8_t *data, size_t len)
{
	uint32_t tail = (uint32_t)atomic_get(&rb->tail);
	uint32_t head = (uint32_t)atomic_get(&rb->head);
	size_t available = (size_t)(head - tail);
	size_t n = RINGBUF_MIN(len, available);
	size_t first_chunk = RINGBUF_MIN(n, rb->size - (tail % rb->size));

	if (n > 0U) {
		memcpy(data, &rb->storage[tail % rb->size], first_chunk);
		if (n > first_chunk) {
			memcpy(&data[first_chunk], &rb->storage[0],
			       n - first_chunk);
		}
	}

	atomic_set(&rb->tail, tail + (uint32_t)n);
	return n;
}

bool ring_buf_is_empty(const ring_buf_t *rb)
{
	return atomic_get(&rb->head) == atomic_get(&rb->tail);
}

bool ring_buf_is_full(const ring_buf_t *rb)
{
	uint32_t head = (uint32_t)atomic_get(&rb->head);
	uint32_t tail = (uint32_t)atomic_get(&rb->tail);

	return (head - tail) >= (uint32_t)rb->size;
}

size_t ring_buf_count(const ring_buf_t *rb)
{
	uint32_t head = (uint32_t)atomic_get(&rb->head);
	uint32_t tail = (uint32_t)atomic_get(&rb->tail);

	return (size_t)(head - tail);
}

size_t ring_buf_free_space(const ring_buf_t *rb)
{
	return rb->size - ring_buf_count(rb);
}

/* ==========================================================================
 * Part 3: demo -- ISR producer + thread consumer
 *
 * A k_timer expiry callback runs in ISR context, making it a realistic
 * stand-in for a hardware interrupt (e.g. a UART RX interrupt) feeding the
 * ring buffer. A dedicated Zephyr thread consumes it.
 *
 * The producer deliberately outpaces the consumer so the buffer fills up
 * and the full-buffer drop path is exercised; the empty path is exercised
 * at startup and whenever the consumer catches up.
 * ========================================================================== */

#define RING_SIZE         32u  /* buffer capacity in bytes       */
#define PRODUCE_PERIOD_MS 5u   /* 1 byte per ISR tick -> 200 B/s */
#define CONSUME_PERIOD_MS 50u  /* consumer wakeup period         */
#define CONSUME_BURST     8u   /* bytes per wakeup -> 160 B/s    */

static uint8_t ring_storage[RING_SIZE];
static ring_buf_t ring;

static atomic_t produced; /* bytes accepted by the ISR producer */
static atomic_t dropped;  /* bytes dropped because buffer was full */
static uint8_t seq;       /* item sequence number, ISR-owned    */

static struct k_timer producer_timer;

/* Runs in ISR context every PRODUCE_PERIOD_MS. */
static void producer_expiry(struct k_timer *timer)
{
	(void)timer;

	seq++;
	if (ring_buf_write(&ring, seq)) {
		atomic_inc(&produced);
	} else {
		/* Buffer full: this item is dropped. A real driver could
		 * retry later or apply a back-pressure policy here. */
		atomic_inc(&dropped);
	}
}

#define CONSUMER_STACK_SIZE 1024
static K_THREAD_STACK_DEFINE(consumer_stack, CONSUMER_STACK_SIZE);
static struct k_thread consumer_thread;
static uint8_t last_rx; /* thread-owned: last sequence consumed */

static void consumer_fn(void *arg1, void *arg2, void *arg3)
{
	(void)arg1;
	(void)arg2;
	(void)arg3;

	uint8_t chunk[CONSUME_BURST];
	unsigned long consumed = 0U;
	unsigned long cycles = 0U;

	while (true) {
		size_t n = ring_buf_read_buf(&ring, chunk, sizeof(chunk));

		if (n > 0U) {
			/* chunk[0] is the oldest pending item; with FIFO
			 * ordering it always carries the lowest sequence
			 * number not seen yet. */
			last_rx = chunk[0];
			consumed += n;
		}
		/* n == 0: buffer empty -- nothing to consume this cycle. */

		if ((++cycles % 5U) == 0U) { /* status line every 250 ms */
			printk("ring: %u/%u used | consumed=%lu dropped=%lu "
			       "last=%u\n",
			       (unsigned int)ring_buf_count(&ring),
			       RING_SIZE,
			       consumed,
			       (unsigned long)atomic_get(&dropped),
			       (unsigned int)last_rx);
		}

		k_msleep(CONSUME_PERIOD_MS);
	}
}

int main(void)
{
	ring_buf_init(&ring, ring_storage, sizeof(ring_storage));

	/* The k_timer expiry handler executes in ISR context. */
	k_timer_init(&producer_timer, NULL, producer_expiry);
	k_timer_start(&producer_timer, K_MSEC(1U), K_MSEC(PRODUCE_PERIOD_MS));

	k_thread_create(&consumer_thread, consumer_stack,
			K_THREAD_STACK_SIZEOF(consumer_stack),
			consumer_fn, NULL, NULL, NULL,
			K_PRIO_COOP(7), 0, K_NO_WAIT);

	printk("ISR-safe ring buffer demo: %u B buffer, producer in ISR "
	       "context, consumer in thread context\n",
	       (unsigned int)RING_SIZE);

	while (1) {
		k_sleep(K_SECONDS(1));
	}

	return 0;
}
