#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gpiod.h>

static void usage(const char *argv0)
{
	fprintf(stderr, "usage: %s <chip-path> <line-offset> <value>\n", argv0);
}

int main(int argc, char **argv)
{
	struct gpiod_chip *chip = NULL;
	struct gpiod_line_settings *settings = NULL;
	struct gpiod_line_config *line_cfg = NULL;
	struct gpiod_request_config *req_cfg = NULL;
	struct gpiod_line_request *request = NULL;
	unsigned int offset;
	int value;
	char *end;
	int ret = 1;

	if (argc != 4) {
		usage(argv[0]);
		return 1;
	}

	errno = 0;
	offset = (unsigned int)strtoul(argv[2], &end, 10);
	if (errno || *end != '\0') {
		fprintf(stderr, "invalid line offset: %s\n", argv[2]);
		return 1;
	}

	if (strcmp(argv[3], "0") == 0)
		value = 0;
	else if (strcmp(argv[3], "1") == 0)
		value = 1;
	else {
		fprintf(stderr, "value must be 0 or 1\n");
		return 1;
	}

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
	gpiod_line_settings_set_direction(settings,
					  GPIOD_LINE_DIRECTION_OUTPUT);
	gpiod_line_settings_set_output_value(
		settings, value ? GPIOD_LINE_VALUE_ACTIVE
				: GPIOD_LINE_VALUE_INACTIVE);

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
	gpiod_request_config_set_consumer(req_cfg, "gpio_toggle");

	request = gpiod_chip_request_lines(chip, req_cfg, line_cfg);
	if (!request) {
		perror("gpiod_chip_request_lines");
		goto out_req_cfg;
	}

	gpiod_line_request_release(request);
	ret = 0;

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
