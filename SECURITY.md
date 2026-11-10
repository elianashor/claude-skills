# Security and confidentiality

These skills were developed on confidential client work and published only after redaction. If you believe anything in this repository, including its git history, identifies a party, an expert, a case, a document produced in a matter, or any other confidential detail:

1. Do not open a public issue or pull request that repeats it.
2. Report it privately through GitHub's **Report a vulnerability** form on this repository's Security tab.

Reports are handled before anything else. A confirmed leak is removed from the working tree and from history, and the guard's patterns or denylist are extended so it cannot recur.

## How the guard works

`pincite guard` runs on every push and pull request. It scans the working tree and every commit for:

- private terms from the `PINCITE_DENYLIST` repository secret (one per line, matched across case, spacing, punctuation and CamelCase), which never appear in the repository itself
- case numbers, MDL numbers, Bates ranges, protective-order legends, dated draft filenames, personal home-directory paths and non-allowlisted email addresses

In CI every match is printed masked, so the build log never becomes the leak.
