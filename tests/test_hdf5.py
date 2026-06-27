"""
hdf5
----------------------------------

Tests for `hspf_reader hdf5` module.
"""

# Standard library imports
from io import BytesIO
from unittest import TestCase

# Third party imports
import pandas as pd
from pandas.testing import assert_frame_equal

# First party imports
import toolbox_utils


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
1977-01,0.007183
"""
        self.extract = toolbox_utils.tsutils.asbestfreq(
            pd.read_csv(BytesIO(self.extract), header=0, index_col=0, parse_dates=True)
        )
        self.extract.index = self.extract.index.to_period()

    def test_extract_one_label_labellist_api(self):
        out = toolbox_utils.tsutils.common_kwds("tests/data.h5,monthly,,1,,AGWS")
        assert_frame_equal(
            out, self.extract, check_dtype=False, check_exact=False, rtol=1e-4
        )

    def test_extract_one_label_labellist_api_2(self):
        out = toolbox_utils.readers.hdf5.hdf5_extract(
            "tests/data.h5", "monthly", ["", 1, "", "AGWS"]
        )
        assert_frame_equal(
            out, self.extract, check_dtype=False, check_exact=False, rtol=1e-4
        )
