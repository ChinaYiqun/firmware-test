"""Static analysis checks for Linux proc file driver."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate proc file driver code structure."""
    details: list[CheckDetail] = []

    has_proc_h = scoped_contains(generated_code, 'linux/proc_fs.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="proc_fs_header",
            passed=has_proc_h,
            expected="linux/proc_fs.h included",
            actual="present" if has_proc_h else "missing",
            check_type="exact_match",
        )
    )

    has_seq_h = scoped_contains(generated_code, 'linux/seq_file.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="seq_file_header",
            passed=has_seq_h,
            expected="linux/seq_file.h included",
            actual="present" if has_seq_h else "missing",
            check_type="exact_match",
        )
    )

    has_proc_ops = scoped_contains(generated_code, 'proc_ops', scope='code_only')
    details.append(
        CheckDetail(
            check_name="proc_ops_struct_used",
            passed=has_proc_ops,
            expected="struct proc_ops defined (modern kernel API)",
            actual="present" if has_proc_ops else "missing (outdated file_operations?)",
            check_type="exact_match",
        )
    )

    has_proc_create = scoped_contains(generated_code, 'proc_create', scope='code_only')
    details.append(
        CheckDetail(
            check_name="proc_create_called",
            passed=has_proc_create,
            expected="proc_create() called in init",
            actual="present" if has_proc_create else "missing",
            check_type="exact_match",
        )
    )

    has_seq_printf = scoped_contains(generated_code, 'seq_printf', scope='code_only')
    details.append(
        CheckDetail(
            check_name="seq_printf_used",
            passed=has_seq_printf,
            expected="seq_printf() used to write proc output",
            actual="present" if has_seq_printf else "missing",
            check_type="exact_match",
        )
    )

    return details
