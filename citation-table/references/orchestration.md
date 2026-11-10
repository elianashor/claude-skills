# Orchestration — how a Cowork session runs this at scale

Design point: a 150-source table finishes in one session by parallelizing the mechanical work. Wall-clock is saved by fan-out, never by thinning a gate.

## Division of labor

**Parallelize the mechanical; serialize the judgment.** Subagent batches handle per-source work: retrieve → read in full → draft the row JSON → self-verify against the source. The orchestrator alone handles whole-table judgments: intake, the manuscript claims map, the schema, section keying, dedup adjudication, cross-source coherence, mode decisions, final QC gates, assembly, delivery. A subagent never decides schema or scope.

## State lives on disk, not in context

Before the first batch, create a run directory with: `runledger.md` (phase log + fix ledger; zero-pending is the exit), `rows/` (one JSON per source), `changelog.md` (every content edit, logged at the moment it is made), `decisions.md` (escalations: safe default applied, question logged — the run never blocks on a decision that belongs to the user), `verification.md` (per-row fresh-eyes results).

**Row-JSON contract (binding on every reading/drafting subagent):** one file `rows/<ID>.json` per source. Keys: the EXACT column header names from the mode's schema in schema.md (for the dated status column use the literal key `In draft`; the orchestrator canonicalizes it to the dated header at assembly), plus `detail_abstract`, `detail_relevance_rationale` (adverse rows: `detail_rationale`), `detail_verification_notes`, `hyperlink`, `read_depth`, `flags`. The orchestrator's assembly script maps ONLY these keys; an alias dict may catch strays, but a subagent emitting nonconforming keys is re-run, not silently mapped. Batches are sized to context; an interrupted run resumes from the ledger, not from memory. Apply rows to the workbook from JSON with a build script — never hand-edit accumulating sheets across turns.

## IDs and ownership

The orchestrator assigns stable row IDs at reference-inventory time, in section order, BEFORE any batching; subagents receive their IDs and never mint or renumber them. The orchestrator also owns the section-key map: batching prompts carry the authoritative TOC extract so no agent re-derives section numbers independently.

## Batching

- Retrieval+reading+drafting: 8–14 sources per subagent (14 proven at scale; drop toward 8 for long/dense sources like agency reports). Launch batches in parallel waves sized to the environment's limits.
- Tell every reading agent explicitly: escape inner quotes so the JSON parses; write the results file BEFORE running low on context; record read depth (`full` / `paywalled` / `unreachable: routes tried`) per source.
- The orchestrator spot-checks a sample of each batch's claims against the originals before accepting the batch (agent output is not the same as reading the sources), and notes distributed reading on the Method sheet.

## Fresh-eyes isolation (non-negotiable)

Verification and stress-testing are distinct roles run by subagents that receive the row, the source locator, and the QC standards — NEVER the drafting rationale, and never performed by the agent that drafted the row. Two passes: (1) per-row verification (quotes character-checked, figures to the decimal, pin cites, citation fields, link resolves, version match); (2) mode-appropriate stress-test (Mode A/B: the cross-exam question this row invites, the five standing checks, steelman — would this evidence fit the opposite world; Mode C: does our attack hold against the strongest reading). A final fresh-eyes auditor receives only the finished workbook and the action list/spec — not fix rationales — and confirms every item is reflected in the file before sign-off.

## Every subagent inherits the constitution

Paste the constitution block from SKILL.md verbatim into EVERY subagent prompt (reading, verification, stress-test, audit). A rule the orchestrator holds but a subagent never saw is a rule that will be broken. In particular: no invention (UNVERIFIED over guess), no identifier construction from memory, no paywall/CAPTCHA bypass, and the confidentiality rule (no party names, expert names, case numbers, or verbatim manuscript text in any external query — search sources by their own bibliographic details only).

## Workbook engineering

Copy, never edit, the original file; the original is the audit baseline. Snapshot the workbook after every phase (suffix a, b, c…) into a `snapshots/` subfolder — recovery is only possible from snapshots that exist. NEVER use openpyxl `insert_rows`/`delete_rows` on sheets containing merged rows — parse the sheet to an in-memory model, mutate the model, delete the sheet, rebuild it fresh; verify row counts and spot-check three rows after every structural change. Map agent-JSON header variants to canonical column names with an alias dict; re-apply hyperlinks in a dedicated pass; verify by reloading the saved file, not by trusting the write.

## Scripts — scope warning

`scripts/extract_footnotes.py` is a Mode A extraction AID: its `quotes.json` output is machine-trimmed with inserted ellipses — a LOCATOR, never table-ready text; every quotation is still located-read-transcribed by hand from the marked body text. `scripts/build_table.py` and `scripts/qc.py` implement only the simple Mode A `Citations` layout; for Mode B/C workbooks, WRITE the build and QC code fresh against references/schema.md (model-based sheet construction) and run `scripts/sweep_workbook.py` (schema-agnostic) for the mechanical gates. Never bend a workbook's structure to satisfy a legacy script.

## Retrieval routes

Exhaust before giving up: publisher site → doi.org → PubMed/PMC (BioC/eutils full-text APIs work; use them for character-verification) → Europe PMC → Google Scholar/SSRN/NBER/RePEc → OpenAlex/Semantic Scholar → agency archives (gao.gov, oversight.gov, ftc.gov, cdc.gov stacks, congress.gov) → author's institutional page. Known fetch-dead publisher domains (Wiley, Elsevier/ScienceDirect, INFORMS, LWW, Duke UP, jamanetwork): do not bypass; route to a lawful mirror (accepted manuscript, PMC deposit) or escalate to the user's pull list. "Tool-blocked domain" is not "paywalled" — record which.

Pull-list timing: the run never stalls on user retrieval. Finish everything else and deliver — affected sources absent from a Mode B table (listed on the pull list handed over at delivery) or carried as `○ Unverified` rows in Modes A/C. When the user later supplies PDFs, their intake is a new increment with its own verification and gates, not an open promise inside this run.

## Sequencing rules (learned the hard way)

1. Intake → manuscript ingestion (full read; build the section/paragraph claims map keyed to the REAL TOC) → reference inventory/corpus → acquisition+reading → row build → per-row self-verify → fresh-eyes verify → stress-test → assembly → gates → delivery. Rows are never built before the claims map exists (rows keyed to guessed sections all had to be redone).
2. In Mode A/QC work, deliver the table-level design verdict BEFORE row-by-row detail (design flaws invalidate row work).
3. Dedup BEFORE reading assignments (or the same source is read twice and written up inconsistently).
4. Draft-side problems (manuscript numbers with no source) go to the draft-side memo as proposed language — the skill never edits the manuscript.
5. Working sheets are archived and deleted at delivery, not before triage is complete.

## Fallback

If this skill is ever invoked somewhere without subagents, the core pipeline runs sequentially, and any verification that loses true fresh-eyes isolation is labeled reduced-isolation in the handoff — never silently faked.
