# QC gates — hard acceptance checklist

The table does not ship until every gate passes. Gates never thin because the table is long or the deadline near. Run gates 1–10 programmatically where possible (script the sweeps), 11–20 by fresh-eyes subagent review. Record every gate's result in the verification report on disk.

## Cell integrity (programmatic sweeps over every sheet, every cell)

1. **No truncation anywhere.** No cell ends mid-word, mid-sentence, or mid-citation; no cell ends in a comma, an open quote, a hyphenated fragment, or a dangling "compariso."-style stub. Explicit whole-workbook final sweep — this is the flagship historical defect and it recurred twice after being "fixed." Procedure: run `scripts/sweep_workbook.py <file>` on EVERY delivered workbook (main + adverse); it checks every cell of every sheet and defines what counts as truncated. Zero unexplained findings to pass; a consciously-accepted finding is listed in the run ledger with its reason.
2. **Finished prose.** Complete sentences, initial capitals, closed quotes/parentheses, no double spaces, no stray field labels ("Background:", "Objective:", "Design:") in any cell.
3. **No generation artifacts.** No reviewer/agent notes, TODOs, placeholders, internal jargon ("escalated", "per QC pass"), or template boilerplate repeated across rows; no stale status blocks (any status/limits text is regenerated at delivery, never carried from an earlier date).
4. **Structural integrity.** Row count per sheet matches the ledger; every main-sheet ID has exactly one Detail row and vice versa; no blank required cells; section-header merges intact; hyperlinks present and resolvable on every Citation cell; no orphaned working sheets left in the workbook.

## Source fidelity (per row, fresh-eyes verified)

5. **One row, one source.** No hybrid citations, no commentary grafted onto a study's line, no excerpt attributed to a different document than the row cites.
6. **Quotes verbatim.** Every quotation character-checked against the source, typography included; every ellipsis marks a real cut; every pin cite points where it says.
7. **Figures are the source's figures**, checked to the decimal, with the statistic type checked (R vs R²) and what the number is OF checked (a saving to one party ≠ a saving to another). No number in the table that cannot be pointed to at a location in the source. Phantom figures are the cardinal sin.
8. **Claims at source strength.** No claim stated stronger than the source's own hedges; observational studies never carry causal language the authors disclaimed.
9. **Version discipline.** Working-paper vs published-version drift checked; the version cited is the version quoted; if a published version exists, its figures were compared (published versions drop or change results).
10. **Citation completeness.** Right authors, year, venue, pages, identifier; one citation style throughout; working hyperlink plus durable locator.

## Honesty and risk (per row)

11. **Five standing checks run on every row:** (a) cited against its own conclusion; (b) undisclosed funding/authorship interest — hardest on sources favorable to our side; (c) superseded or withdrawn authority (agency withdrawals, corrections, errata); (d) false independence (corroborating studies tracing to one reference list); (e) figure fidelity (gate 7).
12. **Limitations column present and honest on every row** — funding, conceded limits, later rebuttals, cross-exam exposure. Never silently dropped, never thinned to make a row look better.
13. **Both edges carried.** Any source with results cutting both ways shows both on its face, or is excluded.
14. **Read-in-full only — scoped by mode.** No row is ever WRITTEN from an abstract, title, or another paper's description. Mode B (we choose the evidence): an unread source does not enter the deliverable at all — working queue/pull list only; paywall is the only acceptable non-read reason and is stated there. Modes A and C (the manuscript chooses the sources): every citation gets a row regardless of accessibility, but an unread source's row carries `○ Unverified` + the reason and asserts NO accuracy judgment or summary — coverage without invention. In all modes, partial verification is labeled on the row face. On `○ Unverified` rows, any cell that would require reading the source carries the literal text "Not assessed — source unread (<reason>)" — never synthesized content.
15. **Honest labels.** Credibility never venue-inflated; relevance is case fit with a written rationale; mandated-inclusion rows carry their disclosures; NO CURRENT ANCHOR and placeholder-dependent labels applied where earned.

## Alignment (whole-table judgments, orchestrator-level)

16. **Section keys verified against the manuscript's actual TOC** — every header number and title matched to the real document; no invented headers; nonexistent sections impossible.
17. **Adverse segregation.** Nothing on the supporting sheet primarily helps the other side; adverse workbook rows each carry an anticipation strategy that does not stop mid-thought.
18. **Cross-source coherence.** No internal contradictions between rows left unflagged; no false-independence clusters presented as triangulation; every "In draft" status re-checked against the manuscript version named in the header.
19. **Ledger zero.** The fix ledger has zero pending lines; every finding from any QC pass is resolved in the file or escalated in the decisions memo with a safe default applied.
20. **Delivery pack.** Method sheet regenerated and current; deliverable fully self-contained (zero references to internal documents or names — grep-sweep for memo names, "ask-", "QC", "intake", "pull list", "hold", personal names); companion documents updated in the same pass; the adverse INTERNAL workbook delivered alongside (to the user, never third parties) and swept by the same gates; the one file to open named to the user; snapshots preserved; original untouched; any transmittal text reviewed per style-guide (counts against the artifact; attachment filename matches the current deliverable).

## Failure response

A failed gate reopens the row (or the workbook), fixes, re-verifies fresh-eyes, and re-runs the affected gates. Never soften a finding to pass a gate; never re-rate ⚠→◐ to improve the tally. If a fix cannot be completed lawfully, the row carries the honest label or leaves the table — a hole beats a bad patch.
