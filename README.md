# Claude skills

Agent skills I built for research, litigation support, and study work. Each folder is a self-contained skill with a `SKILL.md` that Claude (or any harness that reads skill-style instructions) loads on demand.

| Skill | What it does |
|---|---|
| [`citation-table`](citation-table/) | Builds or audits a litigation-grade citation table from an expert report: every source read in full, every quote character-verified with pin cites, every number traced, limitations stated on each row. Ships as an `.xlsx` with QC scripts. |
| [`cheat-sheet`](cheat-sheet/) | Builds a pin-cited cheat sheet PDF from any source material. Covers testimony prep, answering an opposing document, multi-document sets, and a study mode for course material. |
| [`teaching-cheat-sheet`](teaching-cheat-sheet/) | Teaches one section of an authoritative source to a reader who must perform from memory: story page, module summaries, audited diagrams, expected challenges with spoken answers. |
| [`prep-sheet`](prep-sheet/) | A lighter one-section teaching sheet that works from whatever the user provides and folds format corrections back into itself. |
| [`expert-report-section-cheat-sheet`](expert-report-section-cheat-sheet/) | The testimony-prep version for one section of a testifying expert's report, driven by the trial team's mock cross-examination. |

## Install

Copy a skill folder into your skills directory (for Claude Code, `~/.claude/skills/`), or upload it as a custom skill in Claude.

## Note on confidentiality

These skills were developed on real client work. Case names, parties, file names, source titles, and figures have been removed, and the skills themselves forbid carrying case content into their own files.
