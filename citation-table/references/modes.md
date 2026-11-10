# Modes and intake

Purpose is a first-class parameter. Every row answers mode-specific questions; every pipeline stage re-consults the mode. All modes share the verification core (read in full, verbatim quotes, figures to the decimal, five standing checks, Limitations discipline).

## Mode A — Own-report audit (cite-check of our side's manuscript)

Goal: every citation in the manuscript survives the cite-check opposing counsel will run. Per-row questions: Is the citation correct (authors/year/venue/pages/version/link)? Does the source actually support the attached proposition, at the strength claimed? What does citing it cost on cross (funding, concessions, rebuttals)? Did the manuscript's numbers come from this source, to the decimal?
Column emphases: the Accuracy verdict is the spine — glyphs `✓ Accurate` / `◐ Partial` / `⚠ Issue` / `○ Unverified`, and anything other than ✓ names the specific mismatch in a sentence (bare glyphs forbidden). Citing sentence quoted verbatim with every footnote number. Output additionally carries a `HARD ERRORS FOUND` list (one line each: location → what the manuscript says → what the source says) — never buried — and a draft-side memo of proposed conforming edits (the skill NEVER edits the manuscript itself; drafter-owned numbers with no source get "no source exists — re-source or delete" entries).
Severity triage on findings: 🔴 fatal (wrong citation, misquoted source, claim the source doesn't support, source that helps the other side) · 🟡 material (overstated finding, stale data, weak fit, credibility overrated) · ⚪ cosmetic.

## Mode B — Supporting-authority build (the default; the shipped table's mode)

Goal: for each claim the manuscript advances, the strongest verified evidence available, drop-in ready. Per-row questions: What claim does this carry, and in which section does it belong (verified against the actual TOC)? How exactly would we use it — which sentence, with what mandatory scope limits? Which verbatim excerpt would we quote? What are its limitations, conflicts, and later rebuttals? Case-fit relevance 1–5 and honest credibility? Is it already cited in the current draft (the "In draft" column)?
Column emphases: full 13-column schema (references/schema.md). The Limitations column is the value center — a weakness found now is a gift; found by opposing counsel, a disaster. Both-edges rule: a source whose results cut both ways carries both on the row, or is not citable at all. Sources that primarily help the other side NEVER enter the supporting sheet — they go to the adverse workbook. The opposing party's own expert reports are never citable authority rows.

## Mode C — Opposing-report attack (their expert's citations)

Goal: what does each citation actually prove, and where does it break. Per-row questions: What claim is the opposing report using this source for? Read in full, does the source say that — at that strength? What did they omit (adverse findings inside their own source, conceded limits, funding)? Is the source itself weak (design, sample, superseded, withdrawn)? Do we hold a direct rebuttal citation, and which row is it?
Column emphases: replace `How we would use it` with `How they use it / what it actually proves`; replace `Proposed excerpt` with `Their quote vs. the source` (their language next to the source's, mismatches flagged); add `Rebuttal available` (cross-reference to our supporting rows or "none — needs new source"). Keep Limitations, Data, Methods, Relevance (fit to THEIR argument), Credibility. Steelman honestly: rows that survive attack are marked "engage on the merits — cannot be answered by credibility attack," with the engagement strategy spelled out.

## Blends

A manuscript needing more than one mode gets mode assigned per deliverable, chosen at intake (e.g., Mode B table now + Mode A audit later as separate deliverables — never fused into one sheet; the shipped project's lesson is that mixing audit material into a supplemental table confuses the recipient). If the user asks for a blend inside one workbook, adverse/audit material still lives on separate sheets from supporting authority.

## Literature-review variant (no manuscript)

Mode B without a claims map: column D becomes the research question the source answers; grouping by topic instead of report section. Chain highly relevant papers both directions (their references; papers citing them) and state in Method where chaining stopped.

## Intake interview — the only moment for questions

Ask ONE batched set at the start; nothing settled by this skill is re-asked; after intake, zero questions — run on the skill's rules and judgment, applying safe defaults and logging escalations to the decisions memo instead of stopping. Ask only what is table-specific:

0. Before asking anything: verify every named input actually exists at its stated path. If a controlling input is missing, stop and report exactly what is missing — do not improvise around it.
1. Manuscript and scope: which document, which sections, by their real numbering; the manuscript's version DATE (it becomes part of the "In draft" column header and every draft-relative claim); is a newer draft coming.
2. Mode: A audit / B supporting build / C opposing attack / blend — and for C, which opposing report(s).
3. What the case/matter is about — the theory each side is running (relevance scoring is impossible without it; do not assume it from the manuscript's subject area).
4. Recipient and register: expert's own prep vs. third parties (consultants/counsel) vs. may enter the record. Sets voice and how conservative the claims are.
5. Deadline, and whether court-set.
6. Access: are source PDFs in hand (which folder), is there a library-proxy human in the loop for paywalled items, any documents under protective order.
7. Format deviations from references/schema.md, if any (the schema is the default; the user's example file, if provided, overrides it — match the example cell-for-cell and add no fields it lacks).
8. Deduplication default (one row per unique source) and output filename — confirm, don't assume.
9. Anything the user already knows they want included by direction (mandated sources get honest labels and disclosures, never silent inclusion).

If the user's intake answers are silent on any item, do NOT ask again: apply the standing default, state the applied default in the run's decisions memo, and proceed. If she is silent on case theory (item 3), derive a working theory from the manuscript's own argument structure, log it as an assumption in the decisions memo, and flag it at delivery.

Mandated-inclusion rows (item 9): record on the row face that the source is accurately cited AND separately whether it carries weight/impeachment cost — the two judgments never merge (an accurately-cited source with a withdrawal notice "survives cite-check" but costs weight; say both).

Standing defaults applied WITHOUT asking: xlsx output; workbook structure per schema.md; adverse material separate; stable IDs; section-grouped sort with relevance-then-credibility within group; UNVERIFIED labeling; confidentiality rules; copies-not-originals; snapshots.
