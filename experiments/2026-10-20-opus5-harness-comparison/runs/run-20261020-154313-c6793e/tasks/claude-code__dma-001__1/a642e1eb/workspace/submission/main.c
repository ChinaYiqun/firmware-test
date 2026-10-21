/*
 * Zephyr RTOS DMA Memory Transfer Application
 * Copies a 64-byte buffer using DMA
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/dma.h>
#include <zephyr/sys/printk.h>
#include <string.h>

/* Get DMA device from devicetree */
#define DMA_DEVICE_NODE DT_NODELABEL(dma0)
#define DMA_CHANNEL 0

/* Buffer size */
#define BUFFER_SIZE 64

/* Timeout for DMA completion (in milliseconds) */
#define DMA_TIMEOUT_MS 1000

/* Buffers for DMA transfer */
static uint8_t source_buffer[BUFFER_SIZE] __aligned(32);
static uint8_t dest_buffer[BUFFER_SIZE] __aligned(32);

/* Semaphore for signaling DMA completion */
static K_SEM_DEFINE(dma_sem, 0, 1);

/* Transfer status */
static volatile int transfer_status = 0;

/**
 * DMA callback function
 * Called when DMA transfer completes or encounters an error
 */
static void dma_callback(const struct device *dev, void *user_data,
			 uint32_t channel, int status)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);
	ARG_UNUSED(channel);

	transfer_status = status;
	k_sem_give(&dma_sem);
}

/**
 * Initialize source buffer with a known pattern
 * and destination buffer with zeros
 */
static void init_buffers(void)
{
	/* Fill source buffer with incrementing pattern */
	for (int i = 0; i < BUFFER_SIZE; i++) {
		source_buffer[i] = (uint8_t)i;
	}

	/* Fill destination buffer with zeros */
	memset(dest_buffer, 0, BUFFER_SIZE);
}

/**
 * Verify that destination buffer matches source buffer
 */
static bool verify_transfer(void)
{
	return (memcmp(source_buffer, dest_buffer, BUFFER_SIZE) == 0);
}

/**
 * Main application entry point
 */
int main(void)
{
	const struct device *dma_dev;
	struct dma_config dma_cfg = {0};
	struct dma_block_config block_cfg = {0};
	int ret;

	printk("Zephyr DMA Memory Transfer Application\n");
	printk("========================================\n\n");

	/* Step 1: Obtain the DMA controller from devicetree */
	dma_dev = DEVICE_DT_GET(DMA_DEVICE_NODE);
	if (dma_dev == NULL) {
		printk("ERROR: Failed to get DMA device\n");
		return -1;
	}

	/* Step 2: Check that the device is ready */
	if (!device_is_ready(dma_dev)) {
		printk("ERROR: DMA device is not ready\n");
		return -1;
	}
	printk("DMA device ready\n");

	/* Step 3: Initialize buffers */
	init_buffers();
	printk("Buffers initialized:\n");
	printk("  Source buffer: pattern 0x00-0x3F\n");
	printk("  Destination buffer: all zeros\n\n");

	/* Step 4: Configure DMA for memory-to-memory transfer */

	/* Configure the DMA block */
	block_cfg.block_size = BUFFER_SIZE;
	block_cfg.source_address = (uint32_t)source_buffer;
	block_cfg.dest_address = (uint32_t)dest_buffer;

	/* Configure DMA transfer settings */
	dma_cfg.channel_direction = MEMORY_TO_MEMORY;
	dma_cfg.source_data_size = 1;  /* 1 byte */
	dma_cfg.dest_data_size = 1;    /* 1 byte */
	dma_cfg.source_burst_length = 1;
	dma_cfg.dest_burst_length = 1;
	dma_cfg.dma_callback = dma_callback;
	dma_cfg.complete_callback_en = 1;
	dma_cfg.error_callback_en = 1;
	dma_cfg.block_count = 1;
	dma_cfg.head_block = &block_cfg;
	dma_cfg.user_data = NULL;

	/* Configure the DMA channel */
	ret = dma_config(dma_dev, DMA_CHANNEL, &dma_cfg);
	if (ret != 0) {
		printk("ERROR: Failed to configure DMA (error %d)\n", ret);
		return -1;
	}
	printk("DMA channel %d configured\n", DMA_CHANNEL);

	/* Reset transfer status */
	transfer_status = 0;

	/* Start the DMA transfer */
	ret = dma_start(dma_dev, DMA_CHANNEL);
	if (ret != 0) {
		printk("ERROR: Failed to start DMA transfer (error %d)\n", ret);
		return -1;
	}
	printk("DMA transfer started\n");

	/* Step 6: Wait for completion with timeout */
	ret = k_sem_take(&dma_sem, K_MSEC(DMA_TIMEOUT_MS));
	if (ret != 0) {
		printk("ERROR: DMA transfer timeout\n");
		dma_stop(dma_dev, DMA_CHANNEL);
		return -1;
	}

	/* Check transfer status from callback */
	if (transfer_status != 0) {
		printk("ERROR: DMA transfer failed with status %d\n", transfer_status);
		return -1;
	}

	printk("DMA transfer completed\n\n");

	/* Step 7: Verify that destination matches source */
	if (verify_transfer()) {
		printk("SUCCESS: Transfer verification passed!\n");
		printk("Destination buffer matches source buffer\n");
		return 0;
	} else {
		printk("FAILURE: Transfer verification failed!\n");
		printk("Destination buffer does not match source buffer\n");
		return -1;
	}
}
