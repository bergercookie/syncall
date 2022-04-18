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

TODO
