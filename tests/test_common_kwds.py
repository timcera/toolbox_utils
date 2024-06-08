"""
common_kwds
----------------------------------

Tests for `toolbox_utils` module.
"""

import pytest

from toolbox_utils import tsutils


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("file.wdm,test.wdm:another.wdm", ["file.wdm", "test.wdm", "another.wdm"]),
        ("'file.wdm','test,'", ["'file.wdm'", "'test,'"]),
    ],
)
def test_normalize_input(test_input, expected):
    dtr = tsutils.normalize_input(test_input)

    assert dtr == expected
