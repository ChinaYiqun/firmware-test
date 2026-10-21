/*
 * Zephyr RTOS application: DMA memory-to-memory copy.
 *
 * Copies a 64-byte buffer to another location in memory using the DMA
 * controller described by the devicetree node label "dma0".
 *
 * Expected devicetree overlay (example):
 *   &dma_controller {
 *       status = "okay";
 *       dma0: dma {
 *           compatible = "...";
 *       };
 *   };
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/dma.h>

#include <string.h>

#define SRC_BUF_SIZE	64U	/* size of the buffer to transfer in bytes */
#define DMA_CHANNEL	0U	/* DMA channel to use on the controller  */
#define DMA_OP_SIZE	4U	/* transfer chunk size in bytes (32-bit)  */

/* Signalled by the DMA callback when the transfer completes. */
K_SEM_DEFINE(dma_sem, 0, 1);

/* Buffers aligned to satisfy typical DMA controller alignment needs. */
static uint8_t src_buf[SRC_BUF_SIZE] __aligned(32);
static uint8_t dst_buf[SRC_BUF_SIZE] __aligned(32);

/* 0 on success, negative errno if the DMA driver reported an error. */
static int transfer_error;

/*
 * DMA completion callback. Invoked by the driver when the transfer
 * finishes (or fails); it must be able to run in interrupt context.
 */
static void dma_transfer_cb(const struct device *dev, void *user_data,
			    uint32_t channel, void *dma_data)
{
	const struct dma_status *status = dma_data;

	if (status->major_error != 0 || status->minor_error != 0) {
		transfer_error = -EIO;
	}

	k_sem_give(&dma_sem);
}

int main(void)
{
	const struct device *dma_dev;
	struct dma_config cfg;
	int ret;

	/* 1. Obtain the DMA controller from the devicetree. */
	dma_dev = DEVICE_DT_GET(DT_NODELABEL(dma0));
	if (dma_dev == NULL) {
		printk("DMA error: devicetree node label dma0 not found\n");
		return -ENODEV;
	}

	/* 2. Check that the device driver is ready before use. */
	if (!device_is_ready(dma_dev)) {
		printk("DMA error: controller dma0 is not ready\n");
		return -ENODEV;
	}

	/* 3. Prepare the buffers: source gets a known pattern,
	 *    destination is zero-filled.
	 */
	for (size_t i = 0; i < sizeof(src_buf); i++) {
		src_buf[i] = (uint8_t)(i + 1);	/* pattern: 1, 2, 3, ... */
	}
	memset(dst_buf, 0, sizeof(dst_buf));

	/* 4. Configure a memory-to-memory transfer of the whole buffer. */
	cfg.src_addr		= (uintptr_t)src_buf;
	cfg.src_op_size		= DMA_OP_SIZE;
	cfg.src_data_size	= sizeof(src_buf);
	cfg.src_callback_en	= false;
	cfg.dst_addr		= (uintptr_t)dst_buf;
	cfg.dst_op_size		= DMA_OP_SIZE;
	cfg.dst_data_size	= sizeof(dst_buf);
	cfg.dst_callback_en	= true;
	cfg.direction		= DMA_DIRECTION_MEMORY_TO_MEMORY;
	cfg.channel_priority	= 1;
	cfg.dma_mode		= DMA_MODE_M2M;
	cfg.dma_slot		= DMA_SLOT_ANY;

	ret = dma_config(dma_dev, DMA_CHANNEL, &cfg);
	if (ret != 0) {
		printk("DMA error: failed to configure channel %u: %d\n",
		       (unsigned int)DMA_CHANNEL, ret);
		return ret;
	}

	/* 5. Register the completion callback. */
	ret = dma_callback_set(dma_dev, DMA_CHANNEL, dma_transfer_cb, NULL);
	if (ret != 0) {
		printk("DMA error: failed to set callback: %d\n", ret);
		return ret;
	}

	/* 6. Start the transfer and wait for completion. */
	ret = dma_start(dma_dev, DMA_CHANNEL);
	if (ret != 0) {
		printk("DMA error: failed to start transfer: %d\n", ret);
		return ret;
	}

	ret = k_sem_take(&dma_sem, K_SECONDS(5));
	if (ret != 0) {
		printk("DMA error: transfer did not complete in time (timeout)\n");
		dma_stop(dma_dev, DMA_CHANNEL);
		return ret;
	}

	if (transfer_error != 0) {
		printk("DMA error: transfer reported a hardware error\n");
		return transfer_error;
	}

	/* 7. Verify that the destination buffer matches the source. */
	if (memcmp(dst_buf, src_buf, sizeof(src_buf)) == 0) {
		/* 8. Report success. */
		printk("DMA transfer succeeded: %u bytes copied and verified\n",
		       (unsigned int)sizeof(src_buf));
	} else {
		/* 8. Report failure. */
		printk("DMA transfer failed: destination buffer does not match source\n");
		return -EIO;
	}

	/* Keep the application alive so the result remains observable. */
	while (true) {
		k_sleep(K_SECONDS(1));
	}

	return 0;
}
