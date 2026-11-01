# Documentation style guide

Keep documentation useful to three readers: someone discovering the project, a contributor choosing a task, and a researcher checking a claim. Prefer clear navigation and precise evidence over promotional language or file count.

## Structure and navigation

- Give every page one descriptive `#` title. Use `##` and `###` in order; do not skip heading levels to achieve a visual effect.
- Open with the page's purpose and whether it describes a **requirement**, **proposal**, **experiment**, or **verified implementation**.
- Put the answer or main constraint before background. Link to focused documents instead of duplicating long technical sections.
- Use [the documentation guide](README.md) as the index. Add or update its link when creating, moving, or retiring a substantive document.
- Keep local Markdown links relative to the source file. Use stable primary-source links for research citations and record version/revision context when it matters.
- Use tables for comparisons and exact mappings; use short lists for procedures. Avoid very wide hand-written tables when several short subsections would be easier to scan.

## Wording and formatting

- Use descriptive headings such as “Evidence required” or “Failure recovery”, not vague headings such as “Miscellaneous”.
- Prefer plain language and concrete subjects. Define unfamiliar abbreviations on first use, then use them consistently with the [glossary](GLOSSARY.md).
- Follow existing British-English prose conventions (`behaviour`, `licence` as a noun, `programme`) while preserving upstream identifiers and code spelling.
- Use fenced code blocks with language labels. Commands should be executable as written, with working directory and prerequisites clear.
- Keep paragraphs readable in source, but do not mechanically wrap URLs, Markdown tables, generated content, or code solely to meet a column count.
- Avoid decorative badge collections, speculative performance figures, empty placeholder sections, and claims of readiness unsupported by tests.

## Evidence and status language

Use precise verbs:

| Say | When |
| --- | --- |
| **Proposed** or **candidate** | A design, research method, or experiment is specified but not executed. |
| **Implemented** | Functional code meets the stated interface or behaviour on the evidenced revision. |
| **Tested** | A named test actually ran; identify its scope, revision, and result. |
| **Demonstrated in-game** | Legal Minecraft actions achieved the declared outcome in a reproducible game environment. |
| **Production-ready** | Relevant operational, security, compatibility, recovery, and release gates passed. |

Never describe a matrix entry, paper, schema, mock, passing compilation, or unmerged branch as a demonstrated Minecraft capability. Distinguish author-reported research results from results independently reproduced here. Link negative and inconclusive evidence as carefully as positive findings.

## Generated files

[`progress/progress.json`](progress/progress.json) is the sole editable source for tracked items and status percentages. The following are generated and must not be hand-edited:

- `PROGRESS.md`
- `FEATURE_MATRIX.md`
- `MINECRAFT_COMPETENCY_MATRIX.md`
- `RESEARCH_MATRIX.md`
- `MODEL_TRAINING_MATRIX.md`
- `PRODUCTION_READINESS.md`
- The bounded progress sections in `../README.md` and `../ROADMAP.md`

To change their layout, update the generator, validate its output, and keep the source schema/evidence semantics intact. A documentation-only visual cleanup is **not** grounds for promoting any research or implementation status.

## Before submitting documentation changes

Run from the repository root:

```sh
python tools/progress.py validate
python tools/progress.py check
python tools/check_doc_links.py
python -m unittest discover -s tests -p 'test_*.py'
```

Regenerate only when canonical data or generation logic changes. Run the [CI smoke suite](../scripts/ci_smoke.py) on a clean committed tree when relevant; it intentionally rejects dirty-source experiment runs. Inspect the rendered Markdown and the PR diff for broken headings, dead links, duplicated explanations, unexpected generated changes, and claims that exceed the evidence.
