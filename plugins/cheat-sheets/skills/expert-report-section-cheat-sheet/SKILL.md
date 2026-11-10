---
name: "expert-report-section-cheat-sheet"
description: "Build or rebuild a teaching cheat sheet for a section of a testifying expert's report in a litigation matter, end to end: v3 template, mock-cross-driven cross sections, verified ¶ cites, audited diagrams, one PDF per section."
---

# Expert report section cheat sheet (v3)

Build a teaching cheat sheet for one section of the defense expert report. The expert testifies with only the report in front of them, so the sheet teaches; it never audits. It is not filed. Assume the expert will not read the report itself. The full canonical spec lives at `<case folder>/prompt-section-cheat-sheet.md`; read it if reachable. This file restates the binding rules. If the case folder is not connected where this skill runs, ask for the operative report draft and the two prep documents as attachments and deliver the finished PDF in the conversation; everything else applies unchanged.

## Sources — strict

1. **The operative report draft is the sole source of substantive content** (the newest draft in the case folder's report-drafts folder). Never write a claim stronger than the report's words. Every number, quotation, and characterization carries its paragraph cite (¶). Report typos or internal errors go to `notes-for-author*.md` in the case folder (or, without the case folder, to `source-notes-for-author.md` beside the deliverable), never into the sheet.
2. **The team's prep materials pick the cross-examination attacks**: the mock cross-examination outline and the cross-exam themes memo. They supply which attacks to expect, their priority, and their register. Questions may carry plaintiff framing and figures from those documents; answers must be grounded only in the report draft, with ¶ cites. If a prep document was written against an older report draft, drop superseded figures from the questions too, unless plaintiff is still likely to use them. Where the mock cross flags a genuine report weakness, the model answer is the concession plus the pivot to the report's strongest facts, never a defense of the weak point.
3. **Settled content.** When a canonical sheet already exists for the section (its PDF in `Completed Work/Section N/` or its content file), its text is fixed: reproduce it verbatim and change only what the requested revision asks. Note any conflict with the current draft rather than silently rewording. This is the mechanism for exact reproduction; without settled content, expect structure to match and wording to vary.
4. Nothing else: no plaintiff reports, no citation tables, no external research, no web queries. Case confidentiality follows.

## Template

The module unit is the report's second-level heading (III.A, III.B, ...); third-level headings become the rows of the module's table. Module headings get a short teaching title, not the report's full heading, followed by the ¶ range (`III.B  Short Teaching Title  (¶¶ 120–145)`); no "Module A" prefixes.

**Page 1:** section title using the report's own heading and ¶ range; **The story in three sentences** (exactly three); one drawn diagram of the section's central structure; **The map**, a table `Subsection | The point | ¶¶`, one row per module.

**One module per report subsection**, each containing in order:

1. **The point.** One to three sentences, run into the paragraph.
2. **What the report says, subheading by subheading.** Table `Subheading | What it establishes | ¶¶`, one row per report subheading in the module, summaries written from the report's text, each cell at most four printed lines. The table is the reference layer; it carries what the module stands on, not every number.
3. **A module diagram** wherever a model or mechanism could confuse. Visual system: accent #1F3B57, grey #9AA7B4, light #EEF2F6; red #8A3B3B only for plaintiff-premise elements; green #2F5D3A for defense mechanisms. Every label supportable by a ¶ cite.
4. **Why it matters for trial.** Short paragraph tying the module to liability, causation, or damages stakes.
5. **The cross to expect.** Two or three Q/A pairs. Questions in the mock cross register: short, leading, one fact per question, about twenty-five words or fewer, ending on a tag ("Yes or no?", "correct?"). Answers as spoken testimony, two to four sentences with ¶ cites inline, concede-and-pivot on real weaknesses, ending on a number where one exists.
6. **Key takeaways.** Numbered, one to two per module, only items not already carried by the cross or the box: a fact may appear in the reference table and at most one spoken layer.
7. **Boxed line.** The module's line in bold italics (never the word "mantra"), then `Plaintiff's experts' claim:` in small grey italics, then `Defense rebuttal:` as one quoted, speakable sentence in the "your model of X is wrong because Y" shape, ending on a specific fact without adding more words.

**Close page:** "Where Section N sits" (hand-backs and hand-forwards), "The lines" (one per module), and a rehearsal target: the two or three sentences and numbers that carry the section. These restatements are the template's intended exception to the repetition rule.

## Diagram precision — diagrams get the same fidelity audit as prose

A wrong picture teaches a wrong model, so before shipping: (a) every label, number, and ¶ cite in a diagram is checked against the draft's paragraph text, exactly like a sentence; (b) never draw a claim stronger than the report's ("X carries none" becomes "X typically carries none" if that is the report's word; no one-for-one tradeoff unless the report says it); (c) name the population a number is measured on when it could be mistaken for a broader one (e.g., a rate measured only on the plaintiff's own data); (d) quantities drawn as lengths are drawn to scale, or labeled "schematic, not data"; (e) model mechanics stay exact: competition runs among the actual substitutes, steering stays within the relevant class or margin, a supply shift is identified by price falling while quantity rises; (f) after any diagram change, re-render it, inspect the image, and re-check its page's pagination.

## Layout spec

- Arial throughout, prose and diagrams; US Letter; no running headers or footers.
- Tables: accent header row with white text, thin grey rules, alternating row tint.
- Q/A styling: `Q:` then the question in grey italics inside quotation marks; `A:` in accent bold, answer upright. Keep each Q with its A on one page.
- Section labels printed exactly as the Template gives them, in accent bold.
- **Page budget:** the minimum pages that satisfy the box rules. Modules flow; do not force every module onto a fresh page. A five-module section should land near eight to ten pages.

## Format, build, verification

- One PDF per section, clean name `Section-N-Cheat-Sheet.pdf`, delivered to `Completed Work/Section N/` when the case folder is available, otherwise in the conversation. Cheat sheets only; no line cards.
- Page discipline: a module closes on the page it starts or the next one; a boxed line never sits alone on a near-empty page. Fix overflow by cutting duplication first, then shrinking diagrams, then trimming prose; never by appending.
- Prose: no em dashes; no quiz or "say it back" sections; never "mantra"; short paragraphs; no rule-of-three padding.
- **Before shipping:** mechanically verify every (¶, fact) pair, in prose and in diagrams, against the draft's paragraph text, and run a negative control (corrupt two facts, confirm the checker fails, restore them) so the checker itself is proven; render the PDF to page images and inspect every page; state check totals honestly.
- **The checker ships with this skill: `scripts/pincheck.py`.** Before citing, run `python scripts/pincheck.py units SOURCE --expect-count N` to validate the reconstructed paragraph numbering (Word auto-numbering is rebuilt from the list definitions, block quotes attach to their paragraph, footnotes index as n. 1, n. 2). After rendering, run `python scripts/pincheck.py check SOURCE --scan SHEET.pdf --negative-control 10`: it checks every number and quotation in every pin-cited sentence and table row, tells a wrong pin ("found at ¶ 47") from a phantom ("found nowhere"), and exits nonzero unless every corruption in the negative control is caught. Diagram labels and paraphrases the scan cannot see go in a claims file (`[{"pin": "¶ 42", "text": "..."}]`) checked with `--claims`. The totals it prints are the check totals you report.
- When the full set of sections exists, also build one combined document (cover/contents plus all sections in report order) at `Completed Work/`.
- Log durable lessons to `<case folder>/lessons/` at the end of the session, when the case folder is available.