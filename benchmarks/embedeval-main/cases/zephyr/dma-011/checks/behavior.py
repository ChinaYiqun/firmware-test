"""Behavioral checks for dma-011."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    has_device_ready = scoped_contains(generated_code, 'device_is_ready', scope='code_only')
    details.append(
        CheckDetail(
            check_name="device_ready_check",
            passed=has_device_ready,
            expected="device_is_ready() called on DMA device",
            actual="present" if has_device_ready else "missing",
            check_type="constraint",
        )
    )

    return details
