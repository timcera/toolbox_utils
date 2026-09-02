# Third party imports
import pandas as pd


def pandas_period_by_version(new_offset: str) -> str:
    """
    Convert the time offset code to match the version of pandas.

    +------------------------+--------+---------+-----------------------------+
    | DateOffset             | less   | greater | Generic offset class,       |
    |                        | 2.2    | equal   | defaults to absolute 24     |
    |                        |        | 2.2     | hours                       |
    +========================+========+=========+=============================+
    | Year                   | 'A'    | 'Y '    | calendar year               |
    +------------------------+--------+---------+-----------------------------+
    | Hour                   | 'H'    | 'h'     | one hour                    |
    +------------------------+--------+---------+-----------------------------+
    | Minute                 | 'T' or | 'min'   | one minute                  |
    |                        | 'min'  |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | Second                 | 'S'    | 's'     | one second                  |
    +------------------------+--------+---------+-----------------------------+
    | Milli                  | 'L' or | 'ms'    | one millisecond             |
    |                        | 'ms'   |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | Micro                  | 'U' or | 'us'    | one microsecond             |
    |                        | 'us'   |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | Nano                   | 'N'    | 'ns'    | one nanosecond              |
    +------------------------+--------+---------+-----------------------------+

    Parameters
    ----------
    offset
        The new style offset to convert if needed for older pandas version.

    Returns
    -------
    offset_by_version
        The offset for the installed version of pandas.
    """
    new_to_old_period = {}
    major, minor = pd.__version__.split(".")[:2]
    if (int(major) + int(minor) / 10) < 2.2:
        new_to_old_period = {
            "Y": "A",
            "h": "H",
            "min": "T",
            "s": "S",
            "ms": "L",
            "us": "U",
            "ns": "N",
        }
    return new_to_old_period.get(new_offset, new_offset)


def pandas_offset_by_version(new_offset: str) -> str:
    """
    Convert the time offset code to match the version of pandas.

    +------------------------+--------+---------+-----------------------------+
    | DateOffset             | less   | greater | Generic offset class,       |
    |                        | 2.2    | equal   | defaults to absolute 24     |
    |                        |        | 2.2     | hours                       |
    +========================+========+=========+=============================+
    | BDay or BusinessDay    | 'B'    | 'B'     | business day (weekday)      |
    +------------------------+--------+---------+-----------------------------+
    | CDay or                | 'C'    | 'C'     | custom business day         |
    | CustomBusinessDay      |        |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | Week                   | 'W'    | 'W'     | one week, optionally        |
    |                        |        |         | anchored on a day of the    |
    |                        |        |         | week                        |
    +------------------------+--------+---------+-----------------------------+
    | WeekOfMonth            | 'WOM'  | 'WOM'   | the x-th day of the y-th    |
    |                        |        |         | week of each month          |
    +------------------------+--------+---------+-----------------------------+
    | LastWeekOfMonth        | 'LWOM' | 'LWOM'  | the x-th day of the last    |
    |                        |        |         | week of each month          |
    +------------------------+--------+---------+-----------------------------+
    | MonthEnd               | 'M'    | 'ME'    | calendar month end          |
    +------------------------+--------+---------+-----------------------------+
    | MonthBegin             | 'MS'   | 'MS'    | calendar month begin        |
    +------------------------+--------+---------+-----------------------------+
    | BMonthEnd or           | 'BM'   | 'BME'   | business month end          |
    | BusinessMonthEnd       |        |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | BMonthBegin or         | 'BMS'  | 'BMS'   | business month begin        |
    | BusinessMonthBegin     |        |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | CBMonthEnd or          | 'CBM'  | 'CBME'  | custom business month end   |
    | CustomBusinessMonthEnd |        |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | CBMonthBegin or        | 'CBMS' | 'CBMS'  | custom business month begin |
    | CustomBusinessMonthBeg |        |         |                             |
    | in                     |        |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | SemiMonthEnd           | 'SM'   | 'SME'   | 15th (or other              |
    |                        |        |         | day_of_month) and calendar  |
    |                        |        |         | month end                   |
    +------------------------+--------+---------+-----------------------------+
    | SemiMonthBegin         | 'SMS'  | 'SMS'   | 15th (or other              |
    |                        |        |         | day_of_month) and calendar  |
    |                        |        |         | month begin                 |
    +------------------------+--------+---------+-----------------------------+
    | QuarterEnd             | 'Q'    | 'QE'    | calendar quarter end        |
    +------------------------+--------+---------+-----------------------------+
    | QuarterBegin           | 'QS'   | 'QS'    | calendar quarter begin      |
    +------------------------+--------+---------+-----------------------------+
    | BQuarterEnd            | 'BQ    | 'BQE'   | business quarter end        |
    +------------------------+--------+---------+-----------------------------+
    | BQuarterBegin          | 'BQS'  | 'BQS'   | business quarter begin      |
    +------------------------+--------+---------+-----------------------------+
    | FY5253Quarter          | 'REQ'  | 'REQ'   | retail (aka 52-53 week)     |
    |                        |        |         | quarter                     |
    +------------------------+--------+---------+-----------------------------+
    | YearEnd                | 'A'    | 'YE'    | calendar year end           |
    +------------------------+--------+---------+-----------------------------+
    | YearBegin              | 'AS'   | 'YS' or | calendar year begin         |
    |                        | or     | 'BYS'   |                             |
    |                        | 'BYS'  |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | BYearEnd               | 'BA'   | 'BYE'   | business year end           |
    +------------------------+--------+---------+-----------------------------+
    | BYearBegin             | 'BAS'  | 'BYS'   | business year begin         |
    +------------------------+--------+---------+-----------------------------+
    | FY5253                 | 'RE'   | 'RE'    | retail (aka 52-53 week)     |
    |                        |        |         | year                        |
    +------------------------+--------+---------+-----------------------------+
    | Easter                 | None   |         | Easter holiday              |
    +------------------------+--------+---------+-----------------------------+
    | BusinessHour           | 'BH'   | 'bh'    | business hour               |
    +------------------------+--------+---------+-----------------------------+
    | CustomBusinessHour     | 'CBH'  | 'cbh'   | custom business hour        |
    +------------------------+--------+---------+-----------------------------+
    | Day                    | 'D'    | 'D'     | one absolute day            |
    +------------------------+--------+---------+-----------------------------+
    | Hour                   | 'H'    | 'h'     | one hour                    |
    +------------------------+--------+---------+-----------------------------+
    | Minute                 | 'T' or | 'min'   | one minute                  |
    |                        | 'min'  |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | Second                 | 'S'    | 's'     | one second                  |
    +------------------------+--------+---------+-----------------------------+
    | Milli                  | 'L' or | 'ms'    | one millisecond             |
    |                        | 'ms'   |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | Micro                  | 'U' or | 'us'    | one microsecond             |
    |                        | 'us'   |         |                             |
    +------------------------+--------+---------+-----------------------------+
    | Nano                   | 'N'    | 'ns'    | one nanosecond              |
    +------------------------+--------+---------+-----------------------------+

    Parameters
    ----------
    offset
        The new style offset to convert if needed for older pandas version.

    Returns
    -------
    offset_by_version
        The offset for the installed version of pandas.
    """
    new_to_old_freq = {}
    major, minor = pd.__version__.split(".")[:2]
    if (int(major) + int(minor) / 10) < 2.2:
        new_to_old_freq = {
            "ME": "M",
            "BME": "BM",
            "CBME": "CBM",
            "SME": "SM",
            "QE": "Q",
            "QE-JAN": "Q-JAN",
            "QE-FEB": "Q-FEB",
            "QE-MAR": "Q-MAR",
            "QE-APR": "Q-APR",
            "QE-MAY": "Q-MAY",
            "QE-JUN": "Q-JUN",
            "QE-JUL": "Q-JUL",
            "QE-AUG": "Q-AUG",
            "QE-SEP": "Q-SEP",
            "QE-OCT": "Q-OCT",
            "QE-NOV": "Q-NOV",
            "QE-DEC": "Q-DEC",
            "BQE": "BQ",
            "BQE-JAN": "BQ-JAN",
            "BQE-FEB": "BQ-FEB",
            "BQE-MAR": "BQ-MAR",
            "BQE-APR": "BQ-APR",
            "BQE-MAY": "BQ-MAY",
            "BQE-JUN": "BQ-JUN",
            "BQE-JUL": "BQ-JUL",
            "BQE-AUG": "BQ-AUG",
            "BQE-SEP": "BQ-SEP",
            "BQE-OCT": "BQ-OCT",
            "BQE-NOV": "BQ-NOV",
            "BQE-DEC": "BQ-DEC",
            "YE": "A",
            "YS": "AS",
            "BYE": "BA",
            "BYS": "BAS",
            "bh": "BH",
            "cbh": "CBH",
            "h": "H",
            "min": "T",
            "s": "S",
            "ms": "L",
            "us": "U",
            "ns": "N",
            "YE-JAN": "A-JAN",
            "YE-FEB": "A-FEB",
            "YE-MAR": "A-MAR",
            "YE-APR": "A-APR",
            "YE-MAY": "A-MAY",
            "YE-JUN": "A-JUN",
            "YE-JUL": "A-JUL",
            "YE-AUG": "A-AUG",
            "YE-SEP": "A-SEP",
            "YE-OCT": "A-OCT",
            "YE-NOV": "A-NOV",
            "YE-DEC": "A-DEC",
        }
    return new_to_old_freq.get(new_offset, new_offset)
