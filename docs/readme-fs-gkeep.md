# Local Files ⬄ [Google Keep Notes](https://www.google.com/keep/)

## Description

Synchronize all the Google Keep Notes (optionally filtered with a label) with a
List of files under a local directory. The Taskwarrior _filter_ may be a task, a
project or a combination of a project and arbitrary tags.

Upon execution, `fs_gkeep_sync` will synchronize, and on subsequent runs of the
program keep synchronized, the following attributes:

- Text of Google Keep note <-> File contents
- Title of Google Keep note <-> File name

## Usage example

To synchronize all the notes of your Google Keep labelled as `test` with all the
files under `fs_tests_dir` you can use something like:

```sh
fs_gkeep_sync --gkeep-labels test  --fs $PWD/fs_tests_dir
```

You can also save this combination under a specific name and then use that name
instead of specifying all the parameters explicitly

```sh
fs_gkeep_sync --gkeep-labels test  --fs $PWD/fs_tests_dir -s named_sync
# OR
fs_gkeep_sync --gkeep-labels test  --fs $PWD/fs_tests_dir --save-as named_sync

# and then run it using -b/--combination
fs_gkeep_sync -b named_sync
```

See the [Credentials](#credentials) section on how to authenticate with Google.

## Demo

![fs-gkeep-demo](https://github.com/bergercookie/syncall/raw/master/misc/fs-gkeep.gif)

## Limitations

- This synchronization has only been tested on Ubuntu 20.04. It should work on
  other Linux distros and should likely work on MacOS too.
- The root directory specified for the synchronization must be on a filesystem
  that supports [extended
  attributes](https://en.wikipedia.org/wiki/Extended_file_attributes) for
  example `ext4`. `xattr`s are used to associate the files at hand with their
  counterparts in Google Keep
- Currently renaming/moving the root directory for synchronization is not
  supported. You also have to be consistent specifying the name of the said
  directory, i.e., always specify it as an absolute path or always add it as
  the same relative path. As the verbatim name provided is used for naming this
  combination this will create two different combinations and will lead to
  duplication of entries.

  ```sh
  # ❗❗❗ The following set of commands will add duplicate entries in either
  # side
  fs_gkeep_sync --gkeep-labels test  --fs fs_tests_dir/
  fs_gkeep_sync --gkeep-labels test  --fs $PWD/fs_tests_dir/
  ```

  One way to bypass this would be to always name the combination.

  ```sh
  # This will do the right thing and not duplicate entries.
  fs_gkeep_sync --gkeep-labels test  --fs fs_tests_dir/  --save-as my_named_combination
  fs_gkeep_sync --gkeep-labels test  --fs $PWD/fs_tests_dir/ --save-as my_named_combination
  ```

- This only works for `Note` types in Google Keep. If a note is of type `List`
  (i.e., if the checkboxes are enabled) it won't be used for synchronization).

## Installation

### Package Installation

Install the `syncall` package from PyPI, enabling the `gkeep` and `fs`
extras:

```sh
pip3 install syncall[gkeep,fs]
```

### Credentials

We're using the unofficial
[gkeepapi](https://gkeepapi.readthedocs.io/en/latest/index.html) tool to
authenticate and interact with Google Keep. It requires your Google account
username and password to do so. If you're using 2FA, you should create a direct
password and use that instead.

Read more about this [here](https://gkeepapi.readthedocs.io/en/latest/#faq).

To provide the password, you can either use the `GKEEP_USERNAME` and
`GKEEP_PASSWD` before running `fs_gkeep_sync` or (recommended), use [the UNIX
Password Manager](https://wiki.archlinux.org/title/Pass) to store your username and
password to your Google account and provide the paths to them (use
`--user-pass-path ... --passwd-pass-path ...` in this case).

If using the UNIX Password Manager, make sure that you also have the gpg-agent
otherwise the tool will always prompt you for your GPG passphrase and will fail
if that's not provided.
