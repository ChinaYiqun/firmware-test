Write a Linux 5.15 kernel module that registers a generic netlink
family named "embedeval_genl" with a single operation that echoes a
payload string back to the requester.

Scenario:
- Userspace tooling (genl / nl-cli) looks up the family by name,
  sends a single command `EMBEDEVAL_CMD_ECHO`, and expects a
  response containing a null-terminated string attribute.
- The family supports exactly ONE attribute slot (`EMBEDEVAL_ATTR_MSG`).
- The operation runs in process context — sleeping is permitted.
- On module exit, the family must be unregistered before the module
  text unloads.

Requirements:
1. Include the kernel headers for: module metadata, `struct nlattr`
   and the generic-netlink family + ops declarations (net/genetlink.h
   pulls in the rest).
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Declare an enum for the command id (only `EMBEDEVAL_CMD_ECHO`,
   with a count sentinel `__EMBEDEVAL_CMD_MAX` and a public max
   `EMBEDEVAL_CMD_MAX`).
4. Declare an enum for the attribute id (only `EMBEDEVAL_ATTR_MSG`,
   with a count sentinel `__EMBEDEVAL_ATTR_MAX` and a public max
   `EMBEDEVAL_ATTR_MAX`).
5. Declare a module-scope static array of `struct genl_ops` with a
   single entry for `EMBEDEVAL_CMD_ECHO` pointing at your handler.
6. Declare a module-scope `struct genl_family` populated with:
   - `.name` — "embedeval_genl" (no vendor prefix).
   - `.version` — 1.
   - `.module` — THIS_MODULE.
   - `.ops` — the ops array above.
   - `.n_ops` — ARRAY_SIZE(the ops array).
   - `.maxattr` — EMBEDEVAL_ATTR_MAX.
7. Handler function (`int name(struct sk_buff *skb, struct genl_info *info)`):
   - Allocates a reply message using the standard generic-netlink
     reply-allocation helper (sized around NLMSG_DEFAULT_SIZE).
   - Acquires a netlink header inside that reply, keyed to the
     incoming request's info block, for the echo command.
   - Puts an `NLA_STRING` attribute with literal "embedeval-echo".
   - Finalises the netlink message so the reply length header is
     correct, then sends the reply back to the requester.
   - Returns 0 on success or a negative errno on failure.
8. Module init registers the family.
9. Module exit unregisters the family.
10. Use the single-argument family registration form that has been
    the only supported form since around kernel 4.10 — do not use
    the older variant that passed ops as a second argument.

Output ONLY the complete C source file.
