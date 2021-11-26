# Taskwarrior - Google Calendar synchroniser

<table>
  <td>master</td>
  <td>
    <a href="https://github.com/bergercookie/taskw_gcal_sync/actions" alt="master">
    <img src="https://github.com/bergercookie/taskw_gcal_sync/actions/workflows/ci.yml/badge.svg" /></a>
  </td>
  <td>devel</td>
  <td>
    <a href="https://github.com/bergercookie/taskw_gcal_sync/actions" alt="devel">
    <img src="https://github.com/bergercookie/taskw_gcal_sync/actions/workflows/ci.yml/badge.svg?branch=devel" /></a>
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
<a href="https://badge.fury.io/py/taskw-gcal-sync">
<img src="https://badge.fury.io/py/taskw-gcal-sync.svg" alt="PyPI version" height="18"></a>
<a href="https://pepy.tech/project/taskw-gcal-sync">
<img alt="Downloads" src="https://pepy.tech/badge/taskw-gcal-sync"></a>
<a href="https://github.com/psf/black">
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

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
Calendar](https://calendar.google.com). Given a _Calendar_ name for Google
Calendar and a _filter_ for Taskwarrior (currently only a single tag is
supported and tested) synchronise all the events between them.

Overall, it supports synchronisation on the following events:

- Creation of an event
- Modification of an (existing) event
- Deletion of an event

The aforementioned features should work bidirectional, meaning a reminder
created, modified, or deleted from Google Calendar should also be created,
modified, or deleted respectively in TaskWarrior and vice-versa

## Demo - first run - populating calendar in GCal

![demo_gif](misc/demo.gif)

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

- Taskwarrior - [Installation instructions](https://taskwarrior.org/download/) -
  Tested with 2.5.1
- Python version >= 3.8

Installation Options:

- Pypi (may not contain latest version): `pip3 install --user --upgrade taskw_gcal_sync`
- Github: `pip3 install --user git+https://github.com/bergercookie/taskw_gcal_sync`
- Download and install `devel` branch locally - bleeding edge

  ```sh
  git clone https://github.com/bergercookie/taskw_gcal_sync
  cd taskw_gcal_sync
  git checkout devel
  pip3 install --user --upgrade .
  ```

- Setup using [poetry](https://python-poetry.org/) - handy for local
  development:

  ```sh
  git clone https://github.com/bergercookie/taskw_gcal_sync
  poetry install
  # get an interactive shell
  poetry shell

  # now tw_gcal_sync is in your PATH in this shell and you can also edit and the
  # changes will take instant effect
  ...
  ```

## Override Calendar API key

Unfortunately I've yet to verify this app with Google so new users are
currently blocked from using it. To bypass that you can register for your own
developer account with the Google Calendar API with the following steps:

Firstly, removed the `~/.gcal_credentials.pickle` file on your system since that
will be reused if found by the app.

For creating your own Google Developer App:

- Go to the Google developer console
- Make a new project
- From the sidebar go to `API & Services` and once there click the `ENABLE APIS
  AND SERVICES` button
- Look for and Enable the `Calendar API`

Your newly created app now has access to the Calendar API. We now have to create
and download the credentials:

- Again, from the sidebar under `API And Services` click `Credentials`
- Enable the `Calendar API`
- On the sidebar click `Credentials`, and once there click `CREATE CREDENTIALS`
- Create a new `OAuth Client ID`. Set the type to `Desktop App` (app name is not
  important).
- Finally download the credentials in JSON form by clicking the download button
  as shown below. This is the file you need to point to when running
  `tw_gcal_sync`.

  ![download-btn](misc/gcal-json-btn.png)

To specify your custom credentials JSON file use the `--gcal-secret` flag as follows:

```sh
tw_gcal_sync -c "<calendar-name>" -t "<taskwarrior-tag>" --gcal-secret "<path/to/downloaded/json/file>"
```

## Usage instructions

Run the `tw_gcal_sync` to synchronise the Google calendar of your choice with
the selected Taskwarrior tag(s). Run with `--help` for the list of options.

```sh
# Sync the +remindme Taskwarrior tag with the calendar named "TW Reminders"

tw_gcal_sync --help
tw_gcal_sync -t remindme -c "TW Reminders"
```

## Mechanics / Automatic Synchronisation

To achieve synchronization across the two services, we use a push-pull mechanism
which is far easier and less troublesome than an automatic synchronization
solution. In case the latter behavior is desired, users may just run the
script periodically e.g., using cron:

```sh
$ crontab -e
...

# Add the following to sync every 10' - modify Calendar and Tag name accordingly
# See output and potential errors in your system logs (e.g., `/var/log/syslog`)
*/10 * * * * tw_gcal_sync -c "TW Reminders" -t "remindme"
```

## Troubleshooting

- Having trouble installing or using the tool? Take a look at either the
  continuous-integration configuration or the unittsests for the installation
  steps or the recommended way of using the python code respectively.
- Something doesn't work? Does the script fail midway through?

  - Record the problem and report it in the ISSUES page. Include as much
    information as possible so that I can reproduce it.
  - Clean the configuration file. By default that's going to be
    `$HOME/.config/taskw_gcal_sync`:

    `rm -rf ~/.config/taskw_gcal_sync`

  - Remove the corresponding Google Calendar
  - Rerun synchronisation from scratch to populate Google Calendar with all the
      events from your selected taskwarrior filter.

## Self Promotion

If you find this tool useful, please [star it on
Github](https://github.com/bergercookie/taskw_gcal_sync)

## TODO List

See [ISSUES list](https://github.com/bergercookie/taskw_gcal_sync/issues) for
the things that I'm currently either working on or interested in implementing in
the near future. In case there's something you are interesting in working on,
don't hesitate to either ask for clarifications or just do it and directly make
a PR.
