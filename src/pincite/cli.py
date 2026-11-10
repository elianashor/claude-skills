"""`pincite` command line: one entry point for every tool in the package."""

from __future__ import annotations

import importlib
import sys

from . import __version__

COMMANDS = {
    "footnotes": ("footnotes", "main", "extract footnotes, exact marker positions and citing sentences from a PDF"),
    "build": ("workbook", "main", "build a citation-table workbook (supporting/audit/opposing/adverse) from row JSON"),
    "sweep": ("sweep", "main", "mechanical integrity sweep of every cell in a workbook (gates 1-4)"),
    "qc": ("qc", "main", "semantic QC: quotes, bare flags, unread-but-rated rows, residue, relevance"),
    "check": ("pincheck", "main", "verify pin-cited facts against the source, with a negative control"),
    "units": ("pincheck", "main", "show a source's reconstructed paragraph/page/note numbering"),
    "guard": ("guard", "main", "fail if confidential case material appears in the repo"),
    "lint": ("lint", "main", "lint skills, plugin manifests, the marketplace and vendored scripts"),
}


def _usage() -> str:
    width = max(map(len, COMMANDS))
    rows = "\n".join(f"  {k:<{width}}  {v[2]}" for k, v in COMMANDS.items())
    return f"pincite {__version__}\n\nusage: pincite <command> [args]\n\ncommands:\n{rows}\n"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(_usage())
        return 0
    if argv[0] in ("-V", "--version"):
        print(__version__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd not in COMMANDS:
        print(f"unknown command {cmd!r}\n\n{_usage()}", file=sys.stderr)
        return 2
    module, func, _ = COMMANDS[cmd]
    entry = getattr(importlib.import_module(f"pincite.{module}"), func)
    if cmd in ("check", "units"):
        rest = [cmd, *rest]
    return int(entry(rest) or 0)


if __name__ == "__main__":
    sys.exit(main())
