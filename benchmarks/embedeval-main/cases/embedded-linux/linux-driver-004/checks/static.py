"""Static analysis checks for interrupt-driven character device driver."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate IRQ char device code structure."""
    details: list[CheckDetail] = []

    has_module_h = scoped_contains(generated_code, 'linux/module.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="module_header",
            passed=has_module_h,
            expected="linux/module.h included",
            actual="present" if has_module_h else "missing",
            check_type="exact_match",
        )
    )

    has_interrupt_h = scoped_contains(generated_code, 'linux/interrupt.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="interrupt_header",
            passed=has_interrupt_h,
            expected="linux/interrupt.h included",
            actual="present" if has_interrupt_h else "missing",
            check_type="exact_match",
        )
    )

    has_wait_h = scoped_contains(generated_code, 'linux/wait.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="wait_header",
            passed=has_wait_h,
            expected="linux/wait.h included",
            actual="present" if has_wait_h else "missing",
            check_type="exact_match",
        )
    )

    has_spinlock_h = scoped_contains(generated_code, 'linux/spinlock.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="spinlock_header",
            passed=has_spinlock_h,
            expected="linux/spinlock.h included",
            actual="present" if has_spinlock_h else "missing",
            check_type="exact_match",
        )
    )

    has_request_irq = scoped_contains(generated_code, 'request_irq', scope='code_only')
    details.append(
        CheckDetail(
            check_name="request_irq_called",
            passed=has_request_irq,
            expected="request_irq() called in init",
            actual="present" if has_request_irq else "missing",
            check_type="exact_match",
        )
    )

    has_irq_handler = scoped_contains(generated_code, 'irqreturn_t', scope='code_only')
    details.append(
        CheckDetail(
            check_name="irq_handler_defined",
            passed=has_irq_handler,
            expected="IRQ handler with irqreturn_t signature",
            actual="present" if has_irq_handler else "missing",
            check_type="exact_match",
        )
    )

    has_wait_queue = (
        scoped_contains(generated_code, 'wait_queue_head_t', scope='code_only')
        or scoped_contains(generated_code, 'DECLARE_WAIT_QUEUE_HEAD', scope='code_only')
        or scoped_contains(generated_code, 'init_waitqueue_head', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="wait_queue_declared",
            passed=has_wait_queue,
            expected="wait_queue_head_t declared and initialized",
            actual="present" if has_wait_queue else "missing",
            check_type="exact_match",
        )
    )

    return details
