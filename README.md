# Taskwarrior - Google Calendar synchroniser

<table>
  <td>master</td>
  <td>
    <a href="https://travis-ci.com/bergercookie/taskw_gcal_sync" alt="master">
    <img src="https://travis-ci.com/bergercookie/taskw_gcal_sync.svg?branch=master" /></a>
  </td>
  <td>devel</td>
  <td>
    <a href="https://travis-ci.com/bergercookie/taskw_gcal_sync" alt="devel">
    <img src="https://travis-ci.com/bergercookie/taskw_gcal_sync.svg?branch=devel" /></a>
  </td>
</table>

<a href="https://www.codacy.com/app/bergercookie/taskw_gcal_sync" alt="Quality - devel">
<img src="https://api.codacy.com/project/badge/Grade/57206a822c41420bb5792b2cb70f06b5"/></a>
<a href="https://www.codacy.com/app/bergercookie/taskw_gcal_sync">
<img src="https://api.codacy.com/project/badge/Coverage/57206a822c41420bb5792b2cb70f06b5"/></a>
<a href=https://github.com/bergercookie/taskw_gcal_sync/blob/devel/LICENSE" alt="LICENCE">
<img src="https://img.shields.io/github/license/bergercookie/taskw_gcal_sync.svg" /></a>
<a href="https://pypi.org/project/taskw-gcal-sync/" alt="pypi">
<img src="https://img.shields.io/pypi/pyversions/taskw_gcal_sync.svg" /></a>

```
 _            _                                _
| |_ __ _ ___| | ____      __   __ _  ___ __ _| |    ___ _   _ _ __   ___
| __/ _` / __| |/ /\ \ /\ / /  / _` |/ __/ _` | |   / __| | | | '_ \ / __|
| || (_| \__ \   <  \ V  V /  | (_| | (_| (_| | |   \__ \ |_| | | | | (__
 \__\__,_|___/_|\_\  \_/\_/____\__, |\___\__,_|_|___|___/\__, |_| |_|\___|
                         |_____|___/           |_____|   |___/
```

## Description

`taskw_gcal_sync` provides a solution for bidirectional synchronisation between
[Taskwarrior](https://taskwarrior.org) and [Google
Calendar](https://calendar.google.com). Given a *Calendar* name for Google
Calendar and a *filter* for Taskwarrior (currently only a single tag is
supported and tested) synchronise all the events between them.

Overall, it supports synchronisation on the following events:

- Creation of an event
- Modification of an (existing) event
- Deletion of an event

The aforementioned features should work bidirectional, meaning a reminder
created, modified, or deleted from Google Calendar should also be created,
modified, or deleted respectively in TaskWarrior and vice-versa

## Motivation

While Taskwarrior is an excellent tool when it comes to keeping TODO lists,
keeping track of project goals etc., lacks the portability, simplicity and
minimalistic design of Google Calendar. The latter also has the following
advantages:

- Automatic sync across all your devices
- Comfortable addition/modification of events using voice commands
- Actual reminding of events with a variety of mechanisms

## Installation instructions

Requirements:

- Taskwarrior - [Installation instructions](https://taskwarrior.org/download/)
- Python version >= 3.6 (yeah kind of restrictive, but
  [mypy](http://mypy-lang.org/) rocks!)
- Python package dependencies:  `pip3 install --user --upgrade -r requirements.txt # from the repo root dir`

Installation Choices:

- Pypi: `pip3 install --user --upgrade taskw_gcal_sync`
  + (will not contain latest version)
- github: `pip3 install --user git+https://github.com/bergercookie/taskw_gcal_sync`
- Download and install locally - bleeding edge

    ```sh
    git clone https://github.com/bergercookie/taskw_gcal_sync
    cd taskw_gcal_sync
    git checkout devel
    pip3 install --user --upgrade -r requirements.txt
    ```

## Usage instructions

Run the `tw_gcal_sync` to synchronise the Google calendar of your choice with
the selected Taskwarrior tag(s). Run with `--help` for the list of options.

```sh
# Sync the +remindme Taskwarrior tag with the calendar named "TW Reminders"

tw_gcal_sync --help
tw_gcal_sync -t remindme -c "TW Reminders"
```

## Mechanics

To achieve synchronization across the two services, we use a push-pull mechanism
which is far easier and less troublesome than an automatic synchronization
solution. In case the latter behavior is desired, users may just run the
script periodically e.g., using a `cron`.

## Troubleshooting

* Having trouble installing or using the tool? Take a look at either the
    continuous-integration configuration or the unittsests for the installation
    steps or the recommended way of using the python code respectively.
* Something doesn't work? Does the script fail midway through?
  * Record the problem and report it in the ISSUES page. Include as much
      information as possible so that I can reproduce it.
  * Clean the configuration file. By default that's going to be
      `$HOME/.config/taskw_gcal_sync`

      `rm -rf ~/.config/taskw_gcal_sync`
  * Remove the corresponding Google Calendar
  * Rerun synchronisation from scratch

## Self Promotion

If you find this tool useful, please [star it on
Github](https://github.com/bergercookie/taskw_gcal_sync)

## TODO List

See [ISSUES list](https://github.com/bergercookie/taskw_gcal_sync/issues) for
the things that I'm currently either working on or interested in implementing in
the near future. In case there's something you are interesting in working on,
don't hesitate to either ask for clarifications or just do it and directly make
a PR.
