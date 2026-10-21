#!/usr/bin/env python3
"""Apply REQ-03 scope migration to check files.

Rewrites `"<needle>" in generated_code` → `scoped_contains(generated_code, "<needle>")`
in cases/*/checks/{static,behavior}.py, adding an `import` of
`scoped_contains` from `embedeval.check_utils` when it is missing.

Uses AST to find positions and does text-level replacement to preserve
formatting. Conservative: skips expressions whose surrounding line uses
backslash line-continuations or multi-line string literals that defeat
the simple line-based rewrite.

Usage:
    uv run python scripts/apply_scope_migration.py            # dry run
    uv run python scripts/apply_scope_migration.py --apply    # actually rewrite
    uv run python scripts/apply_scope_migration.py --apply --category dma

WARNING: Re-run `uv run pytest` after applying. Scope tightening MAY
flip TC verdicts in cases where checks deliberately matched identifiers
inside comments. Document any flips per user decision 2026-04-19 in
a BENCHMARK-DELTA-<date>.md.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RewriteSpan:
    lineno: int
    col_offset: int
    end_col_offset: int
    original: str
    replacement: str


RAW_CODE_NAMES = frozenset({"generated_code", "code"})


class _Finder(ast.NodeVisitor):
    def __init__(
        self, source_lines: list[str], default_scope: str = "code_only"
    ) -> None:
        self.source_lines = source_lines
        self.default_scope = default_scope
        self.spans: list[RewriteSpan] = []
        self.has_scoped_contains_import = False
        self.has_check_utils_import = False

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module == "embedeval.check_utils":
            self.has_check_utils_import = True
            for n in node.names:
                if n.name == "scoped_contains":
                    self.has_scoped_contains_import = True
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:  # noqa: N802
        if not (
            len(node.ops) == 1
            and isinstance(node.ops[0], ast.In)
            and isinstance(node.left, ast.Constant)
            and isinstance(node.left.value, str)
            and len(node.comparators) == 1
        ):
            self.generic_visit(node)
            return

        right = node.comparators[0]
        target = _name_of(right)
        if target not in RAW_CODE_NAMES:
            self.generic_visit(node)
            return

        needle = node.left.value
        start_col = node.col_offset
        end_col = getattr(node, "end_col_offset", None)
        end_line = getattr(node, "end_lineno", None)
        lineno = node.lineno

        # Bail on multi-line spans — replacement is line-based.
        if end_line is not None and end_line != lineno:
            self.generic_visit(node)
            return
        if end_col is None:
            self.generic_visit(node)
            return

        source_line = self.source_lines[lineno - 1]
        original = source_line[start_col:end_col]
        # Default scope chosen per file (see _scope_for_case). `code_only`
        # matches behavior.py's `strip_comments` idiom for C refs; `raw`
        # is used for Yocto .bb where `strip_comments` mis-strips `file://`
        # and `git://` URLs as C line comments.
        # ALWAYS emit the `scope=` arg explicitly — scoped_contains's own
        # default is `stripped`, which strips string literals and would
        # break `#include "driver/gpio.h"` style checks.
        scope = self.default_scope
        replacement = f"scoped_contains({target}, {needle!r}, scope={scope!r})"

        self.spans.append(
            RewriteSpan(
                lineno=lineno,
                col_offset=start_col,
                end_col_offset=end_col,
                original=original,
                replacement=replacement,
            )
        )
        self.generic_visit(node)


def _name_of(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


def _scope_for_case(path: Path) -> str:
    """Pick scope based on the case category.

    Yocto .bb files contain `file://` and `git://` URLs that `strip_comments`
    mis-interprets as `//` C line comments, silently deleting identifiers
    after the URL. For those, `scope='raw'` is the safe choice since .bb
    format has no C-style comments anyway — this is the REQ-03 semantics
    that "behavior.py's strip_comments idiom" was meant to approximate
    but subtly got wrong on non-C references.

    Same reasoning applies to udev `.rules` syntax (`linux-userspace-005`):
    comments use `#`, not `//`, and rules embed quoted tokens like
    `ATTRS{idVendor}=="1d6b"` that `strip_comments` would not mis-handle
    but `strip_string_literals` (the default `stripped` scope) would empty
    out — breaking checks that verify the literal is present. `raw`
    preserves the existing semantics exactly.

    Default is `code_only` (matches behavior.py idiom on C code).
    """
    case_id = path.parent.parent.name
    url_prefixed_prefixes = ("yocto-",)
    # udev rule TCs — extend this tuple as more land (linux-userspace-*-udev,
    # linux-userspace-014+, ...). Keeping explicit IDs rather than a
    # category lookup avoids a premature abstraction; n=1 today.
    udev_case_ids = ("linux-userspace-005",)
    if case_id.startswith(url_prefixed_prefixes) or case_id in udev_case_ids:
        return "raw"
    return "code_only"


def rewrite_file(path: Path, *, apply: bool) -> tuple[int, str | None]:
    """Rewrite one file. Returns (span_count, error_or_None)."""
    source = path.read_text()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return 0, f"syntax error: {exc}"

    lines = source.splitlines(keepends=True)
    scope = _scope_for_case(path)
    finder = _Finder([line.rstrip("\n") for line in lines], default_scope=scope)
    finder.visit(tree)

    if not finder.spans:
        return 0, None

    # Apply spans in reverse order per line so earlier rewrites don't
    # invalidate later col_offsets. Group spans by lineno.
    by_line: dict[int, list[RewriteSpan]] = {}
    for s in finder.spans:
        by_line.setdefault(s.lineno, []).append(s)

    new_lines = list(lines)
    for lineno, spans in by_line.items():
        line = new_lines[lineno - 1]
        has_newline = line.endswith("\n")
        body = line.rstrip("\n")
        # Rewrite from rightmost span to leftmost so indices stay valid.
        for s in sorted(spans, key=lambda x: x.col_offset, reverse=True):
            # Sanity: confirm the slice still matches what AST said.
            slice_ = body[s.col_offset : s.end_col_offset]
            if slice_ != s.original:
                # Something else modified this region; skip.
                continue
            body = body[: s.col_offset] + s.replacement + body[s.end_col_offset :]
        new_lines[lineno - 1] = body + ("\n" if has_newline else "")

    new_source = "".join(new_lines)

    # Inject import if needed and migration actually happened.
    if finder.spans and not finder.has_scoped_contains_import:
        new_source = _inject_import(new_source, finder.has_check_utils_import)

    # Validate the rewrite still parses.
    try:
        ast.parse(new_source, filename=str(path))
    except SyntaxError as exc:
        return 0, f"rewrite produced invalid python: {exc}"

    if apply and new_source != source:
        path.write_text(new_source)

    return len(finder.spans), None


def _inject_import(source: str, has_check_utils_import: bool) -> str:
    """Add `from embedeval.check_utils import scoped_contains`.

    Always adds a new single-line import rather than amending existing
    imports — amending multi-line `from X import (a, b, c)` imports is
    fragile and can produce invalid syntax. Python allows the same
    module to appear in multiple `from` statements.
    """
    new_import = "from embedeval.check_utils import scoped_contains\n"

    # If a line already exactly matches our target, nothing to do.
    if new_import in source:
        return source

    lines = source.splitlines(keepends=True)

    # Find insertion point by parsing the AST to get exact import end
    # lines. Insert after the last top-level `from`/`import` statement.
    try:
        tree = ast.parse(source)
    except SyntaxError:
        lines.insert(0, new_import)
        return "".join(lines)

    last_import_end = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end = getattr(node, "end_lineno", node.lineno)
            if end > last_import_end:
                last_import_end = end

    # AST lineno is 1-based. Insert AFTER last_import_end → index
    # last_import_end (0-based) in the lines list.
    if last_import_end == 0:
        # No imports — insert after module docstring if present.
        insert_at = 0
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            insert_at = getattr(tree.body[0], "end_lineno", 1)
    else:
        insert_at = last_import_end

    lines.insert(insert_at, new_import)
    return "".join(lines)


def iter_check_files(cases_root: Path, category: str | None) -> list[Path]:
    import sys as _sys

    _src = str(Path(__file__).parent.parent / "src")
    if _src not in _sys.path:
        _sys.path.insert(0, _src)
    from embedeval.runner import iter_case_dirs  # noqa: E402

    files: list[Path] = []
    for case_dir in iter_case_dirs(cases_root):
        if category and not case_dir.name.startswith(category):
            continue
        for name in ("static.py", "behavior.py"):
            p = case_dir / "checks" / name
            if p.is_file():
                files.append(p)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="cases", help="cases root")
    parser.add_argument("--category", help="filter to a category prefix")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="actually rewrite files (default: dry run)",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    cases_root = Path(args.cases).resolve()
    if not cases_root.is_dir():
        print(f"ERROR: cases dir not found: {cases_root}", file=sys.stderr)
        return 2

    total_spans = 0
    total_files = 0
    errors: list[tuple[Path, str]] = []
    for path in iter_check_files(cases_root, args.category):
        n, err = rewrite_file(path, apply=args.apply)
        if err:
            errors.append((path, err))
            continue
        if n > 0:
            total_spans += n
            total_files += 1
            if not args.quiet:
                print(
                    f"{'REWROTE' if args.apply else 'would rewrite'} {path}: {n} spans"
                )

    if not args.quiet:
        verb = "Rewrote" if args.apply else "Would rewrite"
        print(f"\n{verb} {total_spans} spans across {total_files} files")
        if errors:
            print(f"\n{len(errors)} file(s) failed:")
            for path, err in errors:
                print(f"  {path}: {err}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
