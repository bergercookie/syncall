# Taskwarrior Filtering

Synchronizations that interact with Taskwarrior can make use of a few different
command line options to determine the list of Taskwarrior tasks to synchronize.
At the time of writing here's the relevant flags:

```text
-f, --tw-filter TEXT            Taskwarrior filter for specifying the tasks
                                to synchronize. These filters will be
                                concatenated using OR  with potential tags
                                and projects potentially specified.
--all, --taskwarrior-all-tasks  Sync all taskwarrior tasks (potentially very
                                slow).
-t, --taskwarrior-tags TEXT     Taskwarrior tags to synchronize.
-p, --tw-project TEXT           Taskwarrior project to synchronize.
--days, --only-modified-last-X-days TEXT
                                Only synchronize Taskwarrior tasks that have
                                been modified in the last X days (specify X,
                                e.g., 1, 30, 0.5, etc.).
--prefer-scheduled-date         Prefer using the "scheduled" date field
                                instead of the "due" date if the former is
                                available.
```

Note that the `--all` option is mutually exclusive with the rest of the options.

Here's a few different option combinations:

- Synchronize tasks modified in the last 30 days:

  ```sh
  --days 30
  ```

- Synchronize tasks modified in the past month

  ```sh
  -f "modified.after:-1mo"
  ```

- Synchronize using virtual tags, e.g., the tasks that are overdue or are due:today

  ```sh
  -f "+OVERDUE or +TODAY"
  ```

- Synchronize last week's tasks that are tagged with `+work`:

  ```sh
  --days 7 -t work
  ```

## FAQ

### Why specify project / tags via the `-p` / `-t` options if I can can do that via the `-f` / `--tw-filter`

Tasks to be added to Taskwarrior will be assigned the said project/tags when the
`-p` / `-t` options are specified.

For example in the following execution, `tw_gtasks_sync` will pick up the tasks
that are tagged via `mytag`, it will join them with tasks that are `+OVERDUE
description.startswith:myprefix +mytag2` (OR condition) and it will sync them
with the tasks in the `reminders` Google Tasks list. Any tasks newly added from
Google Tasks to Taskwarrior _will_ be assigned the `mytag` tag, however they
won't be assigned the `mytag2` tag since the latter is part of the filter.

```sh
tw_gtasks_sync  -l reminders -t mytag  -f "+OVERDUE description.startswith:myprefix +mytag2"
```

### How can I find out the resulting aggregated filter used to fetch tasks from Taskwarrior

Run your synchronization app in verbose mode, using `-v` or `-vv`. Look for a
line like the following:

```text
10:22:21.42 | DEBUG     | Using the following filter to fetch TW tasks: ( +mytag or ((+OVERDUE pro:myproj) and -mytag2) )
```

This filter was generated from the following `tw_gtasks_sync` execution:

```sh
tw_gtasks_sync -l reminders -t mytag -f "((+OVERDUE pro:myproj) and -mytag2)" -v
```
