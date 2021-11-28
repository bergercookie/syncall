# [Taskwarrior](https://taskwarrior.org/) ⬄ [Notion](https://notion.so)

The main executable for this is called `tw_notion_sync`.

Synchronize all the `to_do` blocks of a Notion page with a filter in
Taskwarrior. The taskwarrior filter may be a task, a project or a combination of
a project and arbitrary tags.

Upon execution, `tw_notion_sync` will synchronize, and on subsequent runs of the
program keep synchronized the following attributes:

- Plaintext description of the to_do block <-> TW task title
- Whether it's checked ✅ or unchecked <-> TW task completion status
- to_do block is deleted / archived <-> TW task deletion

## Usage example

To synchronize the "to_do" blocks of a notion page with a tag called "test" you
can use something like:

```sh
tw_notion_sync -n <page-uuid-grabbed-from-page-url> -t test
```

## Demo

![tw-notion-demo](https://github.com/bergercookie/taskwarrior_syncall/raw/master/misc/tw_notion_sync.gif)

## Installation

### Package installation

Install the `taskwarrior-syncall` package from pypi, enabling the `notion`
extra:

```sh
pip3 install taskwarrior-syncall[notion]
```

### Create a notion application

After installing the python package, you have to create an app at notion. This a
mandatory step for now since I have not made this an official Notion
integration.

Navigate to your [Integrations](https://www.notion.so/my-integrations) create a
new application and copy the API token. The name of the application does not
matter.

You now have to explicitly give access to any page you want the newly created
application to use. After that, you can fetch the `UUID` of the page you want to
sync from the URL and paste it when running the `tw_notion_sync` script.

#### Reading the notion application token

There are two ways `tw_notion_sync` can read the aforementioned API token:

- Via the `NOTION_API_KEY` environment variable or,
- Via the [UNIX Password Manager](https://www.passwordstore.org/). You can
  specify the path in the Pass manager to read the encrypted token from. The
  default path is `notion.so/dev/integration/taskwarrior/token` under the
  password store.

  The latter will run `gpg` on the background and assumes that you are using a
  gpg-agent, otherwise it will ask you for your GPG password.

## FAQ

<details>
  <summary>How do I restart the synchronization from scratch?</summary>

- Clean the configuration file of the app. By default that's going to be:

  `$HOME/.config/taskwarrior_syncall/tw_notion_sync.yaml`

- Remove the items of one of the sides. Keep e.g. the items from the notion
  page and delete the tasks of the tag/project you are using for
  synchronization.
- Rerun synchronization from scratch to populate the one side with the items
  of the other side.

</details>

<details>
  <summary>I want to synchronize more than a single Notion page / TW filter combination</summary>

That's currently not possible but it is a work in progress.
If you want to start synchronizing a different combination, please clean the
configuration file and one of the two sides before doing so. Refer to the
previous FAQ item for more.

</details>
