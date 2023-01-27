"""
tssplit
----------------------------------

Tests for `toolbox_utils` module.
"""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from toolbox_utils import tsutils


@pytest.mark.parametrize(
    "test_input, expected, kwds",
    [
        ("file.wdm,test.wdm:another.wdm", ["file.wdm", "test.wdm", "another.wdm"], {}),
        ("'file.wdm','test,'", ["'file.wdm'", "'test,'"], {"quote_keep": True}),
    ],
)
def test_tssplit(test_input, expected, kwds):
    dtr = tsutils.tssplit(test_input, **kwds)

    assert dtr == expected
