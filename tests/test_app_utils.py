import sys
from unittest.mock import patch

import pytest
from syncall.app_utils import (
    cache_or_reuse_cached_combination,
    fetch_app_configuration,
    inform_about_combination_name_usage,
    report_toplevel_exception,
)
from syncall.cli import _list_named_combinations
from syncall.constants import COMBINATION_FLAGS, ISSUES_URL


def test_list_named_combinations(fs, caplog, mock_prefs_manager):
    del fs

    with patch(
        "syncall.app_utils.PrefsManager",
        return_value=mock_prefs_manager,
    ):
        _list_named_combinations("doesnt matter")
        captured = caplog.text
        assert all(
            expected_config in captured
            for expected_config in (
                "kalimera",
                "kalinuxta",
                "kalispera",
            )
        )


def test_fetch_app_configuration(fs, caplog, mock_prefs_manager):
    del fs

    with patch("syncall.app_utils.PrefsManager", return_value=mock_prefs_manager):
        # invalid combination
        config = fetch_app_configuration(
            side_A_name="side A",
            side_B_name="side B",
            combination="kalimera",
        )
        assert list(config.keys()) == ["a", "b", "c"]
        assert list(config.values()) == [1, 2, [1, 2, 3]]
        captured = caplog.text
        assert "Loading configuration" in captured

        # invalid combination
        caplog.clear()
        with pytest.raises(RuntimeError):
            fetch_app_configuration(
                side_A_name="side A",
                side_B_name="side B",
                combination="doesntexist",
            )
        captured = caplog.text
        assert "No such configuration" not in captured


def test_report_toplevel_exception(caplog):
    report_toplevel_exception(is_verbose=False)
    assert ISSUES_URL in caplog.text


def test_inform_about_combination_name_usage(fs, caplog):
    del fs

    e = "kalimera"
    sys.argv[0] = e
    c = "kalinuxta"
    inform_about_combination_name_usage(combination_name=c)

    assert e in caplog.text
    assert c in caplog.text
    assert COMBINATION_FLAGS[0] in caplog.text
    assert COMBINATION_FLAGS[1] in caplog.text


def test_cache_or_reuse_cached_combination(fs, caplog, mock_prefs_manager):
    del fs
    with patch("syncall.app_utils.PrefsManager", return_value=mock_prefs_manager):
        cache_or_reuse_cached_combination(
            config_args={"a": 1, "b": 2, "c": 3},
            config_fname="TBD",
            custom_combination_savename=None,
        )

        assert "Caching this configuration" in caplog.text
        caplog.clear()

        cache_or_reuse_cached_combination(
            config_args={"a": 1, "b": 2, "c": 3},
            config_fname="kalimera",
            custom_combination_savename=None,
        )

        assert "Loading cached configuration" in caplog.text
        assert "1__2__3" in caplog.text
        caplog.clear()
