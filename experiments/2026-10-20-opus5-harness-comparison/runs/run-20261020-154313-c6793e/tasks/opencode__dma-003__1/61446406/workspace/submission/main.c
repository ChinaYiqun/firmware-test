/*
 * Zephyr DMA circular / ping-pong continuous data collection example.
 *
 * The DMA controller referenced by the devicetree label "dma0" is programmed
 * with a single block that is reloaded from the completion callback, so the
 * peripheral keeps streaming without gaps. Each completion flips the target
 * between buf_a and buf_b (ping-pong) and wakes the main thread, which
 * consumes the buffer that was just filled.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/dma.h>
#include <zephyr/sys/printk.h>
#include <string.h>

/* ------------------------------------------------------------------ */
/* Configuration                                                      */
/* ------------------------------------------------------------------ */

#define DMA_NODE        DT_NODELABEL(dma0)

/* Size of each ping-pong buffer, in bytes. */
#define BUF_SIZE        32U

/* DMA channel and peripheral request line used for the capture. */
#define DMA_CHANNEL     0U
#define DMA_SLOT        0U

/* Number of transfers the main loop must consume before stopping. */
#define XFERS_WANTED    4U

/* Guard so a hung source cannot block the demo forever. */
#define XFER_TIMEOUT    K_MSEC(1000)

/* ------------------------------------------------------------------ */
/* Ping-pong buffers                                                  */
/* ------------------------------------------------------------------ */

/*
 * Buffers are cache-line aligned so they can be safely used as DMA targets
 * on platforms with a data cache.
 */
static uint8_t buf_a[BUF_SIZE] __aligned(32);
static uint8_t buf_b[BUF_SIZE] __aligned(32);

/* Index of the buffer the DMA engine is currently filling: 0 = A, 1 = B. */
static volatile uint8_t active_buf;

/* Buffer that was completed most recently (the one safe to process). */
static volatile uint8_t done_buf;

/* Total number of completed DMA transfers. */
static volatile uint32_t xfer_count;

/* Set when the callback reports an error; processing then aborts. */
static volatile int dma_error;

/* Signalled by the DMA callback once per completed transfer. */
static K_SEM_DEFINE(xfer_sem, 0, XFERS_WANTED + 1);

/* Device handle for the DMA controller from the devicetree. */
static const struct device *const dma_dev = DEVICE_DT_GET(DMA_NODE);

/* Simulated peripheral FIFO / source region for the memory-to-memory case. */
static uint8_t src_fifo[BUF_SIZE] __aligned(32);

static inline uint8_t *buf_ptr(uint8_t idx)
{
	return (idx == 0U) ? buf_a : buf_b;
}

static inline const char *buf_name(uint8_t idx)
{
	return (idx == 0U) ? "buf_a" : "buf_b";
}

/* ------------------------------------------------------------------ */
/* DMA callback and reload logic                                      */
/* ------------------------------------------------------------------ */

/*
 * Called by the DMA driver when a transfer completes (or fails).
 * To achieve circular mode, we reload the DMA channel with the *next*
 * buffer and then signal the main thread that the *previous* buffer is
 * ready for processing.
 */
static void dma_callback(const struct device *dev, void *user_data,
			 uint32_t channel, int status)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(user_data);
	ARG_UNUSED(channel);

	if (status < 0) {
		dma_error = status;
		k_sem_give(&xfer_sem);
		return;
	}

	/* The buffer we just finished filling. */
	done_buf = active_buf;

	/* Increment transfer count. */
	xfer_count++;

	/* Switch to the other buffer for the next transfer. */
	active_buf = (active_buf == 0U) ? 1U : 0U;

	/* Reload the DMA to start filling the newly active buffer. */
	struct dma_block_config block_cfg = {
		.source_address      = (uint32_t)src_fifo,
		.dest_address        = (uint32_t)buf_ptr(active_buf),
		.block_size          = BUF_SIZE,
		.source_addr_adj     = DMA_ADDR_ADJ_NO_CHANGE,
		.dest_addr_adj       = DMA_ADDR_ADJ_INCREMENT,
	};

	struct dma_config dma_cfg = {
		.channel_direction   = MEMORY_TO_MEMORY,
		.source_data_size    = 1U,
		.dest_data_size      = 1U,
		.source_burst_length = 1U,
		.dest_burst_length   = 1U,
		.dma_slot            = DMA_SLOT,
		.block_count         = 1U,
		.head_block          = &block_cfg,
		.dma_callback        = dma_callback,
	};

	int ret = dma_config(dma_dev, DMA_CHANNEL, &dma_cfg);
	if (ret < 0) {
		dma_error = ret;
		k_sem_give(&xfer_sem);
		return;
	}

	ret = dma_start(dma_dev, DMA_CHANNEL);
	if (ret < 0) {
		dma_error = ret;
		k_sem_give(&xfer_sem);
		return;
	}

	/* Wake the main thread so it can process the completed buffer. */
	k_sem_give(&xfer_sem);
}

/* ------------------------------------------------------------------ */
/* Main application                                                   */
/* ------------------------------------------------------------------ */

int main(void)
{
	int ret;

	printk("DMA circular mode (ping-pong) demo\n");

	/* Check that the DMA controller is ready. */
	if (!device_is_ready(dma_dev)) {
		printk("ERROR: DMA device %s not ready\n", dma_dev->name);
		return -ENODEV;
	}
	printk("DMA device %s is ready\n", dma_dev->name);

	/* Initialize ping-pong buffers to a known pattern. */
	memset(buf_a, 0xAA, BUF_SIZE);
	memset(buf_b, 0xBB, BUF_SIZE);

	/* Populate the source FIFO with incrementing data. */
	for (uint32_t i = 0U; i < BUF_SIZE; i++) {
		src_fifo[i] = (uint8_t)i;
	}

	/* Start with buffer A as the first target. */
	active_buf = 0U;
	xfer_count = 0U;
	dma_error  = 0;

	/* Configure and start the initial DMA transfer. */
	struct dma_block_config block_cfg = {
		.source_address      = (uint32_t)src_fifo,
		.dest_address        = (uint32_t)buf_ptr(active_buf),
		.block_size          = BUF_SIZE,
		.source_addr_adj     = DMA_ADDR_ADJ_NO_CHANGE,
		.dest_addr_adj       = DMA_ADDR_ADJ_INCREMENT,
	};

	struct dma_config dma_cfg = {
		.channel_direction   = MEMORY_TO_MEMORY,
		.source_data_size    = 1U,
		.dest_data_size      = 1U,
		.source_burst_length = 1U,
		.dest_burst_length   = 1U,
		.dma_slot            = DMA_SLOT,
		.block_count         = 1U,
		.head_block          = &block_cfg,
		.dma_callback        = dma_callback,
	};

	ret = dma_config(dma_dev, DMA_CHANNEL, &dma_cfg);
	if (ret < 0) {
		printk("ERROR: dma_config failed (%d)\n", ret);
		return ret;
	}

	printk("Starting DMA in circular mode...\n");
	ret = dma_start(dma_dev, DMA_CHANNEL);
	if (ret < 0) {
		printk("ERROR: dma_start failed (%d)\n", ret);
		return ret;
	}

	/* Process at least XFERS_WANTED transfers. */
	for (uint32_t i = 0U; i < XFERS_WANTED; i++) {
		ret = k_sem_take(&xfer_sem, XFER_TIMEOUT);
		if (ret < 0) {
			printk("ERROR: timeout waiting for transfer %u\n", i + 1);
			break;
		}

		if (dma_error) {
			printk("ERROR: DMA callback reported error %d\n", dma_error);
			break;
		}

		/* Process the completed buffer (done_buf). */
		uint8_t *completed = buf_ptr(done_buf);
		printk("Transfer %u complete (%s): first=0x%02x last=0x%02x\n",
		       xfer_count, buf_name(done_buf),
		       completed[0], completed[BUF_SIZE - 1]);
	}

	/* Stop the DMA channel. */
	ret = dma_stop(dma_dev, DMA_CHANNEL);
	if (ret < 0) {
		printk("WARNING: dma_stop failed (%d)\n", ret);
	} else {
		printk("DMA stopped\n");
	}

	printk("Total completed transfers: %u\n", xfer_count);

	return 0;
}
