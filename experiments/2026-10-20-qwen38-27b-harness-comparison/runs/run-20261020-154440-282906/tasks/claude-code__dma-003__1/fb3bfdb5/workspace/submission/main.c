/*
 * Zephyr RTOS - DMA circular (continuous) data collection with ping-pong
 * buffers.
 *
 * Design:
 *   - The DMA controller is obtained from the devicetree node labelled
 *     `dma0` (DEVICE_DT_GET(DT_NODELABEL(dma0))).
 *   - Two 32-byte buffers, buf_a and buf_b, are used as alternating DMA
 *     targets (ping-pong).
 *   - A pointer `active_buf` tracks which buffer the DMA is currently
 *     filling.
 *   - Continuous / circular mode is achieved by reloading the DMA
 *     immediately inside the transfer-completion callback so the next
 *     buffer starts filling as soon as the previous one completes.
 *   - On every completion the callback signals the main thread through a
 *     binary semaphore; the main thread then processes the completed
 *     buffer.
 *   - After processing 4 transfers the main thread stops the DMA and
 *     prints the total number of completed transfers.
 *
 * Kconfig requirements:
 *   CONFIG_DMA=y
 *   CONFIG_LOG=y
 *
 * Devicetree requirement:
 *   The chosen DMA controller node must be present with the label
 *   `dma0` (for example: `dma0: &dmac { status = "okay"; };`).
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/dma/dma.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>
#include <errno.h>

LOG_MODULE_REGISTER(dma_pingpong, LOG_LEVEL_INF);

/* ------------------------------------------------------------------------ */
/* Configuration                                                             */
/* ------------------------------------------------------------------------ */

/* DMA controller instance from the devicetree (node label: dma0). */
#define DMA_NODE      DT_NODELABEL(dma0)

/* DMA slot to use on the controller. */
#define DMA_SLOT      0

/* Size in bytes of each ping-pong buffer. */
#define BUF_SIZE      32

/* Number of transfers to process in the main loop before stopping. */
#define NUM_TRANSFERS 4

/* DMA descriptor alignment (kept generous to satisfy most drivers). */
#define DMA_ALIGN     32

/* ------------------------------------------------------------------------ */
/* Data buffers                                                              */
/* ------------------------------------------------------------------------ */

/* Simulated data source, e.g. a sensor FIFO / device register memory that
 * continuously holds data to be collected. On real hardware this would
 * instead be a peripheral (a source_dev + source_channel in dma_cfg).
 */
static uint8_t src[BUF_SIZE] __aligned(DMA_ALIGN);

/* The two ping-pong DMA target buffers. */
static uint8_t buf_a[BUF_SIZE] __aligned(DMA_ALIGN);
static uint8_t buf_b[BUF_SIZE] __aligned(DMA_ALIGN);

/* ------------------------------------------------------------------------ */
/* Runtime state                                                             */
/* ------------------------------------------------------------------------ */

static const struct device *const dma_dev = DEVICE_DT_GET(DMA_NODE);

/* Binary semaphore used to wake the main thread after each transfer. */
static K_SEM_DEFINE(dma_sem, 0, 1);

/* Buffer the DMA is currently filling. */
static uint8_t *active_buf = buf_a;

/* Buffer that has just completed and is ready for processing. */
static uint8_t *completed_buf = NULL;

/* Total number of successfully completed transfers. */
static volatile uint32_t total_completed = 0;

/* DMA configuration: 1-byte transfers, callback on every completed block.
 * This is the continuous/circular mode setup - the callback restarts the
 * transfer into the other ping-pong buffer.
 */
static const struct dma_cfg dma_config = {
	.source_dev          = NULL,
	.sink_dev            = NULL,
	.direction           = DIRECTION_DEV_TO_CPU,
	.source_channel      = DMA_CHANNEL_NONE,
	.sink_channel        = DMA_CHANNEL_NONE,
	.source_data_size    = 1,
	.sink_data_size      = 1,
	.source_burst_length = 1,
	.sink_burst_length   = 1,
	.byte_count          = BUF_SIZE,
	.cb_mode             = DMA_BLOCK_TRANSFER_COMPLETED,
};

/* ------------------------------------------------------------------------ */
/* Helpers                                                                   */
/* ------------------------------------------------------------------------ */

/* Process a completed buffer in the main thread context. */
static void process_buffer(const uint8_t *buf, int index)
{
	uint32_t checksum = 0;

	for (size_t i = 0; i < BUF_SIZE; i++) {
		checksum += buf[i];
	}

	LOG_INF("Processed buffer %d (%s): checksum 0x%08x, "
		"first bytes: %02x %02x %02x %02x",
		index, (buf == buf_a) ? "buf_a" : "buf_b",
		checksum, buf[0], buf[1], buf[2], buf[3]);
}

/*
 * DMA completion callback (runs in ISR context).
 *
 * Implements the circular/continuous behaviour: as soon as one block
 * finishes we immediately reload the DMA to fill the *other* ping-pong
 * buffer, then signal the main thread to process the buffer that just
 * completed.
 */
static void dma_cb(void *user_data, int status)
{
	ARG_UNUSED(user_data);

	if (status != 0) {
		LOG_ERR("DMA transfer failed (status %d)", status);
		/* Still release main so it can stop the DMA. */
		k_sem_give(&dma_sem);
		return;
	}

	/* The buffer that was active just finished - make it the one to
	 * process - then switch to the other buffer for the next transfer.
	 */
	completed_buf = active_buf;
	active_buf = (active_buf == buf_a) ? buf_b : buf_a;

	/* Count this completed transfer. */
	total_completed++;

	/*
	 * Circular/continuous mode: restart the DMA right away to start
	 * filling the next ping-pong buffer.
	 */
	int rc = dma_start(dma_dev, DMA_SLOT, src, active_buf, BUF_SIZE);

	if (rc != 0) {
		LOG_ERR("Failed to reload DMA for next buffer: %d", rc);
	}

	/* Wake the main thread so it can process the completed buffer. */
	k_sem_give(&dma_sem);
}

/* ------------------------------------------------------------------------ */
/* Main                                                                      */
/* ------------------------------------------------------------------------ */

int main(void)
{
	LOG_INF("DMA ping-pong continuous data collection starting");

	/* 2. Check that the DMA device is ready before use. */
	if (!device_is_ready(dma_dev)) {
		LOG_ERR("DMA controller (%s) is not ready", dma_dev->name);
		return -ENODEV;
	}

	/* Pre-fill the simulated source with data to collect. */
	for (size_t i = 0; i < BUF_SIZE; i++) {
		src[i] = (uint8_t)(0x40 + i);
	}

	/* 4. Start with buf_a as the active (filling) buffer. */
	active_buf   = buf_a;
	completed_buf = NULL;
	total_completed = 0;

	/* Configure the DMA slot and register the completion callback. */
	int rc = dma_init(dma_dev, DMA_SLOT, &dma_config, dma_cb, NULL);

	if (rc != 0) {
		LOG_ERR("dma_init failed: %d", rc);
		return rc;
	}

	/* Kick off the first transfer, filling the active buffer (buf_a). */
	rc = dma_start(dma_dev, DMA_SLOT, src, active_buf, BUF_SIZE);
	if (rc != 0) {
		LOG_ERR("dma_start failed: %d", rc);
		(void)dma_free(dma_dev, DMA_SLOT);
		return rc;
	}

	/* 7 & 8. Process transfers in the main loop: each semaphore signal
	 * means one transfer completed. Process the completed buffer, then
	 * wait for the next. Stop after NUM_TRANSFERS.
	 */
	for (int i = 0; i < NUM_TRANSFERS; i++) {
		if (k_sem_take(&dma_sem, K_FOREVER) != 0) {
			LOG_ERR("Timed out waiting for DMA transfer %d", i);
			break;
		}

		if (completed_buf == NULL) {
			LOG_ERR("No completed buffer to process");
			break;
		}

		process_buffer(completed_buf, i);
	}

	/* Stop the (possibly still in-flight) DMA and release the slot. */
	dma_stop(dma_dev, DMA_SLOT);
	rc = dma_free(dma_dev, DMA_SLOT);
	if (rc != 0) {
		LOG_ERR("dma_free failed: %d", rc);
	}

	/* 9. Print the total number of completed transfers. */
	LOG_INF("Total completed transfers: %u", total_completed);

	return 0;
}