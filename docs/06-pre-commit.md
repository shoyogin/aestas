# 6. Pre-commit (detailed)

Pre-commit runs **automated checks** on your code before a commit is created. This keeps the repository clean and enforces basic quality (formatting, lint, no secrets).

## What is pre-commit?

Pre-commit is a framework for **git hooks**. When you run `git commit`, it can run a series of **hooks** (small scripts). If any hook fails, the commit is aborted. So you fix the issues and try again, and only “clean” code gets committed.

## Setup (one-time)

From the project root:

```bash
# Create a virtualenv if you don’t have one
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Install pre-commit
pip install pre-commit

# Install the git hooks (so they run on every commit)
pre-commit install
```

After that, every time you run `git commit`, the hooks in `.pre-commit-config.yaml` will run.

## What runs on each commit?

1. **pre-commit-hooks** (general)
   - Remove trailing whitespace.
   - Ensure files end with a newline.
   - Check YAML and JSON syntax.
   - Reject files that look like they contain a private key.
   - Reject very large files (over 500 KB by default).

2. **Ruff** (Python in `backend/`)
   - Lints and auto-fixes Python under `backend/`.
   - Catches style issues and simple bugs.

3. **ESLint** (JS/JSX in `frontend/`)
   - Runs from the `frontend/` directory so it uses `frontend/.eslintrc.cjs`.
   - Only on files under `frontend/` matching `*.js` or `*.jsx`.

Only **staged** (or, for “run all,” all) files are passed to the hooks when you commit. So you only check what you’re about to commit.

## Useful commands

- **Run on staged files** (default when you commit):
  Happens automatically on `git commit`.

- **Run on all files** (e.g. after adding the config):
  `pre-commit run --all-files`

- **Run a single hook**:
  `pre-commit run ruff --all-files`
  `pre-commit run eslint --all-files`

- **Update hook versions**:
  `pre-commit autoupdate`

## If a hook fails

The command output will say which hook failed and on which file. Fix the reported issues (e.g. run `ruff check backend/ --fix` or fix ESLint errors in the frontend), stage the changes again, and commit. The hooks will run again.

## Summary

- **pre-commit install** installs git hooks so checks run on every commit.
- Hooks: trailing whitespace / EOF, YAML/JSON, large files, private keys; **Ruff** for backend Python; **ESLint** for frontend JS/JSX.
- Failed hooks block the commit until the issues are fixed.
