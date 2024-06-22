"""A collection of functions used by toolbox_utils, wdmtoolbox, ...etc."""

import bz2
import datetime
import gzip
import inspect
import os
import platform
import re
import sys
from ast import literal_eval
from collections import OrderedDict
from contextlib import suppress
from functools import reduce, wraps
from importlib.metadata import distribution
from io import BytesIO, StringIO, TextIOWrapper
from math import gcd
from pathlib import Path
from string import Template
from textwrap import TextWrapper, dedent
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union
from urllib.parse import urlparse

import dateparser
import numpy as np
import pandas as pd
import pint_pandas  # not used directly, but required to use pint in pandas
from numpy import int64, ndarray
from pandas.core.frame import DataFrame
from pandas.core.indexes.base import Index
from pandas.tseries.frequencies import to_offset

try:
    from pydantic import validate_call
except ImportError:
    from pydantic import validate_arguments as validate_call

from scipy.stats.distributions import lognorm, norm
from tabulate import simple_separated_format
from tabulate import tabulate as tb

from .readers.hbn import hbn_extract as hbn
from .readers.plotgen import plotgen_extract as plotgen
from .readers.wdm import wdm_extract as wdm

# This is here so that linters don't remove the pint_pandas import which is
# needed to use pint in pandas
_ = pint_pandas.version("pint")

new_to_old_freq = {}
major, minor = pd.__version__.split(".")[:2]
if (int(major) + int(minor) / 10) < 2.2:
    #
    # +--------------+--------------+
    # | Old          | New          |
    # +==============+==============+
    # | A            | Y            |
    # +--------------+--------------+
    # | M            | ME           |
    # +--------------+--------------+
    # | H            | h            |
    # +--------------+--------------+
    # | BH           | bh           |
    # +--------------+--------------+
    # | CBH          | cbh          |
    # +--------------+--------------+
    # | T            | min          |
    # +--------------+--------------+
    # | S            | s            |
    # +--------------+--------------+
    # | L            | ms           |
    # +--------------+--------------+
    # | U            | us           |
    # +--------------+--------------+
    # | N            | ns           |
    # +--------------+--------------+
    #
    new_to_old_freq = {
        "Y": "A",
        "ME": "M",
        "h": "H",
        "bh": "BH",
        "cbh": "CBH",
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


def normalize_command_line_args(args: List) -> List:
    """
    Normalize command line arguments.

    Parameters
    ----------
    args
        The command line arguments.

    Returns
    -------
    normalize_command_line_args
        The normalized command line arguments.
    """
    nargs = ",".join(args)
    nargs = nargs.split(",")

    rargs = []

    for arg in nargs:
        if os.path.exists(arg):
            rargs.append([arg])
        else:
            rargs[-1].append(arg)

    return rargs


def error_wrapper(estr: str) -> str:
    """
    Wrap estr into error format used by toolboxes.

    Parameters
    ----------
    estr
        The error message to wrap.

    Returns
    -------
    error_wrapper
        The wrapped error message.
    """
    wrapper = TextWrapper(initial_indent="*   ", subsequent_indent="*   ")

    estr = dedent(estr)

    nestr = ["", "*"]

    for paragraph in estr.split("\n\n"):
        nestr.extend(("\n".join(wrapper.wrap(paragraph.strip())), "*"))
    nestr.append("")

    return "\n".join(nestr)


_CODES = {
    "SUB_D": {
        "N": "Nanoseconds",
        "U": "microseconds",
        "L": "miLliseconds",
        "S": "Secondly",
        "T": "minuTely",
        "H": "Hourly",
    },
    "DAILY": {
        "D": "calendar Day",
        "B": "Business day",
        "C": "Custom business day (experimental)",
    },
    "WEEKLY": {
        "W": "Weekly",
        "W-SUN": "Weekly frequency (SUNdays)",
        "W-MON": "Weekly frequency (MONdays)",
        "W-TUE": "Weekly frequency (TUEsdays)",
        "W-WED": "Weekly frequency (WEDnesdays)",
        "W-THU": "Weekly frequency (THUrsdays)",
        "W-FRI": "Weekly frequency (FRIdays)",
        "W-SAT": "Weekly frequency (SATurdays)",
    },
    "MONTH": {
        "M": "Month end",
        "MS": "Month Start",
        "BM": "Business Month end",
        "BMS": "Business Month Start",
        "CBM": "Custom Business Month end",
        "CBMS": "Custom Business Month Start",
    },
    "QUARTERLY": {
        "Q": "Quarter end",
        "Q-JAN": "Quarterly, quarter ends end of JANuary",
        "Q-FEB": "Quarterly, quarter ends end of FEBruary",
        "Q-MAR": "Quarterly, quarter ends end of MARch",
        "Q-APR": "Quarterly, quarter ends end of APRil",
        "Q-MAY": "Quarterly, quarter ends end of MAY",
        "Q-JUN": "Quarterly, quarter ends end of JUNe",
        "Q-JUL": "Quarterly, quarter ends end of JULy",
        "Q-AUG": "Quarterly, quarter ends end of AUGust",
        "Q-SEP": "Quarterly, quarter ends end of SEPtember",
        "Q-OCT": "Quarterly, quarter ends end of OCTober",
        "Q-NOV": "Quarterly, quarter ends end of NOVember",
        "Q-DEC": "Quarterly, quarter ends end of DECember",
        "QS": "Quarter Start",
        "QS-JAN": "Quarterly, quarter Starts end of JANuary",
        "QS-FEB": "Quarterly, quarter Starts end of FEBruary",
        "QS-MAR": "Quarterly, quarter Starts end of MARch",
        "QS-APR": "Quarterly, quarter Starts end of APRil",
        "QS-MAY": "Quarterly, quarter Starts end of MAY",
        "QS-JUN": "Quarterly, quarter Starts end of JUNe",
        "QS-JUL": "Quarterly, quarter Starts end of JULy",
        "QS-AUG": "Quarterly, quarter Starts end of AUGust",
        "QS-SEP": "Quarterly, quarter Starts end of SEPtember",
        "QS-OCT": "Quarterly, quarter Starts end of OCTober",
        "QS-NOV": "Quarterly, quarter Starts end of NOVember",
        "QS-DEC": "Quarterly, quarter Starts end of DECember",
        "BQ": "Business Quarter end",
        "BQS": "Business Quarter Start",
    },
    "ANNUAL": {
        "A": "Annual end",
        "A-JAN": "Annual, year ends end of JANuary",
        "A-FEB": "Annual, year ends end of FEBruary",
        "A-MAR": "Annual, year ends end of MARch",
        "A-APR": "Annual, year ends end of APRil",
        "A-MAY": "Annual, year ends end of MAY",
        "A-JUN": "Annual, year ends end of JUNe",
        "A-JUL": "Annual, year ends end of JULy",
        "A-AUG": "Annual, year ends end of AUGust",
        "A-SEP": "Annual, year ends end of SEPtember",
        "A-OCT": "Annual, year ends end of OCTober",
        "A-NOV": "Annual, year ends end of NOVember",
        "A-DEC": "Annual, year ends end of DECember",
        "AS": "Annual Start",
        "AS-JAN": "Annual, year Starts end of JANuary",
        "AS-FEB": "Annual, year Starts end of FEBruary",
        "AS-MAR": "Annual, year Starts end of MARch",
        "AS-APR": "Annual, year Starts end of APRil",
        "AS-MAY": "Annual, year Starts end of MAY",
        "AS-JUN": "Annual, year Starts end of JUNe",
        "AS-JUL": "Annual, year Starts end of JULy",
        "AS-AUG": "Annual, year Starts end of AUGust",
        "AS-SEP": "Annual, year Starts end of SEPtember",
        "AS-OCT": "Annual, year Starts end of OCTober",
        "AS-NOV": "Annual, year Starts end of NOVember",
        "AS-DEC": "Annual, year Starts end of DECember",
        "BA": "Business Annual end",
        "BA-JAN": "Business Annual, business year ends end of JANuary",
        "BA-FEB": "Business Annual, business year ends end of FEBruary",
        "BA-MAR": "Business Annual, business year ends end of MARch",
        "BA-APR": "Business Annual, business year ends end of APRil",
        "BA-MAY": "Business Annual, business year ends end of MAY",
        "BA-JUN": "Business Annual, business year ends end of JUNe",
        "BA-JUL": "Business Annual, business year ends end of JULy",
        "BA-AUG": "Business Annual, business year ends end of AUGust",
        "BA-SEP": "Business Annual, business year ends end of SEPtember",
        "BA-OCT": "Business Annual, business year ends end of OCTober",
        "BA-NOV": "Business Annual, business year ends end of NOVember",
        "BA-DEC": "Business Annual, business year ends end of DECember",
        "BAS": "Business Annual Start",
        "BS-JAN": "Business Annual Start, business year starts end of JANuary",
        "BS-FEB": "Business Annual Start, business year starts end of FEBruary",
        "BS-MAR": "Business Annual Start, business year starts end of MARch",
        "BS-APR": "Business Annual Start, business year starts end of APRil",
        "BS-MAY": "Business Annual Start, business year starts end of MAY",
        "BS-JUN": "Business Annual Start, business year starts end of JUNe",
        "BS-JUL": "Business Annual Start, business year starts end of JULy",
        "BS-AUG": "Business Annual Start, business year starts end of AUGust",
        "BS-SEP": "Business Annual Start, business year starts end of SEPtember",
        "BS-OCT": "Business Annual Start, business year starts end of OCTober",
        "BS-NOV": "Business Annual Start, business year starts end of NOVember",
        "BS-DEC": "Business Annual Start, business year starts end of DECember",
    },
}

docstrings = {
    "por": """por
        [optional, default is False]

        The `por` keyword adjusts the operation of `start_date` and
        `end_date`

        If "False" (the default) choose the indices in the time-series
        between `start_date` and `end_date`.  If "True" and if `start_date`
        or `end_date` is outside of the existing time-series will fill the
        time- series with missing values to include the exterior
        `start_date` or `end_date`.""",
    "lat": """lat
        The latitude of the point. North hemisphere is positive from 0 to
        90. South hemisphere is negative from 0 to -90.""",
    "lon": """lon
        The longitude of the point.  Western hemisphere (west of Greenwich
        Prime Meridian) is negative 0 to -180.  The eastern hemisphere
        (east of the Greenwich Prime Meridian) is positive 0 to 180.""",
    "target_units": """target_units: str
        [optional, default is None, transformation]

        The purpose of this option is to specify target units for unit
        conversion.  The source units are specified in the header line of
        the input or using the 'source_units' keyword.

        The units of the input time-series or values are specified as the
        second field of a ':' delimited name in the header line of the
        input or in the 'source_units' keyword.

        Any unit string compatible with the 'pint' library can be used.

        This option will also add the 'target_units' string to the
        column names.""",
    "source_units": """source_units: str
        [optional, default is None, transformation]

        If unit is specified for the column as the second field of a ':'
        delimited column name, then the specified units and the
        'source_units' must match exactly.

        Any unit string compatible with the 'pint' library can be used.""",
    "names": """names: str
        [optional, default is None, transformation]

        If None, the column names are taken from the first row after
        'skiprows' from the input dataset.

        MUST include a name for all columns in the input dataset, including
        the index column.""",
    "index_type": """index_type : str
        [optional, default is 'datetime', output format]

        Can be either 'number' or 'datetime'.  Use 'number' with index
        values that are Julian dates, or other epoch reference.""",
    "input_ts": """input_ts : str
        [optional though required if using within Python, default is '-'
        (stdin)]

        Whether from a file or standard input, data requires a single line
        header of column names.  The default header is the first line of
        the input, but this can be changed for CSV files using the
        'skiprows' option.

        Most common date formats can be used, but the closer to ISO 8601
        date/time standard the better.

        Comma-separated values (CSV) files or tab-separated values (TSV)::

            File separators will be automatically detected.

            Columns can be selected by name or index, where the index for
            data columns starts at 1.

        Command line examples:

            +---------------------------------+---------------------------+
            | Keyword Example                 | Description               |
            +=================================+===========================+
            | --input_ts=fn.csv               | read all columns from     |
            |                                 | 'fn.csv'                  |
            +---------------------------------+---------------------------+
            | --input_ts=fn.csv,2,1           | read data columns 2 and 1 |
            |                                 | from 'fn.csv'             |
            +---------------------------------+---------------------------+
            | --input_ts=fn.csv,2,skiprows=2  | read data column 2 from   |
            |                                 | 'fn.csv', skipping first  |
            |                                 | 2 rows so header is read  |
            |                                 | from third row            |
            +---------------------------------+---------------------------+
            | --input_ts=fn.xlsx,2,Sheet21    | read all data from 2nd    |
            |                                 | sheet all data from       |
            |                                 | "Sheet21" of 'fn.xlsx'    |
            +---------------------------------+---------------------------+
            | --input_ts=fn.hdf5,Table12,T2   | read all data from table  |
            |                                 | "Table12" then all data   |
            |                                 | from table "T2" of        |
            |                                 | 'fn.hdf5'                 |
            +---------------------------------+---------------------------+
            | --input_ts=fn.wdm,210,110       | read DSNs 210, then 110   |
            |                                 | from 'fn.wdm'             |
            +---------------------------------+---------------------------+
            | --input_ts='-'                  | read all columns from     |
            |                                 | standard input (stdin)    |
            +---------------------------------+---------------------------+
            | --input_ts='-' --columns=4,1    | read column 4 and 1 from  |
            |                                 | standard input (stdin)    |
            +---------------------------------+---------------------------+

        If working with CSV or TSV files you can use redirection rather
        than use `--input_ts=fname.csv`.  The following are identical:

        From a file:

            command subcmd --input_ts=fname.csv

        From standard input (since '--input_ts=-' is the default:

            command subcmd < fname.csv

        Can also combine commands by piping:

            command subcmd < filein.csv | command subcmd1 > fileout.csv

        Python library examples::

            You must use the `input_ts=...` option where `input_ts` can be
            one of a [pandas DataFrame, pandas Series, dict, tuple, list,
            StringIO, or file name].""",
    "columns": """columns
        [optional, defaults to all columns, input filter]

        Columns to select out of input.  Can use column names from the
        first line header or column numbers.  If using numbers, column
        number 1 is the first data column.  To pick multiple columns;
        separate by commas with no spaces. As used in `toolbox_utils pick`
        command.

        This solves a big problem so that you don't have to create a data
        set with a certain column order, you can rearrange columns when
        data is read in.""",
    "start_date": """start_date : str
        [optional, defaults to first date in time-series, input filter]

        The start_date of the series in ISOdatetime format, or 'None' for
        beginning.""",
    "end_date": """end_date : str
        [optional, defaults to last date in time-series, input filter]

        The end_date of the series in ISOdatetime format, or 'None' for
        end.""",
    "dropna": """dropna : str
        [optional, defauls it 'no', input filter]

        Set `dropna` to 'any' to have records dropped that have NA value in
        any column, or 'all' to have records dropped that have NA in all
        columns. Set to 'no' to not drop any records.  The default is 'no'.""",
    "print_input": """print_input
        [optional, default is False, output format]

        If set to 'True' will include the input columns in the output
        table.""",
    "round_index": """round_index
        [optional, default is None which will do nothing to the index,
        output format]

        Round the index to the nearest time point.  Can significantly
        improve the performance since can cut down on memory and processing
        requirements, however be cautious about rounding to a very course
        interval from a small one.  This could lead to duplicate values in
        the index.""",
    "float_format": """float_format
        [optional, output format]

        Format for float numbers.""",
    "tablefmt": """tablefmt : str
        [optional, default is 'csv', output format]

        The table format.  Can be one of 'csv', 'tsv', 'plain', 'simple',
        'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'latex', 'latex_raw'
        and 'latex_booktabs'.""",
    "header": """header : str
        [optional, default is 'default', output format]

        This is if you want a different header than is the default for this
        output table.  Pass a list with string column names for each column
        in the table.""",
    "pandas_offset_codes": """

        +-------+---------------+
        | Alias | Description   |
        +=======+===============+
        | N     | Nanoseconds   |
        +-------+---------------+
        | U     | microseconds  |
        +-------+---------------+
        | L     | milliseconds  |
        +-------+---------------+
        | S     | Secondly      |
        +-------+---------------+
        | T     | Minutely      |
        +-------+---------------+
        | H     | Hourly        |
        +-------+---------------+
        | D     | calendar Day  |
        +-------+---------------+
        | W     | Weekly        |
        +-------+---------------+
        | M     | Month end     |
        +-------+---------------+
        | MS    | Month Start   |
        +-------+---------------+
        | Q     | Quarter end   |
        +-------+---------------+
        | QS    | Quarter Start |
        +-------+---------------+
        | A     | Annual end    |
        +-------+---------------+
        | AS    | Annual Start  |
        +-------+---------------+

        Business offset codes.

        +-------+------------------------------------+
        | Alias | Description                        |
        +=======+====================================+
        | B     | Business day                       |
        +-------+------------------------------------+
        | BM    | Business Month end                 |
        +-------+------------------------------------+
        | BMS   | Business Month Start               |
        +-------+------------------------------------+
        | BQ    | Business Quarter end               |
        +-------+------------------------------------+
        | BQS   | Business Quarter Start             |
        +-------+------------------------------------+
        | BA    | Business Annual end                |
        +-------+------------------------------------+
        | BAS   | Business Annual Start              |
        +-------+------------------------------------+
        | C     | Custom business day (experimental) |
        +-------+------------------------------------+
        | CBM   | Custom Business Month end          |
        +-------+------------------------------------+
        | CBMS  | Custom Business Month Start        |
        +-------+------------------------------------+

        Weekly has the following anchored frequencies:

        +-------+-------------+-------------------------------+
        | Alias | Equivalents | Description                   |
        +=======+=============+===============================+
        | W-SUN | W           | Weekly frequency (SUNdays)    |
        +-------+-------------+-------------------------------+
        | W-MON |             | Weekly frequency (MONdays)    |
        +-------+-------------+-------------------------------+
        | W-TUE |             | Weekly frequency (TUEsdays)   |
        +-------+-------------+-------------------------------+
        | W-WED |             | Weekly frequency (WEDnesdays) |
        +-------+-------------+-------------------------------+
        | W-THU |             | Weekly frequency (THUrsdays)  |
        +-------+-------------+-------------------------------+
        | W-FRI |             | Weekly frequency (FRIdays)    |
        +-------+-------------+-------------------------------+
        | W-SAT |             | Weekly frequency (SATurdays)  |
        +-------+-------------+-------------------------------+

        Quarterly frequencies (Q, BQ, QS, BQS) and annual frequencies (A,
        BA, AS, BAS) replace the "x" in the "Alias" column to have the
        following anchoring suffixes:

        +-------+----------+-------------+----------------------------+
        | Alias | Examples | Equivalents | Description                |
        +=======+==========+=============+============================+
        | x-DEC | A-DEC    | A           | year ends end of DECember  |
        |       | Q-DEC    | Q           |                            |
        |       | AS-DEC   | AS          |                            |
        |       | QS-DEC   | QS          |                            |
        +-------+----------+-------------+----------------------------+
        | x-JAN |          |             | year ends end of JANuary   |
        +-------+----------+-------------+----------------------------+
        | x-FEB |          |             | year ends end of FEBruary  |
        +-------+----------+-------------+----------------------------+
        | x-MAR |          |             | year ends end of MARch     |
        +-------+----------+-------------+----------------------------+
        | x-APR |          |             | year ends end of APRil     |
        +-------+----------+-------------+----------------------------+
        | x-MAY |          |             | year ends end of MAY       |
        +-------+----------+-------------+----------------------------+
        | x-JUN |          |             | year ends end of JUNe      |
        +-------+----------+-------------+----------------------------+
        | x-JUL |          |             | year ends end of JULy      |
        +-------+----------+-------------+----------------------------+
        | x-AUG |          |             | year ends end of AUGust    |
        +-------+----------+-------------+----------------------------+
        | x-SEP |          |             | year ends end of SEPtember |
        +-------+----------+-------------+----------------------------+
        | x-OCT |          |             | year ends end of OCTober   |
        +-------+----------+-------------+----------------------------+
        | x-NOV |          |             | year ends end of NOVember  |
        +-------+----------+-------------+----------------------------+

        """,
    "plotting_position_table": """

        +------------+--------+----------------------+--------------------+
        | Name       | a      | Equation             | Description        |
        |            |        | (i-a)/(n+1-2*a)      |                    |
        +============+========+======================+====================+
        | weibull    | 0      | i/(n+1)              | mean of sampling   |
        | (default)  |        |                      | distribution       |
        +------------+--------+----------------------+--------------------+
        | filliben   | 0.3175 | (i-0.3175)/(n+0.365) |                    |
        +------------+--------+----------------------+--------------------+
        | yu         | 0.326  | (i-0.326)/(n+0.348)  |                    |
        +------------+--------+----------------------+--------------------+
        | tukey      | 1/3    | (i-1/3)/(n+1/3)      | approx. median of  |
        |            |        |                      | sampling           |
        |            |        |                      | distribution       |
        +------------+--------+----------------------+--------------------+
        | blom       | 0.375  | (i-0.375)/(n+0.25)   |                    |
        +------------+--------+----------------------+--------------------+
        | cunnane    | 2/5    | (i-2/5)/(n+1/5)      | subjective         |
        +------------+--------+----------------------+--------------------+
        | gringorton | 0.44   | (1-0.44)/(n+0.12)    |                    |
        +------------+--------+----------------------+--------------------+
        | hazen      | 1/2    | (i-1/2)/n            | midpoints of n     |
        |            |        |                      | equal intervals    |
        +------------+--------+----------------------+--------------------+
        | larsen     | 0.567  | (i-0.567)/(n-0.134)  |                    |
        +------------+--------+----------------------+--------------------+
        | gumbel     | 1      | (i-1)/(n-1)          | mode of sampling   |
        |            |        |                      | distribution       |
        +------------+--------+----------------------+--------------------+
        | california | NA     | i/n                  |                    |
        +------------+--------+----------------------+--------------------+

        Where 'i' is the sorted rank of the y value, and 'n' is the total
        number of values to be plotted.

        The 'blom' plotting position is also known as the 'Sevruk and
        Geiger'.""",
    "clean": """clean
        [optional, default is False, input filter]

        The 'clean' command will repair a input index, removing duplicate
        index values and sorting.""",
    "skiprows": """skiprows: list-like or integer or callable
        [optional, default is None which will infer header from first line,
        input filter]

        Line numbers to skip (0-indexed) if a list or number of lines to
        skip at the start of the file if an integer.

        If used in Python can be a callable, the callable function will be
        evaluated against the row indices, returning True if the row should
        be skipped and False otherwise.  An example of a valid callable
        argument would be

        ``lambda x: x in [0, 2]``.""",
    "groupby": """groupby: str
        [optional, default is None, transformation]

        The pandas offset code to group the time-series data into.
        A special code is also available to group 'months_across_years'
        that will group into twelve monthly categories across the entire
        time-series.""",
    "force_freq": """force_freq: str
        [optional, output format]

        Force this frequency for the output.  Typically you will only want
        to enforce a smaller interval where toolbox_utils will insert
        missing values as needed.  WARNING: you may lose data if not
        careful with this option.  In general, letting the algorithm
        determine the frequency should always work, but this option will
        override.  Use PANDAS offset codes.""",
    "output_names": """output_names: str
        [optional, output_format]

        The toolbox_utils will change the names of the output columns to
        include some record of the operations used on each column.  The
        `output_names` will override that feature.  Must be a list or tuple
        equal to the number of columns in the output data.""",
}


def flatten(list_of_lists: Union[List, Tuple]) -> List:
    """
    Recursively flatten a list of lists or tuples into a single list.

    Parameters
    ----------
    list_of_lists
        A list of lists or tuples to flatten.

    Returns
    -------
    flatten
        A single list of all the values in the input list.
    """
    if isinstance(list_of_lists, (list, tuple)):
        if not list_of_lists:
            return list_of_lists

        if isinstance(list_of_lists[0], (list, tuple)):
            return list(flatten(list_of_lists[0])) + list(flatten(list_of_lists[1:]))

        return list(list_of_lists[:1]) + list(flatten(list_of_lists[1:]))

    return list_of_lists


@validate_call
def stride_and_unit(sunit: str) -> Tuple[str, int]:
    """
    Split a stride/unit combination into component parts.

    Parameters
    ----------
    sunit
        A stride/unit combination.

    Returns
    -------
    stride_and_unit
        A tuple of the stride and unit.
    """
    if sunit is None:
        return sunit
    unit = sunit.lstrip("+-. 1234567890")
    sunit = sunit[: sunit.index(unit)]
    stride = int(sunit) if sunit else 1

    return unit, stride


@validate_call
def set_ppf(ptype: Optional[Literal["norm", "lognorm", "weibull"]]) -> Callable:
    """
    Return correct Percentage Point Function for `ptype`.

    Parameters
    ----------
    ptype
        The type of distribution to use.

    Returns
    -------
    set_ppf
        The Percentage Point Function for the specified distribution.
    """
    if ptype == "norm":
        ppf = norm.ppf
    elif ptype == "lognorm":
        ppf = lognorm.freeze(0.5, loc=0).ppf
    elif ptype == "weibull":

        def ppf(y_vals):
            """Percentage Point Function for the weibull distribution."""

            return np.log(-np.log(1 - np.array(y_vals)))

    elif ptype is None:

        def ppf(y_vals):
            return y_vals

    return ppf


@validate_call
def _handle_curly_braces_in_docstring(input_str: str, **kwargs) -> str:
    """Replace missing keys with a pattern."""
    ret = "{{{}}}"
    try:
        return input_str.format(**kwargs)
    except KeyError as exc:
        keyname = exc.args[0]

        return _handle_curly_braces_in_docstring(
            input_str, **{keyname: ret.format(keyname)}, **kwargs
        )


@validate_call
def copy_doc(source: Callable) -> Callable:
    """
    Copy docstring from source.

    Parameters
    ----------
    source
        Function to take doc string from.

    Returns
    -------
    copy_doc
        Wrapped function that has docstring from `source`.
    """

    def wrapper_copy_doc(func: Callable) -> Callable:
        if source.__doc__:
            func.__doc__ = source.__doc__  # noqa: WPS125

        return func

    return wrapper_copy_doc


@validate_call
def doc(fdict: dict) -> Callable:
    """
    Return a decorator that formats a docstring.

    Uses a template docstring replacing ${key} with fdict[key] from passed
    in dictionary.

    Parameters
    ----------
    fdict
        Dictionary of strings with values to replace {keys} in docstring.

    Returns
    -------
    doc
        Function with docstring formatted with fdict.
    """

    def outer_func(inner_func):
        inner_func.__doc__ = Template(inner_func.__doc__).safe_substitute(**fdict)

        return inner_func

    return outer_func


@validate_call(config={"arbitrary_types_allowed": True})
@doc(docstrings)
def set_plotting_position(
    cnt: Union[int, int64],
    plotting_position: Union[
        float,
        Literal[
            "weibull",
            "benard",
            "bos-levenbach",
            "filliben",
            "yu",
            "tukey",
            "blom",
            "cunnane",
            "gringorton",
            "hazen",
            "larsen",
            "gumbel",
            "california",
        ],
    ] = "weibull",
) -> ndarray:
    """
    Create plotting position 1D array using linspace.

    {plotting_position_table}

    Parameters
    ----------
    cnt
        The number of values to create plotting positions for.
    plotting_position
        The plotting position to use.  If a float, the plotting position
        will be used as is.  If a string, the plotting position will be
        looked up in the plotting position dictionary.

    Returns
    -------
    set_plotting_position
        The plotting position array.
    """
    ppdict: Dict[str, float] = {
        "weibull": 0,
        "benard": 0.3,
        "filliben": 0.3175,
        "yu": 0.326,
        "tukey": 1 / 3,
        "blom": 0.375,
        "cunnane": 2 / 5,
        "gringorton": 0.44,
        "hazen": 1 / 2,
        "larsen": 0.567,
        "gumbel": 1,
    }

    if plotting_position == "california":
        return np.linspace(1.0 / cnt, 1.0, cnt)
    coeff: float = ppdict.get(plotting_position, plotting_position)
    index = np.arange(1, cnt + 1)

    return (index - coeff) / float(cnt + 1 - 2 * coeff)


@validate_call
def parsedate(
    dstr: Optional[Any], strftime: Optional[Any] = None, settings: Optional[Any] = None
) -> datetime.datetime:
    """
    Use dateparser to parse a wide variety of dates.

    Used for start and end dates.

    Parameters
    ----------
    dstr
        The date string to parse.
    strftime
        The format to return the date string in.
    settings
        The settings to use for dateparser.parse.

    Returns
    -------
    parsedate
        The parsed date.
    """
    # The API should boomerang a datetime.datetime instance and None.
    if dstr is None:
        return dstr
    if isinstance(dstr, datetime.datetime):
        return dstr if strftime is None else dstr.strftime(strftime)

    try:
        pdate = pd.to_datetime(dstr)
    except ValueError:
        pdate = dateparser.parse(dstr, settings=settings)

    if pdate is None:
        raise ValueError(error_wrapper(f"""Could not parse date string '{dstr}'. """))

    return pdate if strftime is None else pdate.strftime(strftime)


def about(name: str):
    """
    Print generic 'about' information used across all toolboxes.

    Parameters
    ----------
    name
        The name of the package to print information for.

    Returns
    -------
    about
        Prints information to stdout.
    """
    dist = distribution(name.split(".")[0])
    about_dict = OrderedDict()
    about_dict["package_name"] = dist.name
    about_dict["package_version"] = dist.version
    about_dict["platform_architecture"] = platform.architecture()
    about_dict["platform_machine"] = platform.machine()
    about_dict["platform"] = platform.platform()
    about_dict["platform_processor"] = platform.processor()
    about_dict["platform_python_build"] = platform.python_build()
    about_dict["platform_python_compiler"] = platform.python_compiler()
    about_dict["platform_python_branch"] = platform.python_branch()
    about_dict["platform_python_implementation"] = platform.python_implementation()
    about_dict["platform_python_revision"] = platform.python_revision()
    about_dict["platform_python_version"] = platform.python_version()
    about_dict["platform_release"] = platform.release()
    about_dict["platform_system"] = platform.system()
    about_dict["platform_version"] = platform.version()
    return about_dict


def _round_index(ntsd: DataFrame, round_index: Optional[str] = None) -> DataFrame:
    """
    Round the index, typically time, to the nearest interval.

    Parameters
    ----------
    ntsd
        The dataframe to round the index of.
    round_index
        The interval to round the index to.

    Returns
    -------
    _round_index
        The dataframe with the rounded index.
    """
    if round_index is None:
        return ntsd
    ntsd.index = ntsd.index.round(round_index)

    return ntsd


def _pick_column_or_value(tsd: DataFrame, var):
    """
    Return a keyword value or a time-series.

    Parameters
    ----------
    tsd
        The time-series dataframe that contains the column `var`.  If `var`
        is not a column in `tsd`, then it is assumed to be a value.
    var
        The column name to return from `tsd`.

    Returns
    -------
    _pick_column_or_value
        The column from `tsd` or the value of `var`.
    """
    try:
        var = np.array([float(var)])
    except ValueError:
        var = tsd.loc[:, var].values

    return var


def make_list(
    *strorlist: Union[str, List],
    n: Optional[int] = None,
    sep: str = ",",
    flat: bool = True,
) -> Any:
    """
    Normalize strings, converting to numbers or lists.

    Parameters
    ----------
    strorlist
        The string or list to normalize.
    n
        The number of elements to return.  If None, then return all
        elements.
    sep
        The separator to use when splitting a string.
    flat
        Whether to flatten the list.

    Returns
    -------
    make_list
        The normalized list.
    """
    # Pre-process
    if isinstance(strorlist, (list, tuple)) and flat:
        strorlist = flatten(strorlist)

    if isinstance(strorlist, (list, tuple)) and len(strorlist) == 1:
        # Normalize lists and tuples of length 1 to scalar for
        # further processing.
        strorlist = strorlist[0]

    if isinstance(strorlist, (int, float)):
        # 1      -> [1]
        # 1.2    -> [1.2]
        strorlist = [strorlist]

    # Boomerang
    if isinstance(strorlist, Path):
        return [strorlist]

    if isinstance(strorlist, (pd.DataFrame, pd.Series)):
        return [pd.DataFrame(strorlist)]

    if (
        strorlist is None
        or isinstance(strorlist, (type(None)))
        or strorlist in ("None", "", b"None", b"")
    ):
        # None -> None
        # 'None' -> None
        # ''     -> None
        return None

    if isinstance(strorlist, (StringIO, BytesIO)):
        return strorlist

    if isinstance(strorlist, (str, bytes)):
        # Anything other than a scalar int or float continues.
        # '1'   -> [1]
        # '5.7' -> [5.7]
        try:
            return [int(strorlist)]
        except ValueError:
            with suppress(ValueError):
                return [float(strorlist)]

        # Deal with str or bytes.
        strorlist = strorlist.strip()

        if isinstance(strorlist, str) and ("\r" in strorlist or "\n" in strorlist):
            return [StringIO(strorlist)]

        if isinstance(strorlist, bytes) and (b"\r" in strorlist or b"\n" in strorlist):
            return [BytesIO(strorlist)]

        strorlist = strorlist.split(
            sep if isinstance(strorlist, str) else bytes(sep, encoding="utf8")
        )

    # At this point 'strorlist' variable should be a list or tuple.

    if n is None:
        n = len(strorlist)

    if len(strorlist) != n:
        raise ValueError(
            error_wrapper(
                f"""
                The list {strorlist} should have {n} members
                according to function requirements. """
            )
        )

    # [1, 2, 3]          -> [1, 2, 3]
    # ['1', '2']         -> [1, 2]

    # [1, 'er', 5.6]     -> [1, 'er', 5.6]
    # [1,'er',5.6]       -> [1, 'er', 5.6]
    # ['1','er','5.6']   -> [1, 'er', 5.6]

    # ['1','','5.6']     -> [1, None, 5.6]
    # ['1','None','5.6'] -> [1, None, 5.6]

    ret = []

    for each in strorlist:
        if isinstance(each, (type(None), int, float, pd.DataFrame, pd.Series, Path)):
            ret.append(each)
            continue

        if not flat and isinstance(each, list):
            ret.append(each)
            continue

        if each is None or each.strip() == "" or each == "None":
            ret.append(None)
            continue

        try:
            ret.append(int(each))
        except ValueError:
            try:
                ret.append(float(each))
            except ValueError:
                ret.append(each)

    return ret


def make_iloc(columns: List, col_list: List):
    """
    Imitates the .ix option with subtracting 1 to convert.

    Parameters
    ----------
    columns
        The list of column names.
    col_list
        The list of column names or indices.

    Returns
    -------
    make_iloc : list
        The list of column indices.
    """
    # ["1", "Value2"]    ->    [0, "Value2"]
    # [1, 2, 3]          ->    [0, 1, 2]
    col_list = make_list(col_list)
    ntestc = []

    for i in col_list:
        try:
            ntestc.append(int(i) - 1)
        except ValueError:
            ntestc.append(columns.index(i))

    return ntestc


# NOT SET YET...
#
# Take `air_pressure` from df.loc[:, 1]
# Take `short_wave_rad` from df.loc[:, 'swaverad']
# The `temperature` keyword is set to 23.4 for all time periods
# The `wind_speed` keyword is set to 2.4 and 3.1 in turn
#
# Will output two columns, one with wind_speed equal to 2.4, the next
# with wind_speed equal to 3.1.
#
# API:
# testfunction(input_ts=df,
#              air_pressure='_1',
#              short_wave_rad='swaverad',
#              temperature=23.4,
#              wind_speed=[2.4, 3.1])
#             )
#
# CLI:
# mettoolbox testfunction --air_pressure=_1 \
#                         --short_wave_rad=swaverad \
#                         --temperature 23.4 \
#                         --wind_speed 2.4,3.1 < df.csv


def _normalize_units(
    ntsd: DataFrame,
    source_units: Optional[str],
    target_units: Optional[str],
    source_units_required: bool = False,
) -> DataFrame:
    """
    Following is aspirational and may not reflect the code.

    +--------------+--------------+--------------+--------------+--------------+
    | INPUT        | INPUT        | INPUT        | RETURN       | RETURN       |
    | ntsd.columns | source_units | target_units | source_units | target_units |
    +==============+==============+==============+==============+==============+
    | ["col1:cm",  | ["ft", "cm"] | ["m", "cm"]  | ValueError   |              |
    | "col2:cm"]   |              |              |              |              |
    +--------------+--------------+--------------+--------------+--------------+
    | ["col1:cm",  | ["cm"]       | ["ft"]       | ValueError   |              |
    | "col2:cm"]   |              |              |              |              |
    +--------------+--------------+--------------+--------------+--------------+
    | ["col1:cm",  | ["cm"]       | ["ft"]       | ["cm", ""]   | ["ft", ""]   |
    | "col2"]      |              |              |              |              |
    +--------------+--------------+--------------+--------------+--------------+
    | ["col1",     | ["", "cm"]   | ["", "ft"]   | ["", "cm"]   | ["", "ft"]   |
    | "col2:cm"]   |              |              |              |              |
    +--------------+--------------+--------------+--------------+--------------+
    |              | ["cm"]       | ["ft"]       | ["cm"]       | ["ft"]       |
    +--------------+--------------+--------------+--------------+--------------+
    | ["cm"]       | None         | ["ft"]       | ["cm"]       | ["ft"]       |
    +--------------+--------------+--------------+--------------+--------------+

    Parameters
    ----------
    ntsd : DataFrame
        The input time series data.
    source_units : str, list, or None
        The units of the input time series data.
    target_units : str, list, or None
        The units of the output time series data.
    source_units_required : bool
        Whether or not the source units are required.

    Returns
    -------
    ntsd : DataFrame
        The time series data with the converted units.
    """
    # Enforce DataFrame
    ntsd = pd.DataFrame(ntsd)

    target_units = make_list(target_units, n=len(ntsd.columns))
    if target_units is None:
        return ntsd
    target_units = ["" if i is None else i for i in target_units]

    isource_units = make_list(source_units, n=len(ntsd.columns))
    if isource_units is not None:
        isource_units = ["" if i is None else i for i in isource_units]

    # Create completely filled list of units from the column names.
    tsource_units = []

    for column_name in ntsd.columns:
        if isinstance(column_name, (str, bytes)):
            words = column_name.split(":")

            if len(words) >= 2:
                tsource_units.append(words[1])
            else:
                tsource_units.append("")
        else:
            tsource_units.append(column_name)

    # Combine isource_units and tsource_units into stu.
    stu = []
    if isource_units is not None:
        for isource, tsource in zip(isource_units, tsource_units):
            if not tsource:
                tsource = isource

            if isource != tsource:
                raise ValueError(
                    error_wrapper(
                        f"""
                        The units specified by the "source_units" keyword and
                        in the second ":" delimited field in the DataFrame
                        column name must match.

                        "source_unit" keyword is {isource_units} Column name
                        source units are {tsource_units}"""
                    )
                )
            stu.append(tsource)
    else:
        stu = ["" for _ in ntsd.columns]

    if source_units_required and "" in stu:
        raise ValueError(
            error_wrapper(
                f"""
                Source units must be specified either using "source_units"
                keyword of in the second ":" delimited field in the column
                name.  Instead you have {stu}. """
            )
        )
    names = []

    for inx, unit in enumerate(stu):
        if isinstance(ntsd.columns[inx], (str, bytes)):
            words = ntsd.columns[inx].split(":")

            if unit:
                tmpname = ":".join([words[0], unit])

                if len(words) > 2:
                    tmpname = f"{tmpname}:{':'.join(words[2:])}"
                names.append(tmpname)
            else:
                names.append(":".join(words))
        else:
            names.append(ntsd.columns[inx])
    ntsd.columns = names

    if stu is None and target_units is not None:
        raise ValueError(
            error_wrapper(
                f"""
                To specify target_units, you must also specify source_units.
                You can specify source_units either by using the `source_units`
                keyword or placing in the name of the data column as the second
                ':' separated field.

                The `source_units` keyword must specify units that are
                convertible to the `target_units`: {target_units} """
            )
        )

    # Convert source_units to target_units.

    if target_units is not None:
        ncolumns = []

        for inx, colname in enumerate(ntsd.columns):
            if isinstance(colname, (str, bytes)):
                words = colname.split(":")

                if words:
                    # convert units in words[1] to units in target_units[inx]
                    try:
                        # Would be nice in the future to carry around units,
                        # however at the moment most toolbox_utils functions will
                        # not work right with units specified.
                        # This single command uses pint to convert units and
                        # the "np.array(..., dtype=float)" command removes pint
                        # units from the converted pandas Series.
                        ntsd[colname] = np.array(
                            pd.Series(
                                ntsd[colname].astype(float), dtype=f"pint[{words[1]}]"
                            ).pint.to(target_units[inx]),
                            dtype=float,
                        )
                        words[1] = target_units[inx]
                    except AttributeError as exc:
                        raise ValueError(
                            error_wrapper(
                                f"""
                                No conversion between {words[1]} and
                                {target_units[inx]}."""
                            )
                        ) from exc
                ncolumns.append(":".join(words))
            else:
                ncolumns.append(colname)
        ntsd.columns = ncolumns

    return memory_optimize(ntsd)


def get_default_args(func: Callable) -> Dict[str, Any]:
    """
    Get default arguments of the function through inspection.

    Parameters
    ----------
    func
        The function to inspect.

    Returns
    -------
    get_default_args
        A dictionary of the default arguments of the function.
    """
    signature = inspect.signature(func)

    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def transform_args(**trans_func_for_arg: Dict) -> Callable:
    """
    Transforms function arguments before calling the function.

    Works with plain functions and bounded methods.

    Parameters
    ----------
    trans_func_for_arg
        Dictionary of functions keyed to argument names.

    Returns
    -------
    transform_args_decorator
        Decorator that transforms function arguments before calling the
        function.
    """

    def transform_args_decorator(func):
        sig = inspect.signature(func)

        @wraps(func)
        def transform_args_wrapper(*args, **kwargs):
            # get a {argname: argval, ...} dict from *args and **kwargs
            # Note: Didn't really need an if/else here but I am assuming
            # that getcallargs gives us an overhead that can be avoided if
            # there's only keyword args.
            val_of_argname = sig.bind(*args, **kwargs)
            val_of_argname.apply_defaults()

            for argname, trans_func in trans_func_for_arg.items():
                val_of_argname.arguments[argname] = trans_func(
                    val_of_argname.arguments[argname]
                )
            # apply transform functions to argument values

            return func(*val_of_argname.args, **val_of_argname.kwargs)

        return transform_args_wrapper

    return transform_args_decorator


@transform_args(
    pick=make_list,
    names=make_list,
    source_units=make_list,
    target_units=make_list,
    usecols=make_list,
)
@validate_call
@doc(docstrings)
def common_kwds(
    input_tsd=None,
    start_date=None,
    end_date=None,
    pick: Optional[List[Union[int, str]]] = None,
    force_freq: Optional[str] = None,
    groupby: Optional[str] = None,
    dropna: Optional[Literal["no", "any", "all"]] = "no",
    round_index: Optional[str] = None,
    clean: bool = False,
    target_units=None,
    source_units=None,
    source_units_required: bool = False,
    bestfreq: bool = True,
    parse_dates: bool = True,
    extended_columns: bool = False,
    skiprows: Optional[Union[List[int], int]] = None,
    index_type: Literal["datetime", "number"] = "datetime",
    names: Optional[Union[List[str], str]] = None,
    usecols: Optional[List[Union[int, str]]] = None,
    por: bool = False,
):
    """
    Process all common_kwds across sub-commands into single function.

    Parameters
    ----------
    ${input_ts}
    ${start_date}
    ${end_date}
    ${columns}
    ${force_freq}
    ${groupby}
    ${dropna}
    ${round_index}
    ${clean}
    ${target_units}
    ${source_units}
    source_units_required : bool
        If the source_units are required, either in the DataFrame column
        name or the source_units keyword.
    bestfreq : bool
        Analyze the frequency of the data and return the best frequency.
    parse_dates : bool
        Whether to detect and parse dates in the index column.
    extended_columns : bool
        Whether to create extended column names.
    ${skiprows}
    ${index_type}
    ${names}
    ${usecols}
    ${por}

    Returns
    -------
    df : pandas.DataFrame
        DataFrame altered according to options.
    """
    # The "por" keyword is stupid, since it is a synonym for "dropna" equal
    # to "no".  Discovered this after implementation and should deprecate
    # and remove in the future.
    if por or force_freq:
        dropna = "no"

    ntsd = read_iso_ts(
        input_tsd,
        parse_dates=parse_dates,
        extended_columns=extended_columns,
        dropna=dropna,
        skiprows=skiprows,
        index_type=index_type,
        usecols=usecols,
        clean=clean,
    )

    if names is not None:
        ntsd.columns = names

    ntsd = _pick(ntsd, pick)

    ntsd = _normalize_units(
        ntsd, source_units, target_units, source_units_required=source_units_required
    )

    if clean:
        ntsd = ntsd.sort_index()
        ntsd = ntsd[~ntsd.index.duplicated()]

    ntsd = _round_index(ntsd, round_index=round_index)

    if bestfreq:
        ntsd = asbestfreq(ntsd, force_freq=force_freq)

    ntsd = _date_slice(ntsd, start_date=start_date, end_date=end_date, por=por)

    if ntsd.index.inferred_type == "datetime64":
        ntsd.index.name = "Datetime"

    if dropna in ("any", "all"):
        ntsd = ntsd.dropna(axis="index", how=dropna)
    else:
        with suppress(ValueError):
            if bestfreq:
                ntsd = asbestfreq(ntsd, force_freq=force_freq)

    if groupby is not None:
        if groupby == "months_across_years":
            return ntsd.groupby(lambda x: x.month)

        return ntsd.resample(groupby)

    return ntsd


def _pick(tsd: DataFrame, columns: List[Union[str, int]]) -> DataFrame:
    """
    Pick columns from a DataFrame.

    Parameters
    ----------
    tsd : pandas.DataFrame
        DataFrame to pick columns from.
    columns
        Columns to pick.  Very important - I set the first data column
        number to 1!

    Returns
    -------
    tsd
        DataFrame with only the columns specified.
    """
    columns = make_list(columns)

    if not columns:
        return tsd
    ncolumns = []

    for i in columns:
        if i in tsd.columns:
            # if using column names
            ncolumns.append(tsd.columns.tolist().index(i))

            continue

        if i == tsd.index.name:
            # if wanting the index
            # making it -1 that will be evaluated later...
            ncolumns.append(-1)

            continue
        # if using column numbers
        try:
            target_col = int(i) - 1
        except ValueError as exc:
            raise ValueError(
                error_wrapper(
                    f"""
                    The name {i} isn't in the list of column names
                    {tsd.columns}. """
                )
            ) from exc

        if target_col < -1:
            raise ValueError(
                error_wrapper(
                    f"""
                    The requested column "{i}" must be greater than or equal to
                    0. First data column is 1, index is column 0. """
                )
            )

        if target_col > len(tsd.columns):
            raise ValueError(
                error_wrapper(
                    f"""
                    The request column index {i} must be less than or equal to
                    the number of columns {len(tsd.columns)}. """
                )
            )

        # columns names or numbers or index organized into
        # numbers in ncolumns
        ncolumns.append(target_col)

    if len(ncolumns) == 1 and ncolumns[0] != -1:
        return pd.DataFrame(tsd[tsd.columns[ncolumns]])

    newtsd = pd.DataFrame()

    for index, col in enumerate(ncolumns):
        if col == -1:
            # Use the -1 marker to indicate index
            jtsd = pd.DataFrame(tsd.index, index=tsd.index)
        else:
            try:
                jtsd = pd.DataFrame(tsd.iloc[:, col], index=tsd.index)
            except IndexError:
                jtsd = pd.DataFrame(tsd.loc[:, col], index=tsd.index)

        newtsd = newtsd.join(jtsd, lsuffix=f"_{index}", how="outer")

    return newtsd


def _date_slice(
    input_tsd: DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    por=False,
) -> DataFrame:
    """
    Private function to slice time series.

    Parameters
    ----------
    input_tsd
        DataFrame to slice.
    start_date
        Start date of slice.  If None, use first date in input_tsd.
    end_date
        End date of slice.  If None, use last date in input_tsd.
    por
        If True, set start_date to first day of year and end_date to last
        day of year.

    Returns
    -------
    _data_slice
        Sliced DataFrame.
    """
    if input_tsd.index.inferred_type == "datetime64":
        start_date = pd.Timestamp(start_date or input_tsd.index[0])
        end_date = pd.Timestamp(end_date or input_tsd.index[-1])

        if input_tsd.index.tz is not None:
            try:
                start_date = start_date.tz_convert(input_tsd.index.tz)
            except TypeError:
                start_date = start_date.tz_localize(
                    input_tsd.index.tz, ambiguous=True, nonexistent="shift_forward"
                )
            try:
                end_date = end_date.tz_convert(input_tsd.index.tz)
            except TypeError:
                end_date = end_date.tz_localize(
                    input_tsd.index.tz, ambiguous=True, nonexistent="shift_forward"
                )

        input_tsd = input_tsd.loc[start_date:end_date]

        if por is True:
            if start_date < input_tsd.index[0]:
                input_tsd = pd.DataFrame(index=[start_date]).append(input_tsd)

            if end_date > input_tsd.index[-1]:
                input_tsd = input_tsd.append(pd.DataFrame(index=[end_date]))
            input_tsd = asbestfreq(input_tsd)

    return input_tsd


_ANNUALS: Dict[int, str] = {
    0: "DEC",
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


def asbestfreq(data: DataFrame, force_freq: Optional[str] = None) -> DataFrame:
    """
    Test to determine best frequency to represent data.

    This uses several techniques.
    0.5.  If index is not DateTimeIndex, return
    1. If force_freq is set use .asfreq.
    2. If data.index.freq is not None, just return.
    3. If data.index.inferred_freq is set use .asfreq.
    4. Use pd.infer_freq - fails if any missing
    5. Use .is_* functions to establish A, AS, A-*, AS-*, Q, QS, M, MS
    6. Use minimum interval to establish the fixed time periods up to
       weekly
    7. Gives up returning None for PANDAS offset string

    Parameters
    ----------
    data
        DataFrame to test.
    force_freq
        Force the frequency to this value.

    Returns
    -------
    asbestfreq
        DataFrame with index set to best frequency.
    """
    if not isinstance(data.index, pd.DatetimeIndex):
        return data

    if force_freq is not None:
        return data.asfreq(force_freq)

    if data.index.freq is not None:
        return data

    # Since pandas doesn't set data.index.freq and data.index.freqstr when
    # using .asfreq, this function returns that PANDAS time offset alias code
    # also.  Not ideal at all.
    #
    # This gets most of the frequencies...
    if data.index.inferred_freq is not None:
        with suppress(ValueError):
            return data.asfreq(data.index.inferred_freq)

    # pd.infer_freq would fail if given a large dataset
    slic = slice(None, 999) if len(data.index) > 1000 else slice(None, None)
    try:
        infer_freq = pd.infer_freq(data.index[slic])
    except ValueError:
        infer_freq = None
    if infer_freq is not None:
        return data.asfreq(infer_freq)

    # At this point pd.infer_freq failed probably because of missing values.
    # The following algorithm would not capture things like BQ, BQS
    # ...etc.
    if np.all(data.index.is_year_end):
        infer_freq = "A"
    elif np.all(data.index.is_year_start):
        infer_freq = "AS"
    elif np.all(data.index.is_quarter_end):
        infer_freq = "Q"
    elif np.all(data.index.is_quarter_start):
        infer_freq = "QS"
    elif np.all(data.index.is_month_end):
        if np.all(data.index.month == data.index[0].month):
            # Actually yearly with different ends
            infer_freq = f"A-{_ANNUALS[data.index[0].month]}"
        else:
            infer_freq = "M"
    elif np.all(data.index.is_month_start):
        if np.all(data.index.month == data.index[0].month):
            # Actually yearly with different start
            infer_freq = f"A-{_ANNUALS[data.index[0].month - 1]}"
        else:
            infer_freq = "MS"
    if infer_freq is not None:
        return data.asfreq(infer_freq)

    ndiff = (
        data.index.values.astype("int64")[1:] - data.index.values.astype("int64")[:-1]
    )

    if np.any(ndiff <= 0):
        raise ValueError(
            error_wrapper(
                f"""
                Duplicate or time reversal index entry at record
                {np.where(ndiff <= 0)[0][0] + 1} (start count at 0):
                "{data.index[:-1][ndiff <= 0][0]}".

                Perhaps use the "--clean" keyword on the CLI or "clean=True" if
                using Python or edit the input data..
                """
            )
        )

    # Use the minimum of the intervals to test a new interval.
    # Should work for fixed intervals.
    ndiff = sorted(set(ndiff))
    ngcd = ndiff[0] if len(ndiff) == 1 else reduce(gcd, ndiff)
    if ngcd < 1000:
        infer_freq = f"{ngcd}N"
    elif ngcd < 1000000:
        infer_freq = f"{ngcd // 1000}U"
    elif ngcd < 1000000000:
        infer_freq = f"{ngcd // 1000000}L"
    elif ngcd < 60000000000:
        infer_freq = f"{ngcd // 1000000000}S"
    elif ngcd < 3600000000000:
        infer_freq = f"{ngcd // 60000000000}T"
    elif ngcd < 86400000000000:
        infer_freq = f"{ngcd // 3600000000000}H"
    elif ngcd < 604800000000000:
        infer_freq = f"{ngcd // 86400000000000}D"
    elif ngcd < 2419200000000000:
        infer_freq = f"{ngcd // 604800000000000}W"
        if np.all(data.index.dayofweek == data.index[0].dayofweek):
            infer_freq = f"{infer_freq}-{_WEEKLIES[data.index[0].dayofweek]}"
        else:
            infer_freq = "D"

    return data.asfreq(infer_freq) if infer_freq is not None else data


def dedup_index(
    idx: List[str], fmt: Optional[Any] = None, ignore_first: bool = True
) -> Index:
    """
    Remove duplicate values in list.

    Parameters
    ----------
    idx
        List of strings.
    fmt
        A string format that receives two arguments: name and a counter. By
        default: fmt='%s.%03d'
    ignore_first : bool
        Disable/enable postfixing of first element.

    Returns
    -------
    dedup_index
        A pandas index with duplicate values removed.
    """
    idx = pd.Series(idx)
    duplicates = idx[idx.duplicated()].unique()
    fmt = "%s.%03d" if fmt is None else fmt
    for name in duplicates:
        dups = idx == name
        ret = [
            fmt % (name, i) if (i != 0 or not ignore_first) else name
            for i in range(dups.sum())
        ]
        idx.loc[dups] = ret
    return pd.Index(idx)


@validate_call
def renamer(column_names: str, suffix: Optional[str] = "") -> str:
    """
    Print the suffix into the third ":" separated field of the header.

    Parameters
    ----------
    column_names
        The location of the time series.
    suffix
        The suffix to be added to the location.

    Returns
    -------
    renamer
        The new location with the suffix added.
    """
    if suffix is None:
        suffix = ""
    words = column_names.split(":")

    if len(words) == 1:
        words.extend(("", suffix))
    elif len(words) == 2:
        words.append(suffix)
    elif len(words) == 3 and suffix:
        words[2] = f"{words[2]}_{suffix}" if words[2] else suffix

    return ":".join(words)


# Utility
def print_input(
    iftrue: bool,
    intds: DataFrame,
    output: DataFrame,
    suffix: str = "",
    date_format: str = None,
    float_format: str = "g",
    tablefmt: str = "csv",
    showindex: str = "never",
):
    """
    Print the input time series also.

    Parameters
    ----------
    iftrue
        If true, print the input time series also.
    intds
        The input time series.
    output
        The output time series.
    suffix
        The suffix to be added to the column names.
    date_format
        The date format to be used.
    float_format
        The float format to be used.
    tablefmt
        The table format to be used.
    showindex
        Include the index.
    """
    return printiso(
        return_input(iftrue, intds, output, suffix=suffix),
        date_format=date_format,
        float_format=float_format,
        tablefmt=tablefmt,
        showindex=showindex,
    )


def return_input(
    iftrue: Union[bool, str],
    intds: DataFrame,
    output: DataFrame,
    suffix: Optional[str] = "",
    reverse_index: bool = False,
    output_names: Optional[List] = None,
) -> DataFrame:
    """
    Return the input time series also with the output dataframe.

    Parameters
    ----------
    iftrue
        If true, print the input time series also.
    intds
        The input time series.
    output
        The output time series.
    suffix
        The suffix to be added to the column names.
    reverse_index
        Reverse the index.
    output_names
        The names of the output columns.

    Returns
    -------
    return_input
        The input time series also with the output dataframe.
    """

    if output_names is None:
        output_names = []
    output.columns = output_names or [renamer(i, suffix) for i in output.columns]

    if iftrue:
        return memory_optimize(
            intds.join(output, lsuffix="_1", rsuffix="_2", how="outer")
        )

    if reverse_index:
        return memory_optimize(output.iloc[::-1])

    return memory_optimize(output)


def _apply_across_columns(func, xtsd, **kwds):
    """Apply a function to each column in turn."""

    for col in xtsd.columns:
        xtsd[col] = func(xtsd[col], **kwds)

    return xtsd


def _printiso(
    tsd: DataFrame,
    date_format: Optional[Any] = None,
    sep: str = ",",
    float_format: str = "g",
    showindex: Union[str, bool] = True,
    headers: str = "keys",
    tablefmt: Optional[str] = "csv",
) -> None:
    """Separate this function so can use in tests."""
    showindex = {"always": True, "never": False, True: True, False: False}[showindex]

    if isinstance(tsd, (pd.DataFrame, pd.Series)):
        if isinstance(tsd, pd.Series):
            tsd = pd.DataFrame(tsd)

        if tsd.columns.empty:
            tsd = pd.DataFrame(index=tsd.index)

        if not tsd.index.name:
            tsd.index.name = "UniqueID"

        if isinstance(tsd.index, (pd.DatetimeIndex, pd.PeriodIndex)):
            tsd.index.name = "Datetime"

    elif isinstance(tsd, (int, float, tuple, np.ndarray)):
        tablefmt = None

    ntablefmt = None

    if tablefmt in ("csv", "tsv", "csv_nos", "tsv_nos"):
        sep = {"csv": ",", "tsv": "\t", "csv_nos": ",", "tsv_nos": "\t"}[tablefmt]

        if isinstance(tsd, pd.DataFrame):
            try:
                tsd.to_csv(
                    sys.stdout,
                    float_format=f"%{float_format}",
                    date_format=date_format,
                    sep=sep,
                    index=showindex,
                )

                return
            except OSError:
                return
        else:
            ntablefmt = simple_separated_format(sep)

    if tablefmt is None:
        print(str(list(tsd))[1:-1])

    if ntablefmt is None:
        all_table = tb(
            tsd,
            tablefmt=tablefmt,
            showindex=showindex,
            headers=headers,
            floatfmt=float_format,
        )
    else:
        all_table = tb(
            tsd,
            tablefmt=ntablefmt,
            showindex=showindex,
            headers=headers,
            floatfmt=float_format,
        )

    if tablefmt in ("csv_nos", "tsv_nos"):
        print(all_table.replace(" ", ""))
    else:
        print(all_table)


# Make _printiso public.  Keep both around until convert all toolboxes.
printiso = _printiso


def open_local(filein: str) -> TextIOWrapper:
    """
    Open the given input file.

    It can decode various formats too, such as gzip and bz2.
    """
    base, ext = os.path.splitext(os.path.basename(filein))

    if ext in (".gz", ".GZ"):
        return gzip.open(filein, "rb"), base

    if ext in (".bz", ".bz2"):
        return bz2.BZ2File(filein, "rb"), base

    return open(filein, encoding="utf-8"), os.path.basename(filein)


def reduce_mem_usage(props):
    """
    Kept here, but was too aggressive in terms of setting the dtype.

    Not used any longer.
    """

    for col in props.columns:
        try:
            if props[col].dtype == object:  # Exclude strings
                continue
        except AttributeError:
            continue

        # make variables for Int, max and min
        mxx = props[col].max()
        mnn = props[col].min()

        # test if column can be converted to an integer
        try:
            asint = props[col].astype(np.int64)
            result = all((props[col] - asint) == 0)
        except ValueError:
            # Want missing values to remain missing so
            # they need to remain float.
            result = False

        if result:
            if mnn >= 0:
                if mxx < np.iinfo(np.uint8).max:
                    props[col] = props[col].astype(np.uint8)
                elif mxx < np.iinfo(np.uint16).max:
                    props[col] = props[col].astype(np.uint16)
                elif mxx < np.iinfo(np.uint32).max:
                    props[col] = props[col].astype(np.uint32)
                else:
                    props[col] = props[col].astype(np.uint64)
            elif mnn > np.iinfo(np.int8).min and mxx < np.iinfo(np.int8).max:
                props[col] = props[col].astype(np.int8)
            elif mnn > np.iinfo(np.int16).min and mxx < np.iinfo(np.int16).max:
                props[col] = props[col].astype(np.int16)
            elif mnn > np.iinfo(np.int32).min and mxx < np.iinfo(np.int32).max:
                props[col] = props[col].astype(np.int32)
            elif mnn > np.iinfo(np.int64).min and mxx < np.iinfo(np.int64).max:
                props[col] = props[col].astype(np.int64)

    return props


def memory_optimize(tsd: DataFrame) -> DataFrame:
    """
    Convert all columns to known types.

    "convert_dtypes" replaced some code here such that the
    "memory_optimize" function might go away.  Kept in case want to add
    additional optimizations.
    """
    tsd.index = pd.Index(tsd.index, dtype=None)
    tsd = tsd.convert_dtypes()
    with suppress(TypeError, ValueError):
        # TypeError: Not datetime like index
        # ValueError: Less than three rows
        tsd.index.freq = pd.infer_freq(tsd.index)

    return tsd


def is_valid_url(url: Union[bytes, str], qualifying: Optional[Any] = None) -> bool:
    """Return whether "url" is valid."""
    min_attributes = ("scheme", "netloc")
    qualifying = min_attributes if qualifying is None else qualifying
    token = urlparse(url)

    return all(getattr(token, qualifying_attr) for qualifying_attr in qualifying)


@validate_call
def read_iso_ts(
    *inindat,
    dropna: Optional[Literal["no", "any", "all"]] = None,
    extended_columns: bool = False,
    parse_dates: bool = True,
    skiprows: Optional[Union[int, List[int]]] = None,
    index_type: Literal["datetime", "number"] = "datetime",
    names: Optional[str] = None,
    header: Optional[Union[int, str]] = "infer",
    sep: Optional[str] = ",",
    index_col=0,
    usecols=None,
    **kwds,
) -> pd.DataFrame:
    """
    Read the format printed by 'printiso' and maybe other formats.

    Parameters
    ----------
    *inindat
        The input data.
    dropna
        If "no", do not drop any rows.  If "any", drop rows with any
        missing values.  If "all", drop rows with all missing values.
    extended_columns
        If True, then the first row of the input data is a list of
        column names.  If False, then the first row of the input data
        is a list of column numbers.
    parse_dates
        If True, then convert the index to a datetime index.
    skiprows
        Line numbers to skip (0-indexed) or number of lines to skip
        (int) at the start of the file.  If callable, the callable
        function will be evaluated against the row indices, returning
        True if the row should be skipped and False otherwise.
    index_type
        If "datetime", then the index is a datetime index.  If
        "number", then the index is a number index.
    names
        List of column names to use.  If file contains no header row,
        then you should explicitly pass header=None.
    header
        Row number(s) to use as the column names, and the start of the
        data.  Default behavior is to infer the column names: if no
        names are passed the behavior is identical to header=0 and
        column names are inferred from the first line of the file, if
        column names are passed explicitly then the behavior is
        identical to header=None. Explicitly pass header=0 to be able
        to replace existing names.
    sep
        Delimiter to use.  If sep is None, will try to automatically
        determine this.  Separators longer than 1 character and
        different from '\\s+' will be interpreted as regular
        expressions, will force use of the python parsing engine and
        will ignore quotes in the data.  Regex example: '\r\t'.
    index_col
        Column(s) to use as the row labels of the DataFrame, either
        given as string name or column index.  If a sequence of int /
        str is given, a MultiIndex is used.
    usecols
        Return a subset of the columns.  If list-like, all elements
        must either be positional (i.e. integer indices into the
        document columns) or strings that correspond to column names
        provided either by the user in names or inferred from the
        document header row(s).  For example, a valid list-like
        usecols parameter would be [0, 1, 2] or ['foo', 'bar',
        'baz'].  Element order is ignored, so usecols=[0, 1] is the
        same as [1, 0].  To instantiate a DataFrame from data with
        element order preserved use pd.read_csv(data,
        usecols=['foo', 'bar'])[['foo', 'bar']] for columns in ['foo',
        'bar'] order or pd.read_csv(data, usecols=['foo', 'bar'])[['bar',
        'foo']] for ['bar', 'foo'] order.  If callable, the callable
        function will be evaluated against the column names, returning
        names where the callable function evaluates to True.  An
        example of a valid callable argument would be lambda x:
        x.upper() in ['AAA', 'BBB', 'DDD'].  Using this parameter
        results in much faster parsing time and lower memory usage.
    **kwds
        Any additional keyword arguments are passed to
        pandas.read_csv().

    Returns
    -------
    df: DataFrame
        Returns a DataFrame.
    """
    # inindat
    #
    # CLI                              API                             TRANSFORM
    # ("-",)                           "-"                             [["-"]]
    #                                                                  all columns from standard input
    #
    # ("1,2,Value",)                   [1, 2, "Value"]                 [["-", 1, 2, "Value"]]
    #                                                                  extract columns from standard input
    #
    # ("fn.csv,skiprows=4",)           ["fn.csv", {"skiprow":4}]       [["fn.csv", "skiprows=4"]]
    #                                                                  all columns from "fn.csv"
    #                                                                  skipping the 5th row
    #
    # ("fn.csv,1,4,Val",)              ["fn.csv", 1, 4, "Val"]         [["fn.csv", 1, 4, "Val"]]
    #                                                                  extract columns from fn.csv
    #
    # ("fn.wdm,1002,20000",)           ["fn.wdm", 1002, 20000]         [["fn.wdm", 1002, 20000]]
    #                                                                  WDM files MUST have DSNs
    #                                                                  extract DSNs from "fn.wdm"
    #
    # ("fn.csv,Val1,Q,4 fn.wdm,201",)  [["fn.csv", "Val1", "Q", 4], ["fn.wdm", 101, 201]]
    #                                                                  extract columns from fn.csv
    #                                                                  extract DSNs from fn.wdm
    #
    #                                  dataframe                       dataframe
    #
    #                                  series                          dataframe
    clean = kwds.get("clean", False)
    names = kwds.get("names")

    if not inindat:
        inindat = "-"

    # Would want this to be more generic...
    na_values = []
    for spc in range(20)[1:]:
        spcs = " " * spc
        na_values.extend([spcs, f"{spcs}nan"])

    fstr = "{0}.{1}" if extended_columns else "{1}"
    if names is not None:
        header = 0
        names = make_list(names)

    if index_type == "number":
        parse_dates = False

    if (
        isinstance(inindat[0], (tuple, list, pd.DataFrame, pd.Series))
        and len(inindat) == 1
    ):
        inindat = inindat[0]
    sources = make_list(inindat, sep=" ", flat=False)

    lresult_list = []
    zones = set()
    result = pd.DataFrame()
    stdin_df = pd.DataFrame()
    for source_index, source in enumerate(sources):
        res = pd.DataFrame()
        if isinstance(source, str):
            parameters = re.split(r",(?![^\[]*\])", source)
        else:
            parameters = make_list(source)

        if isinstance(parameters, list) and parameters:
            fname = parameters.pop(0)
        else:
            fname = parameters
            parameters = []

        # Python API
        if isinstance(fname, pd.DataFrame):
            res = fname[parameters] if parameters else fname
        elif isinstance(fname, (pd.Series, dict)):
            res = pd.DataFrame(inindat)
        elif isinstance(fname, (tuple, list, float)):
            res = pd.DataFrame({f"values{source_index}": fname}, index=[0])

        newkwds: Dict[str, Union[str, bool]] = {}
        if res.empty:
            # Store keywords for each source.
            parameters = [str(p) for p in parameters]

            args = [i for i in parameters if "=" not in i]

            newkwds = dict([i.split("=") for i in parameters if "=" in i])
            newkwds = {k: literal_eval(v) for k, v in newkwds.items()}

            # Command line API
            # Uses hspf_reader or pd.read_* functions.
            fpi = None

            if fname in ("-", b"-"):
                # if from stdin format must be the toolbox_utils standard
                # pandas read_csv supports file like objects

                if "header" not in kwds:
                    kwds["header"] = 0
                header = 0
                fpi = sys.stdin
            elif isinstance(fname, (StringIO, BytesIO)):
                fpi = fname
                header = 0
            elif os.path.exists(str(fname)):
                # a local file
                # Read all wdm, hdf5, and, xls* files here
                sep = ","
                index_col = 0
                usecols = None
                fpi = fname
                _, ext = os.path.splitext(fname)

                if ext.lower() == ".wdm":
                    nres = []

                    for par in args:
                        nres.extend(
                            wdm(fname, npar) for npar in range_to_numlist(str(par))
                        )
                    res = pd.concat(nres, axis="columns")
                elif ext.lower() == ".hbn":
                    res = pd.DataFrame()
                    # fname: str,
                    # interval: Literal["yearly", "monthly", "daily", "bivl"],
                    # *labels,
                    interval, *labels = args
                    res = res.join(hbn(fname, interval, labels), how="outer")
                elif ext.lower() == ".plt":
                    res = plotgen(fname)
                elif ext.lower() == ".hdf5":
                    if args:
                        res = pd.DataFrame()

                        for i in args:
                            res = res.join(
                                pd.read_hdf(fname, key=i, **newkwds), how="outer"
                            )
                    else:
                        res = pd.read_hdf(fpi, **newkwds)
                elif ext.lower() in (
                    ".xls",
                    ".xlsx",
                    ".xlsm",
                    ".xlsb",
                    ".odf",
                    ".ods",
                    ".odt",
                ):
                    # Sometime in the future, we may want to be able to
                    # create a multi-index, but for now, we'll just
                    # use the first row as the header.
                    header = 0

                    sheet = make_list(args) if args else 0
                    try:
                        res = pd.read_excel(
                            fname,
                            sheet_name=sheet,
                            keep_default_na=True,
                            header=header,
                            na_values=na_values,
                            index_col=index_col,
                            usecols=usecols,
                            parse_dates=parse_dates,
                            skiprows=skiprows,
                            **newkwds,
                        )
                    except ValueError:
                        res = pd.read_excel(
                            fname,
                            sheet_name=sheet,
                            keep_default_na=True,
                            header=header,
                            na_values=na_values,
                            index_col=index_col,
                            usecols=usecols,
                            parse_dates=parse_dates,
                            skiprows=skiprows,
                            **newkwds,
                        )

                    if isinstance(res, dict):
                        res = pd.concat(res, axis="columns")
                        # Collapse columns MultiIndex
                        flat_index = res.columns.to_flat_index()
                        flat_index = [
                            "_".join((str(i[0]), str(i[1]))) for i in flat_index
                        ]
                        res.columns = flat_index

            elif is_valid_url(str(fname)):
                # a url?
                header = "infer"
                fpi = fname
            elif isinstance(fname, bytes):
                # Python API

                if b"\n" in fname or b"\r" in fname:
                    fpi = BytesIO(fname)
                else:
                    args.insert(0, fname)
                    fname = "-"
                    fpi = sys.stdin
                # a string?
                header = 0
            elif isinstance(fname, str):
                # Python API

                if "\n" in fname or "\r" in fname:
                    fpi = StringIO(fname)
                else:
                    args.insert(0, fname)
                    fpi = sys.stdin
                    fname = "-"
                # a string?
                header = 0
            else:
                # Maybe fname and args are actual column names of standard
                # input.
                args.insert(0, fname)
                fname = "-"
                header = 0
                fpi = sys.stdin

        if res.empty:
            if fname == "-" and not stdin_df.empty:
                res = stdin_df
            else:
                res = pd.read_csv(
                    fpi,
                    engine="python",
                    keep_default_na=True,
                    skipinitialspace=True,
                    header=header,
                    sep=sep,
                    na_values=na_values,
                    index_col=index_col,
                    parse_dates=parse_dates,
                    **newkwds,
                )

            if fname == "-" and stdin_df.empty:
                stdin_df = res
            res = _pick(res, args)

        lresult_list.append(res)
        with suppress(AttributeError):
            zones.add(res.index.tzinfo)

    first = []
    second = []
    rest = []

    for col in res.columns:
        words = [i.strip() for i in str(col).split(":")]
        nwords = [i.strip("0123456789") for i in words]

        first.append(fstr.format(fname, words[0].strip()))

        if len(words) > 1:
            second.append([nwords[1]])
        else:
            second.append([])

        if len(nwords) > 2:
            rest.append(nwords[2:])
        else:
            rest.append([])
    first = [[i.strip()] for i in dedup_index(first)]
    res.columns = [":".join(i + j + k) for i, j, k in zip(first, second, rest)]

    res = memory_optimize(res)

    if res.index.inferred_type == "datetime64":
        try:
            words = res.index.name.split(":")
        except AttributeError:
            words = []

        if len(words) > 1:
            with suppress(TypeError):
                res.index = res.index.tz_localize(words[1])
            res.index.name = f"Datetime:{words[1]}"
        else:
            res.index.name = "Datetime"
    else:
        with suppress(KeyError):
            res.set_index(0, inplace=True)

    if dropna in ("any", "all"):
        res.dropna(how=dropna, inplace=True)

    if len(lresult_list) > 1:
        epoch = pd.to_datetime("2000-01-01")
        moffset = epoch + to_offset("A")
        offset_set = set()

        for res in lresult_list:
            if res.index.inferred_type != "datetime64":
                continue

            if len(zones) != 1:
                with suppress(TypeError, AttributeError):
                    res.index = res.index.tz_convert(None)

            # Remove duplicate times if hourly and daylight savings.

            if clean is True:
                res = res.sort_index()
                res = res[~res.index.duplicated()]

            res = asbestfreq(res)

            if res.index.inferred_freq is not None and moffset > epoch + to_offset(
                res.index.inferred_freq
            ):
                moffset = epoch + to_offset(res.index.inferred_freq)
                offset_set.add(moffset)

        result = pd.DataFrame()

        for lres in lresult_list:
            if len(offset_set) < 2:
                result = result.join(lres, how="outer", rsuffix="_r")
            else:
                result = result.join(
                    lres.asfreq(moffset - epoch), how="outer", rsuffix="_r"
                )
    else:
        result = lresult_list[0]

    # Assign names to the index and columns.

    if names is not None:
        result.index.name = names.pop(0)
        result.columns = names

    result.sort_index(inplace=True)

    return result.convert_dtypes()


@validate_call
def range_to_numlist(rangestr: Union[str, int, List]) -> List:
    """
    Convert a range string to a list of numbers.

    Parameters
    ----------
    rangestr
        A string containing a range of numbers.  The range can be a single
        number, a range of numbers separated by a colon, or a list of
        ranges separated by a plus sign.  Examples: "1", "1:4",
        "1:4+16:22".

    Returns
    -------
    range_to_numlist
        A list of numbers.
    """
    if isinstance(rangestr, int):
        return [rangestr]

    numlist = []
    subranges = make_list(rangestr, sep="+")

    for sub in subranges:
        slices = make_list(sub, sep=":")
        for tst in slices:
            if not isinstance(tst, int):
                raise ValueError(
                    error_wrapper(
                        f"""Invalid range specification in '{sub}' of the
                        '{rangestr}'.  The value {tst} is not an integer.
                        """
                    )
                )
        if len(slices) == 1:
            num = slices[0]
            numlist.append(num)
        elif len(slices) in {2, 3}:
            rstart = slices[0]
            rend = slices[1] + 1
            if rstart >= rend:
                raise ValueError(
                    error_wrapper(
                        f"""Invalid range specification in '{sub}' of the
                        '{rangestr}'.  The start value of {rstart} is
                        greater than or equal to the end value of {rend - 1}.
                        """
                    )
                )
            step = 1 if len(slices) == 2 else slices[2]
            numlist.extend(range(rstart, rend, step))
        else:
            raise ValueError(
                error_wrapper(
                    f"""Invalid range specification in '{sub}' of the
                    '{rangestr}'. The correct syntax is one or more integers or
                    colon-delimited range groups such as "99", "1:2", or
                    "101:120", with multiple groups connected by "+" signs.
                    Example: "1:4+16:22+30"
                    """
                )
            )

    return numlist
