"""
catalog
----------------------------------

Tests for `toolbox_utils` module.
"""

from io import BytesIO, StringIO

import pytest
from pandas.testing import assert_frame_equal

from toolbox_utils import tsutils


@pytest.mark.parametrize(
    "test_input, kwds, expected",
    [
        ("1+2", {}, [1, 2]),
        ([1, 2], {}, [1, 2]),
        (["1:5"], {}, [1, 2, 3, 4, 5]),
        ("2+8:11+15", {}, [2, 8, 9, 10, 11, 15]),
        ("8:11:2+15+0:9", {}, [8, 10, 15, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        (2, {}, [2]),
    ],
)
def test_range_to_numlist(test_input, expected, kwds):
    test_output = tsutils.range_to_numlist(test_input, **kwds)

    try:
        if isinstance(test_output[0], (StringIO, BytesIO)):
            test_output = test_output[0].read()
            expected = expected[0].read()
    except TypeError:
        pass

    if isinstance(test_output, (StringIO, BytesIO)):
        test_output = test_output.read()
        expected = expected.read()

    try:
        assert test_output == expected
    except ValueError:
        assert_frame_equal(test_output[0], expected[0])


@pytest.mark.parametrize(
    "test_input, kwds, expected",
    [
        ("1,2", {}, [1, 2]),
        (
            [1.0, 2.1, 3, [4.2, 5, 6.0], 3.4],
            {},
            [1, 2.1, 3, [4.2, 5, 6], 3.4],
        ),
        (["astr,4.12,4.0,bstr"], {}, ["astr", 4.12, 4, "bstr"]),
        ((1, 2.1, "astr"), {}, [1, 2.1, "astr"]),
        (2.3, {}, [2.3]),
    ],
)
def test_range_to_numlist_exception(test_input, expected, kwds):
    with pytest.raises(Exception):
        _ = tsutils.range_to_numlist(test_input, **kwds)
