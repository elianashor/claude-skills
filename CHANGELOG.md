# Changelog

All notable changes are recorded here. Versions follow [Semantic Versioning](https://semver.org).

## [1.0.0] - 2026-11-09

First packaged release.

### Added
- Claude Code plugin marketplace with two plugins: `citation-table` and `cheat-sheets`.
- `pincite` Python toolkit and CLI (`footnotes`, `build`, `sweep`, `qc`, `units`, `check`, `guard`, `lint`).
- `pincite build`: one schema-driven builder for supporting, audit, opposing and adverse workbooks, with a strict row-JSON contract and reload verification. Replaces the legacy Mode A-only table script.
- `pincite check`: pin-cite verification against DOCX (rebuilt Word auto-numbering, attached block quotes, footnotes), PDF and text sources; scanning of rendered sheets and tables; wrong-pin vs. phantom diagnosis; negative control.
- `pincite qc` is now schema-aware across all modes and adds unread-but-rated, process-residue, relevance-scale, venue-inflation and unearned-claim checks.
- `pincite guard`: confidentiality guard with a secret denylist, built-in legal-leak patterns, full-history scanning and masked CI output. Usable as a pre-commit hook in any repository.
- `pincite lint`: SKILL.md, plugin manifest, marketplace and vendored-script checks.
- CI on Linux, macOS and Windows across Python 3.10 to 3.13; release workflow with reproducible skill bundles, checksums and an opt-in PyPI trusted-publishing job.
- Synthetic examples and a test suite covering every command.

### Fixed
- Footnote extraction no longer fuses the last word of a wrapped or page-straddling footnote to the next line's first word.
- Running-header detection now identifies the header by page position, so repeated body text is never deleted as a header.

### Security
- All case-identifying material (parties, experts, file names, source titles, figures) removed from the published skills.
