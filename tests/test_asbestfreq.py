import re

import pandas as pd
import pytest

# Constants for testing
_ANNUALS = {
    1: "JAN",
    2: "FEB",
    3: "MAR",
    4: "APR",
    5: "MAY",
    6: "JUN",
    7: "JUL",
    8: "AUG",
    9: "SEP",
    10: "OCT",
    11: "NOV",
    12: "DEC",
}
_WEEKLIES = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN"}


# Helper function to create a DataFrame with a DatetimeIndex
def create_test_data(start, periods, freq, columns=["value"]):
    index = pd.date_range(start=start, periods=periods, freq=freq)
    data = pd.DataFrame(index=index, columns=columns)
    data["value"] = range(periods)
    return data


@pytest.mark.parametrize(
    "test_input, expected",
    [
        # Happy path tests
        pytest.param(create_test_data("2021-01-01", 10, "D"), "D", id="daily_freq"),
        pytest.param(
            create_test_data("2021-01-01", 10, "M"), "(ME|M)", id="monthly_freq"
        ),
        pytest.param(
            create_test_data("2021-01-01", 10, "A"), "(YE-DEC|A-DEC)", id="annual_freq"
        ),
        # Edge cases
        pytest.param(
            create_test_data("2021-01-01", 10, "5H"), "(5h|5H)", id="5_hour_freq"
        ),
        pytest.param(
            create_test_data("2021-01-01", 10, "15T"),
            "(15min|15T)",
            id="15_minute_freq",
        ),
        # Error cases
        pytest.param(
            create_test_data("2021-01-01", 10, "D").iloc[::2], "2D", id="2_day"
        ),
        pytest.param(
            pd.concat(
                [
                    create_test_data("2021-01-01", 2, "D"),
                    create_test_data("2021-01-01", 2, "D"),
                ]
            ),
            ValueError,
            id="duplicate_index",
        ),
    ],
)
def test_asbestfreq(test_input, expected):
    from toolbox_utils.tsutils import asbestfreq

    # Act
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            asbestfreq(test_input)
    else:
        result = asbestfreq(test_input)

    # Assert
    if not isinstance(expected, type):
        assert re.compile(expected).match(result.index.freqstr) is not None
