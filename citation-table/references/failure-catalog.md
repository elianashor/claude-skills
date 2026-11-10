# Failure catalog — every defect this project actually produced, with its prevention

Each failure below happened at least once in the two-week build. The prevention is binding. Read before the per-row build begins; re-read before delivery.

## Reading and sourcing failures

- **Abstract-skim presented as a read.** Rows written from abstracts/titles; "not read"/"unverified" rows shipped in-line. → Read in full or the source does not enter; unread material segregated to the working queue, never the deliverable.
- **Fabricated/guessed identifiers.** A guessed PMCID retrieved an unrelated paper (titanium hearing implants); a fabricated Health Affairs DOI 404'd; a wrong DOI pointed to a different article and survived until fresh-eyes QC. → Never construct an identifier from memory; resolve every DOI/PMCID and confirm the landing page title matches before writing it into a cell.
- **Wrong corpus.** A literature review built on the wrong subject matter for the case. → Case theory at intake; purpose re-checked before any corpus work.
- **Version drift.** Working-paper figures under published citations; a published version silently dropping the WP's headline results; an NBER WP cited when the journal version existed. → Gate 9.
- **Superseded authority.** An agency staff comment cited without the agency's later caution against reliance. → Standing check (c); disclose on the row face or swap the source.

## Extraction and quotation failures

- **Character-window extraction.** Excerpts starting/ending mid-word or with commas — the project's signature defect; recurred after the first fix; two adverse cells shipped truncated mid-word ("…the headline compariso."). → Locate-read-transcribe only; programmatic window extraction forbidden; truncation sweep is a hard gate.
- **Running headers/footers leaking into quotes.** → Font-based extraction; read the assembled quote for sense before writing it.
- **Quote alterations.** An acronym altered from the source's own form; casing artifacts introduced systematically by one pass; a truncated quote dropping a comparison clause without an ellipsis. → Character-level verification including typography; every cut marked.
- **Meaningless extraction.** Text pulled without establishing meaning (220-word dumps; structured-abstract labels left in cells). → Summarize in own words for narrative cells; verbatim only in the excerpt column; strip scaffolding.

## Attribution and structure failures

- **Hybrid rows.** A press release's figures quoted under a different agency report's citation; a commentary grafted onto the row for the study it discussed; an excerpt attributed to the wrong document. → One row, one source; split hybrids into their own rows.
- **Substring misfiling.** A paper filed under the wrong heading because a co-author's name matched another paper's citation string. → Key rows by verified content, not string matching; every section assignment justified by the claim, not by lexical accident.
- **Invented structure.** A section header that exists nowhere in the draft; a nonexistent section key; invented taxonomy labels ("claim type: world"). → Section keys only from the manuscript's actual TOC; no labels the user didn't define.
- **Phantom figures.** Draft numbers assumed verified because they sat near a citation — none existed in any cited source. → Every number traced to a location or flagged "no source exists" in the draft-side memo.
- **Duplicate rows / bad merges.** Same source written up twice by different readers; near-identical titles auto-merged (WP vs published are DIFFERENT documents). → Dedup on normalized first-author+year+title; near-matches flagged for judgment, never auto-merged; worst rating governs a merge.

## Judgment failures

- **Relevance = venue echo.** All relevance-5 rows were top venues; a case-central study in a modest venue was undervalued. → Relevance is fit-to-this-case; rationale written per row.
- **Venue inflation.** "Top-5 economics journal" on a commentary journal the author co-edits. → Honest labels; check what the venue actually is.
- **Risk columns dropped.** Funding/conflicts/limitations collected in working files, then omitted from the deliverable. → The Limitations column is mandatory and the single highest-value column; never drop collected risk fields.
- **Overstated function.** A 7-row sheet sold as a "rebuttal engine"; superlatives ("most relevant published in the last 10 years") asserted when unprovable. → Size claims to contents; distinguish provable process claims from superlatives; offer the accurate substitute.
- **Side-blind triage.** Sources called "valuable" without saying valuable-for-whom. → Every assessment leads with which side it helps.
- **Plaintiff-authored/opposing-expert material as authority.** → Adverse workbook, with anticipation strategy; never the supporting sheet.

## Process and delivery failures

- **Wrong deliverable.** A diagnostic worksheet delivered instead of the specified table. → Build the artifact asked for, to its schema; scope drift is a defect even when diligent.
- **Merged-cell corruption.** openpyxl `insert_rows` on a merged-header sheet silently wiped three rows' content. → NEVER insert_rows on sheets with merged rows; rebuild the sheet from an in-memory model; verify row counts and spot-check content after every structural edit; snapshots exist for recovery.
- **Stale companion state.** "Known Limits" shipped describing gates closed days earlier; cover note listing open items invisible to the recipient. → Regenerate every status block at delivery; sweep companions in the same pass; if the workbook is all the recipient gets, everything material lives inside it.
- **Process residue in the deliverable.** References to internal memo files, memo names, personal names in cells. → Finished-product sweep (gate 20).
- **Unexplained working files.** Snapshot proliferation (v1b/c/d) and a Finder-renamed canonical file ("won't open"). → Name the one file to open; keep snapshots in a subfolder or explain them; verify the canonical filename exists at delivery; check rename/lock/cloud-sync before assuming corruption.
- **Coverage claims ahead of visible work.** "All rows reviewed" when some lived only in a file; "background work" implied between messages. → Every claimed unit locatable; never imply work happens between turns.
- **Stopped early / asked mid-run.** Pauses awaiting acknowledgment; content questions mid-run; ended turns on promises. → Intake once; then run to completion; interim comms are progress-only; never end on a promise.
- **Re-arguing the user's structural calls.** Adverse-sheet inclusion defended three times after two soft signals. → One concise pushback, then execute; deliverable scope is the user's call; a repeated instruction means the first one was already binding.
