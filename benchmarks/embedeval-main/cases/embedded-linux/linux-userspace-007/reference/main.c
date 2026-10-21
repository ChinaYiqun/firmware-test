#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <systemd/sd-bus.h>

static int method_ping(sd_bus_message *m, void *userdata, sd_bus_error *ret_error)
{
	const char *greeting = NULL;
	char reply[256];
	int r;

	(void)userdata;
	(void)ret_error;

	r = sd_bus_message_read(m, "s", &greeting);
	if (r < 0) {
		fprintf(stderr, "sd_bus_message_read failed: %s\n", strerror(-r));
		return r;
	}

	snprintf(reply, sizeof(reply), "pong: %s", greeting ? greeting : "");
	return sd_bus_reply_method_return(m, "s", reply);
}

static const sd_bus_vtable example_vtable[] = {
	SD_BUS_VTABLE_START(0),
	SD_BUS_METHOD("Ping", "s", "s", method_ping, SD_BUS_VTABLE_UNPRIVILEGED),
	SD_BUS_VTABLE_END,
};

int main(void)
{
	sd_bus *bus = NULL;
	sd_bus_slot *slot = NULL;
	int r;

	r = sd_bus_open_system(&bus);
	if (r < 0) {
		fprintf(stderr, "sd_bus_open_system failed: %s\n", strerror(-r));
		goto finish;
	}

	r = sd_bus_add_object_vtable(bus, &slot, "/com/embedeval/Example",
				     "com.embedeval.Example", example_vtable,
				     NULL);
	if (r < 0) {
		fprintf(stderr, "sd_bus_add_object_vtable failed: %s\n",
			strerror(-r));
		goto finish;
	}

	r = sd_bus_request_name(bus, "com.embedeval.Example", 0);
	if (r < 0) {
		fprintf(stderr, "sd_bus_request_name failed: %s\n", strerror(-r));
		goto finish;
	}

	for (;;) {
		r = sd_bus_process(bus, NULL);
		if (r < 0) {
			fprintf(stderr, "sd_bus_process failed: %s\n",
				strerror(-r));
			goto finish;
		}
		if (r > 0)
			continue; /* more work queued — drain */
		r = sd_bus_wait(bus, (uint64_t)-1);
		if (r < 0) {
			fprintf(stderr, "sd_bus_wait failed: %s\n", strerror(-r));
			goto finish;
		}
	}

finish:
	slot = sd_bus_slot_unref(slot);
	bus = sd_bus_unref(bus);
	(void)slot;
	(void)bus;
	return r < 0 ? EXIT_FAILURE : EXIT_SUCCESS;
}
