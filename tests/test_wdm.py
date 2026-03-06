"""
test_wdm
----------------------------------

Tests for `hspf_reader` module.
"""

from unittest import TestCase

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from toolbox_utils import tsutils


class TestWDM(TestCase):
    def test_extract1(self):
        ret1 = tsutils.common_kwds("tests/data.wdm,1")
        ret1.columns = ["data.wdm_1"]
        ret2 = tsutils.asbestfreq(
            pd.read_csv("tests/data_wdm_1.csv", index_col=0, parse_dates=True)
        )
        assert_frame_equal(ret1, ret2, check_dtype=False)

    def test_extract2(self):
        ret1 = tsutils.common_kwds("tests/data.wdm,2")
        ret1.columns = ["data.wdm_2"]
        ret2 = tsutils.asbestfreq(
            pd.read_csv("tests/data_wdm_2.csv", index_col=0, parse_dates=True)
        )
        assert_frame_equal(ret1, ret2, check_dtype=False, check_index_type=False)

    def test_extract_range(self):
        ret1 = tsutils.common_kwds("tests/data.wdm,1:2")
        ret1.columns = ["data.wdm_1", "data.wdm_2"]
        ret2 = tsutils.asbestfreq(
            pd.read_csv("tests/data_wdm_1.csv", index_col=0, parse_dates=True)
        )
        ret2 = ret2.join(
            tsutils.asbestfreq(
                pd.read_csv("tests/data_wdm_2.csv", index_col=0, parse_dates=True)
            ),
            how="outer",
        )
        try:
            ret1 = ret1.replace(np.nan, pd.NA)
        except RecursionError:
            pass
        try:
            ret2 = ret2.replace(np.nan, pd.NA)
        except RecursionError:
            pass
        assert_frame_equal(ret1, ret2, check_dtype=False, rtol=1e-7)

    def test_extract_range_plus(self):
        ret1 = tsutils.common_kwds("tests/data.wdm,1+2")
        ret1.columns = ["data.wdm_1", "data.wdm_2"]
        ret1[ret1.isnull()] = np.nan
        ret2 = tsutils.asbestfreq(
            pd.read_csv("tests/data_wdm_1.csv", index_col=0, parse_dates=True)
        )
        ret2 = ret2.join(
            tsutils.asbestfreq(
                pd.read_csv("tests/data_wdm_2.csv", index_col=0, parse_dates=True)
            ),
            how="outer",
        )
        try:
            ret1 = ret1.replace(np.nan, pd.NA)
        except RecursionError:
            pass
        try:
            ret2 = ret2.replace(np.nan, pd.NA)
        except RecursionError:
            pass
        assert_frame_equal(ret1, ret2, check_dtype=False, rtol=1e-7)
