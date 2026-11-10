---
name: teaching-cheat-sheet
description: "Build a teaching cheat sheet for one section of any authoritative source (an expert report, a textbook chapter, a technical document): a story page, per-module summaries with pin cites, precision-audited diagrams, expected challenges with spoken answers, and boxed lines, shipped as a single verified PDF."
---

# Teaching cheat sheet

Build a cheat sheet that teaches one section of a source document to a reader who must perform from memory: an expert testifying with only the report in front of them, a student sitting an exam, a presenter facing hostile questions. The sheet teaches; it never audits. Assume the reader will not reread the source itself. The test for every element: could the reader reconstruct it from memory under pressure? If not, compress it until they can.

## Sources — strict

1. **One authoritative source document is the sole source of substantive content** (the report, the chapter, the manual). Never write a claim stronger than the source's words. Every number, quotation, and characterization carries a pin cite: paragraph, page, section, table, or equation number. If pin units are auto-numbered (Word paragraph numbering), reconstruct the numbering from the file itself and validate the count before citing.
2. **A challenge source, when one exists, picks which challenges to expect**: a mock cross-examination outline, past exam questions, a referee report, a standing list of objections. It supplies the attacks, their priority, and their register. Questions may carry the challenger's framing and figures; answers must rest only on the primary source, with pin cites. If the challenge source was written against an older version of the primary source, drop figures the current version has superseded from the questions too, unless the challenger is still likely to use them. Where the challenge source flags a genuine weakness in the primary source, the model answer is the concession plus the pivot to the source's strongest material, never a defense of the weak point.
3. **Settled content, when provided.** If a canonical earlier sheet or a settled-content file accompanies the source, its text is fixed: reproduce it verbatim, apply judgment only where it is silent, and note any conflict with the current source rather than silently rewording. This is the mechanism for exact reproduction; without it, expect the structure to match and the wording to vary.
4. Nothing else: no outside research and no web queries during the build. Errors, typos, or internal tensions found in the source go to a separate notes file for its author (`source-notes-for-author.md` beside the deliverable), never into the sheet, except where the challenge source attacks the flaw directly; there the sheet handles it as concession plus pivot.

## Template

The module unit is the source's second-level heading (III.A, chapter section 3.1); third-level headings become the rows of the module's table. Module headings get a short teaching title, not the source's full heading, followed by the pin range: `3.2  Elasticity: What the Slope Doesn't Tell You  (pp. 41–58)`. No "Module A" prefixes.

**Page 1:** the sheet title; one line naming the source and pin range; **The story in three sentences** (exactly three); one drawn diagram of the section's central structure; **The map**, a table `Subsection | The point | pin cites`, one row per module, each point one or two sentences.

**One module per subsection**, each containing in order, under these labels:

1. **"The point."** One to three sentences, run into the paragraph.
2. **"What the source says, subheading by subheading:"** table `Subheading | What it establishes | pin cites`. One row per third-level heading, summaries written from the source's text, each cell at most four printed lines. The table is the reference layer; it does not need every number, only what the module stands on.
3. **A module diagram** wherever a model or mechanism could confuse.
4. **"Why it matters."** (For a litigation sheet: "Why it matters for trial.") One short paragraph tying the module to the stakes the reader faces.
5. **"The challenge to expect."** (For a litigation sheet: "The cross to expect.") Two or three Q/A pairs. Questions in the challenger's register: one fact per question, about twenty-five words or fewer, ending on the tag ("Yes or no?", "correct?", "isn't it?"). Answers are written to be spoken: two to four sentences, pin cites inline, concede what must be conceded, pivot to the source's strongest facts, and end on a number where one exists.
6. **"Key takeaways."** Numbered, one to two per module, only items not already carried by the challenge answers or the boxed line. A fact may appear in the reference table and in at most one spoken layer (a challenge answer, a takeaway, or the boxed line), never several.
7. **The boxed line**, a tinted box with three labeled parts: the module's line in bold italics (one repeatable sentence); then `[Challenger]'s claim:` in small gray italics, stating the misconception in their words (for a litigation sheet: `Plaintiff's experts' claim:`); then `Rebuttal:` (for a litigation sheet: `Defense rebuttal:`) as one quoted, speakable sentence in the shape "your model of X is wrong, because Y," ending on a specific fact without adding more words.

**Close page:** **"Where the section sits"** (two or three short paragraphs: what it inherits from earlier sections, what it hands to later ones); **"The lines"**, the boxed lines listed in order; and a **rehearsal target**: the two or three sentences and numbers that carry the section. These restatements are the template's intended exception to the repetition rule.

## Diagram precision — diagrams get the same fidelity audit as prose

A wrong picture teaches a wrong model, so before shipping: (a) every label, number, and pin cite in a diagram is checked against the source's text, exactly like a sentence; (b) never draw a claim stronger than the source's ("X carries none" becomes "X typically carries none" if that is the source's word, and no one-for-one tradeoff is drawn unless the source states it); (c) name the population or sample a number is measured on whenever it could be mistaken for a broader one; (d) quantities drawn as lengths are drawn to scale, or labeled "schematic, not data"; (e) model mechanics stay exact, in the economist's version rather than the vivid approximation: competition runs among the actual substitutes, steering stays within the relevant class or margin, and a supply shift is identified by price falling while quantity rises; (f) after any diagram change, re-render it, inspect the image, and re-check its page's layout.

## Layout spec

- One clean sans-serif face throughout, prose and diagrams (Arial or equivalent); letter-size pages; roughly 0.8-inch side margins; no running headers or footers unless asked.
- Color system, used identically in text and diagrams: one dark accent for structure and headings (a deep slate blue works); gray for the challenger's quoted words; a light tint for fills; red reserved solely for the challenger's premise or mistaken model; green for the correct mechanism. Nothing else.
- Tables: dark accent header row with white text, thin gray rules, alternating row tint.
- Q/A styling: `Q:` then the question in gray italics inside quotation marks; `A:` in accent bold, answer in upright text. Keep each Q with its A on one page.
- Section labels are printed exactly as given in the Template, in accent bold.
- **Page budget:** the minimum pages that satisfy the box rule. Modules flow; do not force every module onto a fresh page. A module must close on the page it starts or the next one, a boxed line never sits alone on a near-empty page, and overflow is fixed by cutting duplication first, then shrinking diagrams, then trimming prose, never by appending. A section of five modules should land near eight to ten pages.

## Format, build, verification

- One PDF per section, cleanly named (`Section-N-Cheat-Sheet.pdf`, `Chapter-3-Cheat-Sheet.pdf`).
- Prose: short paragraphs, hard structure, no filler, no quiz gimmicks, and no em dashes (en dashes in numeric ranges are fine).
- **Before shipping:** mechanically verify every (pin cite, fact) pair, in prose and in diagrams, against the source's text, and run a negative control (corrupt two facts, confirm the checker fails, restore them) so the checker itself is proven; render the PDF to page images and inspect every page; state the check totals honestly, including anything that could not be verified and why.
- **The checker ships with this skill: `scripts/pincheck.py`.** Before citing, run `python scripts/pincheck.py units SOURCE --expect-count N` to validate the reconstructed paragraph numbering (Word auto-numbering is rebuilt from the list definitions, block quotes attach to their paragraph, footnotes index as n. 1, n. 2). After rendering, run `python scripts/pincheck.py check SOURCE --scan SHEET.pdf --negative-control 10`: it checks every number and quotation in every pin-cited sentence and table row, tells a wrong pin ("found at ¶ 47") from a phantom ("found nowhere"), and exits nonzero unless every corruption in the negative control is caught. Diagram labels and paraphrases the scan cannot see go in a claims file (`[{"pin": "¶ 42", "text": "..."}]`) checked with `--claims`. The totals it prints are the check totals you report.
- When the full set of sections exists, also build one combined volume: a cover and contents page plus every section in order.

## Two worked uses

An expert report, one sheet per report section, with challenges drawn from the trial team's mock cross-examination outline. A textbook, one sheet per chapter, with challenges drawn from past exams and the questions students most often miss.
