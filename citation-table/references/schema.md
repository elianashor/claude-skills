# Schema — derived from the shipped final table

Ground truth: the first shipped supporting-authority workbook and its internal adverse-evidence companion, extracted programmatically. Where this file and any other description disagree, this file wins. Read this file BEFORE writing the first row.

## Workbook shape

Submission workbook (what the recipient gets): **Supporting Authority · Detail · Method** — three sheets, nothing else. Adverse material lives in a SEPARATE internal workbook, never in the submission file unless the user says otherwise at intake. Working sheets (open-studies queues, pull lists, hold areas) exist only during the build and are archived off-workbook (CSV) and deleted before delivery.

## Sheet 1 — Supporting Authority (13 columns, A–M)

Layout: row 1 title · row 2 reading-standard note (italic, 9pt) · row 3 column headers · row 4+ data grouped under section-header band rows. Freeze panes at C4 (ID and Citation stay visible). Column widths: A=6, B=36, C=34, D=34, E=36, F=38, G=38, H=38, I=30, J=28, K=9, L=26, M=30.

- Row 1 (A1, merged A:M): title, bold 14pt. Pattern: `<Deliverable name> — <matter descriptor>` (e.g., "Additional Supporting Literature — Defense Expert Report"). The deliverable name is the USER'S choice — never finalize a title she hasn't adopted.
- Row 2 (merged A:M, italic 9pt, wrapped): one-paragraph standard note: every source opened and read in full; grouped by the report's actual TOC; placeholder-dependent rows say so; excerpt column verbatim; relevance is case fit not venue prestige.
- Row 3: headers, bold 10pt, fill D9E2F3 (light blue), wrap, centered both ways.
- Section headers: one merged row A:M per report section, text `§ <number> — <exact heading text from the manuscript TOC>`, bold, white text on 1F4E79 (dark blue) fill. Special headers used when earned: `§ <N> — … (subsections not yet drafted)` for placeholder-dependent groups; `NO CURRENT ANCHOR — included for completeness; not recommended for citation in the report` as the last group for user-mandated rows with no draft anchor.
- Data rows: Calibri 10, wrap_text=True, vertical=top on all prose cells. ID cell bold. Row heights auto/~52pt typical.

Column spec (typical cell lengths from the shipped table: median/max chars):

| Col | Header | Contents | Len (med/max) |
|---|---|---|---|
| A | ID | Stable row ID `S01`… assigned once, never renumbered; gaps from consolidation stay and are explained on Method. Bold. | 3 |
| B | Citation | Full citation: authors (surname, initials), (year), title, venue, vol/pages, identifier (DOI/report no.). HYPERLINK embedded on the cell (target = durable open-access URL or DOI), font color 0563C1. Version cited = version quoted. | 294/1478 |
| C | What this source is | 1–3 sentences: document type, who produced it, what it examined. Not the abstract. | 260/538 |
| D | Claim it supports | The specific proposition from the manuscript this source carries — scoped to what the source honestly supports, never stronger than the source's own hedges. | 433/835 |
| E | How we would use it | Section anchor (§ + ¶ refs where known), what sentence/argument it serves, and the scope limits that must accompany any citation. | 1157/2105 |
| F | Findings | The source's actual results with numbers, each pin-cited (page/table/figure). Every number must be pointable-to in the source. | 1069/2897 |
| G | Proposed excerpt (verbatim) | Drop-in quotation(s), character-verified against the source including typography, with pin cite. Complete clauses only; every ellipsis marks a real cut. Selection rule: among candidate passages, choose the one that most directly verbalizes the claim AS THE MANUSCRIPT PHRASES IT (mirror the draft's own framing words where the source offers a passage that does), then add secondary quotes only if they carry distinct load. | 630/1445 |
| H | Limitations / conflicts / later rebuttals | The risk column — NEVER dropped or thinned: funding/COI (source's own disclosure, quoted), conceded limitations, later rebuttals/corrections, cross-exam exposure, version-drift notes, UNVERIFIED labels with reason. Longest column by design. | 2989/6839 |
| I | Data | Sample, population, period, jurisdiction, N. | 434/993 |
| J | Methods / test | Study design / analytic method, stated plainly (e.g., "interrupted time series", "narrative review; no statistical analysis"). | 392/1057 |
| K | Relevance | Integer 1–5, case fit ONLY (venue prestige forbidden as input). Calibration: 5 = directly decides a contested, case-central proposition with the case's subject matter in its data; 4 = case-central but partial fit, or strong support for a lightly contested point; 3 = solid background / uncontested point — and a source with NO case-subject content (e.g., no observations of the product or conduct at issue) caps at 3; 2 = tangential; 1 = no current anchor. When torn between two scores take the LOWER — prestige never rounds up. Fill FFE699 (light amber), centered. Rationale for every score lives on Detail col C. | 1 |
| L | Credibility | Honest venue label, never inflated ("Government / agency source (GAO)", "peer-reviewed commentary journal"). Append material facts: author conflicts, "cited by an opposing expert's report". | 51/143 |
| M | In draft (<draft date>) | Status vs. the manuscript version stated in the header: `Cited in draft` / `Not yet cited` / specific flags ("Cited in draft, working-paper version; update cite to the published version", "Draft cites a different work by same author — reconcile"). | 13/88 |

## Sheet 2 — Detail (4 columns)

Headers row 1 (same header style): `ID` | `Full abstract (or written summary where none published)` | `Relevance rationale (case fit)` | `Reading/verification notes`. Widths 8/110/60/50. One row per main-sheet row, same ID order. Abstract cell: the published abstract verbatim with structured labels (Background:/Objective:) STRIPPED into prose — or, where none exists, a written-from-the-reading summary opening exactly "This source carries no published abstract; the following is written from the reading." Relevance rationale: one sentence of case-fit reasoning (may be blunt: "venue-strong but case-peripheral"). Verification notes: what was checked against which URL/version this session, row history notes (splits, re-keys).

## Sheet 3 — Method (1 column, width 120)

Single-column prose blocks: bold dark-blue (1F4E79) section-label rows alternating with 10pt body rows. Required sections, in order: `METHOD AND COVERAGE` (what the workbook is, sheet list, row counts incl. cited/not-yet-cited split, finalized date) · `READING AND VERIFICATION STANDARD` (read-in-full, verbatim character-checked quotes, figures to the decimal, Limitations discipline) · `COVERAGE AND ORGANIZATION` (section grouping, special labels, ID stability, relevance/credibility definitions, "In draft" column definition) · `NOTES ON VERIFICATION LABELS` (only real, current open items — regenerated at delivery time, never carried stale) · `SOURCE-SPECIFIC NOTES` (per-source disclosures the recipient must see). Written in finished-product voice: zero references to internal memos, process artifacts, or people's names.

## Sorting and ordinals

Within each section group: Relevance descending, then Credibility class descending. Credibility classes rank, high to low: (1) top general-science/economics journal or flagship field journal, peer-reviewed; (2) peer-reviewed field journal; (3) government/agency document (GAO, OIG, CDC/NCHS, agency data); (4) working paper (NBER/SSRN) or peer-reviewed commentary; (5) policy/consulting/advocacy or press material. Ties: alphabetical by first author. IDs are assigned once by the orchestrator at reference-inventory time (before any batching), in section order, and never reassigned.

## Mode A workbook layout (own-report audit)

THIS SECTION is the Mode A layout authority; where `scripts/build_table.py` or `scripts/qc.py` disagree (they implement an older 5-column layout), adapt the scripts or write fresh code — never bend the workbook to a legacy script. Sheets: `Citations` + `Notes` (+ `Detail` optional at scale). Row 1 title `Citation Table — <manuscript, author, year>`; row 2 tally line `N ✓ Accurate · N ◐ Partial · N ⚠ Issue · N ○ Unverified. Total: N unique references.`; row 3 headers: `ID` | `Reference` (hyperlinked full citation) | `Summary` (what the source is and finds, from the read) | `Role in manuscript / result cited` (the proposition it carries, pin-cited) | `Citing paragraph(s)` (complete citing sentence(s) verbatim + every footnote number) | `Accuracy` (glyph + the specific reason — bare glyphs forbidden) | `Limitations / conflicts / later rebuttals`. Same fonts/fills/freeze conventions as the Mode B sheet. Notes sheet headings: SOURCE PAPER · EXTRACTION · DEDUPLICATION · READING (counts full/partial/none + reasons) · ACCURACY RATINGS (the four definitions) · RECURRING PATTERNS · **HARD ERRORS FOUND** (one line each: footnote → what the manuscript says → what the source says; never buried). The draft-side memo (proposed conforming edits to the manuscript) is a separate markdown file `draft-side-memo.md` delivered alongside — never cells in the workbook.

## Mode C workbook layout (opposing-report attack)

Sheets: `Opposing Citations` + `Detail` + `Method`, same styling. Columns, in order: `ID` | `Citation` (hyperlinked) | `What this source is` | `How they use it / what it actually proves` | `Their quote vs. the source` | `Weaknesses` (design, sample, superseded, withdrawn) | `Limitations / conflicts / later rebuttals` | `Data` | `Methods / test` | `Relevance` (fit to THEIR argument, same 1–5 calibration) | `Rebuttal available` (cross-ref to our rows or "none — needs new source") | `Section of their report` | `Credibility`. Grouped by the opposing report's own section structure; rows that survive attack are marked "engage on the merits" with the strategy stated.

## Adverse workbook (internal companion, built in every mode, delivered separately)

Filename: `<DeliverableName>_Adverse_Evidence_INTERNAL.xlsx`, saved in the same folder as the main deliverable and named in the delivery pack (it is part of what ships to the USER, never to third parties).

Sheets: `Adverse Evidence` + its Detail rows + `Notes` (provenance and intended use). Adverse Evidence: 9 columns, same title/note/header styling, freeze C4, widths A=6, B=36, C=30, D=42, E=42, F=42, G=38, H=18, I=26: `ID` (A01…) | `Citation` (hyperlinked) | `What this source is` | `What it finds` | `Why it cuts against us` | `Anticipation strategy (how the report should meet it)` | `Limitations / conflicts / later rebuttals` | `Section it bears on` | `Credibility`. Row 2 note: "Recorded because opposing counsel has these; the report is better off meeting them than being met with them. All rows read in full."

## Formatting not readable programmatically (confirm with the user, never invent)

Print settings/margins, exact rendered row heights beyond stored values, tab colors, and any conditional formatting were not extractable; the shipped table used none detectably. If the user's example shows more, match the example.
