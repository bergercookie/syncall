import sys
from unittest.mock import patch

import pytest

from syncall import (
    cache_or_reuse_cached_combination,
    fetch_app_configuration,
    inform_about_combination_name_usage,
    list_named_combinations,
    report_toplevel_exception,
)
from syncall.constants import COMBINATION_FLAGS, ISSUES_URL


def test_list_named_combinations(fs, caplog, mock_prefs_manager):
    with patch(
        "syncall.app_utils.PrefsManager",
        return_value=mock_prefs_manager,
    ):
        list_named_combinations("doesnt matter")
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
    with patch("syncall.app_utils.PrefsManager", return_value=mock_prefs_manager):
        # invalid combination
        config = fetch_app_configuration(config_fname="doesntmatter", combination="kalimera")
        assert list(config.keys()) == ["a", "b", "c"]
        assert list(config.values()) == [1, 2, [1, 2, 3]]
        captured = caplog.text
        assert "Loading configuration" in captured

        # invalid combination
        caplog.clear()
        with pytest.raises(RuntimeError):
            fetch_app_configuration(config_fname="doesntmatter", combination="doesntexist")
            captured = caplog.text
            assert "No such configuration" in captured


def test_report_toplevel_exception(caplog):
    report_toplevel_exception(is_verbose=False)
    assert ISSUES_URL in caplog.text


def test_inform_about_combination_name_usage(fs, caplog):
    e = "kalimera"
    sys.argv[0] = e
    c = "kalinuxta"
    inform_about_combination_name_usage(combination_name=c)
    assert (
        e in caplog.text
        and c in caplog.text
        and COMBINATION_FLAGS[0] in caplog.text
        and COMBINATION_FLAGS[1] in caplog.text
    )


def test_cache_or_reuse_cached_combination(fs, caplog, mock_prefs_manager):
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

        assert "Loading cached configuration" in caplog.text and "1__2__3" in caplog.text
        caplog.clear()
