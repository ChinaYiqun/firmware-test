"""Behavioral checks for networking-kernel-002 (sk_buff lifecycle).

Validates:
  - sk_buff_head declared + initialised via skb_queue_head_init.
  - skb_clone used with GFP_ATOMIC and the result NULL-checked.
  - Enqueue pushes via skb_queue_tail; worker dequeues with skb_dequeue.
  - Worker releases consumed packets via consume_skb — NOT kfree_skb —
    on the normal completion path.
  - Exit drains the queue via skb_queue_purge after cancelling work.
"""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_function_body,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def _find_worker_body(code: str) -> str:
    stripped = strip_comments(code)
    m = re.search(r"INIT_WORK\s*\(\s*[^,]+,\s*(\w+)\s*\)", stripped)
    if m:
        body = extract_function_body(stripped, m.group(1))
        if body:
            return body
    m = re.search(
        r"static\s+void\s+(\w+)\s*\(\s*struct\s+work_struct\s*\*\s*\w+\s*\)\s*\{",
        stripped,
    )
    if m:
        return extract_function_body(stripped, m.group(1)) or ""
    return ""


def _find_enqueue_body(code: str) -> str:
    """Locate the producer function — the first non-init function that
    passes a struct sk_buff * argument and is NOT the worker
    signature."""
    stripped = strip_comments(code)
    m = re.search(
        r"(?<!EXPORT_SYMBOL\()\b(?:void|int)\s+(\w+)\s*\(\s*struct\s+sk_buff\s*\*\s*\w+\s*\)\s*\{",
        stripped,
    )
    if m:
        return extract_function_body(stripped, m.group(1)) or ""
    return ""


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)
    init_body = extract_module_init_body(generated_code) or ""
    exit_body = extract_module_exit_body(generated_code) or ""
    worker_body = _find_worker_body(generated_code)
    enqueue_body = _find_enqueue_body(generated_code)

    # 1. sk_buff_head declared at module scope.
    has_head = bool(
        re.search(r"\bstruct\s+sk_buff_head\s+\w+\s*;", stripped)
    )
    details.append(
        CheckDetail(
            check_name="sk_buff_head_declared",
            passed=has_head,
            expected="struct sk_buff_head <name>; at module scope",
            actual="present" if has_head else "missing",
            check_type="constraint",
        )
    )

    # 2. Init calls skb_queue_head_init (the dedicated initialiser).
    init_called = has_api_call(init_body, "skb_queue_head_init")
    details.append(
        CheckDetail(
            check_name="skb_queue_head_init_called",
            passed=init_called,
            expected="skb_queue_head_init(&q) in init",
            actual="present" if init_called else "missing",
            check_type="constraint",
        )
    )

    # 3. Producer uses skb_clone.
    clones = has_api_call(enqueue_body, "skb_clone")
    details.append(
        CheckDetail(
            check_name="producer_uses_skb_clone",
            passed=clones,
            expected="skb_clone(skb, ...) in producer",
            actual="present" if clones else "missing",
            check_type="constraint",
        )
    )

    # 4. skb_clone uses GFP_ATOMIC. Extract the second argument of the
    # first skb_clone call in the enqueue body.
    m = re.search(r"skb_clone\s*\([^,]+,\s*([A-Z_]+)\s*\)", enqueue_body)
    gfp_ok = bool(m) and m.group(1) == "GFP_ATOMIC"
    details.append(
        CheckDetail(
            check_name="skb_clone_uses_gfp_atomic",
            passed=gfp_ok,
            expected="skb_clone(..., GFP_ATOMIC)",
            actual=f"uses {m.group(1) if m else 'none'}",
            check_type="constraint",
        )
    )

    # 5. Clone return value NULL-checked. Extract the LHS of the clone
    # assignment and verify a NULL / !lhs guard follows.
    lhs_match = re.search(
        r"(\w+)\s*=\s*skb_clone\s*\(", enqueue_body
    )
    null_guard = False
    if lhs_match:
        name = re.escape(lhs_match.group(1))
        null_guard = bool(
            re.search(
                rf"if\s*\(\s*!\s*{name}\b|if\s*\(\s*{name}\s*==\s*NULL\b",
                enqueue_body,
            )
        )
    details.append(
        CheckDetail(
            check_name="skb_clone_return_null_checked",
            passed=null_guard,
            expected="if (!clone) / if (clone == NULL) after skb_clone",
            actual="guarded" if null_guard else "missing null check",
            check_type="constraint",
        )
    )

    # 6. skb_queue_tail in producer.
    tail_pushed = has_api_call(enqueue_body, "skb_queue_tail")
    details.append(
        CheckDetail(
            check_name="skb_queue_tail_called",
            passed=tail_pushed,
            expected="skb_queue_tail(&q, clone) in producer",
            actual="present" if tail_pushed else "missing",
            check_type="constraint",
        )
    )

    # 7. Worker uses skb_dequeue.
    worker_deq = has_api_call(worker_body, "skb_dequeue")
    details.append(
        CheckDetail(
            check_name="worker_uses_skb_dequeue",
            passed=worker_deq,
            expected="skb_dequeue(&q) inside worker",
            actual="present" if worker_deq else "missing",
            check_type="constraint",
        )
    )

    # 8. Worker uses consume_skb on the success path.
    worker_consume = has_api_call(worker_body, "consume_skb")
    details.append(
        CheckDetail(
            check_name="worker_uses_consume_skb_on_success",
            passed=worker_consume,
            expected="consume_skb(skb) in worker (not kfree_skb)",
            actual="present" if worker_consume else "missing",
            check_type="constraint",
        )
    )

    # 9. Worker MUST NOT call kfree_skb on the success path — if present
    # it signals wrong free fn for dropwatch instrumentation.
    worker_kfree = has_api_call(worker_body, "kfree_skb")
    details.append(
        CheckDetail(
            check_name="no_kfree_skb_on_success_path",
            passed=not worker_kfree,
            expected="kfree_skb absent from worker (use consume_skb)",
            actual="present" if worker_kfree else "clean",
            check_type="constraint",
        )
    )

    # 10. Exit calls skb_queue_purge AFTER cancel_work_sync.
    cancel_pos = exit_body.find("cancel_work_sync")
    purge_pos = exit_body.find("skb_queue_purge")
    order_ok = cancel_pos != -1 and purge_pos != -1 and cancel_pos < purge_pos
    details.append(
        CheckDetail(
            check_name="exit_cancels_work_then_purges_queue",
            passed=order_ok,
            expected="cancel_work_sync then skb_queue_purge in exit",
            actual=(
                f"order ok: cancel@{cancel_pos} < purge@{purge_pos}"
                if order_ok
                else f"WRONG order: cancel@{cancel_pos}, purge@{purge_pos}"
            ),
            check_type="constraint",
        )
    )

    # 11. Producer does NOT use GFP_KERNEL anywhere in its body.
    enqueue_has_gfp_kernel = "GFP_KERNEL" in enqueue_body
    details.append(
        CheckDetail(
            check_name="enqueue_not_using_gfp_kernel",
            passed=not enqueue_has_gfp_kernel,
            expected="producer body uses GFP_ATOMIC, not GFP_KERNEL",
            actual="clean" if not enqueue_has_gfp_kernel else "GFP_KERNEL used — unsafe in softirq",
            check_type="constraint",
        )
    )

    # 12. EXPORT_SYMBOL the producer.
    has_export = scoped_contains(generated_code, "EXPORT_SYMBOL(", scope="code_only")
    details.append(
        CheckDetail(
            check_name="producer_exported",
            passed=has_export,
            expected="EXPORT_SYMBOL(producer)",
            actual="present" if has_export else "missing",
            check_type="constraint",
        )
    )

    # 13. No cross-platform APIs.
    cross_plat = check_no_cross_platform_apis(
        generated_code, skip_platforms=["Linux_Userspace", "POSIX"]
    )
    details.append(
        CheckDetail(
            check_name="no_cross_platform_apis",
            passed=len(cross_plat) == 0,
            expected="No FreeRTOS / Zephyr / Arduino / STM32 HAL APIs",
            actual="clean" if not cross_plat else f"found: {[a for a, _ in cross_plat]}",
            check_type="constraint",
        )
    )

    return details
