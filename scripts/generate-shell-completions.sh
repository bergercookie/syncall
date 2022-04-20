#!/usr/bin/env bash
set -e
# set -x

# helpers ----------------------------------------------------------------------
function finish {
    tabs 8
}
trap finish EXIT

function inside_virtualenv() {
    python3 -qc "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)"
}

function inside_git_repo() {
    git rev-parse
}

function completion_dir_for() {
    dir_=$completions_dir/$1
    mkdir -p $dir_
    echo "$dir_/$2"
}

function get_ext_for() {
    if [[ "$1" == "bash" || "$1" == "zsh" ]]; then
        echo ".sh"
    elif [[ "$1" == "fish" ]]; then
        echo ".fish"
    else
        echo ""
    fi
}

# sanity checks ----------------------------------------------------------------
if ! inside_virtualenv; then
    echo "You are not inside a virtualenv, can't proceed. Run "poetry shell" first".
    exit 1
fi

if ! inside_git_repo; then
    echo "You are not inside a git repo..."
    exit 1
fi

git_root_dir=$(git rev-parse --show-toplevel)

if [[ $(basename $git_root_dir) != "syncall" ]]; then
    echo "This isn't the syncall repo -> $git_root_dir"
    exit 1
fi

completions_dir="${git_root_dir}/completions"
mkdir -p $completions_dir

# main loop --------------------------------------------------------------------
for exec in tw_gkeep_sync tw_notion_sync tw_gcal_sync tw_asana_sync fs_gkeep_sync; do
    tabs 4
    # Run the following, grab the output and dumpt it to the completions/ files...
    # _TW_GKEEP_SYNC_COMPLETE=fish_source tw_gkeep_sync
    envvar="_$(echo $exec | tr "[:lower:]" "[:upper:]")_COMPLETE"
    for shell in "bash" "zsh" "fish"; do
        echo -e "Generating completions for [$exec\t| $shell\t]"

        # Execute command, grab its output, redirect it to file.
        export $envvar=${shell}_source
        contents=$($exec)

        path="$(completion_dir_for $shell $exec)$(get_ext_for $shell)"
        echo "$contents" > "$path"
    done
done
