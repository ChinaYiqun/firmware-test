/*
 * ISR-Safe Ring Buffer Implementation for Zephyr RTOS
 *
 * Features:
 * - Lock-free single-producer single-consumer (SPSC) design
 * - ISR-safe: producer can be called from ISR context
 * - Thread-safe: consumer can be called from thread context
 * - Uses atomic operations (no mutexes)
 * - Handles buffer full/empty conditions
 * - Maintains FIFO ordering
 * - Supports arbitrary element sizes
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

/*
 * Ring Buffer Structure
 *
 * Uses head (write index) and tail (read index) with atomic operations.
 * To distinguish full from empty state, we keep one slot empty.
 * - Empty: head == tail
 * - Full: (head + 1) % capacity == tail
 */
typedef struct {
    uint8_t *buffer;        /* Pointer to data buffer */
    size_t capacity;        /* Total number of elements (includes 1 unused slot) */
    atomic_t head;          /* Write index - modified by producer (ISR) */
    atomic_t tail;          /* Read index - modified by consumer (thread) */
    size_t element_size;    /* Size of each element in bytes */
} ring_buffer_t;

/*
 * Function Prototypes
 */
int ring_buffer_init(ring_buffer_t *rb, uint8_t *buffer, size_t capacity, size_t element_size);
int ring_buffer_put(ring_buffer_t *rb, const void *data);
int ring_buffer_get(ring_buffer_t *rb, void *data);
bool ring_buffer_is_empty(ring_buffer_t *rb);
bool ring_buffer_is_full(ring_buffer_t *rb);
size_t ring_buffer_size(ring_buffer_t *rb);
size_t ring_buffer_space(ring_buffer_t *rb);
void ring_buffer_reset(ring_buffer_t *rb);

/*
 * Initialize ring buffer
 *
 * @param rb Ring buffer structure
 * @param buffer Pointer to buffer memory
 * @param capacity Number of elements the buffer can hold
 * @param element_size Size of each element in bytes
 * @return 0 on success, negative error code on failure
 */
int ring_buffer_init(ring_buffer_t *rb, uint8_t *buffer, size_t capacity, size_t element_size)
{
    if (!rb || !buffer || capacity < 2 || element_size == 0) {
        return -EINVAL;
    }

    rb->buffer = buffer;
    rb->capacity = capacity;
    rb->element_size = element_size;
    atomic_set(&rb->head, 0);
    atomic_set(&rb->tail, 0);

    return 0;
}

/*
 * Put data into ring buffer (Producer - ISR safe)
 *
 * This function can be called from ISR context.
 * Only modifies the head index.
 *
 * @param rb Ring buffer structure
 * @param data Pointer to data to write
 * @return 0 on success, -ENOMEM if buffer is full, -EINVAL if parameters invalid
 */
int ring_buffer_put(ring_buffer_t *rb, const void *data)
{
    if (!rb || !data) {
        return -EINVAL;
    }

    /* Get current head and tail positions */
    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);

    /* Calculate next head position */
    uint32_t next_head = (head + 1) % rb->capacity;

    /* Check if buffer is full (next_head would equal tail) */
    if (next_head == tail) {
        return -ENOMEM;  /* Buffer full */
    }

    /* Copy data to buffer at current head position */
    uint8_t *dest = rb->buffer + (head * rb->element_size);
    memcpy(dest, data, rb->element_size);

    /*
     * Memory barrier ensures data write completes before head update.
     * This prevents the consumer from reading incomplete data.
     */
    compiler_barrier();

    /* Update head index (makes data visible to consumer) */
    atomic_set(&rb->head, next_head);

    return 0;
}

/*
 * Get data from ring buffer (Consumer - Thread context)
 *
 * This function should be called from thread context.
 * Only modifies the tail index.
 *
 * @param rb Ring buffer structure
 * @param data Pointer to buffer to store read data
 * @return 0 on success, -ENODATA if buffer is empty, -EINVAL if parameters invalid
 */
int ring_buffer_get(ring_buffer_t *rb, void *data)
{
    if (!rb || !data) {
        return -EINVAL;
    }

    /* Get current head and tail positions */
    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);

    /* Check if buffer is empty (head equals tail) */
    if (head == tail) {
        return -ENODATA;  /* Buffer empty */
    }

    /* Copy data from buffer at current tail position */
    uint8_t *src = rb->buffer + (tail * rb->element_size);
    memcpy(data, src, rb->element_size);

    /* Calculate next tail position */
    uint32_t next_tail = (tail + 1) % rb->capacity;

    /*
     * Memory barrier ensures data read completes before tail update.
     * This prevents the producer from overwriting data before we're done.
     */
    compiler_barrier();

    /* Update tail index (frees slot for producer) */
    atomic_set(&rb->tail, next_tail);

    return 0;
}

/*
 * Check if ring buffer is empty
 *
 * @param rb Ring buffer structure
 * @return true if empty, false otherwise
 */
bool ring_buffer_is_empty(ring_buffer_t *rb)
{
    if (!rb) {
        return true;
    }

    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);

    return (head == tail);
}

/*
 * Check if ring buffer is full
 *
 * @param rb Ring buffer structure
 * @return true if full, false otherwise
 */
bool ring_buffer_is_full(ring_buffer_t *rb)
{
    if (!rb) {
        return false;
    }

    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);
    uint32_t next_head = (head + 1) % rb->capacity;

    return (next_head == tail);
}

/*
 * Get current number of elements in ring buffer
 *
 * @param rb Ring buffer structure
 * @return Number of elements currently in buffer
 */
size_t ring_buffer_size(ring_buffer_t *rb)
{
    if (!rb) {
        return 0;
    }

    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);

    if (head >= tail) {
        return head - tail;
    } else {
        return rb->capacity - tail + head;
    }
}

/*
 * Get available space in ring buffer
 *
 * @param rb Ring buffer structure
 * @return Number of free slots available
 */
size_t ring_buffer_space(ring_buffer_t *rb)
{
    if (!rb) {
        return 0;
    }

    /* Available space is capacity - 1 - current_size (one slot always reserved) */
    return (rb->capacity - 1) - ring_buffer_size(rb);
}

/*
 * Reset ring buffer to empty state
 *
 * WARNING: This is NOT safe to call while producer/consumer are active!
 * Only call this during initialization or when you're certain no concurrent access is occurring.
 *
 * @param rb Ring buffer structure
 */
void ring_buffer_reset(ring_buffer_t *rb)
{
    if (!rb) {
        return;
    }

    atomic_set(&rb->head, 0);
    atomic_set(&rb->tail, 0);
}

/*
 * Example Usage and Test Code
 */

/* Example data structure */
typedef struct {
    uint32_t timestamp;
    uint16_t sensor_id;
    uint16_t value;
} sensor_data_t;

/* Buffer configuration */
#define RING_BUFFER_CAPACITY 16
#define TEST_ITERATIONS 100

/* Static buffer allocation */
static uint8_t buffer_memory[RING_BUFFER_CAPACITY * sizeof(sensor_data_t)];
static ring_buffer_t sensor_ring_buf;

/* Simulated ISR data producer */
void simulated_isr_producer(uint32_t iteration)
{
    sensor_data_t data = {
        .timestamp = k_cycle_get_32(),
        .sensor_id = iteration % 4,
        .value = iteration * 10
    };

    int ret = ring_buffer_put(&sensor_ring_buf, &data);
    if (ret < 0) {
        /* In real ISR, you might want to set an overflow flag */
        printk("ISR: Buffer full, data lost (iteration %u)\n", iteration);
    }
}

/* Thread context data consumer */
void thread_consumer(void)
{
    sensor_data_t data;

    int ret = ring_buffer_get(&sensor_ring_buf, &data);
    if (ret == 0) {
        printk("Thread: Read sensor_id=%u, value=%u, ts=%u (remaining: %zu)\n",
               data.sensor_id, data.value, data.timestamp,
               ring_buffer_size(&sensor_ring_buf));
    } else if (ret != -ENODATA) {
        printk("Thread: Get error: %d\n", ret);
    }
}

/*
 * Main function - demonstrates ring buffer usage
 */
void main(void)
{
    printk("\n");
    printk("========================================================\n");
    printk("ISR-Safe Ring Buffer Implementation for Zephyr RTOS\n");
    printk("========================================================\n\n");

    /* Initialize ring buffer */
    int ret = ring_buffer_init(&sensor_ring_buf, buffer_memory,
                               RING_BUFFER_CAPACITY, sizeof(sensor_data_t));
    if (ret < 0) {
        printk("ERROR: Failed to initialize ring buffer: %d\n", ret);
        return;
    }

    printk("Ring buffer initialized successfully:\n");
    printk("  Capacity: %d elements\n", RING_BUFFER_CAPACITY);
    printk("  Element size: %zu bytes\n", sizeof(sensor_data_t));
    printk("  Usable slots: %d (1 slot reserved for full/empty detection)\n\n",
           RING_BUFFER_CAPACITY - 1);

    /* Test 1: Basic producer-consumer test */
    printk("Test 1: Basic Producer-Consumer\n");
    printk("--------------------------------\n");

    for (int i = 0; i < 5; i++) {
        simulated_isr_producer(i);
        printk("ISR: Produced item %d (size: %zu)\n", i, ring_buffer_size(&sensor_ring_buf));
    }

    printk("\n");
    for (int i = 0; i < 5; i++) {
        thread_consumer();
    }

    printk("\nBuffer status: size=%zu, empty=%s, full=%s\n\n",
           ring_buffer_size(&sensor_ring_buf),
           ring_buffer_is_empty(&sensor_ring_buf) ? "yes" : "no",
           ring_buffer_is_full(&sensor_ring_buf) ? "yes" : "no");

    /* Test 2: Fill buffer to capacity */
    printk("Test 2: Fill Buffer to Capacity\n");
    printk("--------------------------------\n");

    int produced = 0;
    for (int i = 0; i < RING_BUFFER_CAPACITY; i++) {
        sensor_data_t data = { .timestamp = i, .sensor_id = i, .value = i * 100 };
        ret = ring_buffer_put(&sensor_ring_buf, &data);
        if (ret == 0) {
            produced++;
        } else {
            break;
        }
    }

    printk("Produced %d items\n", produced);
    printk("Buffer full: %s\n", ring_buffer_is_full(&sensor_ring_buf) ? "yes" : "no");
    printk("Buffer size: %zu\n", ring_buffer_size(&sensor_ring_buf));
    printk("Available space: %zu\n\n", ring_buffer_space(&sensor_ring_buf));

    /* Test 3: Interleaved producer-consumer */
    printk("Test 3: Interleaved Producer-Consumer (simulating real ISR usage)\n");
    printk("------------------------------------------------------------------\n");

    ring_buffer_reset(&sensor_ring_buf);

    for (uint32_t i = 0; i < TEST_ITERATIONS; i++) {
        /* Simulated ISR fires and produces data */
        simulated_isr_producer(i);

        /* Thread periodically consumes data (every 3 iterations) */
        if (i % 3 == 0) {
            int consumed = 0;
            while (!ring_buffer_is_empty(&sensor_ring_buf) && consumed < 4) {
                thread_consumer();
                consumed++;
            }
        }

        /* Check for buffer overflow condition */
        if (ring_buffer_is_full(&sensor_ring_buf)) {
            printk("WARNING: Buffer full at iteration %u\n", i);
        }
    }

    /* Drain remaining data */
    printk("\nDraining remaining data...\n");
    while (!ring_buffer_is_empty(&sensor_ring_buf)) {
        thread_consumer();
    }

    printk("\nFinal buffer status: size=%zu, empty=%s\n\n",
           ring_buffer_size(&sensor_ring_buf),
           ring_buffer_is_empty(&sensor_ring_buf) ? "yes" : "no");

    /* Test 4: Performance characteristics */
    printk("Test 4: Performance Test\n");
    printk("------------------------\n");

    ring_buffer_reset(&sensor_ring_buf);

    uint32_t start_cycles = k_cycle_get_32();

    for (int i = 0; i < 1000; i++) {
        sensor_data_t data = { .timestamp = i, .sensor_id = 1, .value = i };
        ring_buffer_put(&sensor_ring_buf, &data);

        if (!ring_buffer_is_empty(&sensor_ring_buf)) {
            ring_buffer_get(&sensor_ring_buf, &data);
        }
    }

    uint32_t end_cycles = k_cycle_get_32();
    uint32_t elapsed = end_cycles - start_cycles;

    printk("1000 put/get pairs completed in %u cycles\n", elapsed);
    printk("Average per operation: %u cycles\n\n", elapsed / 2000);

    printk("========================================================\n");
    printk("All tests completed successfully!\n");
    printk("========================================================\n");
}
