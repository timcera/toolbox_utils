"""
hdf5
----------------------------------

Tests for `hspf_reader hdf5` module.
"""

# Standard library imports
from io import BytesIO
from unittest import TestCase

# Third party imports
import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

# First party imports
from toolbox_utils import tsutils
from toolbox_utils.readers import hdf5

major_np_version = np.__version__.split(".")[0]
major_pd_version = pd.__version__.split(".")[0]


class TestDescribe(TestCase):
    def setUp(self):
        self.extract = b"""Datetime,PERLND_1_AGWS
1976-01,0.150145
1976-02,0.641031
1976-03,1.198025
1976-04,1.52049
1976-05,1.047159
1976-06,0.758416
1976-07,0.138915
1976-08,0.0
1976-09,0.0
1976-10,0.003539
1976-11,0.0
1976-12,0.007189
"""
        self.extract = tsutils.asbestfreq(
            pd.read_csv(BytesIO(self.extract), header=0, index_col=0, parse_dates=True)
        )
        self.extract.index = self.extract.index.to_period()

    @pytest.mark.skipif(
        major_np_version == "1" and major_pd_version == "1",
        reason="fails if using older versions of the numpy and pandas libraries",
    )
    def test_extract_one_label_labellist_api(self):
        out = tsutils.common_kwds("tests/data.h5,monthly,,1,,AGWS")
        assert_frame_equal(
            out, self.extract, check_dtype=False, check_exact=False, rtol=1e-4
        )

    @pytest.mark.skipif(
        major_np_version == "1" and major_pd_version == "1",
        reason="fails if using older versions of the numpy and pandas libraries",
    )
    def test_extract_one_label_labellist_api_2(self):
        out = hdf5.hdf5_extract("tests/data.h5", "monthly", ["", 1, "", "AGWS"])
        assert_frame_equal(
            out, self.extract, check_dtype=False, check_exact=False, rtol=1e-4
        )
