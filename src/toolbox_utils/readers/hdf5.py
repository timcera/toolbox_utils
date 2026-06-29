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

code2intervalmap = {5: "yearly", 4: "monthly", 3: "daily", 2: "bivl"}

interval2codemap = {"yearly": 5, "monthly": 4, "daily": 3, "bivl": 2}

code2freqmap = {
    5: pd.offsets.YearEnd(),
    4: pd.offsets.MonthEnd(),
    3: "D",
    2: None,
}

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


def tuple_match(a, b):
    """Part of partial ordered matching.
    See http://stackoverflow.com/a/4559604
    """
    return len(a) == len(b) and all(
        i is None or j is None or i == j for i, j in zip(a, b)
    )


def tuple_combine(a, b):
    """Part of partial ordered matching.
    See http://stackoverflow.com/a/4559604
    """
    return tuple(i is None and j or i for i, j in zip(a, b))


def tuple_search(findme, haystack):
    """Partial ordered matching with 'None' as wildcard
    See http://stackoverflow.com/a/4559604
    """
    return [
        (i, tuple_combine(findme, h))
        for i, h in enumerate(haystack)
        if tuple_match(findme, h)
    ]


def _get_data(binfilename, interval="daily", labels=None, catalog_only=True):
    """Underlying function to read from the binary file.  Used by
    'extract', 'catalog'.
    """
    ext = str(Path(binfilename).suffix).lower()
    if ext not in [".h5", ".hdf5"]:
        raise ValueError(f"""
            This function works with HDF5 files that typically have an filename
            extension of '*.h5' or '*.hdf5'.  You have {binfilename}.""")

    if labels is None:
        labels = [",,,"]
    testem = {
        "PERLND": [
            "ATEMP",
            "SNOW",
            "PWATER",
            "SEDMNT",
            "PSTEMP",
            "PWTGAS",
            "PQUAL",
            "MSTLAY",
            "PEST",
            "NITR",
            "PHOS",
            "TRACER",
            "",
        ],
        "IMPLND": ["ATEMP", "SNOW", "IWATER", "SOLIDS", "IWTGAS", "IQUAL", ""],
        "RCHRES": [
            "HYDR",
            "CONS",
            "HTRCH",
            "SEDTRN",
            "GQUAL",
            "OXRX",
            "NUTRX",
            "PLANK",
            "PHCARB",
            "INFLOW",
            "OFLOW",
            "ROFLOW",
            "",
        ],
        "BMPRAC": [""],
        "": [""],
    }

    collect_dict = {}
    lablist = []

    # Normalize interval code
    try:
        intervalcode = interval2codemap[interval.lower()]
    except AttributeError:
        intervalcode = None

    # convert label tuples to lists
    labels = list(labels)

    # turn into a list of lists
    nlabels = []
    for label in labels:
        if isinstance(label, str):
            nlabels.append(label.split(","))
        else:
            nlabels.append(label)
    labels = nlabels

    # Check the list members for valid values
    for label in labels:
        if len(label) != 4:
            raise ValueError(
                tsutils.error_wrapper(
                    f"""
                    The label '{label}' has the wrong number of entries.
                    """
                )
            )

        # replace empty fields with None
        words = [None if i == "" else i for i in label]

        # first word must be a valid operation type or None
        if words[0] is not None:
            # force uppercase before comparison
            words[0] = words[0].upper()
            if words[0] not in testem:
                raise ValueError(
                    tsutils.error_wrapper(
                        f"""
                        Operation type must be one of 'PERLND', 'IMPLND',
                        'RCHRES', or 'BMPRAC', or missing (to get all) instead
                        of {words[0]}.
                        """
                    )
                )

        # second word must be integer 1-999 or None or range to parse
        if words[1] is not None:
            try:
                words[1] = int(words[1])
                luelist = [words[1]]
            except ValueError:
                luelist = tsutils.range_to_numlist(words[1])
            for luenum in luelist:
                if luenum < 1 or luenum > 999:
                    raise ValueError(
                        tsutils.error_wrapper(
                            f"""
                            The land use element must be an integer from 1 to
                            999 inclusive, instead of {luenum}.
                            """
                        )
                    )
        else:
            luelist = [None]

        # third word must be a valid group name or None
        if words[2] is not None:
            words[2] = words[2].upper()
            if (words[0] is not None) and (words[2] not in testem[words[0]]):
                raise ValueError(
                    tsutils.error_wrapper(
                        f"""
                        The {words[0]} operation type only allows the variable
                        groups: {testem[words[0]][:-1]},
                        instead you gave {words[2]}.
                        """
                    )
                )

        # fourth word is currently not checked - assumed to be a variable name
        # if not, it will simply never be found in the file, so ok
        # but no warning for the user - add check?

        # add interval code as fifth word in list
        words.append(intervalcode)

        # add to new list of checked and expanded lists
        for luenum in luelist:
            words[1] = luenum
            lablist.append(list(words))

    labeltest = set()
    with pd.HDFStore(binfilename, "r") as store:
        # "/RESULTS/RCHRES_R005/SEDTRN"
        keys = store.keys()

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
                res = tuple_search(tmpkey, [lbl])
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
                                series = df[vname].resample(code2freqmap[ival]).last()
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

    ndates = sorted(list(ndates))

    if catalog_only:
        for key in collect_dict:
            delta = ndates[1] - ndates[0] if key[4] == 2 else code2freqmap[key[4]]
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
    if interval == "bivl":
        result.index = result.index.to_period(result.index[1] - result.index[0])
    else:
        result.index = result.index.to_period()
    result.index.name = "Datetime"

    return result
