#compdef tw_gcal_sync

_tw_gcal_sync_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[tw_gcal_sync] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _TW_GCAL_SYNC_COMPLETE=zsh_complete tw_gcal_sync)}")

    for type key descr in ${response}; do
        if [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
            fi
        elif [[ "$type" == "dir" ]]; then
            _path_files -/
        elif [[ "$type" == "file" ]]; then
            _path_files -f
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

compdef _tw_gcal_sync_completion tw_gcal_sync;
