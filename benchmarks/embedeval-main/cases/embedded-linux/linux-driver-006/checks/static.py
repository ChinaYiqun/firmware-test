"""Static analysis checks for Linux ioctl driver."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate ioctl driver code structure."""
    details: list[CheckDetail] = []

    has_ioctl_h = scoped_contains(generated_code, 'linux/ioctl.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="ioctl_header_included",
            passed=has_ioctl_h,
            expected="linux/ioctl.h included",
            actual="present" if has_ioctl_h else "missing",
            check_type="exact_match",
        )
    )

    has_uaccess = scoped_contains(generated_code, 'linux/uaccess.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uaccess_header_included",
            passed=has_uaccess,
            expected="linux/uaccess.h included",
            actual="present" if has_uaccess else "missing",
            check_type="exact_match",
        )
    )

    has_magic = scoped_contains(generated_code, '_IOW(', scope='code_only') or scoped_contains(generated_code, '_IOR(', scope='code_only') or scoped_contains(generated_code, '_IO(', scope='code_only') or scoped_contains(generated_code, '_IOWR(', scope='code_only')
    details.append(
        CheckDetail(
            check_name="ioctl_command_defined",
            passed=has_magic,
            expected="ioctl command defined with _IOW/_IOR/_IO/_IOWR macro",
            actual="present" if has_magic else "missing",
            check_type="exact_match",
        )
    )

    has_unlocked_ioctl = scoped_contains(generated_code, 'unlocked_ioctl', scope='code_only')
    details.append(
        CheckDetail(
            check_name="unlocked_ioctl_in_fops",
            passed=has_unlocked_ioctl,
            expected=".unlocked_ioctl in file_operations",
            actual="present" if has_unlocked_ioctl else "missing",
            check_type="exact_match",
        )
    )

    has_license = scoped_contains(generated_code, 'MODULE_LICENSE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="module_license",
            passed=has_license,
            expected="MODULE_LICENSE defined",
            actual="present" if has_license else "missing",
            check_type="exact_match",
        )
    )

    return details
