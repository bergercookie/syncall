import sys
from pathlib import Path
from typing import Optional, Sequence

import click
from bubop import (
    check_optional_mutually_exclusive,
    format_dict,
    log_to_syslog,
    logger,
    loguru_tqdm_sink,
)

from syncall import inform_about_app_extras
from syncall.cli import opt_filename_extension, opt_gkeep_ignore_labels

try:
    from syncall import GKeepNoteSide
except ImportError:
    inform_about_app_extras(["gkeep", "fs"])

from syncall import (
    Aggregator,
    FilesystemSide,
    __version__,
    cache_or_reuse_cached_combination,
    convert_filesystem_file_to_gkeep_note,
    convert_gkeep_note_to_filesystem_file,
    fetch_app_configuration,
    get_resolution_strategy,
    inform_about_combination_name_usage,
    list_named_combinations,
    report_toplevel_exception,
)
from syncall.app_utils import gkeep_read_username_password_token, write_to_pass_manager
from syncall.cli import (
    opt_combination,
    opt_custom_combination_savename,
    opt_filesystem_root,
    opt_gkeep_labels,
    opt_gkeep_passwd_pass_path,
    opt_gkeep_token_pass_path,
    opt_gkeep_user_pass_path,
    opt_list_combinations,
    opt_resolution_strategy,
)


@click.command()
# google keep options -------------------------------------------------------------------------
@opt_gkeep_labels()
@opt_gkeep_ignore_labels()
@opt_gkeep_user_pass_path()
@opt_gkeep_passwd_pass_path()
@opt_gkeep_token_pass_path()
# filesystem options --------------------------------------------------------------------------
@opt_filename_extension()
@opt_filesystem_root()
# misc options --------------------------------------------------------------------------------
@opt_list_combinations("Filesystem", "Google Keep")
@opt_resolution_strategy()
@opt_combination("Filesystem", "Google Keep")
@opt_custom_combination_savename("Filesystem", "Google Keep")
@click.option("-v", "--verbose", count=True)
@click.version_option(__version__)
def main(
    filesystem_root: Optional[str],
    gkeep_labels: Sequence[str],
    gkeep_ignore_labels: Sequence[str],
    gkeep_user_pass_path: str,
    gkeep_passwd_pass_path: str,
    gkeep_token_pass_path: str,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    do_list_combinations: bool,
    filename_extension: str,
):
    """
    Synchronize Notes from your Google Keep with text files in a directory on your filesystem.

    You can only synchronize a subset of your Google Keep notes based on a set of provided
    labels and you can specify where to create the files by specifying the path to a local
    directory. If you don't specify Google Keep Labels it will synchronize all your Google Keep
    notes.

    For each Google Keep Note, fs_gkeep_sync will create a corresponding file under the
    specified root directory with a matching name. Any addition, deletion and modification of
    the files on the filesystem will result in the corresponding addition, deletion and
    modification of the corresponding Google Keep item. The same holds the other way around.
    """
    # setup logger ----------------------------------------------------------------------------
    loguru_tqdm_sink(verbosity=verbose)
    log_to_syslog(name="fs_gkeep_sync")
    logger.debug("Initialising...")
    inform_about_config = False

    if do_list_combinations:
        list_named_combinations(config_fname="fs_gkeep_configs")
        return 0

    # cli validation --------------------------------------------------------------------------
    check_optional_mutually_exclusive(gkeep_labels, gkeep_ignore_labels)
    check_optional_mutually_exclusive(combination_name, custom_combination_savename)
    combination_of_filesystem_root_and_gkeep_labels_and_gkeep_ignore_labels = any(
        [
            filesystem_root,
            gkeep_labels,
            gkeep_ignore_labels,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name,
        combination_of_filesystem_root_and_gkeep_labels_and_gkeep_ignore_labels,
    )

    filesystem_root_path = None
    if filesystem_root is not None:
        filesystem_root_path = Path(filesystem_root)
        if not filesystem_root_path.is_dir():
            logger.error(
                "An existing directory must be provided for the synchronization ->"
                f" {filesystem_root_path}"
            )
            return 1

    # Let's strip any "."s in the name of this configuration - may mess up the PrefsManager
    if filename_extension.startswith("."):
        filename_extension = filename_extension[1:]

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            config_fname="fs_gkeep_configs", combination=combination_name
        )
        filesystem_root_path = Path(app_config["filesystem_root"])
        gkeep_labels = app_config["gkeep_labels"]
        gkeep_ignore_labels = app_config["gkeep_ignore_labels"]
        filename_extension = app_config["filename_extension"]
    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "filesystem_root": filesystem_root,
                "gkeep_labels": gkeep_labels,
                "gkeep_ignore_labels": gkeep_ignore_labels,
                "filename_extension": filename_extension,
            },
            config_fname="fs_gkeep_configs",
            custom_combination_savename=custom_combination_savename,
        )

    # more checks -----------------------------------------------------------------------------
    if filesystem_root_path is None:
        logger.error(
            "You have to provide at least one valid filesystem root path to use for "
            " synchronization. You can do so either via CLI arguments or by specifying an"
            " existing saved combination"
        )
        sys.exit(1)

    if not gkeep_labels and not gkeep_ignore_labels:
        logger.error(
            "Refusing to run without any Google Keep labels to keep or remove - please provide"
            " at least one of these two to continue"
        )
        sys.exit(1)

    # announce configuration ------------------------------------------------------------------
    logger.info(
        format_dict(
            header="Configuration",
            items={
                "Filesystem Root": filesystem_root,
                "Google Keep Labels": gkeep_labels,
                "Google Keep Labels to Ignore": gkeep_ignore_labels,
                "Filename Extension": filename_extension,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )

    # initialize sides ------------------------------------------------------------------------
    gkeep_user, gkeep_passwd, gkeep_token = gkeep_read_username_password_token(
        gkeep_user_pass_path,
        gkeep_passwd_pass_path,
        gkeep_token_pass_path,
    )

    # initialize google keep  -----------------------------------------------------------------
    gkeep_side = GKeepNoteSide(
        gkeep_labels=gkeep_labels,
        gkeep_ignore_labels=gkeep_ignore_labels,
        gkeep_user=gkeep_user,
        gkeep_passwd=gkeep_passwd,
        gkeep_token=gkeep_token,
    )

    # initialize Filesystem Side --------------------------------------------------------------
    filesystem_side = FilesystemSide(
        filesystem_root=filesystem_root_path, filename_extension=filename_extension
    )

    # sync ------------------------------------------------------------------------------------
    def converter_A_to_B(gkeep_note):
        return convert_gkeep_note_to_filesystem_file(
            gkeep_note=gkeep_note,
            filename_extension=filename_extension,
            filesystem_root=filesystem_root_path,
        )

    converter_A_to_B.__doc__ = convert_gkeep_note_to_filesystem_file.__doc__

    try:
        with Aggregator(
            side_A=gkeep_side,
            side_B=filesystem_side,
            converter_B_to_A=convert_filesystem_file_to_gkeep_note,
            converter_A_to_B=converter_A_to_B,
            resolution_strategy=get_resolution_strategy(
                resolution_strategy,
                side_A_type=type(gkeep_side),
                side_B_type=type(filesystem_side),
            ),
            config_fname=combination_name,
            ignore_keys=(
                (),
                (),
            ),
        ) as aggregator:
            aggregator.sync()
    except KeyboardInterrupt:
        logger.error("Exiting...")
        return 1
    except:
        report_toplevel_exception(is_verbose=verbose >= 1)
        return 1

    # cache the token
    token = gkeep_side.get_master_token()
    if token is not None:
        logger.debug(f"Caching the gkeep token in pass -> {gkeep_token_pass_path}...")
        write_to_pass_manager(password_path=gkeep_token_pass_path, passwd=token)

    if inform_about_config:
        inform_about_combination_name_usage(combination_name)

    return 0


if __name__ == "__main__":
    main()
