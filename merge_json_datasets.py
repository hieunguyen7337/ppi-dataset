"""Utility to merge per-dataset JSONL files into unified train/test splits.

This script scans an input directory for JSON files that match train/test
patterns (by default, filenames containing ``train`` or ``test``) and
concatenates them into two aggregated JSONL outputs. It assumes each source
file is structured with one JSON object per line, as in ``test_0.json``.

Example usage:
    python merge_json_datasets.py \
        --input-dir json_output \
        --output-train unified_train.json \
        --output-test unified_test.json
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List


def collect_files(directory: Path, pattern: str, output_names: Iterable[Path]) -> List[Path]:
    """Return files in *directory* matching *pattern* while excluding outputs.

    Args:
        directory: Directory to scan.
        pattern: Glob pattern (e.g., ``"*train*.json"``).
        output_names: Paths to exclude from the results to avoid self-merging.

    Returns:
        Sorted list of matching files.
    """
    excluded = {path.resolve() for path in output_names}
    files = [
        path
        for path in sorted(directory.glob(pattern))
        if path.is_file() and path.resolve() not in excluded
    ]
    return files


def merge_jsonl(files: Iterable[Path], output_path: Path) -> int:
    """Merge JSONL files into a single output file.

    Blank lines are skipped, and the order of files is preserved.

    Args:
        files: Iterable of JSONL files to merge.
        output_path: Destination file.

    Returns:
        Number of lines written to *output_path*.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines_written = 0
    with output_path.open("w", encoding="utf-8") as outfile:
        for file_path in files:
            with file_path.open("r", encoding="utf-8") as infile:
                for line in infile:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    outfile.write(stripped + "\n")
                    lines_written += 1
    return lines_written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("json_output"),
        help="Directory containing per-dataset train/test JSONL files.",
    )
    parser.add_argument(
        "--train-pattern",
        default="*train*.json",
        help="Glob pattern for train files inside the input directory.",
    )
    parser.add_argument(
        "--test-pattern",
        default="*test*.json",
        help="Glob pattern for test files inside the input directory.",
    )
    parser.add_argument(
        "--output-train",
        type=Path,
        default=Path("unified_train.json"),
        help="Output path for the merged train JSONL file.",
    )
    parser.add_argument(
        "--output-test",
        type=Path,
        default=Path("unified_test.json"),
        help="Output path for the merged test JSONL file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir

    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {input_dir}")

    output_paths = [args.output_train, args.output_test]
    train_files = collect_files(input_dir, args.train_pattern, output_paths)
    test_files = collect_files(input_dir, args.test_pattern, output_paths)

    if not train_files:
        raise SystemExit(f"No train files matched pattern '{args.train_pattern}' in {input_dir}")
    if not test_files:
        raise SystemExit(f"No test files matched pattern '{args.test_pattern}' in {input_dir}")

    train_count = merge_jsonl(train_files, args.output_train)
    test_count = merge_jsonl(test_files, args.output_test)

    print(f"Merged {len(train_files)} train files into {args.output_train} ({train_count} lines)")
    print(f"Merged {len(test_files)} test files into {args.output_test} ({test_count} lines)")


if __name__ == "__main__":
    main()
