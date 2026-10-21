#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gpiod.h>

#define BUF_CAP 16
#define WAIT_NS 1000000000LL /* 1 second */

static volatile sig_atomic_t exit_flag = 0;

static void handle_sigterm(int signo)
{
	(void)signo;
	exit_flag = 1;
}

int main(int argc, char **argv)
{
	struct gpiod_chip *chip = NULL;
	struct gpiod_line_settings *settings = NULL;
	struct gpiod_line_config *line_cfg = NULL;
	struct gpiod_request_config *req_cfg = NULL;
	struct gpiod_line_request *request = NULL;
	struct gpiod_edge_event_buffer *buf = NULL;
	struct sigaction sa = {0};
	unsigned int offset;
	unsigned long counter = 0;
	char *end;
	int ret = 1;

	if (argc != 3) {
		fprintf(stderr, "usage: %s <chip-path> <line-offset>\n", argv[0]);
		return 1;
	}

	errno = 0;
	offset = (unsigned int)strtoul(argv[2], &end, 10);
	if (errno || *end != '\0') {
		fprintf(stderr, "invalid line offset: %s\n", argv[2]);
		return 1;
	}

	sa.sa_handler = handle_sigterm;
	sigaction(SIGTERM, &sa, NULL);
	sigaction(SIGINT, &sa, NULL);

	chip = gpiod_chip_open(argv[1]);
	if (!chip) {
		perror("gpiod_chip_open");
		return 1;
	}

	settings = gpiod_line_settings_new();
	if (!settings) {
		perror("gpiod_line_settings_new");
		goto out_chip;
	}
	gpiod_line_settings_set_direction(settings, GPIOD_LINE_DIRECTION_INPUT);
	gpiod_line_settings_set_edge_detection(settings, GPIOD_LINE_EDGE_RISING);

	line_cfg = gpiod_line_config_new();
	if (!line_cfg) {
		perror("gpiod_line_config_new");
		goto out_settings;
	}
	if (gpiod_line_config_add_line_settings(line_cfg, &offset, 1, settings) < 0) {
		perror("gpiod_line_config_add_line_settings");
		goto out_line_cfg;
	}

	req_cfg = gpiod_request_config_new();
	if (!req_cfg) {
		perror("gpiod_request_config_new");
		goto out_line_cfg;
	}
	gpiod_request_config_set_consumer(req_cfg, "gpio_monitor");

	request = gpiod_chip_request_lines(chip, req_cfg, line_cfg);
	if (!request) {
		perror("gpiod_chip_request_lines");
		goto out_req_cfg;
	}

	buf = gpiod_edge_event_buffer_new(BUF_CAP);
	if (!buf) {
		perror("gpiod_edge_event_buffer_new");
		goto out_request;
	}

	while (!exit_flag) {
		int n = gpiod_line_request_wait_edge_events(request, WAIT_NS);
		if (n < 0) {
			if (errno == EINTR)
				continue;
			perror("gpiod_line_request_wait_edge_events");
			break;
		}
		if (n == 0)
			continue; /* timeout — re-check exit_flag */

		int got = gpiod_line_request_read_edge_events(request, buf, BUF_CAP);
		if (got < 0) {
			perror("gpiod_line_request_read_edge_events");
			break;
		}
		for (int i = 0; i < got; i++) {
			struct gpiod_edge_event *ev =
				gpiod_edge_event_buffer_get_event(buf, i);
			counter++;
			printf("edge %lu at %llu ns\n", counter,
			       (unsigned long long)gpiod_edge_event_get_timestamp_ns(ev));
		}
	}

	ret = 0;

	gpiod_edge_event_buffer_free(buf);
out_request:
	gpiod_line_request_release(request);
out_req_cfg:
	gpiod_request_config_free(req_cfg);
out_line_cfg:
	gpiod_line_config_free(line_cfg);
out_settings:
	gpiod_line_settings_free(settings);
out_chip:
	gpiod_chip_close(chip);
	return ret;
}
