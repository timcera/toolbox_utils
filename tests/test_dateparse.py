"""
catalog
----------------------------------

Tests for `toolbox_utils` module.
"""

# Standard library imports
import datetime

# Third party imports
import pandas as pd
import pytest

# First party imports
from toolbox_utils import tsutils


@pytest.mark.parametrize(
    "test_input, strftime, expected",
    [
        (
            "2001-01-01T00:00:00+0000",
            None,
            datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc),
        ),
        ("2001-01-01", "%Y", "2001"),
        (pd.to_datetime("2001-01-01"), "%Y", "2001"),
        (
            pd.to_datetime("2001-01-01T00:00:00+0000"),
            None,
            datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc),
        ),
        (None, "%Y", None),
    ],
)
def test_parsedate(test_input, strftime, expected):
    dtr = tsutils.parsedate(test_input, strftime=strftime)

    assert dtr == expected


@pytest.mark.parametrize(
    "test_input, strftime, expected",
    [
        (
            "2001-01-01",
            datetime.datetime(2000, 1, 2, tzinfo=datetime.timezone.utc),
            "2001",
        ),
        ("2001-01-00", None, "2001"),
    ],
)
def test_parsedate_exceptions(test_input, strftime, expected):
    with pytest.raises((TypeError, ValueError)):
        _ = tsutils.parsedate(test_input, strftime=strftime)
