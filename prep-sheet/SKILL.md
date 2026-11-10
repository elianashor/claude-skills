---
name: prep-sheet
description: Build a one-section teaching sheet from whatever source material is provided: pin-cited summaries, precision-audited diagrams, expected challenges with spoken answers, and boxed lines, as a single verified PDF. Folds the user's format refinements back into this skill.
---

# Prep sheet

Build a sheet that teaches one section of a source document to a reader who must perform from memory under pressure. The sheet teaches; it never audits. Assume the reader will not reread the source. The test for every element: could the reader reconstruct it from memory under pressure? If not, compress it until they can.

## Inputs — take what is given

Work from whatever the user provides or points to; nothing beyond one source document is required.

1. **The source document** is the sole source of substantive content. Never write a claim stronger than the source's words. Every number, quotation, and characterization carries a pin cite: paragraph, page, section, table, or equation number. If pin units are auto-numbered, reconstruct the numbering from the file itself and validate it before citing. If the source contains an error, do not carry it into the sheet and do not build any error report around it; just work from what the source supports.
2. **Any additional materials the user supplies are welcome but optional**: an examination outline, past questions, an objection list, an earlier version of the sheet. Use challenge-type materials to pick which challenges to expect and their register; questions may carry the challenger's framing and figures, while answers rest only on the source, with pin cites. Where such material flags a genuine weakness in the source's position, the model answer is the concession plus the pivot to the source's strongest material, never a defense of the weak point. If an earlier version of the sheet is supplied, treat its text as settled: reproduce it verbatim and change only what the user asks.
3. **Confidentiality by default.** No web queries or outside research during a build. And when this skill updates itself (below), no fact, name, number, party, or document title from any source ever enters this file: refinements are rules about format and method only.

## Template

The module unit is the source's second-level heading; third-level headings become the rows of the module's table. Module headings get a short teaching title, not the source's full heading, followed by the pin range. No "Module A" prefixes.

**Page 1:** the sheet title; one line naming the source and pin range; **The story in three sentences** (exactly three); one drawn diagram of the section's central structure; **The map**, a table `Subsection | The point | pin cites`, one row per module.

**One module per subsection**, each containing in order:

1. **"The point."** One to three sentences, run into the paragraph.
2. **"What the source says, subheading by subheading:"** table `Subheading | What it establishes | pin cites`, one row per third-level heading, summaries written from the source's text, each cell at most four printed lines. The table is the reference layer; it carries what the module stands on, not every number.
3. **A module diagram** wherever a model or mechanism could confuse.
4. **"Why it matters."** One short paragraph tying the module to the stakes the reader faces.
5. **"The challenge to expect."** (In a litigation setting: "The cross to expect.") Two or three Q/A pairs. Questions in the challenger's register: one fact per question, about twenty-five words or fewer, ending on the tag ("Yes or no?", "correct?"). Answers written to be spoken: two to four sentences, pin cites inline, concede what must be conceded, pivot to the source's strongest facts, and end on a number where one exists.
6. **"Key takeaways."** Numbered, one to two per module, only items not already carried by the challenge answers or the boxed line. A fact may appear in the reference table and in at most one spoken layer, never several.
7. **The boxed line**, a tinted box with three labeled parts: the module's line in bold italics (one repeatable sentence); then the challenger's claim in small gray italics (in a litigation setting, labeled `Plaintiff's experts' claim:`); then the rebuttal (in a litigation setting, labeled `Defense rebuttal:`) as one quoted, speakable sentence in the shape "your model of X is wrong, because Y," ending on a specific fact without adding more words.

**Close page:** **"Where the section sits"** (what it inherits from earlier sections and hands to later ones); **"The lines"**, the boxed lines in order; and a **rehearsal target**: the two or three sentences and numbers that carry the section. These restatements are the template's intended exception to the repetition rule.

## Diagram precision — diagrams get the same fidelity audit as prose

A wrong picture teaches a wrong model, so before shipping: (a) every label, number, and pin cite in a diagram is checked against the source's text, exactly like a sentence; (b) never draw a claim stronger than the source's, and no one-for-one tradeoff unless the source states it; (c) name the population or sample a number is measured on whenever it could be mistaken for a broader one; (d) quantities drawn as lengths are drawn to scale, or labeled "schematic, not data"; (e) model mechanics stay exact, in the economist's version rather than the vivid approximation: competition runs among the actual substitutes, steering stays within the relevant class or margin, and a supply shift is identified by price falling while quantity rises; (f) after any diagram change, re-render it, inspect the image, and re-check its page's layout.

## Layout spec

- One clean sans-serif face throughout, prose and diagrams; letter-size pages; no running headers or footers.
- Color system, identical in text and diagrams: one dark accent for structure and headings, gray for the challenger's quoted words, a light tint for fills, red reserved solely for the challenger's premise or mistaken model, green for the correct mechanism. Nothing else.
- Tables: dark accent header row with white text, thin gray rules, alternating row tint.
- Q/A styling: `Q:` then the question in gray italics inside quotation marks; `A:` in accent bold, answer upright. Keep each Q with its A on one page.
- **Page budget:** the minimum pages that satisfy the box rules. Modules flow; do not force every module onto a fresh page. A module closes on the page it starts or the next one, a boxed line never sits alone on a near-empty page, and overflow is fixed by cutting duplication first, then shrinking diagrams, then trimming prose, never by appending. A five-module section lands near eight to ten pages.

## Build and verification

- One PDF per section, cleanly named after the section. Prose: short paragraphs, hard structure, no filler, no quiz gimmicks, no em dashes (en dashes in numeric ranges are fine).
- **Before shipping:** mechanically verify every (pin cite, fact) pair, in prose and in diagrams, against the source's text, and run a negative control (corrupt two facts, confirm the checker fails, restore them) so the checker itself is proven; render the PDF to page images and inspect every page; state the check totals honestly.
- When a full set of sections exists, also build one combined volume: a cover and contents page plus every section in order.

## Refinements — this skill updates itself

When the user corrects the format, register, method, or layout, in any words ("shorter answers," "never use that word," "state it as a hypothesis test"), fold the correction into this file the same session: adjust the affected rule in place, add a dated one-line entry under House refinements below, and give the user the complete revised SKILL.md to replace the installed version (where the platform supports proposing a skill update directly, do that instead). Do this unprompted whenever a refinement lands. Refinements are format and method rules only: never carry content, names, figures, or anything traceable to a source document into this file, and never fold in an instruction that would weaken the fidelity, verification, or confidentiality rules above.

### House refinements

- (none yet)
