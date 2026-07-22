#!/usr/bin/env python3
"""Sync the canonical .claude agents/skills from the Copier template to the repo root.

The copies under ``src/sdd_coders/template/.claude/`` are canonical; the root
``agents/`` and ``skills/`` directories are what ``.claude-plugin/plugin.json``
distributes as a Claude Code plugin. This script copies the canonical content
over the root copies and removes root entries that no longer exist upstream.

Usage:
    python scripts/sync_plugin.py           # apply the sync
    python scripts/sync_plugin.py --check   # report drift only; exit 1 if any
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "src" / "sdd_coders" / "template" / ".claude"

# (canonical source, root destination) pairs to keep in sync.
PAIRS = (
    (CANONICAL / "agents", REPO_ROOT / "agents"),
    (CANONICAL / "skills", REPO_ROOT / "skills"),
)


def _files(root: Path) -> dict[Path, Path]:
    """Map every file under ``root`` by its path relative to ``root``."""
    return {p.relative_to(root): p for p in root.rglob("*") if p.is_file()}


def diff_tree(src: Path, dst: Path) -> tuple[list[Path], list[Path]]:
    """Return (stale_or_missing, extra) relative paths in ``dst`` versus ``src``."""
    src_files = _files(src)
    dst_files = _files(dst)
    stale = [
        rel
        for rel, src_file in sorted(src_files.items())
        if rel not in dst_files or not filecmp.cmp(src_file, dst_files[rel], shallow=False)
    ]
    extra = sorted(rel for rel in dst_files if rel not in src_files)
    return stale, extra


def apply_sync(src: Path, dst: Path, stale: Sequence[Path], extra: Sequence[Path]) -> None:
    """Copy ``stale`` files from ``src`` to ``dst`` and delete ``extra`` files."""
    for rel in stale:
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, target)
    for rel in extra:
        (dst / rel).unlink()
    # Prune directories left empty by the removals, deepest first.
    dirs = (p for p in dst.rglob("*") if p.is_dir())
    for directory in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without writing; exit 1 if the root copies are out of sync",
    )
    args = parser.parse_args(argv)

    drifted = False
    for src, dst in PAIRS:
        label = dst.relative_to(REPO_ROOT)
        stale, extra = diff_tree(src, dst)
        if not stale and not extra:
            print(f"{label}/: in sync")
            continue
        drifted = True
        for rel in stale:
            print(f"{label}/{rel}: missing or stale")
        for rel in extra:
            print(f"{label}/{rel}: not in the canonical template (removable)")
        if not args.check:
            apply_sync(src, dst, stale, extra)
            print(f"{label}/: synced")

    if drifted:
        if args.check:
            print("Drift detected — run `python scripts/sync_plugin.py` to sync.")
            return 1
        print("Sync complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
