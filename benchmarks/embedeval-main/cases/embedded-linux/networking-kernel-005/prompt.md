Write a Linux 5.15 kernel module that observes when any network
interface on the system goes administratively UP or DOWN, and emits a
`pr_info` trace containing the interface name for each transition.

Scenario:
- The module plugs into the kernel-wide notifier chain that the
  networking core uses to broadcast interface events.
- The callback receives an event number and an opaque pointer; the
  modern-kernel convention (since 3.11) is to pass a
  `struct netdev_notifier_info *` through that pointer. You must use
  the dedicated accessor helper to get the `struct net_device *`
  back out — do NOT cast directly.
- The callback returns the notifier-chain "OK" or "DONE" constant —
  it does NOT return 0 or -errno.
- Registration in init; unregistration in exit. If registration
  fails, propagate the errno.

Requirements:
1. Include the kernel headers for: module metadata, netdevice
   definitions (pulls in notifier events), and notifier chain types.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Declare a module-scope static `struct notifier_block` with the
   `.notifier_call` field pointing at your callback.
4. Callback signature `int name(struct notifier_block *nb,
   unsigned long event, void *ptr)`:
   - Acquires the `struct net_device *` from `ptr` using the
     dedicated accessor helper.
   - Switches on the event; for UP and DOWN emits a `pr_info` trace
     containing `dev->name` and the event direction.
   - Returns the notifier-OK / notifier-DONE constant (NOT 0).
5. Module init:
   - Registers the notifier via the netdevice-notifier registration
     API.
   - Checks the return; on failure returns the errno.
6. Module exit:
   - Unregisters the notifier.

Output ONLY the complete C source file.
