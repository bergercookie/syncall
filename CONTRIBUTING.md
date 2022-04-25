# Contributing Guide

## Development

- We're using [poetry](https://python-poetry.org/docs/) for building and
  packaging of this Python project. You can find installation instructions
  [here](https://python-poetry.org/docs/#installation).

- We're using `pytest` for testing the code and a variety of plugins for linting
  and checking for bugs, including:

  - [mypy](http://mypy-lang.org/)
  - [pyright](https://github.com/Microsoft/pyright)
  - [pycln](https://hadialqattan.github.io/pycln/)
  - [isort](https://pypi.org/project/isort/)
  - [pre-commit](https://pre-commit.com/)

  All these development dependencies will be available inside the virtual
  environment that poetry sets up. You can get a prompt inside the said virtual
  environment by running `poetry shell` while at the root of this repo.

  ```sh
  # install dependencies and all extras - which are required for running the
  # tests.
  poetry install -E google -E gkeep -E notion

  # get a shell inside the virtualenv
  poetry shell
  ```

  To run all the linters in one go you can use `pre-commit`. To do this:

  1. Setup the `virtulenv` with `poetry` as described above.
  1. Get a shell inside the virtualenv. Install the `pre-commit` hook.

     ```sh
     pre-commit install
     ```

  1. While inside this `virtualenv` you can run `pre-commit run --all-files` to
     run all the linting/formatting checks (excluding the tests).
  1. The linting and formatting programs will run on all files that changed on
     every new commit automatically.

- To run the tests just run `pytest`. The pytest configuration for this project
  (as well as the configuration for each one of the tools can be found in the
  `pyproject.toml` file. At the time of writing this:

  ```toml
  # pytest -----------------------------------------------------------------------
  [tool.pytest.ini_options]
  addopts = ["--ignore-glob=quickstart*", "--doctest-modules"]
  ```

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
