"""
catalog
----------------------------------

Tests for `toolbox_utils` module.
"""

from io import BytesIO, StringIO

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from toolbox_utils import tsutils


@pytest.mark.parametrize(
    "test_input, kwds, expected",
    [
        ("1,2", {}, [1, 2]),
        ("1, 2", {}, [1, 2]),
        ("1.0, 2.1, 3", {}, [1, 2.1, 3]),
        ("1.0, 2.1,, 3", {}, [1, 2.1, None, 3]),
        ("1.0 2.1 3", {"sep": " "}, [1, 2.1, 3]),
        ("1.0 2.1  3", {"sep": " "}, [1, 2.1, None, 3]),
        ([1.0, 2.1, 3], {}, [1, 2.1, 3]),
        ([1.0, 2.1, 3, [4.2, 5, 6.0], 3.4], {}, [1, 2.1, 3, 4.2, 5, 6, 3.4]),
        (
            [1.0, 2.1, 3, [4.2, 5, 6.0], 3.4],
            {"flat": False},
            [1, 2.1, 3, [4.2, 5, 6], 3.4],
        ),
        (None, {}, None),
        ("None", {}, None),
        ("", {}, None),
        (["astr,4.12,4.0,bstr"], {}, ["astr", 4.12, 4, "bstr"]),
        ((1, 2.1, "astr"), {"n": 3}, [1, 2.1, "astr"]),
        (
            pd.DataFrame([1, 2], index=[3, 4]),
            {"n": 1},
            [pd.DataFrame([1, 2], index=[3, 4])],
        ),
        (pd.Series([1, 2]), {}, [pd.DataFrame(pd.Series([1, 2]))]),
        (1, {}, [1]),
        (2.3, {}, [2.3]),
        ("This\n is\na\n test", {}, [StringIO("This\n is\na\n test")]),
        (b"This\n is\na\n test", {}, [BytesIO(b"This\n is\na\n test")]),
        (StringIO("a\nb"), {}, StringIO("a\nb")),
        (BytesIO(b"c\nd"), {}, BytesIO(b"c\nd")),
        ("This\r is\ra\r test", {}, [StringIO("This\r is\ra\r test")]),
        (StringIO("a\rb"), {}, StringIO("a\rb")),
        (BytesIO(b"c\rd"), {}, BytesIO(b"c\rd")),
    ],
)
def test_make_list(test_input, expected, kwds):
    test_output = tsutils.make_list(test_input, **kwds)

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
        ("1,2", {"n": 1}, [1, 2]),
        (
            [1.0, 2.1, 3, [4.2, 5, 6.0], 3.4],
            {"flat": False, "n": 1},
            [1, 2.1, 3, [4.2, 5, 6], 3.4],
        ),
        (["astr,4.12,4.0,bstr"], {"n": 2}, ["astr", 4.12, 4, "bstr"]),
        ((1, 2.1, "astr"), {"n": 4}, [1, 2.1, "astr"]),
        (1, {"n": 2}, [1]),
        (2.3, {"n": 2}, [2.3]),
    ],
)
def test_make_list_exception(test_input, expected, kwds):
    with pytest.raises(Exception):
        _ = tsutils.make_list(test_input, **kwds)
