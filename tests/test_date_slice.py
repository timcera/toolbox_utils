import pandas as pd
import pytest
from pandas._libs.tslibs.parsing import DateParseError


@pytest.mark.parametrize(
    "input_tsd, start_date, end_date, por, expected",
    [
        # Happy path tests
        (
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
            "2020-01-01",
            "2020-12-31",
            False,
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
        ),
        (
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
            "2020-06-01",
            "2020-06-30",
            False,
            pd.DataFrame(index=pd.date_range("2020-06-01", "2020-06-30")),
        ),
        (
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
            None,
            None,
            True,
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
        ),
        # Edge cases
        (
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
            None,
            "2020-06-30",
            False,
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-06-30")),
        ),
        (
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
            "2020-06-01",
            None,
            False,
            pd.DataFrame(index=pd.date_range("2020-06-01", "2020-12-31")),
        ),
        (
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
            None,
            None,
            False,
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
        ),
        # Error cases
        (
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
            "invalid_date",
            "2020-12-31",
            False,
            DateParseError,
        ),
        (
            pd.DataFrame(index=pd.date_range("2020-01-01", "2020-12-31")),
            "2020-01-01",
            "invalid_date",
            False,
            DateParseError,
        ),
    ],
    ids=[
        item[0]
        for item in [
            # IDs for test cases
            "happy_path_full_range",
            "happy_path_partial_range",
            "happy_path_por_true",
            "edge_case_start_date_none",
            "edge_case_end_date_none",
            "edge_case_both_dates_none",
            "error_case_invalid_start_date",
            "error_case_invalid_end_date",
        ]
    ],
)
def test_date_slice(input_tsd, start_date, end_date, por, expected):
    from toolbox_utils.tsutils import _date_slice

    # Arrange
    input_tsd = pd.DataFrame(index=pd.to_datetime(input_tsd.index))

    # Act
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            _date_slice(input_tsd, start_date, end_date, por)
    else:
        result = _date_slice(input_tsd, start_date, end_date, por)

        # Assert
        pd.testing.assert_frame_equal(result, expected)
