Write a Linux 5.15 kernel module that opens a kernel-side datagram
endpoint on a dedicated netlink protocol number and echoes back every
message it receives from user space.

Scenario:
- The module uses a custom netlink protocol number (not the generic
  or usersock reserved numbers — pick 31, which is free on 5.15).
- The module registers an input callback with the kernel that gets
  invoked for each incoming message, in process context on the
  socket's receive queue (sleeping is allowed here).
- The input callback reads the first netlink message from the
  incoming socket buffer, looks at the source PID, builds a reply
  containing the literal string "embedeval-ack", and sends the
  reply via unicast to that same PID.
- Module init creates the kernel endpoint in the initial network
  namespace; on failure it returns -ENOMEM / the error from the
  creation API with no partial state left behind.
- Module exit releases the endpoint with the dedicated release API.

Requirements:
1. Include the kernel headers for: module metadata, socket-layer
   types (sock), skbuff, the netlink and net-level netlink helpers,
   and network namespaces.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Define a compile-time constant for your custom protocol number
   (31).
4. Declare a module-scope `struct sock *` for the kernel endpoint.
5. Declare the config struct with the `.input` function pointer
   filled in — this is the struct the kernel-side netlink create
   API consumes.
6. Input callback (`void name(struct sk_buff *skb)`):
   - Obtains the netlink message header from the skb.
   - Reads the source port-id (the PID the userspace sender
     registered against).
   - Allocates a reply message via the standard netlink reply
     allocation API.
   - Fills in a netlink message header and payload inside the reply
     skb, reserving room for the payload size.
   - Sends the reply to the requesting PID via unicast.
7. Module init:
   - Calls the endpoint-creation API with the init_net namespace,
     your protocol number, and the config struct.
   - Returns -ENOMEM (or the observed error) if the return is NULL.
8. Module exit:
   - Calls the endpoint-release API only if the sock pointer is
     non-NULL.

Output ONLY the complete C source file.
