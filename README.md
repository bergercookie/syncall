# syncall

<p align="center">
  <img src="https://raw.githubusercontent.com/bergercookie/syncall/master/misc/meme.png"/>
</p>

<a href="https://github.com/bergercookie/syncall/actions" alt="master">
<img src="https://github.com/bergercookie/syncall/actions/workflows/ci.yml/badge.svg?branch=master" /></a>
<a href='https://coveralls.io/github/bergercookie/syncall?branch=master'>
<img src='https://coveralls.io/repos/github/bergercookie/syncall/badge.svg?branch=master' alt='Coverage Status' /></a>
<a href="https://github.com/pre-commit/pre-commit">
<img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white" alt="pre-commit"></a>
<a href="https://github.com/bergercookie/syncall/blob/master/LICENSE" alt="LICENSE">
<img src="https://img.shields.io/github/license/bergercookie/syncall.svg" /></a>
<a href="https://pypi.org/project/syncall" alt="PyPI">
<img src="https://img.shields.io/pypi/pyversions/syncall.svg" /></a>
<a href="https://badge.fury.io/py/syncall">
<img src="https://badge.fury.io/py/syncall.svg" alt="PyPI version" height="18"></a>
<a href="https://pepy.tech/project/syncall">
<img alt="Downloads" src="https://pepy.tech/badge/syncall"></a>
<a href="https://github.com/psf/black">
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## Description

`syncall` is your one-stop software to bi-directionally synchronize and keep in
sync the data from a variety of services. The framework is targeted towards, but
not limited to, the synchronization of note-taking and task management data.
Each synchronization comes with its own executable which handles the
synchronization services/sides at hand.

One of the main goals of `syncall` is to be extendable. Thus it should be easy
to introduce support for either a new service / synchronization side (e.g.,
ClickUp) or a new synchronization altogether (e.g., ClickUp <-> Google Keep)
given that you [implement the corresponding synchronization
sides and conversion methods](implement-a-new-synchronization.md). See also the
[CONTRIBUTING](CONTRIBUTING.md) guide to get started.

At the moment the list of supported synchronizations is the following:

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
    <td><a href="https://github.com/bergercookie/syncall/blob/master/readme-tw-gcal.md">README</a></td>
    <td> <a href="https://taskwarrior.org/">Taskwarrior</a> ⬄ <a href="https://calendar.google.com/">Google Calendar</a></td>
    <td><tt>tw-gcal-sync</tt></td>
  </tr>
  <tr>
    <td><a href="https://github.com/bergercookie/syncall/blob/master/readme-tw-notion.md">README</a></td>
    <td> <a href="https://taskwarrior.org/">Taskwarrior</a> ⬄ <a href="https://notion.so">Notion Checkboxes</a></td>
    <td><tt>tw-notion-sync</tt></td>
  </tr>
  <tr>
    <td><a href="https://github.com/bergercookie/syncall/blob/master/readme-tw-gkeep.md">README</a></td>
    <td> <a href="https://taskwarrior.org/">Taskwarrior</a> ⬄ <a href="https://www.google.com/keep/">Google Keep Checkboxes</a></td>
    <td><tt>tw-gkeep-sync</tt></td>
  </tr>
  <tr>
    <td><a href="https://github.com/bergercookie/syncall/blob/master/readme-tw-asana.md">README</a></td>
    <td> <a href="https://taskwarrior.org/">Taskwarrior</a> ⬄ <a href="https://www.asana.com">Asana Tasks</a></td>
    <td><tt>tw-asana-sync</tt></td>
  </tr>
  <tr>
    <td><a href="https://github.com/bergercookie/syncall/blob/master/readme-tw-caldav.md">README</a></td>
    <td> <a href="https://taskwarrior.org/">Taskwarrior</a> ⬄ Generic <a href="https://en.wikipedia.org/wiki/CalDAV">Caldav </a> server</td>
    <td><tt>tw-caldav-sync</tt></td>
  </tr>
  <tr>
    <td><a href="https://github.com/bergercookie/syncall/blob/master/readme-fs-gkeep.md">README</a></td>
    <td>  Local Files ⬄  <a href="https://www.google.com/keep/">Google Keep Notes</a></td>
    <td><tt>fs-gkeep-sync</tt></td>
  </tr>
</tbody>
</table>

Each of the above should support _bi-directional_ synchronization between the
said services. This means that on an _addition_, _modification_, or _deletion_
of an item on one side, a corresponding addition, modification or deletion of
the counterpart item will occur on the other side so that the two sides are
eventually in sync. All synchronizations also support conflict resolution
meaning that it can successfully deal with item edits on both sides.

Currently unless the executable at hand specifies otherwise, the following
conflict resolution strategies are available:

<!-- START sniff-and-replace tw_gcal_sync --list-resolution-strategies START -->
<!-- OVERRIDES --no-collapsible --no-markdown OVERRIDES -->

1. MostRecentRS
2. LeastRecentRS
3. AlwaysFirstRS
4. AlwaysSecondRS

<!-- END sniff-and-replace -->

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
        * Items updated: 0
        * Items deleted: 0
```

Refer to the corresponding README from the list above for instructions specific
to the synchronization with that particular service. Before jumping to that
though, please complete the installation instructions below.

## Installation instructions

### Requirements

- Python version >= `3.8`
- For the integrations that require Taskwarrior - ([Installation
  instructions](https://taskwarrior.org/download/)) version `>=2.6` is required.

### Installation Options

You have to specify at least one extra. To do so use the `[]` syntax in pip:

```sh
# for installing integration with google (e.g. Google Keep / Calendar) and Notion
pip3 install syncall[notion,google]
```

Here's some of the available options for installing it:

- From PyPI - e.g., Specify three extras for integrations - Google Calendar, Google Keep, Notion): `pip3 install --user --upgrade syncall[notion,google,gkeep]`
- From Github - e.g., Specify two extras: `pip3 install --user "syncall[gkeep,fs] @ git+https://github.com/bergercookie/syncall"`
- Download and install `devel` branch locally - bleeding edge

  ```sh
  git clone https://github.com/bergercookie/syncall
  cd syncall
  git checkout devel
  pip3 install --user --upgrade .[gkeep,fs,google,tw,caldav,asana]
  ```

- Setup using [poetry](https://python-poetry.org/) - handy for local
  development and for isolation of dependencies:

  ```sh
  git clone https://github.com/bergercookie/syncall
  poetry install --all-extras
  # get an interactive shell
  poetry shell

  # now the executables of all the services should be in your PATH for the
  # current shell and you can also edit the source code without further
  # re-installation ...
  ```

### Sample Usage Instructions

Here's the CLI help page for the synchronizations available.

<!-- START sniff-and-replace tw_gcal_sync --help START -->

<details>
 <summary><tt>tw_gcal_sync --help</tt></summary>

```
Usage: tw_gcal_sync [OPTIONS]

  Synchronize calendars from your Google Calendar with filters from
  Taskwarrior.

  The list of TW tasks is determined by a combination of TW tags and a TW
  project while the calendar in GCal should be provided by their name. if it
  doesn't exist it will be crated

Options:
  -c, --gcal-calendar TEXT        Name of the Google Calendar to synchronize
                                  (will be created if not there)
  --google-secret FILE            Override the client secret used for the
                                  communication with the Google APIs
  --oauth-port INTEGER            Port to use for OAuth Authentication with
                                  Google Applications
  -t, --taskwarrior-tags TEXT     Taskwarrior tags to synchronize
  -p, --tw-project TEXT           Taskwarrior project to synchronize
  --list-combinations             List the available named TW<->Google
                                  Calendar combinations
  --list-resolution-strategies    List all the available resolution strategies
                                  and exit
  -r, --resolution-strategy [MostRecentRS|LeastRecentRS|AlwaysFirstRS|AlwaysSecondRS]
                                  Resolution strategy to use during conflicts
  -b, --combination TEXT          Name of an already saved TW<->Google
                                  Calendar combination
  -s, --save-as TEXT              Save the given TW<->Google Calendar filters
                                  combination using a specified custom name.
  --prefer-scheduled-date         Prefer using the "scheduled" date field
                                  instead of the "due" date if the former is
                                  available
  --default-event-duration-mins INTEGER
                                  The default duration of an event that is to
                                  be created on Google Calendar [in minutes]
  -v, --verbose
  --version                       Show the version and exit.
  --help                          Show this message and exit.

```

</details>

<!-- END sniff-and-replace -->
<!-- START sniff-and-replace tw_notion_sync --help START -->

<details>
 <summary><tt>tw_notion_sync --help</tt></summary>

```
Usage: tw_notion_sync [OPTIONS]

  Synchronise filters of TW tasks with the to_do items of Notion pages

  The list of TW tasks is determined by a combination of TW tags and TW
  project while the notion pages should be provided by their URLs.

Options:
  -n, --notion-page TEXT          Page ID of the Notion page to synchronize
  --token, --token-pass-path TEXT
                                  Path in the UNIX password manager to fetch
  -t, --taskwarrior-tags TEXT     Taskwarrior tags to synchronize
  -p, --tw-project TEXT           Taskwarrior project to synchronize
  -r, --resolution-strategy [MostRecentRS|LeastRecentRS|AlwaysFirstRS|AlwaysSecondRS]
                                  Resolution strategy to use during conflicts
  -b, --combination TEXT          Name of an already saved TW<->Notion
                                  combination
  --list-combinations             List the available named TW<->Notion
                                  combinations
  -s, --save-as TEXT              Save the given TW<->Notion filters
                                  combination using a specified custom name.
  -v, --verbose
  --version                       Show the version and exit.
  --help                          Show this message and exit.

```

</details>

<!-- END sniff-and-replace -->
<!-- START sniff-and-replace tw_gkeep_sync --help START -->

<details>
 <summary><tt>tw_gkeep_sync --help</tt></summary>

```
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
  --token, --token-pass-path TEXT
                                  Path in the UNIX password manager to fetch
                                  the google keep token from
  -t, --taskwarrior-tags TEXT     Taskwarrior tags to synchronize
  -p, --tw-project TEXT           Taskwarrior project to synchronize
  --list-combinations             List the available named TW<->Google Keep
                                  combinations
  -r, --resolution-strategy [MostRecentRS|LeastRecentRS|AlwaysFirstRS|AlwaysSecondRS]
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

<!-- END sniff-and-replace -->
<!-- START sniff-and-replace tw_asana_sync --help START -->

<details>
 <summary><tt>tw_asana_sync --help</tt></summary>

```
Usage: tw_asana_sync [OPTIONS]

Options:
  --token, --token-pass-path TEXT
                                  Path in the UNIX password manager to fetch
  -w, --asana-workspace-gid TEXT  Asana workspace GID used to filter tasks
  -W, --asana-workspace-name TEXT
                                  Asana workspace name used to filter tasks
  --list-asana-workspaces         List the available Asana workspaces
  -t, --taskwarrior-tags TEXT     Taskwarrior tags to synchronize
  -p, --tw-project TEXT           Taskwarrior project to synchronize
  -r, --resolution-strategy [MostRecentRS|LeastRecentRS|AlwaysFirstRS|AlwaysSecondRS]
                                  Resolution strategy to use during conflicts
  -b, --combination TEXT          Name of an already saved TW<->Asana
                                  combination
  --list-combinations             List the available named TW<->Asana
                                  combinations
  -s, --save-as TEXT              Save the given TW<->Asana filters
                                  combination using a specified custom name.
  -v, --verbose
  --version                       Show the version and exit.
  --help                          Show this message and exit.

```

</details>

<!-- END sniff-and-replace -->
<!-- START sniff-and-replace tw_caldav_sync --help START -->

<details>
 <summary><tt>tw_caldav_sync --help</tt></summary>

```
Usage: tw_caldav_sync [OPTIONS]

  Synchronize lists of tasks from your caldav Calendar with filters from
  Taskwarrior.

  The list of TW tasks is determined by a combination of TW tags and a TW
  project. Use `--all` to synchronize all tasks.

  The calendar in Caldav should be provided by their name. If it doesn't exist
  it will be created.

Options:
  --caldav-calendar TEXT          Name of the caldav Calendar to sync (will be
                                  created if not there)
  --caldav-url TEXT               URL where the caldav calendar is hosted at
                                  (including /dav if applicable)
  --caldav-user TEXT              The caldav username for the given caldav
                                  instance
  --caldav-passwd, --caldav-passwd-pass-path TEXT
                                  Path in the UNIX password manager to fetch
                                  the caldav password from
  --all, --taskwarrior-all-tasks  Sync all taskwarrior tasks [potentially very
                                  slow]
  -t, --taskwarrior-tags TEXT     Taskwarrior tags to synchronize
  -p, --tw-project TEXT           Taskwarrior project to synchronize
  --30-days, --only-modified-last-30-days
                                  Only synchronize Taskwarrior tasks that have
                                  been modified in the last 30 days
  --list-combinations             List the available named TW<->Caldav
                                  combinations
  -r, --resolution-strategy [MostRecentRS|LeastRecentRS|AlwaysFirstRS|AlwaysSecondRS]
                                  Resolution strategy to use during conflicts
  -b, --combination TEXT          Name of an already saved TW<->Caldav
                                  combination
  -s, --save-as TEXT              Save the given TW<->Caldav filters
                                  combination using a specified custom name.
  -v, --verbose
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

</details>

<!-- END sniff-and-replace -->
<!-- START sniff-and-replace fs_gkeep_sync --help START -->

<details>
 <summary><tt>fs_gkeep_sync --help</tt></summary>

```
Usage: fs_gkeep_sync [OPTIONS]

  Synchronize Notes from your Google Keep with text files in a directory on
  your filesystem.

  You can only synchronize a subset of your Google Keep notes based on a set
  of provided labels and you can specify where to create the files by
  specifying the path to a local directory. If you don't specify Google Keep
  Labels it will synchronize all your Google Keep notes.

  For each Google Keep Note, fs_gkeep_sync will create a corresponding file
  under the specified root directory with a matching name. Any addition,
  deletion and modification of the files on the filesystem will result in the
  corresponding addition, deletion and modification of the corresponding
  Google Keep item. The same holds the other way around.

Options:
  -k, --gkeep-labels TEXT         Google Keep labels whose notes to
                                  synchronize
  -i, --gkeep-ignore-labels TEXT  Google Keep labels whose notes will be
                                  explicitly ignored
  --user, --user-pass-path TEXT   Path in the UNIX password manager to fetch
                                  the Google username from
  --passwd, --passwd-pass-path TEXT
                                  Path in the UNIX password manager to fetch
                                  the Google password from
  --token, --token-pass-path TEXT
                                  Path in the UNIX password manager to fetch
                                  the google keep token from
  --ext, --filename-extension TEXT
                                  Use this extension for locally created files
  --fs, --fs-root TEXT            Directory to consider as root for
                                  synchronization operations
  --list-combinations             List the available named Filesystem<->Google
                                  Keep combinations
  -r, --resolution-strategy [MostRecentRS|LeastRecentRS|AlwaysFirstRS|AlwaysSecondRS]
                                  Resolution strategy to use during conflicts
  -b, --combination TEXT          Name of an already saved Filesystem<->Google
                                  Keep combination
  -s, --save-as TEXT              Save the given Filesystem<->Google Keep
                                  filters combination using a specified custom
                                  name.
  -v, --verbose
  --version                       Show the version and exit.
  --help                          Show this message and exit.

```

</details>

<!-- END sniff-and-replace -->

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
   `~/.config/syncall/testnote__None__test_tag.yaml`.

1. Remove the section for your combination in the `<sideA_sideB_configs.yaml>`
   configuration file under the `~/.config/syncall/` directory.

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
href="https://github.com/bergercookie/syncall/blob/master/combinations.md">combinations.md</a>.

</details>

## Tab Completion

All synchronization executables support tab auto-completion for their options
for `bash`, `zsh` and `fish`. You can find them under `completions/`

## Miscellaneous

- [Implement a New Synchronization Service](implement-a-new-synchronization.md)
- [Using Multiple Combinations](combinations.md)
- [Contributing Guide](CONTRIBUTING.md)

## Self Promotion

If you find this tool useful, please [star it on
Github](https://github.com/bergercookie/syncall)

## TODO List

See [ISSUES list](https://github.com/bergercookie/syncall/issues) for
the things that I'm currently either working on or interested in implementing in
the near future. In case there's something you are interesting in working on,
don't hesitate to either ask for clarifications or just do it and directly make
a PR.
