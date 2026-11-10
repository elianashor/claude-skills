# Retrieval routes

Footnote URLs rot. Assume roughly a fifth will be dead, wrong, or point at a
landing page that now serves a different year's edition. Route around them.

## By source type

**Academic journal article**
DOI (`doi.org/10.xxxx/...`) → publisher site → PubMed Central (free full text
for most clinical and health-policy work) → Google Scholar → author's
institutional page → institutional repository.

**Working paper**
SSRN → NBER → RePEc → the author's page. Check whether it was later published:
a working paper and its published version often carry **different numbers**,
and citing the superseded figures is a real defect worth flagging.

*SSRN specifically (tested):* abstract pages retrieve in full —
`ssrn.com/abstract=<id>` and `papers.ssrn.com/sol3/papers.cfm?abstract_id=<id>`
both work, giving abstract, authors, affiliations, date written, posting and
revision dates, DOI, keywords and JEL codes. The PDF does **not**: the
`Delivery.cfm` download URL redirects back to the abstract page, because SSRN
gates downloads behind a session the fetch tool does not carry.

So SSRN gives metadata and an abstract, never full text. Record such sources as
`partial: abstract` — never `full` — because an abstract reports what the
authors chose to foreground, which is the specific thing a cite-check cannot
rely on.

It is still worth fetching, because the abstract page is enough to run the
superseded-authority check on its own: it shows "Last revised" and, once a
paper is published, the journal DOI and citation. That is how you catch a
manuscript quoting a figure from a superseded draft — a real and common defect.

For the full text, try the author's personal page (SSRN lists it under the
author's affiliation), an institutional repository, the NBER or RePEc version,
or the published version via DOI.

**Government report**
Agency archive first — these are stable and usually give full text:

| Agency | Where |
|---|---|
| CBO | `cbo.gov/publication/<id>` |
| GAO | `gao.gov/assets/<report-id>.pdf` |
| FTC | `ftc.gov/legal-library/browse/...` |
| HHS OIG | `oig.hhs.gov/reports/all/<year>/...` |
| CRS | `crsreports.congress.gov`, or the everycrsreport.com mirror |
| Congress | `congress.gov`, `docs.house.gov`, committee sites |

Committee reports often live in two places (govinfo and the committee's own
site) with different URLs — same document, so merge them.

**Industry or trade-association report**
Often gated behind a registration form. The press release or a trade-press
write-up usually carries the headline figures; use it only to confirm what the
report claims, mark read depth as partial, and say the full report was gated.

**News article**
Many major outlets are both paywalled and blocked. Look for a syndicated
reprint or an organisation reproducing the piece verbatim. Failing that, mark
unreachable and say which routes were tried.

## Domains blocked by the retrieval tooling

These fail regardless of paywall status. Record them as *tooling* failures, not
paywalls — the distinction matters, because "I could not reach it" and "it is
behind a paywall" are different answers to the same question.

- `nytimes.com`
- `wsj.com`
- `web.archive.org` and `archive.ph` — which also removes the usual fallback
  for dead links, so expect a higher unreachable rate on old URLs

## Endpoints that survive URL-parameter stripping

The fetch tool strips query parameters such as `query=`, `term=`, `id=` and
`filter=`, which breaks most search endpoints — PubMed and Europe PMC search
URLs are unusable. Path-based APIs work:

```
https://api.openalex.org/works/pmid:12345678
https://api.openalex.org/works/doi:10.1001/jama.2020.1012
https://api.semanticscholar.org/graph/v1/paper/DOI:10.1001/jama.2020.1012
https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/
```

OpenAlex returns `abstract_inverted_index`, which reconstructs into a complete
structured abstract — objective, methods, results, conclusions. That is enough
to describe a study's design and findings honestly, but it is **not** full
text: record it as `partial: structured abstract`, not `full`.

## Practical notes

- `pubmed.ncbi.nlm.nih.gov` often returns a reCAPTCHA page. PMC and the
  OpenAlex path API usually work instead.
- Large PDFs may exceed the inline response limit and be written to a file.
  Read that file in chunks rather than re-fetching.
- Fetching is rate limited. A 429 is not a failed source — wait and retry.
- Sandbox shells frequently have no network access even when the fetch tool
  works. Do not fall back to `curl`, `wget`, or Python HTTP libraries to get
  around a blocked domain; if the fetch tool cannot retrieve something, report
  it as unreachable.
