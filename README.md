# taskwarrior-syncall

<p align="center">
  <img src="https://github.com/bergercookie/taskwarrior-syncall/blob/devel/misc/meme.png"/>
</p>

<table>
  <td>master</td>
  <td>
    <a href="https://github.com/bergercookie/taskwarrior-syncall/actions" alt="master">
    <img src="https://github.com/bergercookie/taskwarrior-syncall/actions/workflows/ci.yml/badge.svg?branch=master" /></a>
  </td>
  <td>devel</td>
  <td>
    <a href="https://github.com/bergercookie/taskwarrior-syncall/actions" alt="devel">
    <img src="https://github.com/bergercookie/taskwarrior-syncall/actions/workflows/ci.yml/badge.svg?branch=devel" /></a>
  </td>
</table>

<a href='https://coveralls.io/github/bergercookie/taskwarrior-syncall?branch=master'>
<img src='https://coveralls.io/repos/github/bergercookie/taskwarrior-syncall/badge.svg?branch=master' alt='Coverage Status' /></a>
<a href="https://github.com/pre-commit/pre-commit">
<img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white" alt="pre-commit"></a>
<a href="https://github.com/bergercookie/taskwarrior-syncall/blob/master/LICENSE" alt="LICENSE">
<img src="https://img.shields.io/github/license/bergercookie/taskwarrior-syncall.svg" /></a>
<a href="https://pypi.org/project/takwarrior-syncall" alt="PyPI">
<img src="https://img.shields.io/pypi/pyversions/taskwarrior-syncall.svg" /></a>
<a href="https://badge.fury.io/py/taskwarrior-syncall">
<img src="https://badge.fury.io/py/taskwarrior-syncall.svg" alt="PyPI version" height="18"></a>
<a href="https://pepy.tech/project/taskwarrior-syncall">
<img alt="Downloads" src="https://pepy.tech/badge/taskwarrior-syncall"></a>
<a href="https://github.com/psf/black">
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## Description

`taskwarrior-syncall` is your one-stop software to bi-directionally synchronize a variety of
services with taskwarrior. Each synchronization comes with its own executable
which handles the synchronization between that particular service and
taskwarrior. Note that the name is `taskwarrior`-specific but it's not tied to
taskwarrior; You can synchronize items/tasks etc. from two arbitrary sides,
given that you [implement the corresponding synchronization
sides](implement-a-new-synchronization.md).

At the moment the list of supported synchronization combinations is the following:

<table style="undefined;table-layout: fixed; width: 823px">
<thead>
  <tr>
    <th></th>
    <th>Description</th>
    <th>Executable</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td><a href="https://github.com/bergercookie/taskwarrior-syncall/blob/master/readme-gcal.md">README</a></td>
    <td> <a href="https://taskwarrior.org/">Taskwarrior</a> ⬄ <a href="https://calendar.google.com/">Google Calendar</a></td>
    <td><tt>tw-gcal-sync</tt></td>
  </tr>
  <tr>
    <td><a href="https://github.com/bergercookie/taskwarrior-syncall/blob/master/readme-notion.md">README</a></td>
    <td> <a href="https://taskwarrior.org/">Taskwarrior</a> ⬄ <a href="https://notion.so">Notion Checkboxes</a></td>
    <td><tt>tw-notion-sync</tt></td>
  </tr>
  <tr>
    <td><a href="https://github.com/bergercookie/taskwarrior-syncall/blob/master/readme-gkeep.md">README</a></td>
    <td> <a href="https://taskwarrior.org/">Taskwarrior</a> ⬄ <a href="https://www.google.com/keep/">Google Keep Checkboxes</a></td>
    <td><tt>tw-gkeep-sync</tt></td>
  </tr>
</tbody>
</table>

Overall, each of the above should support _bi-directional_ synchronization
between the said services. This means that on an _addition_, _modification_, or
_deletion_ of an item on one side, a corresponding addition, modification or
deletion of the counterpart item will occur on the other side so that the two
sides are eventually in sync. All services also support dependency resolution
and a few different synchronization strategies so that, on conflict, the user
can specify whether to always select the change from side A (`AlwaysFirstRS`),
the change from side B (`AlwaysSecondRS`), the most recent change of the two
(`MostRecentRS`), or the least (`LeastRecentRS`).

By the end of the run, it should show you a summary of what's been done, like
the following.

```
Google Keep
-----------
        * Items created: 3
        * Items updated: 2
        * Items deleted: 1

Taskwarrior
-----------
        * Items created: 1
        * Items updated: 2
        * Items deleted: 0
```

Refer to the corresponding README for the list above for instructions specific
to the synchronization with that particular service. Before jumping to that
though, please complete the installation instructions below.

### Sample Usage Instructions

Here's the CLI help page for the synchronizations available. Run with `--help`
to get the most updated instructions

<!-- pastehere start cli_help -->
<details>
  <summary><tt>tw_gcal_sync</tt></summary>

```
tw_gcal_sync --help
Usage: tw_gcal_sync [OPTIONS]

  Synchronize calendars from your Google Calendar with filters from
  Taskwarrior.

  The list of TW tasks is determined by a combination of TW tags and a TW
  project while the calendar in GCal should be provided by their name. if it
  doesn't exist it will be crated

Options:
  -c, --gcal-calendar TEXT        Name of the Google Calendar to sync (will be
                                  created if not there)
  --google-secret FILE            Override the client secret used for the
                                  communication with the Google APIs
  --oauth-port INTEGER            Port to use for OAuth Authentication with
                                  Google Applications
  -t, --taskwarrior-tags TEXT     Taskwarrior tags to sync
  -p, --tw-project TEXT           Taskwarrior project to sync
  --list-configs                  List the available named TW<->Google
                                  Calendar combinations
  -r, --resolution_strategy [MostRecentRS|LeastRecentRS|AlwaysFirstRS|AlwaysSecondRS]
                                  Resolution strategy to use during conflicts
  -b, --combination TEXT          Name of an already saved TW<->Google
                                  Calendar combination
  -s, --save-as TEXT              Save the given TW<->Google Calendar filters
                                  combination using a specified custom name.
  -v, --verbose
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

</details>
<details>
  <summary><tt>tw_notion_sync</tt></summary>

```
$ tw_notion_sync --help
Usage: tw_notion_sync [OPTIONS]

  Synchronise filters of TW tasks with the to_do items of Notion pages

  The list of TW tasks is determined by a combination of TW tags and TW
  project while the notion pages should be provided by their URLs.

Options:
  -n, --notion-page TEXT          Page ID of the Notion page to sync
  --token, --token-pass-path TEXT
                                  Path in the UNIX password manager to fetch
  -t, --taskwarrior-tags TEXT     Taskwarrior tags to sync
  -p, --tw-project TEXT           Taskwarrior project to sync
  -r, --resolution_strategy [MostRecentRS|LeastRecentRS|AlwaysFirstRS|AlwaysSecondRS]
                                  Resolution strategy to use during conflicts
  -b, --combination TEXT          Name of an already saved TW<->Notion
                                  combination
  --list-configs                  List the available named TW<->Notion
                                  combinations
  -s, --save-as TEXT              Save the given TW<->Notion filters
                                  combination using a specified custom name.
  -v, --verbose
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

</details>
<details>
  <summary><tt>tw_gkeep_sync</tt></summary>

```
tw_gkeep_sync --help
Usage: tw_gkeep_sync [OPTIONS]

  Synchronize Notes from your Google Keep with filters from Taskwarrior.

  The list of TW tasks is determined by a combination of TW tags and a TW
  project while the note in GKeep should be specified using their full name.
  if it doesn't exist it will be created.

  This service will create TaskWarrior tasks with the specified filter for
  each one of the checkboxed items in the specified Google Keep note and will
  create Google Keep items for each one of the tasks in the Taskwarrior
  filter. You have to first "Show checkboxes" in the Google Keep Note in order
  to use it with this service.

Options:
  -k, --gkeep-note TEXT           Full title of the Google Keep Note to
                                  synchronize - Make sure you enable the
                                  checkboxes
  --user, --user-pass-path TEXT   Path in the UNIX password manager to fetch
                                  the Google username from
  --passwd, --passwd-pass-path TEXT
                                  Path in the UNIX password manager to fetch
                                  the Google password from
  -t, --taskwarrior-tags TEXT     Taskwarrior tags to sync
  -p, --tw-project TEXT           Taskwarrior project to sync
  --list-configs                  List the available named TW<->Google Keep
                                  combinations
  -r, --resolution_strategy [MostRecentRS|LeastRecentRS|AlwaysFirstRS|AlwaysSecondRS]
                                  Resolution strategy to use during conflicts
  -b, --combination TEXT          Name of an already saved TW<->Google Keep
                                  combination
  -s, --save-as TEXT              Save the given TW<->Google Keep filters
                                  combination using a specified custom name.
  -v, --verbose
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

</details>
<!-- pastehere end cli_help -->

## Installation instructions

### Requirements

- Taskwarrior - [Installation instructions](https://taskwarrior.org/download/) -
  Tested with `2.6.1`, should work with `>=2.6`.
- Python version >= `3.8`

### Installation Options

You have to specify at least one extra. To do so use the `[]` syntax in pip:

```sh
# for installing integration with google (e.g. Google Keep / Calendar) and Notion
pip3 install taskwarrior-syncall[notion,google]
```

- PyPI (may not contain latest version): `pip3 install --user --upgrade taskwarrior-syncall[notion,google,gkeep]`
- Github: `pip3 install --user git+https://github.com/bergercookie/taskwarrior-syncall`
- Download and install `devel` branch locally - bleeding edge

  ```sh
  git clone https://github.com/bergercookie/taskwarrior-syncall
  cd taskwarrior-syncall
  git checkout devel
  pip3 install --user --upgrade .
  ```

- Setup using [poetry](https://python-poetry.org/) - handy for local
  development and for isolation of dependencies:

  ```sh
  git clone https://github.com/bergercookie/taskwarrior-syncall
  poetry install
  # get an interactive shell
  poetry shell

  # now the executables of all the services should be in your PATH for the
  # current shell and you can also edit the source code without further
  # re-installation ...
  ```

## Mechanics / Automatic synchronization

To achieve synchronization between two arbitrary services, we use a push-pull
mechanism which is far easier and less troublesome than an automatic
synchronization solution. This means that you have to explicitly call the
executable for the synchronization you want to achieve. If you want to automate
this, consider adding a `cron` job or a `systemd` timer.

```sh
crontab -e
...

# Add the following to sync every 10' - modify the arguments according to your
# preferences and according to the instructions of the corresponding executable
# for example for `tw_gcal_sync`:
#
# See output and potential errors in your system logs (e.g., `/var/log/syslog`)
*/10 * * * * tw_gcal_sync -c "TW Reminders" -t "remindme"
```

## FAQ

<details>
  <summary>How do I reset the synchronization and start it from scratch?</summary>

1. Remove the combination file that corresponds to your synchronization. For
   example, if you're executing synchronization of `Google Keep` with
   `Taskwarrior`, like the following, your combination name is
   `testnote__None__test_tag`.

   ```sh
   tw_gkeep_sync -t test_tag -k "testnote"
   ```

   The executable also mentions the combination name at the end of the run.

   ```
   ...
   14:00:03.41 | INFO      | Flushing data to remote Google Keep...
   14:00:04.32 | SUCCESS   | Sync completed successfully. You can now use the -b/--combination option to refer to this particular combination

     tw_gkeep_sync --combination testnote__None__test_tag
   ```

   For this combination, on Linux, remove
   `~/.config/taskwarrior_syncall/testnote__None__test_tag.yaml`.

1. Remove the section for your combination in the `<sideA_sideB_configs.yaml>`
   configuration file under the `~/.config/taskwarrior_syncall/` directory.

   This section will have the same name as the combination file deleted in the
   earlier step and will look like this:

   ```yaml

   ---
   testnote__None__test_tag:
     gkeep_note: testnote
     tw_project: null
     tw_tags: !!python/tuple
       - test_tag
   ```

1. Remove the items of one of the sides. Keep e.g. the items from the Google Keep
   note and delete the tasks of the tag/project you are using for
   synchronization.
1. Rerun synchronization from scratch to populate the one side with the items of
   the other side.

</details>

<details>
  <summary>I want to synchronize more than a single (Notion page / TW filter),  (Google Calendar / TW filter) etc. combination.</summary>

See <a
href="https://github.com/bergercookie/taskwarrior-syncall/blob/master/combinations.md">combinations.md</a>.

</details>

## Miscellaneous

- [Implement a New Synchronization Service](implement-a-new-synchronization.md)
- [Using Multiple Combinations](combinations.md)

## Self Promotion

If you find this tool useful, please [star it on
Github](https://github.com/bergercookie/taskwarrior-syncall)

## TODO List

See [ISSUES list](https://github.com/bergercookie/taskwarrior-syncall/issues) for
the things that I'm currently either working on or interested in implementing in
the near future. In case there's something you are interesting in working on,
don't hesitate to either ask for clarifications or just do it and directly make
a PR.
