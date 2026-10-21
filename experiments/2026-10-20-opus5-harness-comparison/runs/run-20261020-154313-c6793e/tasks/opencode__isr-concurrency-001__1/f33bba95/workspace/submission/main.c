/**
 * ISR-Safe Ring Buffer Implementation for Zephyr RTOS
 * 
 * This implementation provides a lock-free ring buffer that allows:
 * - ISR context to produce (write) data
 * - Thread context to consume (read) data
 * - Atomic operations instead of mutexes
 * - Proper handling of buffer full and empty conditions
 * - FIFO ordering
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/barrier.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include <errno.h>

/* ========================================================================
 * RING BUFFER HEADER
 * ======================================================================== */

/**
 * Ring buffer structure
 * Uses atomic variables for head and tail to ensure thread-safety
 * between ISR (producer) and thread (consumer) contexts
 */
typedef struct {
    uint8_t *buffer;           /* Pointer to the data buffer */
    atomic_t head;             /* Write position (producer) */
    atomic_t tail;             /* Read position (consumer) */
    size_t size;               /* Total buffer size (must be power of 2) */
    size_t mask;               /* Size mask for efficient modulo */
} isr_ring_buffer_t;

/**
 * Initialize a ring buffer
 * 
 * @param rb Pointer to ring buffer structure
 * @param buffer Pointer to backing buffer array
 * @param size Size of buffer (must be power of 2)
 * @return 0 on success, negative error code on failure
 */
int isr_ring_buffer_init(isr_ring_buffer_t *rb, uint8_t *buffer, size_t size);

/**
 * Write data to ring buffer (typically called from ISR)
 * This is the producer function - safe to call from ISR context
 * 
 * @param rb Pointer to ring buffer structure
 * @param data Pointer to data to write
 * @param len Length of data to write
 * @return Number of bytes written, or negative error code
 */
int isr_ring_buffer_put(isr_ring_buffer_t *rb, const uint8_t *data, size_t len);

/**
 * Read data from ring buffer (typically called from thread)
 * This is the consumer function - safe to call from thread context
 * 
 * @param rb Pointer to ring buffer structure
 * @param data Pointer to buffer to read into
 * @param len Maximum length to read
 * @return Number of bytes read, or negative error code
 */
int isr_ring_buffer_get(isr_ring_buffer_t *rb, uint8_t *data, size_t len);

/**
 * Get number of bytes available to read
 * 
 * @param rb Pointer to ring buffer structure
 * @return Number of bytes available
 */
size_t isr_ring_buffer_available(isr_ring_buffer_t *rb);

/**
 * Get free space in buffer
 * 
 * @param rb Pointer to ring buffer structure
 * @return Number of bytes free
 */
size_t isr_ring_buffer_space(isr_ring_buffer_t *rb);

/**
 * Check if buffer is empty
 * 
 * @param rb Pointer to ring buffer structure
 * @return true if empty, false otherwise
 */
bool isr_ring_buffer_is_empty(isr_ring_buffer_t *rb);

/**
 * Check if buffer is full
 * 
 * @param rb Pointer to ring buffer structure
 * @return true if full, false otherwise
 */
bool isr_ring_buffer_is_full(isr_ring_buffer_t *rb);

/**
 * Reset/clear the ring buffer
 * Note: Should only be called when producer and consumer are not active
 * 
 * @param rb Pointer to ring buffer structure
 */
void isr_ring_buffer_reset(isr_ring_buffer_t *rb);

/* ========================================================================
 * RING BUFFER IMPLEMENTATION
 * ======================================================================== */

/**
 * Check if a number is a power of 2
 */
static inline bool is_power_of_2(size_t n)
{
    return (n != 0) && ((n & (n - 1)) == 0);
}

int isr_ring_buffer_init(isr_ring_buffer_t *rb, uint8_t *buffer, size_t size)
{
    if (rb == NULL || buffer == NULL || size == 0) {
        return -EINVAL;
    }
    
    /* Size must be power of 2 for efficient modulo operation */
    if (!is_power_of_2(size)) {
        return -EINVAL;
    }
    
    rb->buffer = buffer;
    rb->size = size;
    rb->mask = size - 1;
    atomic_set(&rb->head, 0);
    atomic_set(&rb->tail, 0);
    
    return 0;
}

size_t isr_ring_buffer_available(isr_ring_buffer_t *rb)
{
    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);
    
    /* Calculate available data using unsigned arithmetic
     * This handles wrap-around correctly */
    return (head - tail);
}

size_t isr_ring_buffer_space(isr_ring_buffer_t *rb)
{
    /* We keep one slot empty to distinguish full from empty
     * So available space is size - available - 1 */
    return rb->size - isr_ring_buffer_available(rb) - 1;
}

bool isr_ring_buffer_is_empty(isr_ring_buffer_t *rb)
{
    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);
    
    return (head == tail);
}

bool isr_ring_buffer_is_full(isr_ring_buffer_t *rb)
{
    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);
    
    /* Full when head + 1 == tail (keeping one slot empty) */
    return ((head - tail) >= (rb->size - 1));
}

void isr_ring_buffer_reset(isr_ring_buffer_t *rb)
{
    atomic_set(&rb->head, 0);
    atomic_set(&rb->tail, 0);
}

int isr_ring_buffer_put(isr_ring_buffer_t *rb, const uint8_t *data, size_t len)
{
    if (rb == NULL || data == NULL || len == 0) {
        return -EINVAL;
    }
    
    /* Get current head and tail positions
     * We read these atomically to ensure consistency */
    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);
    
    /* Calculate available space
     * We keep one slot empty to distinguish full from empty */
    size_t available_space = rb->size - (head - tail) - 1;
    
    /* Limit write to available space */
    if (len > available_space) {
        len = available_space;
    }
    
    if (len == 0) {
        return 0; /* Buffer full */
    }
    
    /* Write data in two parts if it wraps around */
    uint32_t head_idx = head & rb->mask;
    size_t first_part = len;
    size_t second_part = 0;
    
    /* Check if write wraps around */
    if (head_idx + len > rb->size) {
        first_part = rb->size - head_idx;
        second_part = len - first_part;
    }
    
    /* Copy first part */
    memcpy(&rb->buffer[head_idx], data, first_part);
    
    /* Copy second part if wrapping */
    if (second_part > 0) {
        memcpy(&rb->buffer[0], data + first_part, second_part);
    }
    
    /* Memory barrier to ensure all writes complete before updating head */
    barrier_dmem_fence_full();
    
    /* Update head atomically
     * This must be done AFTER data is written to ensure consumer
     * doesn't read incomplete data */
    atomic_set(&rb->head, head + len);
    
    return (int)len;
}

int isr_ring_buffer_get(isr_ring_buffer_t *rb, uint8_t *data, size_t len)
{
    if (rb == NULL || data == NULL || len == 0) {
        return -EINVAL;
    }
    
    /* Get current head and tail positions */
    uint32_t head = atomic_get(&rb->head);
    uint32_t tail = atomic_get(&rb->tail);
    
    /* Memory barrier to ensure we see all data written before head was updated */
    barrier_dmem_fence_full();
    
    /* Calculate available data */
    size_t available_data = head - tail;
    
    /* Limit read to available data */
    if (len > available_data) {
        len = available_data;
    }
    
    if (len == 0) {
        return 0; /* Buffer empty */
    }
    
    /* Read data in two parts if it wraps around */
    uint32_t tail_idx = tail & rb->mask;
    size_t first_part = len;
    size_t second_part = 0;
    
    /* Check if read wraps around */
    if (tail_idx + len > rb->size) {
        first_part = rb->size - tail_idx;
        second_part = len - first_part;
    }
    
    /* Copy first part */
    memcpy(data, &rb->buffer[tail_idx], first_part);
    
    /* Copy second part if wrapping */
    if (second_part > 0) {
        memcpy(data + first_part, &rb->buffer[0], second_part);
    }
    
    /* Memory barrier to ensure reads complete before freeing the space */
    barrier_dmem_fence_full();
    
    /* Update tail atomically
     * This must be done AFTER data is read to ensure producer
     * doesn't overwrite data we're still reading */
    atomic_set(&rb->tail, tail + len);
    
    return (int)len;
}

/* ========================================================================
 * EXAMPLE USAGE AND TEST CODE
 * ======================================================================== */

#define RING_BUFFER_SIZE 256

/* Static buffer and ring buffer instance */
static uint8_t ring_buffer_data[RING_BUFFER_SIZE];
static isr_ring_buffer_t my_ring_buffer;

/**
 * Simulated ISR that writes data to the ring buffer
 * In a real application, this would be an actual ISR handler
 */
void simulated_isr_handler(void)
{
    static uint8_t counter = 0;
    uint8_t data[4];
    
    /* Prepare some data */
    for (int i = 0; i < 4; i++) {
        data[i] = counter++;
    }
    
    /* Write to ring buffer (ISR context) */
    int written = isr_ring_buffer_put(&my_ring_buffer, data, sizeof(data));
    
    /* Compare as signed int: a negative return is an error, not a short write */
    if (written < (int)sizeof(data)) {
        /* Buffer full or partial write - handle as needed */
        printk("ISR: Only wrote %d bytes (buffer full)\n", written);
    }
}

/**
 * Thread function that reads data from the ring buffer
 */
void consumer_thread(void)
{
    uint8_t read_buffer[64];
    
    while (1) {
        /* Check if data is available */
        if (!isr_ring_buffer_is_empty(&my_ring_buffer)) {
            /* Read available data */
            int bytes_read = isr_ring_buffer_get(&my_ring_buffer, 
                                                  read_buffer, 
                                                  sizeof(read_buffer));
            
            if (bytes_read > 0) {
                printk("Thread: Read %d bytes: ", bytes_read);
                for (int i = 0; i < bytes_read && i < 16; i++) {
                    printk("%02x ", read_buffer[i]);
                }
                printk("\n");
            }
        }
        
        /* Sleep to simulate processing */
        k_msleep(100);
    }
}

/**
 * Main function - demonstrates usage
 */
int main(void)
{
    int ret;
    
    printk("ISR-Safe Ring Buffer Demo for Zephyr RTOS\n");
    printk("=========================================\n\n");
    
    /* Initialize the ring buffer */
    ret = isr_ring_buffer_init(&my_ring_buffer, 
                                ring_buffer_data, 
                                RING_BUFFER_SIZE);
    
    if (ret != 0) {
        printk("Failed to initialize ring buffer: %d\n", ret);
        return ret;
    }
    
    printk("Ring buffer initialized (size: %d bytes)\n", RING_BUFFER_SIZE);
    printk("Available space: %zu bytes\n", 
           isr_ring_buffer_space(&my_ring_buffer));
    printk("\n");
    
    /* Simulate ISR writing data */
    printk("Simulating ISR writes...\n");
    for (int i = 0; i < 5; i++) {
        simulated_isr_handler();
    }
    
    printk("Available data: %zu bytes\n", 
           isr_ring_buffer_available(&my_ring_buffer));
    printk("Available space: %zu bytes\n", 
           isr_ring_buffer_space(&my_ring_buffer));
    printk("\n");
    
    /* Read some data in thread context */
    printk("Reading data in thread context...\n");
    uint8_t test_buffer[10];
    int bytes_read = isr_ring_buffer_get(&my_ring_buffer, 
                                          test_buffer, 
                                          sizeof(test_buffer));
    
    printk("Read %d bytes: ", bytes_read);
    for (int i = 0; i < bytes_read; i++) {
        printk("%02x ", test_buffer[i]);
    }
    printk("\n\n");
    
    printk("Available data: %zu bytes\n", 
           isr_ring_buffer_available(&my_ring_buffer));
    printk("Available space: %zu bytes\n", 
           isr_ring_buffer_space(&my_ring_buffer));
    printk("\n");
    
    /* Test buffer full condition */
    printk("Testing buffer full condition...\n");
    uint8_t fill_data[RING_BUFFER_SIZE];
    for (int i = 0; i < RING_BUFFER_SIZE; i++) {
        fill_data[i] = i & 0xFF;
    }
    
    int written = isr_ring_buffer_put(&my_ring_buffer, 
                                       fill_data, 
                                       RING_BUFFER_SIZE);
    printk("Wrote %d bytes\n", written);
    printk("Is full: %s\n", isr_ring_buffer_is_full(&my_ring_buffer) ? "yes" : "no");
    printk("Available space: %zu bytes\n", 
           isr_ring_buffer_space(&my_ring_buffer));
    printk("\n");
    
    /* Try to write when full */
    printk("Attempting to write when buffer is full...\n");
    uint8_t more_data[10] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x11, 0x22, 0x33, 0x44};
    written = isr_ring_buffer_put(&my_ring_buffer, more_data, sizeof(more_data));
    printk("Wrote %d bytes (expected 0)\n", written);
    printk("\n");
    
    /* Clear buffer and test empty condition */
    printk("Clearing buffer...\n");
    isr_ring_buffer_reset(&my_ring_buffer);
    printk("Is empty: %s\n", isr_ring_buffer_is_empty(&my_ring_buffer) ? "yes" : "no");
    printk("Available space: %zu bytes\n", 
           isr_ring_buffer_space(&my_ring_buffer));
    printk("\n");
    
    printk("Demo complete!\n");
    
    return 0;
}
