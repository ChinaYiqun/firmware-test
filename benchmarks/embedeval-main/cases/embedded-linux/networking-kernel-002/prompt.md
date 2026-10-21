Write a Linux 5.15 kernel module that captures copies of incoming
packets into a per-module queue, processes them asynchronously from a
kernel worker, and tears down the queue cleanly when the module
unloads.

Scenario:
- An exported function `embedeval_enqueue_skb(struct sk_buff *skb)`
  is called from a non-process context (softirq / packet path). It
  must make a private copy of the skb (the original is owned by the
  caller), push the copy onto a per-module FIFO, and return quickly.
- A kernel worker dequeues from the FIFO and emits a `pr_info` trace
  for each packet consumed (in process context — sleeping is
  permitted there).
- Making the private copy is an allocation. In the caller's context
  you cannot use the default memory flag — pick the allocation flag
  that is safe in softirq / interrupt context.
- The copy operation may fail under memory pressure and will return
  NULL. You must handle that, without leaking anything.
- When the module unloads, every still-queued skb must be freed.
- On the normal-completion path in the worker, distinguish between
  "I consumed this packet successfully" and "I dropped this packet
  due to error" — the kernel has two different free functions so
  that dropwatch / tracing tooling can tell the two apart. Use the
  right one for successful consumption.

Requirements:
1. Include the kernel headers for: module metadata, skbuff, the
   sk_buff_head queue interface, the deferred-task facility, and
   slab.
2. Provide MODULE_LICENSE("GPL"), MODULE_AUTHOR, MODULE_DESCRIPTION.
3. Declare a module-scope `struct sk_buff_head` FIFO and a
   `struct work_struct` for the drain worker.
4. Module init:
   - Initialise the FIFO head (the kernel has a dedicated init
     function for sk_buff_head, not a generic list init).
   - Initialise the work_struct.
5. Exported producer `embedeval_enqueue_skb(struct sk_buff *skb)`:
   - Makes a private skb copy using the dedicated per-packet clone
     function.
   - If the clone fails (returns NULL), returns without enqueuing
     and without dereferencing the clone.
   - Pushes the clone on the FIFO tail.
   - Schedules the drain worker.
6. Drain worker:
   - Dequeues from the FIFO head until empty.
   - Emits `pr_info` for each packet.
   - Releases each successfully-processed packet via the
     "successful consumption" free function — not the "drop /
     error" one.
7. Module exit:
   - Cancels the worker synchronously.
   - Drains any packets still on the FIFO, freeing every one.
8. EXPORT_SYMBOL the producer.

Output ONLY the complete C source file.
