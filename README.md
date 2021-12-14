# taskwarrior-syncall

<p align="center">
  <img src="https://github.com/bergercookie/taskwarrior-syncall/blob/devel/misc/meme.png"/>
</p>

<table>
  <td>master</td>
  <td>
    <a href="https://github.com/bergercookie/taskwarrior-syncall/actions" alt="master">
    <img src="https://github.com/bergercookie/taskwarrior-syncall/actions/workflows/ci.yml/badge.svg" /></a>
  </td>
  <td>devel</td>
  <td>
    <a href="https://github.com/bergercookie/taskwarrior-syncall/actions" alt="devel">
    <img src="https://github.com/bergercookie/taskwarrior-syncall/actions/workflows/ci.yml/badge.svg?branch=devel" /></a>
  </td>
</table>

<a href="https://github.com/pre-commit/pre-commit">
<img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white" alt="pre-commit"></a>
<a href="https://www.codacy.com/app/bergercookie/taskwarrior-syncall" alt="Quality - devel">
<img src="https://api.codacy.com/project/badge/Grade/57206a822c41420bb5792b2cb70f06b5"/></a>
<a href="https://www.codacy.com/app/bergercookie/taskwarrior-syncall">
<img src="https://api.codacy.com/project/badge/Coverage/57206a822c41420bb5792b2cb70f06b5"/></a>
<a href="https://github.com/bergercookie/taskwarrior-syncall/blob/master/LICENSE" alt="LICENSE">
<img src="https://img.shields.io/github/license/bergercookie/taskwarrior-syncall.svg" /></a>
<a href="https://pypi.org/project/takwarrior-syncall" alt="pypi">
<img src="https://img.shields.io/pypi/pyversions/taskwarrior-syncall.svg" /></a>
<a href="https://badge.fury.io/py/taskwarrior-syncall">
<img src="https://badge.fury.io/py/taskwarrior-syncall.svg" alt="PyPI version" height="18"></a>
<a href="https://pepy.tech/project/taskwarrior-syncall">
<img alt="Downloads" src="https://pepy.tech/badge/taskwarrior-syncall"></a>
<a href="https://github.com/psf/black">
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## Description

`taskwarrior-syncall` is your one-stop software to synchronize a variety of
services with taskwarrior - in a bi-directional manner. Each synchronization
comes with one executable which handles the synchronization between that
particular service and taskwarrior.

At the moment the list of services supported is a bit limited but keeps growing
by the day:

- [[readme-gcal](https://github.com/bergercookie/taskwarrior-syncall/blob/devel/readme-gcal.md)] Taskwarrior ⬄ [Google Calendar](https://calendar.google.com/) Synchronization, via `tw_gcal_sync`
- [[readme-notion](https://github.com/bergercookie/taskwarrior-syncall/blob/devel/readme-notion.md)] Taskwarrior ⬄ [Notion](https://notion.so) Synchronization, via `tw_notion_sync`
- [ONGOING] [[readme-clickup](https://github.com/bergercookie/taskwarrior-syncall/blob/devel/readme-clickup.md)] Taskwarrior ⬄ [ClickUp](https://clickup.com) Synchronization, via `tw_clickup_sync`

Overall, each of the above should support _bi-directional_ synchronization between
Taskwarrior and the service of your preference. This means that on an
addition, modification, deletion etc. of an item on one side, a corresponding
addition, modification or deletion of a counterpart item will occur on the other
side so that the two sides are eventually in sync. This should work
bi-directionally, meaning an item created, modified, or deleted from a service
should also be created, modified, or deleted respectively in Taskwarrior and
vice-versa.

Refer to the corresponding README for the list above for instructions specific
to the synchronization with that particular service. Before jumping to that
README though, please complete the installation instructions below.

## Installation instructions

Requirements:

- Taskwarrior - [Installation instructions](https://taskwarrior.org/download/) -
  Tested with `2.6.1`, should work with `>=2.6`.
- Python version >= `3.8`

Installation Options:

- Pypi (may not contain latest version): `pip3 install --user --upgrade taskwarrior-syncall`
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

To achieve synchronization across taskwarrior and a service at hand, we use a
push-pull mechanism which is far easier and less troublesome than an automatic
synchronization solution. In case the latter behavior is desired, users may just
run the script periodically e.g., using cron:

```sh
$ crontab -e
...

# Add the following to sync every 10' - modify the arguments according to your
# preferences and according to the instructions of the corresponding executable
# for example for `tw_gcal_sync`:
#
# See output and potential errors in your system logs (e.g., `/var/log/syslog`)
*/10 * * * * tw_gcal_sync -c "TW Reminders" -t "remindme"
```

## Self Promotion

If you find this tool useful, please [star it on
Github](https://github.com/bergercookie/taskwarrior-syncall)

## TODO List

See [ISSUES list](https://github.com/bergercookie/taskwarrior-syncall/issues) for
the things that I'm currently either working on or interested in implementing in
the near future. In case there's something you are interesting in working on,
don't hesitate to either ask for clarifications or just do it and directly make
a PR.
