---
name: citation-table
description: >-
  Build or audit a litigation-grade citation table from a manuscript, expert
  report, or opposing expert's report. Fires on: "citation table", "cite
  check", "citation map", "audit the citations", "check the citations",
  "supporting authority table", "supplemental/additional supporting
  literature", "review the literature on X", "verify the sources", "does this
  source say what we cite it for", or a handed-over PDF with "what do its
  footnotes really support". Three modes: audit our own report's citations
  (survive opposing counsel's cite-check), build verified supporting authority
  for each claim in a draft (organized by report section, drop-in excerpts,
  limitations on every row), or attack an opposing report's citations (what
  each source actually proves, where it breaks, whether we hold a rebuttal).
  Produces a finished xlsx to a fixed schema: every source read in full,
  every quote character-verified with pin cites, every number traced to the
  source, funding/conflicts/rebuttals stated on the row face.
---

# Citation table (v2 — supersedes v1 entirely)

A citation table is a verification device, not a bibliography. Every row places what the source actually says next to what the manuscript claims (Mode A), what our draft needs (Mode B), or what the opposing expert asserts (Mode C). The finished product is judged by one test: it survives the scrutiny of a hostile professional reader, row by row, with zero corrections needed from the user.

## Constitution — carry into every subagent prompt verbatim

1. Never enter a source you have not opened and read in full. Abstract, title, another paper's description, or memory is not a read.
2. Invent nothing. Every assertion about a source comes from the source. Never construct a DOI/PMCID/URL from memory — resolve it and confirm the landing title matches.
3. UNVERIFIED is an honest answer, stated on the row face with its reason. Paywall is the only acceptable non-read reason (it excludes a source in Mode B; in Modes A/C the unread citation stays as an ○ Unverified row — see gate 14). Never bypass paywalls, CAPTCHAs, or access controls.
4. No shading. If honest reading weakens a row — or helps the other side — say so plainly. A weakness found now is a gift; found by opposing counsel, a disaster. A hole beats a bad patch.
5. Work on copies, never the original file; snapshot after every phase.
6. Confidentiality: no party names, expert names, case numbers, or verbatim manuscript text in any external query. Search sources by their own bibliographic details; search facts by generic content.
7. The source beats every earlier memo, spec, or review note. Claims never exceed the source's own hedges.

## Pipeline

Each stage names its mandatory reading. Do not draft ahead of the reading.

0. **Load context** — read `references/schema.md` and `references/modes.md` NOW, before intake.
1. **Intake** — one batched interview (the exact questions and the standing defaults are in modes.md). The only moment questions are allowed; afterward run autonomously: safe defaults applied, user-owned decisions logged to `decisions.md`, never blocking. If the user supplies an example file, IT overrides the schema — match it cell-for-cell and add no fields it lacks.
2. **Manuscript ingestion** — read the manuscript in full; build the claims map on disk: real TOC (numbers + exact heading text), sections → paragraphs → claims. In Mode A also extract every footnote (`scripts/extract_footnotes.py` — font-based separation; read its gap report). No row exists before the claims map does.
3. **Reference inventory** — Mode A/C: the manuscript's own citations, deduplicated (normalized author+year+title; near-matches flagged for judgment, never auto-merged — a working paper and its published version are different documents). Mode B: corpus search driven by the claims map and the case theory from intake (confidentiality rule applies to every query).
4. **Acquisition and reading** — fan out per `references/orchestration.md` (mandatory reading before the first batch launches): 8–14 sources per subagent, read-in-full, row JSON + read-depth to disk. Inaccessible high-priority sources go on a pull list for the user; their rows wait.
5. **Row build** — per the schema and the mode's per-row questions; every cell finished prose; excerpts located-read-transcribed, never window-extracted; drafting agent self-verifies against the source immediately after writing.
6. **Fresh-eyes verification** — every row re-verified by a subagent that never saw the drafting rationale (quotes character-level incl. typography, figures to the decimal, pin cites, links, version match).
7. **Stress-test** — mode-appropriate red team, fresh-eyes: five standing checks, the cross-exam question each row invites, steelman against our own thesis; adverse discoveries move rows to the adverse workbook or onto the row face.
8. **Assembly** — build the workbook from row JSONs by script (model-rebuild, never insert_rows on merged sheets); stable IDs; section-grouped, relevance-then-credibility sorted; Detail and Method sheets generated; adverse workbook built separately.
9. **QC gates** — read `references/qc-gates.md` and `references/failure-catalog.md` NOW, in full, then run every gate. `scripts/sweep_workbook.py` runs on every delivered workbook (any mode); `scripts/qc.py` adds legacy checks for the Mode A layout only, adapted to schema.md. Fix ledger to zero pending.
10. **Delivery** — read `references/style-guide.md` NOW: finished-product sweep (self-contained, no process residue, status blocks regenerated), companions updated in the same pass, the one-file-to-open named, transmittal blurb offered in her register, snapshots preserved, handoff notes listing anything UNVERIFIED and every decision logged in `decisions.md`.

## Modes (full spec in references/modes.md — mandatory at stage 0)

- **A — Own-report audit:** does every citation survive the cite-check opposing counsel will run; accuracy glyphs with named mismatches; HARD ERRORS list never buried; draft-side memo for manuscript-text problems (never edit the manuscript).
- **B — Supporting-authority build (default):** strongest verified evidence per claim, keyed to the draft's real sections; "In draft" status column; limitations on every row; adverse material to the separate internal workbook.
- **C — Opposing-report attack:** what their citation actually proves, what they omitted, whether the source itself is weak, and which of our rows rebuts it; honest about the rows that survive attack.
- Blends chosen at intake; audit material and supporting authority never fuse into one sheet.

## Non-negotiables that live above every stage

- The user's structural calls are final after one concise pushback; repeated instructions were already binding the first time.
- New user message mid-run preempts everything: stop, read, re-plan.
- Interim messages are progress-only; run to completion; never end a turn on a promise.
- Deliver the artifact that was asked for, to its schema — no invented labels, no scope drift, no diagnostic worksheet in place of the deliverable.
- Every claimed unit of coverage must be visibly locatable; partial verification is not "done".
- Counts and claims in anything user-facing are checked against the artifact before sending; process claims yes, unprovable superlatives no.

## Fallback

If invoked without subagents available, the pipeline runs sequentially; any verification that loses true fresh-eyes isolation is labeled reduced-isolation in the handoff — never silently faked.

## Files

| Path | Mandatory at stage |
|---|---|
| `references/schema.md` | 0 (before intake), again at 8 |
| `references/modes.md` | 0 (before intake) |
| `references/orchestration.md` | 4 (before first batch) |
| `references/qc-gates.md` | 9 (before gates) |
| `references/failure-catalog.md` | 5 (skim before row build), 9 (full) |
| `references/style-guide.md` | 5 (cell-prose section), 10 (full) |
| `references/retrieval-routes.md` | 4 (routes that work; blocked domains) |
| `scripts/extract_footnotes.py` | 2 (Mode A; its quotes.json is a locator aid, never table-ready text) |
| `scripts/build_table.py` + `scripts/qc.py` | 8–9, Mode A simple layout ONLY — for Mode B/C write build/QC code fresh from schema.md |
| `scripts/sweep_workbook.py` | 9 (mandatory on every delivered workbook, any mode) |
