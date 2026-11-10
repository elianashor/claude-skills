# Examples

Everything here is synthetic. Run from the repository root after `pip install -e .`.

## Build, sweep and QC a supporting-authority table

```bash
pincite build examples/citation-table/spec.json --out /tmp/Supporting_Authority.xlsx
pincite sweep /tmp/Supporting_Authority.xlsx
pincite qc /tmp/Supporting_Authority.xlsx --strict
```

## Verify a cheat sheet against its source

```bash
pincite units examples/pincheck/report.txt --expect-count 5
pincite check examples/pincheck/report.txt --scan examples/pincheck/sheet.md --negative-control 6
pincite check examples/pincheck/report.txt --claims examples/pincheck/claims.json
```

The sheet contains one planted error: the table row says the 412 plans are at ¶ 43, but the
source states it at ¶ 40. The checker reports it as a wrong pin, not a phantom, and the
negative control proves the checker would have caught a changed digit or a swapped word.
