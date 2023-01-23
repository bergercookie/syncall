# Combinations

## Description

Let's say you want to sync the events of a `Google Calendar` called `home` with
the tasks of a Taskwarrior tag,  `+home_rems`. You then decide to synchronize
the events of a second calendar, `work` with the contents of a second
project/tag combination `project:work +customerA`.

Each one of these, (i.e.: `calendar=home,tags=(+home_rems),project=None` and
`calendar=work,tags=(+customerA),project=work`) is called a `combination`.
`syncall` automatically isolates the execution of different
combinations, meaning that it doesn't mix the items of one combination with
the items of a different one. Regardless of the synchronization that you use,

You don't need to explicitly specify the name of the combination you want to
use. In this case, the name of the combination will automatically be determined,
and `syncall` will print this combination name at the end of the
run.

```
$ tw_gkeep_sync -t test_tag -k "testnote"
16:13:34.99 | INFO      | Loading preferences...
16:13:34.99 | INFO      |

Configuration:
===============

  - TW Tags         : ('test_tag',)
  - TW Project      : None
  - Google Keep Note: testnote

  ...

16:13:40.28 | INFO      | Flushing data to remote Google Keep...
16:13:40.62 | SUCCESS   | Sync completed successfully. You can now use the -b/--combination option to refer to this particular combination

  tw_gkeep_sync --combination testnote__None__test_tag
```

On subsequent synchronizations, you can either fully specify the arguments for
this synchronization, like you did the first time, or alternatively you can use
the `-b <combinationname>` flag.

```
tw_gkeep_sync -b testnote__None__test_tag
16:16:14.89 | INFO      | Loading preferences...
16:16:14.90 | INFO      |

Loading configuration - /home/berger/.config/syncall/tw_gkeep_configs.yaml.testnote__None__test_tag
16:16:14.90 | INFO      |

Configuration:
===============

  - TW Tags         : ('test_tag',)
  - TW Project      : None
  - Google Keep Note: testnote



16:16:15.19 | INFO      | Loading preferences...
16:16:17.70 | INFO      | Initializing Taskwarrior...
16:16:19.55 | INFO      | Detecting changes from GKeep...
16:16:19.58 | INFO      | Detecting changes from Tw...
16:16:19.58 | WARNING   |

Google Keep
-----------
        * Items created: 0
        * Items updated: 0
        * Items deleted: 0

Taskwarrior
-----------
        * Items created: 0
        * Items updated: 0
        * Items deleted: 0

16:16:19.58 | INFO      | Flushing data to remote Google Keep...
```

You can also manually name your combinations using the `-s/--save-as` option. Be
careful to only specify the `--save-as` on the first synchronization of your
services. If you have already synchronized them once, and on a subsequent run,
you re-synchronize with `--save-as <custom-name>` a full duplicate
synchronization will take place which is not what you want. In the future, the
tool will not allow using `-s/--save-as` if a combination already exists.

## Listing All Available Combinations

To list all the registered combinations for a particular executable, use the
`--list-combinations` flag. For example for `tw_gkeep_sync`:

```
$ tw_gkeep_sync --list-combinations
19:10:07.93 | SUCCESS   |

Named combinations currently available:
============================================

  - another_note__None__test1
  - mycombination
  - testnote__None__test_tag
```
