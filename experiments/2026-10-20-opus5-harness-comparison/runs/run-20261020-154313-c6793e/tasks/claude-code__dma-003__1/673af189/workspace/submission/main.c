/*
 * Continuous DMA data collection using circular (ping-pong) buffering.
 *
 * Two equally sized buffers alternate as the DMA destination. The DMA
 * completion callback immediately reloads the controller onto the other
 * buffer, so capture continues without a gap while the main thread
 * processes the buffer that was just filled.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/dma.h>
#include <zephyr/sys/printk.h>

#define DMA_NODE     DT_NODELABEL(dma0)
#define DMA_CHANNEL  0
#define BUF_SIZE     32
#define XFERS_WANTED 4

/* Ping-pong destinations. DMA engines commonly require aligned buffers. */
static uint8_t buf_a[BUF_SIZE] __aligned(32);
static uint8_t buf_b[BUF_SIZE] __aligned(32);

/*
 * Stand-in for the capture source. With a real peripheral this would be the
 * peripheral's data register and the transfer direction would be
 * PERIPHERAL_TO_MEMORY with a hardware request line in dma_slot.
 */
static uint8_t src_buf[BUF_SIZE] __aligned(32);

/* Index of the buffer the DMA is currently writing into: 0 = A, 1 = B. */
static volatile uint8_t active_buf;

/* Buffer that has just been filled and is safe for the main thread to read. */
static uint8_t *volatile ready_buf;

static volatile uint32_t completed_xfers;
static volatile int dma_error;

/* Signals the main thread that one buffer has been filled. */
static K_SEM_DEFINE(xfer_done, 0, 1);

static const struct device *const dma_dev = DEVICE_DT_GET(DMA_NODE);

static uint8_t *buf_at(uint8_t idx)
{
	return (idx == 0) ? buf_a : buf_b;
}

static void dma_callback(const struct device *dev, void *user_data,
			 uint32_t channel, int status)
{
	ARG_UNUSED(user_data);

	if (status < 0) {
		dma_error = status;
		k_sem_give(&xfer_done);
		return;
	}

	/* The buffer that was active is now complete. */
	ready_buf = buf_at(active_buf);
	completed_xfers++;

	/* Flip to the other buffer and restart: this is the circular part. */
	active_buf ^= 1U;

	status = dma_reload(dev, channel, (uint32_t)(uintptr_t)src_buf,
			    (uint32_t)(uintptr_t)buf_at(active_buf), BUF_SIZE);
	if (status == 0) {
		status = dma_start(dev, channel);
	}

	if (status < 0) {
		dma_error = status;
	}

	k_sem_give(&xfer_done);
}

int main(void)
{
	struct dma_config cfg = {0};
	struct dma_block_config blk = {0};
	int ret;

	printk("DMA ping-pong circular buffer demo\n");

	if (!device_is_ready(dma_dev)) {
		printk("ERROR: DMA device not ready\n");
		return -1;
	}

	/* Initialize source with a recognizable pattern. */
	for (size_t i = 0; i < BUF_SIZE; i++) {
		src_buf[i] = (uint8_t)i;
	}

	/* Start with buffer A as the active target. */
	active_buf = 0;
	completed_xfers = 0;
	dma_error = 0;

	/* Configure the DMA transfer (memory-to-memory for demo purposes). */
	blk.block_size = BUF_SIZE;
	blk.source_address = (uint32_t)(uintptr_t)src_buf;
	blk.dest_address = (uint32_t)(uintptr_t)buf_a;

	cfg.channel_direction = MEMORY_TO_MEMORY;
	cfg.source_data_size = 1;  /* 1 byte per transfer unit */
	cfg.dest_data_size = 1;
	cfg.source_burst_length = 1;
	cfg.dest_burst_length = 1;
	cfg.dma_callback = dma_callback;
	cfg.user_data = NULL;
	cfg.block_count = 1;
	cfg.head_block = &blk;

	ret = dma_config(dma_dev, DMA_CHANNEL, &cfg);
	if (ret < 0) {
		printk("ERROR: DMA config failed (%d)\n", ret);
		return ret;
	}

	/* Start the first transfer. The callback will chain subsequent ones. */
	ret = dma_start(dma_dev, DMA_CHANNEL);
	if (ret < 0) {
		printk("ERROR: DMA start failed (%d)\n", ret);
		return ret;
	}

	printk("DMA started, waiting for %d transfers...\n", XFERS_WANTED);

	/* Wait for the requested number of transfers. */
	for (int i = 0; i < XFERS_WANTED; i++) {
		k_sem_take(&xfer_done, K_FOREVER);

		if (dma_error) {
			printk("ERROR: DMA error (%d)\n", dma_error);
			break;
		}

		/*
		 * The 'ready_buf' pointer references the buffer that was just
		 * filled. In a real application, you'd parse or forward it here.
		 */
		printk("Transfer %d complete, first byte=0x%02x\n",
		       i + 1, ready_buf[0]);
	}

	/* Stop further transfers. */
	ret = dma_stop(dma_dev, DMA_CHANNEL);
	if (ret < 0) {
		printk("WARNING: DMA stop returned %d\n", ret);
	}

	printk("\nTotal completed transfers: %u\n", completed_xfers);

	return 0;
}
