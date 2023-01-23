function _fs_gkeep_sync_completion;
    set -l response;

    for value in (env _FS_GKEEP_SYNC_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) fs_gkeep_sync);
        set response $response $value;
    end;

    for completion in $response;
        set -l metadata (string split "," $completion);

        if test $metadata[1] = "dir";
            __fish_complete_directories $metadata[2];
        else if test $metadata[1] = "file";
            __fish_complete_path $metadata[2];
        else if test $metadata[1] = "plain";
            echo $metadata[2];
        end;
    end;
end;

complete --no-files --command fs_gkeep_sync --arguments "(_fs_gkeep_sync_completion)";
