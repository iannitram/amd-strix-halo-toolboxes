# Rules for agents in this fork (our pipeline)

This fork keeps its own pipeline files beside upstream's. Upstream owns `README.md`, `AGENTS.md`, `toolboxes/`, `benchmark/`, `docs/` and the image workflows; change those only when an issue says so, because every change there is a future merge conflict. Our work lives in `workstation/`, `tests/workstation/`, `pyproject.toml`, `.github/workflows/workstation-ci.yml` and the pipeline files. Everything you need is in this repo. The full pipeline and rules live in the pipeline repo (private); this is the short copy.

1. **Find the stage** in `PIPELINE.md`. The spec is `SPEC.md`, the plan `ROADMAP.md`, the code map `CODE_MAP.md`.
2. **Work from an issue.** Take one that is not `in-progress`, not `after-1.0` and not blocked; add `in-progress` before you start. Its body is your brief; an Easy issue has a "Qwen brief" section and a "Tests (locked)" file: commit that test file first, unchanged, and never edit it.
3. **Your own platform's issues first.** The toolboxes run on a Strix Halo host running Linux; the Mission Control page must work in a browser on Mac, Windows and Linux. Say which you built on.
4. **Prove it**: `python -m pytest tests/workstation` and `python -m ruff check workstation tests`, then open the PR with that output in its body. The reviewer checks the expected results.
5. **Default checks touch nothing real**: no image pulls, no model downloads, no GPU or SSH work, no host settings. Use the fakes in `workstation/runtime/fake.py`. Hardware runs are their own issues.
6. **Runtime code is standard-library Python 3.10+**; tests use pytest. The web page is plain HTML, CSS and JavaScript with no build step.
7. **Label the PR** `by:<machine>` and `model:<model>`, and write `Closes #N`. When a module lands, move its code map status from planned to present in the same PR.
8. **A failed job** gets a comment on the issue saying what happened, and the issue moves up one size (Easy -> Medium -> Hard).
9. **Upstream**: upstream has no licence file (kyuz0/amd-strix-halo-toolboxes#141), so nothing from this fork goes upstream and nothing is published until it has one. Never push, open PRs or post on kyuz0's repos. Peers with no licence (see `SPEC.md`, Prior art) give ideas only: copy no code from them.
10. **No private details** in code, commits or PR text: no names, e-mail addresses, home paths or machine names; describe machines by their hardware. Commit as the no-reply identity. No secrets in files or issues.
