# Contributing Guide

## Development

### Environment setup

Development uses [devbox](https://www.jetify.com/devbox) to provide a
reproducible, isolated shell with all required tools (Python 3.12, `uv`,
`just`, `taskwarrior`, etc.) without touching your system packages.

1. [Install devbox](https://www.jetify.com/docs/devbox/installing-devbox).

1. Enter the dev shell and set up the project in one go:

   ```sh
   devbox shell
   just setup-dev
   ```

   `devbox shell` activates the environment (creates a `.venv` and installs
   Python dependencies via `uv` automatically on first run). `just setup-dev`
   installs the package in editable mode and registers the `pre-commit` hooks.

1. For subsequent sessions just re-enter the shell:

   ```sh
   devbox shell   # or: just shell
   ```

### Common tasks via `just`

`just` is the project's task runner. Run `just` (no arguments) inside the dev
shell to list all available recipes.

| Recipe | What it does |
|---|---|
| `just setup-dev` | Full first-time setup (deps + pre-commit) |
| `just setup-deps` | Re-install Python dependencies only |
| `just setup-pre-commit` | (Re-)install pre-commit hooks |
| `just shell` | Open a devbox shell |
| `just check` | Run all pre-commit checks across the whole codebase |
| `just test` | Run the test suite |
| `just gen-completions` | Regenerate shell completions |

### Linting and formatting

The project uses [ruff](https://docs.astral.sh/ruff/) for linting and
formatting, wired up through [pre-commit](https://pre-commit.com/). The
configuration lives in `pyproject.toml` under `[tool.ruff]`.

Use `just check` to run all checks (including ruff) across the whole codebase:

```sh
just check
```

All hooks also run automatically on every commit. To run only the ruff hooks:

```sh
pre-commit run ruff --all-files
```

### Running the tests

```sh
just test
```

The pytest configuration lives in `pyproject.toml`.

### Isolating test runs from your real data

Set `SYNCALL_TESTENV` before running a sync executable to redirect all config
reads/writes to `$XDG_CONFIG_HOME/test_syncall` instead of the default
`$XDG_CONFIG_HOME/syncall`. This lets you experiment without touching your
live synchronization data.

## Git Guidelines

- Make sure that the branch from which you're making a Pull Request is rebased
  on top of the branch you're making the PR to.
- In terms of the commit message:

  - Start the message header with a verb
  - Capitalise the first word (the verb mentioned above).
  - Format your commit messages in imperative form
  - If the pull-request is referring to a particular `Side`, prefix it with
    `[side-name]`

  For example...

  ```gitcommit
  # ❌ don't do...
  implemented feature A for google calendar
  # ✅ instead do...
  [gcal] Implement feature A
  # ✅ if this is about a synchronization that's about two sides, join them by
  # a dash...
  [tw-gcal] Fix regression in Taskwarrior - Google Keep todo blocks integration.
  ```
