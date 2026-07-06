r"""Count physical lines in a large DSV/CSV-style file without loading it into memory.

Usage:
    python count_dsv_lines.py "C:\path\to\file.dsv"

This counts newline-delimited lines efficiently in binary chunks, so it is
safe to use on multi-gigabyte files.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def count_lines(path: Path, chunk_size: int = 8 * 1024 * 1024) -> int:
    """Count physical lines by scanning the file in binary chunks."""

    line_count = 0
    last_byte = b""

    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(chunk_size), b""):
            line_count += chunk.count(b"\n")
            last_byte = chunk[-1:]

    if path.stat().st_size > 0 and last_byte not in {b"\n", b""}:
        line_count += 1

    return line_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Count lines in a large DSV/CSV-style file efficiently."
    )
    parser.add_argument("path", type=Path, help="Path to the DSV/CSV file")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=8 * 1024 * 1024,
        help="Read size in bytes for each pass (default: 8388608)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    path = args.path
    if not path.exists():
        parser.error(f"File not found: {path}")
    if not path.is_file():
        parser.error(f"Not a file: {path}")

    total_lines = count_lines(path, chunk_size=args.chunk_size)
    print(f"{total_lines:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())