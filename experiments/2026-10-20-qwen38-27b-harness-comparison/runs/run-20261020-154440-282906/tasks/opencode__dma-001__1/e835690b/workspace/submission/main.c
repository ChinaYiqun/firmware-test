#include <zephyr/kernel.h>
#include <zephyr/dma/dma.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>

#include <string.h>

#define DMA_NODE   DT_NODELABEL(dma0)
#define DMA_DEVICE DEVICE_DT_GET(DMA_NODE)

#define BUF_SIZE     64
#define DMA_TIMEOUT_MS 1000

LOG_MODULE_REGISTER(dma_copy, LOG_LEVEL_INF);

static uint8_t src_buf[BUF_SIZE];
static uint8_t dst_buf[BUF_SIZE];

K_SEM_DEFINE(dma_done, 0, 1);

static void dma_transfer_callback(const struct device *dev, void *user_data,
				  uint32_t channel, int status)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(channel);

	if (user_data != NULL) {
		*(int *)user_data = status;
	}

	k_sem_give(&dma_done);
}

int main(void)
{
	const struct device *dma_dev = DMA_DEVICE;
	struct dma_dmap dmap;
	struct dma_config config;
	struct dma_status status;
	int transfer_status = DMA_STATUS_COMPLETED;
	int err;

	if (!device_is_ready(dma_dev)) {
		LOG_ERR("DMA controller %s is not ready", dma_dev->name);
		return -ENODEV;
	}

	for (size_t i = 0; i < BUF_SIZE; i++) {
		src_buf[i] = (uint8_t)(i + 1);
	}

	memset(dst_buf, 0, sizeof(dst_buf));

	err = dma_request_dmap(dma_dev, &dmap);
	if (err != 0) {
		LOG_ERR("Failed to request DMA map: %d", err);
		return err;
	}

	memset(&config, 0, sizeof(config));
	config.direction = DMA_DIRECTION_MEMORY_TO_MEMORY;
	config.source_data_size = 1;
	config.dest_data_size = 1;
	config.source_repetition = DMA_REPETITION_NONE;
	config.dest_repetition = DMA_REPETITION_NONE;
	config.dma_validation = DMA_VALIDATION_DISABLE;
	config.priority = 0;
	config.source_address = (uintptr_t)src_buf;
	config.dest_address = (uintptr_t)dst_buf;
	config.source_byte_increment = 1;
	config.dest_byte_increment = 1;
	config.source_block_length = BUF_SIZE;
	config.dest_block_length = BUF_SIZE;
	config.max_bytes = BUF_SIZE;

	err = dma_configure_dmap(dma_dev, &dmap, &config, &status);
	if (err != 0) {
		LOG_ERR("Failed to configure DMA channel: %d", err);
		goto release_dmap;
	}

	err = dma_add_callback_dmap(dma_dev, &dmap, dma_transfer_callback,
				    &transfer_status);
	if (err != 0) {
		LOG_ERR("Failed to add DMA transfer callback: %d", err);
		goto release_dmap;
	}

	err = dma_start_dmap(dma_dev, &dmap);
	if (err != 0) {
		LOG_ERR("Failed to start DMA transfer: %d", err);
		goto release_dmap;
	}

	err = k_sem_take(&dma_done, K_MSEC(DMA_TIMEOUT_MS));
	if (err != 0) {
		LOG_ERR("Timed out waiting for DMA transfer to complete");
		dma_stop_dmap(dma_dev, &dmap);
		goto release_dmap;
	}

	if (transfer_status != DMA_STATUS_COMPLETED) {
		LOG_ERR("DMA transfer completed with error status %d",
			transfer_status);
		err = -EIO;
		goto release_dmap;
	}

	if (memcmp(src_buf, dst_buf, BUF_SIZE) != 0) {
		LOG_ERR("DMA transfer failed: destination buffer does not "
			"match source buffer");
		err = -EIO;
		goto release_dmap;
	}

	LOG_INF("DMA transfer succeeded: %d bytes copied from source to "
		"destination", BUF_SIZE);
	err = 0;

release_dmap:
	dma_release_dmap(dma_dev, &dmap);

	return err;
}
