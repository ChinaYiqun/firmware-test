/*
 * Zephyr RTOS DMA Memory-to-Memory Transfer Application
 *
 * Copies a 64-byte source buffer to a 64-byte destination buffer using
 * a DMA controller obtained from the devicetree (node label: dma0).
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/dma.h>
#include <zephyr/sys/printk.h>
#include <string.h>

#define BUFFER_SIZE     64
#define DMA_TIMEOUT_MS  1000
#define DMA_CHANNEL     0

/* DMA buffers. Aligned to 32 bytes so they are safe for controllers that
 * require alignment and for cache maintenance on cached platforms.
 */
static uint8_t source_buffer[BUFFER_SIZE] __aligned(32);
static uint8_t dest_buffer[BUFFER_SIZE] __aligned(32);

/* Signals completion of the DMA transfer from the callback context. */
static K_SEM_DEFINE(dma_done_sem, 0, 1);

/* Status reported by the DMA driver in the callback. */
static volatile int dma_status;

/*
 * DMA completion callback. Runs in interrupt context, so it only records
 * the status and wakes the waiting thread.
 */
static void dma_callback(const struct device *dev, void *user_data,
			 uint32_t channel, int status)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);
	ARG_UNUSED(channel);

	dma_status = status;
	k_sem_give(&dma_done_sem);
}

/* Fill the source buffer with a known pattern and zero the destination. */
static void init_buffers(void)
{
	for (size_t i = 0; i < BUFFER_SIZE; i++) {
		/* Incrementing pattern XORed with a constant so that a
		 * partially-copied buffer is easy to spot.
		 */
		source_buffer[i] = (uint8_t)(i ^ 0xA5);
	}

	memset(dest_buffer, 0, BUFFER_SIZE);
}

/* Return the index of the first mismatching byte, or -1 if buffers match. */
static int find_mismatch(void)
{
	for (size_t i = 0; i < BUFFER_SIZE; i++) {
		if (dest_buffer[i] != source_buffer[i]) {
			return (int)i;
		}
	}

	return -1;
}

int main(void)
{
	const struct device *dma_dev;
	struct dma_block_config block_cfg = { 0 };
	struct dma_config cfg = { 0 };
	int mismatch;
	int ret;

	printk("Zephyr DMA memory-to-memory transfer (%d bytes)\n", BUFFER_SIZE);

	/* 1. Obtain the DMA controller from the devicetree. */
	dma_dev = DEVICE_DT_GET(DT_NODELABEL(dma0));

	/* 2. Make sure the device exists and is initialized. */
	if (!device_is_ready(dma_dev)) {
		printk("ERROR: DMA device dma0 is not ready\n");
		printk("DMA transfer FAILED\n");
		return -ENODEV;
	}
	printk("Using DMA controller: %s\n", dma_dev->name);

	/* 3. Prepare the buffers. */
	init_buffers();

	/* 4. Describe the transfer: one block, whole buffer, mem-to-mem. */
	block_cfg.source_address = (uint32_t)(uintptr_t)source_buffer;
	block_cfg.dest_address = (uint32_t)(uintptr_t)dest_buffer;
	block_cfg.block_size = BUFFER_SIZE;
	block_cfg.source_addr_adj = DMA_ADDR_ADJ_INCREMENT;
	block_cfg.dest_addr_adj = DMA_ADDR_ADJ_INCREMENT;
	block_cfg.next_block = NULL;

	cfg.channel_direction = MEMORY_TO_MEMORY;
	cfg.complete_callback_en = 0;   /* callback only on whole transfer */
	cfg.error_callback_dis = 0;     /* also notify on errors */
	cfg.source_handshake = 1;       /* software triggered */
	cfg.dest_handshake = 1;
	cfg.source_data_size = 1;
	cfg.dest_data_size = 1;
	cfg.source_burst_length = 1;
	cfg.dest_burst_length = 1;
	cfg.block_count = 1;
	cfg.head_block = &block_cfg;

	/* 5. Signal completion through the callback. */
	cfg.dma_callback = dma_callback;
	cfg.user_data = NULL;

	ret = dma_config(dma_dev, DMA_CHANNEL, &cfg);
	if (ret != 0) {
		printk("ERROR: dma_config() on channel %d failed (%d)\n",
		       DMA_CHANNEL, ret);
		printk("DMA transfer FAILED\n");
		return ret;
	}

	ret = dma_start(dma_dev, DMA_CHANNEL);
	if (ret != 0) {
		printk("ERROR: dma_start() on channel %d failed (%d)\n",
		       DMA_CHANNEL, ret);
		printk("DMA transfer FAILED\n");
		return ret;
	}

	/* 6. Wait for the callback, bounded by a timeout. */
	ret = k_sem_take(&dma_done_sem, K_MSEC(DMA_TIMEOUT_MS));
	if (ret != 0) {
		printk("ERROR: DMA transfer timed out after %d ms\n",
		       DMA_TIMEOUT_MS);
		(void)dma_stop(dma_dev, DMA_CHANNEL);
		printk("DMA transfer FAILED\n");
		return -ETIMEDOUT;
	}

	if (dma_status < 0) {
		printk("ERROR: DMA transfer reported error status %d\n",
		       dma_status);
		(void)dma_stop(dma_dev, DMA_CHANNEL);
		printk("DMA transfer FAILED\n");
		return dma_status;
	}

	/* 7. Verify the destination against the source. */
	mismatch = find_mismatch();
	if (mismatch >= 0) {
		printk("ERROR: data mismatch at byte %d "
		       "(expected 0x%02x, got 0x%02x)\n",
		       mismatch, source_buffer[mismatch], dest_buffer[mismatch]);
		printk("DMA transfer FAILED\n");
		return -EIO;
	}

	/* 8. Report the result. */
	printk("Verified %d bytes, destination matches source\n", BUFFER_SIZE);
	printk("DMA transfer SUCCEEDED\n");

	return 0;
}
