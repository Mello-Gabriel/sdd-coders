"""Bring the spec-driven workflow into a repository that already has code.

``sdd-coders init`` scaffolds a whole new fullstack app from the bundled
template. ``adopt`` is the brownfield counterpart: it drops the agent roster,
the ``/sdd-*`` skills, the commit hooks and a **stack-agnostic** ``specs/``
skeleton into a repo that already has its own stack, and leaves everything else
alone.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from sdd_coders.scaffold import TEMPLATE_DIR

#: Stack-agnostic assets used only by ``adopt``. The template's own ``specs/``
#: is written against the fixed Next.js + FastAPI stack, so it cannot be reused
#: for a foreign repository.
ADOPT_ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "adopt"

#: Where Claude Code looks for a project's agents, skills, hooks and settings.
CLAUDE_DIR = ".claude"

#: Template ``.claude/`` subdirectories that carry no stack assumptions.
_TEMPLATE_CLAUDE_SUBDIRS = ("agents", "skills")

#: The one template hook that works unchanged in any repository.
_SHARED_HOOK = "secret-guard.sh"


@dataclass
class CopyReport:
    """What a copy pass did, as paths relative to the target repository."""

    added: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    overwritten: list[Path] = field(default_factory=list)

    def extend(self, other: CopyReport) -> None:
        """Fold ``other`` into this report."""
        self.added.extend(other.added)
        self.skipped.extend(other.skipped)
        self.overwritten.extend(other.overwritten)


def copy_file(source: Path, target: Path, *, base: Path, force: bool = False) -> CopyReport:
    """Copy one file, recording whether it was added, overwritten or skipped.

    Existing files are left untouched unless ``force`` is set — adopting must
    never clobber a repository's own work. ``base`` is the target repository
    root, used so the report shows paths the user recognises.
    """
    report = CopyReport()
    relative = target.relative_to(base)
    if target.exists():
        if not force:
            report.skipped.append(relative)
            return report
        report.overwritten.append(relative)
    else:
        report.added.append(relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    # copy2 preserves the executable bit the hook scripts rely on.
    shutil.copy2(source, target)
    return report


def copy_tree(src: Path, dst: Path, *, base: Path, force: bool = False) -> CopyReport:
    """Copy every file under ``src`` into ``dst``, recording what happened."""
    report = CopyReport()
    for source in sorted(p for p in src.rglob("*") if p.is_file()):
        target = dst / source.relative_to(src)
        report.extend(copy_file(source, target, base=base, force=force))
    return report


def adopt_project(target: Path, *, force: bool = False) -> CopyReport:
    """Install the agents, skills, hooks and ``specs/`` skeleton into ``target``.

    Only the parts of the template that are stack-agnostic are reused: the agent
    roster, the ``/sdd-*`` skills and the secret guard. The commit gate and the
    permission rules come from :data:`ADOPT_ASSETS_DIR` instead, because the
    template's versions are written against the fixed Next.js + FastAPI layout
    and would silently do nothing in a foreign repository.
    """
    report = CopyReport()
    for name in _TEMPLATE_CLAUDE_SUBDIRS:
        report.extend(
            copy_tree(
                TEMPLATE_DIR / CLAUDE_DIR / name,
                target / CLAUDE_DIR / name,
                base=target,
                force=force,
            )
        )
    report.extend(
        copy_file(
            TEMPLATE_DIR / CLAUDE_DIR / "hooks" / _SHARED_HOOK,
            target / CLAUDE_DIR / "hooks" / _SHARED_HOOK,
            base=target,
            force=force,
        )
    )
    report.extend(copy_tree(ADOPT_ASSETS_DIR, target, base=target, force=force))
    return report
