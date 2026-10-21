"""Static analysis checks for Linux character device driver."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate Linux driver code structure."""
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

    has_fs_h = scoped_contains(generated_code, 'linux/fs.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="fs_header",
            passed=has_fs_h,
            expected="linux/fs.h included",
            actual="present" if has_fs_h else "missing",
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

    has_fops = scoped_contains(generated_code, 'file_operations', scope='code_only')
    details.append(
        CheckDetail(
            check_name="file_operations_struct",
            passed=has_fops,
            expected="struct file_operations defined",
            actual="present" if has_fops else "missing",
            check_type="exact_match",
        )
    )

    has_init = scoped_contains(generated_code, 'module_init', scope='code_only')
    has_exit = scoped_contains(generated_code, 'module_exit', scope='code_only')
    details.append(
        CheckDetail(
            check_name="init_exit_macros",
            passed=has_init and has_exit,
            expected="module_init() and module_exit() macros",
            actual=f"init={has_init}, exit={has_exit}",
            check_type="exact_match",
        )
    )

    return details
