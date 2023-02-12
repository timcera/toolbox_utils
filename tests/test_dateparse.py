"""
catalog
----------------------------------

Tests for `toolbox_utils` module.
"""

import datetime

import pandas as pd
import pytest

from toolbox_utils import tsutils


@pytest.mark.parametrize(
    "test_input, strftime, expected",
    [
        ("2001-01-01", None, datetime.datetime(2001, 1, 1)),
        ("2001-01-01", "%Y", "2001"),
        (pd.to_datetime("2001-01-01"), "%Y", "2001"),
        (pd.to_datetime("2001-01-01"), None, datetime.datetime(2001, 1, 1)),
        (None, "%Y", None),
    ],
)
def test_parsedate(test_input, strftime, expected):
    dtr = tsutils.parsedate(test_input, strftime=strftime)

    assert dtr == expected


@pytest.mark.parametrize(
    "test_input, strftime, expected",
    [
        ("2001-01-01", datetime.datetime(2000, 1, 2), "2001"),
        ("2001-01-00", None, "2001"),
    ],
)
def test_parsedate_exceptions(test_input, strftime, expected):
    with pytest.raises(Exception):
        _ = tsutils.parsedate(test_input, strftime=strftime)
