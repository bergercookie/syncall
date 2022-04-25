# [Taskwarrior](https://taskwarrior.org/) ⬄ [Google Keep Checkboxes](https://notion.so)

## Description

Synchronize all the items of a Google Keep note/list with a filter in
Taskwarrior. The taskwarrior filter may be a task, a project or a combination of
a project and arbitrary tags.

Upon execution, `tw_gkeep_sync` will synchronize, and on subsequent runs of the
program keep synchronized, the following attributes:

- Text of Google Keep list item <-> TW task title
- Whether a Google Keep list item is checked ✅ or unchecked <-> TW task completion status
- Google Keep list item item block is deleted <-> TW task deletion

## Usage example

To synchronize all the items of a Google Keep list called "Test Note" with a tag called
"test_tag" you can use something like:

```sh
tw_gkeep_sync -t test_tag -k "Test Note"
```

## Demo

![tw-gkeep-demo](https://github.com/bergercookie/taskwarrior_syncall/raw/master/misc/tw_gkeep_sync.gif)

## Installation

### Package Installation

Install the `taskwarrior-syncall` package from PyPI, enabling the `gkeep`
extra:

```sh
pip3 install taskwarrior-syncall[gkeep]
```

### Credentials

We're using the unofficial
[gkeepapi](https://gkeepapi.readthedocs.io/en/latest/index.html) tool to
authenticate and interact with Google Keep. It requires your Google account
username and password to do so. If you're using 2FA, you should create a direct
password and use that instead.

Read more about this [here](https://gkeepapi.readthedocs.io/en/latest/#faq).

To provide the password, you can either use the `GKEEP_USERNAME` and
`GKEEP_PASSWD` before running `tw_gkeep_sync` or (recommended), use [the UNIX
Password Manager](https://www.passwordstore.org/) to store your username and
password to your Google account and provide the paths to them (use
`--user-pass-path ... --passwd-pass-path ...` in this case).
