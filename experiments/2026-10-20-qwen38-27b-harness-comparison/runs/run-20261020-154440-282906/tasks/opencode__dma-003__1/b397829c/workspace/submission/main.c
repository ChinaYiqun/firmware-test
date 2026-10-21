#include <errno.h>
#include <stdint.h>

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/logging/log.h>
#include <drivers/dma/dma.h>

LOG_MODULE_REGISTER(dma_pingpong, LOG_LEVEL_INF);

#define DMA_NODE      DT_NODELABEL(dma0)
#define BUF_SIZE      32
#define NUM_TRANSFERS 4

static const struct device *const dma_dev = DEVICE_DT_GET(DMA_NODE);

static uint8_t buf_a[BUF_SIZE];
static uint8_t buf_b[BUF_SIZE];
static const uint8_t *const buffers[] = { buf_a, buf_b };

static uint8_t active_buf;
static uint32_t completed_transfers;

static K_SEM_DEFINE(dma_complete_sem, 0, 1);

static void process_buffer(uint8_t index)
{
	uint32_t sum = 0;

	for (int i = 0; i < BUF_SIZE; i++) {
		sum += (uint32_t)buffers[index][i];
	}

	LOG_INF("buffer %c filled, sum %u",
		(index == 0) ? 'a' : 'b', sum);
}

static void restart_dma(void)
{
	active_buf ^= 1;

	struct dma_rx_config cfg = {
		.buffer = (uintptr_t)buffers[active_buf],
		.data_length = BUF_SIZE,
		.burst_size = 1,
		.data_size = 1,
	};

	(void)dma_rx_setup(dma_dev, &cfg, NULL);
	(void)dma_rx_start(dma_dev);
}

static void dma_transfer_complete(void *user_data)
{
	ARG_UNUSED(user_data);

	completed_transfers++;
	restart_dma();
	k_sem_give(&dma_complete_sem);
}

int main(void)
{
	int err;

	if (!device_is_ready(dma_dev)) {
		LOG_ERR("DMA controller %s is not ready", DT_NODE_LABEL(DMA_NODE));
		return -ENODEV;
	}

	err = dma_set_channel_callback(dma_dev, 0, dma_transfer_complete, NULL);
	if (err) {
		return err;
	}

	active_buf = 0;

	struct dma_rx_config cfg = {
		.buffer = (uintptr_t)buf_a,
		.data_length = BUF_SIZE,
		.burst_size = 1,
		.data_size = 1,
	};

	err = dma_rx_setup(dma_dev, &cfg, NULL);
	if (err) {
		return err;
	}

	err = dma_rx_start(dma_dev);
	if (err) {
		return err;
	}

	while (completed_transfers < NUM_TRANSFERS) {
		err = k_sem_take(&dma_complete_sem, K_FOREVER);
		if (err == 0) {
			process_buffer(active_buf ^ 1u);
		}
	}

	(void)dma_stop(dma_dev);
	(void)dma_unsetup(dma_dev);

	LOG_INF("Total completed transfers: %u", completed_transfers);

	return 0;
}
