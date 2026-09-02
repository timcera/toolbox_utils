"""
Read Hydrological Simulation Program Python (HSPsquared) HDF5 files.
"""

# Standard library imports
import sys
from pathlib import Path
from typing import Literal

# Third party imports
import pandas as pd
from pydantic import validate_call

# Local folder imports
from .. import tsutils
from . import utils

_LOCAL_DOCSTRINGS = {
    "hdf5filename": r"""hdf5filename: str
        The HDF5 binary output file.  This file must have been created from
        a completed HSP2 model run."""
}

tablefmt_docstring = """[optional, default is 'cvs_nos']

The table format.  Can be one of 'csv', 'tsv', 'csv_nos', 'tsv_nos',
'plain', 'simple', 'github', 'grid', 'fancy_grid', 'pipe', 'orgtbl',
'jira', 'presto', 'psql', 'rst', 'mediawiki', 'moinmoin', 'youtrack',
'html', 'latex', 'latex_raw', 'latex_booktabs' and 'textile'.
"""

float_format_docstring = """[optional, default is 'g']

The format for floating point numbers in the output table.
"""


def _get_data(binfilename, interval="daily", labels=None, catalog_only=True):
    """Underlying function to read from the binary file.  Used by
    'extract', 'catalog'.
    """
    ext = str(Path(binfilename).suffix).lower()
    if ext not in [".h5", ".hdf5"]:
        raise ValueError(f"""
            This function works with HDF5 files that typically have an filename
            extension of '*.h5' or '*.hdf5'.  You have {binfilename}.""")

    lablist, intervalcode = utils.normalize_labels(labels, interval)

    labeltest = set()
    with pd.HDFStore(binfilename, "r") as store:
        # "/RESULTS/RCHRES_R005/SEDTRN"
        keys = store.keys()

    _dirname = Path(__file__).parent.parent
    hspf_time_series = pd.read_csv(_dirname / "data" / "HSPF_TIME_SERIES.csv")

    collect_dict = {}
    for key in keys:
        keyparts = key.strip("/").split("/")
        if keyparts[0] != "RESULTS":
            continue
        optype, lue = keyparts[1].split("_")
        lue = int(lue[1:])
        group = keyparts[2]

        with pd.HDFStore(binfilename, "r") as store:
            df = store.get(key)

        if df.index[0].year < 1677:
            raise ValueError(
                tsutils.error_wrapper(
                    """
                    Error occurred that only happens if numpy version is 1.*
                    and pandas version is 1.*.  This only impacts "pd.read_hdf"
                    and I didn't find a work-around.  If you need this feature
                    please update the numpy and pandas versions.
                    """
                )
            )

        for vname in df.columns:
            tmpkey = (
                optype,
                lue,
                group,
                vname,
                None,
            )

            for lbl in lablist:
                res = utils.tuple_search(tmpkey, [lbl])
                if not res:
                    continue
                nres = res[0][1]
                labeltest.add(tuple(lbl))
                # *.h5 files only have "bivl" (code 2) level, so we have to
                # make "daily", "monthly", and "yearly" versions of the labels
                # to match and then calculate whatever aggregation is requested
                # by the user.
                for ival in [2, 3, 4, 5]:
                    nres = nres[:-1] + (ival,)
                    if catalog_only:
                        collect_dict[nres] = ival
                    else:
                        if intervalcode == ival:
                            if ival == 2:
                                series = df[vname]
                            else:
                                min_count = 1
                                min_count = utils.code2min_count[
                                    (df.index.freqstr, ival)
                                ]
                                agg_type = hspf_time_series.loc[
                                    (hspf_time_series["OPERATION"] == nres[0])
                                    & (hspf_time_series["GROUP"] == nres[2])
                                    & (hspf_time_series["MEMN"] == nres[3]),
                                    "AGGREGATE",
                                ].squeeze()
                                # Suspect that "ANY" or "NONE" would never come
                                # up in binary output.  Just in case assigned
                                # those categories to the same aggregation for
                                # "LAST".
                                if agg_type in ["LAST", "ANY", "NONE"]:
                                    series = (
                                        df[vname]
                                        .resample(utils.code2freqmap[ival])
                                        .last(min_count=min_count)
                                    )
                                elif agg_type == "SUM":
                                    series = (
                                        df[vname]
                                        .resample(utils.code2freqmap[ival])
                                        .sum(min_count=min_count)
                                    )
                            series = series.loc[: series.last_valid_index()].asfreq(
                                utils.code2freqmap[ival]
                            )
                            ndates = series.index
                            collect_dict[nres] = series.values

    if not collect_dict:
        raise ValueError(
            tsutils.error_wrapper(
                f"""
                The label specifications below matched no records in the binary
                file.

                {lablist}
                """
            )
        )

    ndates = sorted(ndates)

    if catalog_only:
        for key in collect_dict:
            delta = ndates[1] - ndates[0] if key[4] == 2 else utils.code2freqmap[key[4]]
            collect_dict[key] = (
                pd.Period(ndates[0], freq=delta),
                pd.Period(ndates[-1], freq=delta),
            )
    else:
        for lbl in lablist:
            if tuple(lbl) not in labeltest:
                sys.stderr.write(
                    tsutils.error_wrapper(
                        f"""
                        Warning: The label '{lbl}' matched no records in the
                        binary file.
                        """
                    )
                )

    return ndates, collect_dict


@validate_call
def hdf5_extract(
    hdf5filename: str,
    interval: Literal["yearly", "monthly", "daily", "bivl"],
    *labels,
    start_date=None,
    end_date=None,
    sort_columns: bool = False,
):
    """
    Extracts data from a HSP2 HDF5 output file.

    Parameters
    ----------
    ${hdf5filename}
    interval : str
        One of 'yearly', 'monthly', 'daily', or 'bivl'.  The 'bivl' option is
        a sub-daily interval defined in the UCI file.  Typically 'bivl' is used
        for hourly output, but can be set to any value that evenly divides into
        a day.
    labels : str
        The remaining arguments uniquely identify a time-series in the
        binary file.  The format is 'OPERATIONTYPE,ID,VARIABLEGROUP,VARIABLE'.

        For example: 'PERLND,101,PWATER,UZS IMPLND,101,IWATER,RETS'

        Leaving a section without an entry will wild card that
        specification.  To get all the PWATER variables for PERLND 101 the
        label would read:

        'PERLND,101,PWATER,'

        To get TAET for all PERLNDs:

        'PERLND,,,TAET'

        Note that there are spaces ONLY between label specifications not within
        the labels themselves.

        OPERATIONTYE can be PERLND, IMPLND, RCHRES, and BMPRAC.

        ID is the operation type identification number specified in the UCI
        file. These numbers must be in the range 1-999.

        Here, the user can specify

            - a single ID number to match
            - no entry, matching any operation ID number
            - a range, specified as any combination of simple integers and
              groups of integers marked as "start:end", with multiple allowed
              sub-ranges separated by the "+" sign.

        Examples::

            +-----------------------+-------------------------------+
            | Label ID              | Expands to:                   |
            +=======================+===============================+
            | 1:10                  | 1,2,3,4,5,6,7,8,9,10          |
            +-----------------------+-------------------------------+
            | 101:119+221:239       | 101,102..119,221,221,...239   |
            +-----------------------+-------------------------------+
            | 3:5+7                 | 3,4,5,7                       |
            +-----------------------+-------------------------------+

        VARIABLEGROUP depends on OPERATIONTYPE where::

            if OPERATIONTYPE is PERLND then VARIABLEGROUP can be one of
                'ATEMP', 'SNOW', 'PWATER', 'SEDMNT', 'PSTEMP', 'PWTGAS',
                'PQUAL', 'MSTLAY', 'PEST', 'NITR', 'PHOS', 'TRACER'

            if OPERATIONTYPE is IMPLND then VARIABLEGROUP can be one of
                'ATEMP', 'SNOW', 'IWATER', 'SOLIDS', 'IWTGAS', 'IQUAL'

            if OPERATIONTYPE is RCHRES then VARIABLEGROUP can be one of
                'HYDR', 'CONS', 'HTRCH', 'SEDTRN', 'GQUAL', 'OXRX', 'NUTRX',
                'PLANK', 'PHCARB', 'INFLOW', 'OFLOW', 'ROFLOW'

            if OPERATIONTYPE is BMPRAC then VARIABLEGROUP is not used and you
            have to leave VARIABLEGROUP as a wild card.  For example,
            'BMPRAC,875,,RMVOL'.

        The Time Series Catalog in the HSPF Manual lists all of the variables
        in each of these VARIABLEGROUPs.  For BMPRAC, all of the variables in
        all Groups in the Catalog are available in the unnamed (blank) Group.

    ${start_date}

    ${end_date}

    sort_columns:
        [optional, default is False]

        If set to False will maintain the columns order of the labels.  If set
        to True will sort all columns by their columns names.
    """
    interval = interval.lower()
    if interval not in ["bivl", "daily", "monthly", "yearly"]:
        raise ValueError(
            tsutils.error_wrapper(
                f"""
                The "interval" argument must be one of "bivl", "daily",
                "monthly", or "yearly".  You supplied "{interval}".
                """
            )
        )

    index, data = _get_data(hdf5filename, interval, labels, catalog_only=False)
    skeys = list(data.keys())
    if sort_columns:
        skeys.sort(key=lambda tup: tup[1:])
    columns = [f"{i[0]}_{i[1]}_{i[3]}".replace(" ", "-") for i in skeys]
    result = pd.DataFrame(
        pd.concat(
            [pd.Series(data[i], index=index) for i in skeys], sort=False, axis=1
        ).reindex(pd.Index(index))
    )
    result.columns = columns
    result = tsutils.asbestfreq(result)
    result = tsutils.common_kwds(result, start_date=start_date, end_date=end_date)
    if len(result) > 1:
        if interval == "bivl":
            result.index = result.index.to_period(result.index[1] - result.index[0])
        else:
            result.index = result.index.to_period()
    result.index.name = "Datetime"

    return result
