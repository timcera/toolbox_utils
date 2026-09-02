"""A collection of functions used by toolbox_utils, wdmtoolbox, ...etc."""

# Standard library imports

# Third party imports
import pandas as pd
import pint_pandas  # not used directly, but required to use pint in pandas

# Local folder imports
from .. import tsutils, utils

code2intervalmap = {5: "yearly", 4: "monthly", 3: "daily", 2: "bivl"}

interval2codemap = {"yearly": 5, "monthly": 4, "daily": 3, "bivl": 2}

code2freqmap = {
    5: pd.offsets.YearEnd(),
    4: pd.offsets.MonthEnd(),
    3: "D",
    2: None,
}

code2min_count = {
    (utils.pandas_offset_by_version("h"), 3): 20,
    ("D", 4): 24,
    ("D", 5): 300,
    ("60min", 3): 20,
    ("60min", 4): 576,
    ("60min", 5): 7200,
}

# This is here so that linters don't remove the pint_pandas import which is
# needed to use pint in pandas
_ = pint_pandas.version("pint")

test_labels = {
    "BMPRAC": [
        "",
        "INFLOW",
        "RECEIV",
        "REMOVE",
        "ROFLOW",
    ],
    "IMPLND": [
        "",
        "ATEMP",
        "IQUAL",
        "IWATER",
        "IWTGAS",
        "SNOW",
        "SOLIDS",
    ],
    "PERLND": [
        "",
        "ATEMP",
        "MSTLAY",
        "NITR",
        "PEST",
        "PHOS",
        "PQUAL",
        "PSTEMP",
        "PWATER",
        "PWTGAS",
        "SEDMNT",
        "SNOW",
        "TRACER",
    ],
    "RCHRES": [
        "",
        "CONS",
        "GQUAL",
        "HTRCH",
        "HYDR",
        "INFLOW",
        "NUTRX",
        "OFLOW",
        "OXRX",
        "PHCARB",
        "PLANK",
        "ROFLOW",
        "SEDTRN",
    ],
    "": [""],
}


def normalize_labels(labels: str | list[str] | None, interval) -> tuple[list[str], int]:
    """
    Process labels for the hbn and hdf5 functions.

    Parameters
    ----------
    labels
        The labels to be processed.
    interval
        The aggregation interval.

    Returns
    -------
    process_labels
        A list of processed labels.
    interval_code
        The HSPF interval code.
    """
    # Normalize interval code
    try:
        intervalcode = interval2codemap[interval.lower()]
    except AttributeError:
        intervalcode = None

    if labels is None:
        labels = [",,,"]

    lablist = []

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
            if words[0] not in test_labels:
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
            if (words[0] is not None) and (words[2] not in test_labels[words[0]]):
                raise ValueError(
                    tsutils.error_wrapper(
                        f"""
                        The {words[0]} operation type only allows the variable
                        groups: {test_labels[words[0]][:-1]},
                        instead you gave {words[2]}.
                        """
                    )
                )

        # fourth word is currently not checked - assumed to be a variable name
        # if not, it will simply never be found in the file, so ok
        # but no warning for the user - add check?

        # add to new list of checked and expanded lists
        for luenum in luelist:
            words[1] = luenum
            lablist.append(list(words))

    # add interval code as fifth word in list
    lablist = [i + [intervalcode] for i in lablist]

    return lablist, intervalcode


def tuple_match(findme, hay):
    """Part of partial ordered matching.
    See http://stackoverflow.com/a/4559604
    """
    return len(findme) == len(hay) and all(
        i is None or j is None or i == j for i, j in zip(findme, hay)
    )


def tuple_combine(findme, hay):
    """Part of partial ordered matching.
    See http://stackoverflow.com/a/4559604
    """
    return tuple(i is None and j or i for i, j in zip(findme, hay))


def tuple_search(findme, haystack):
    """Partial ordered matching with 'None' as wildcard
    See http://stackoverflow.com/a/4559604
    """
    return [
        (index, tuple_combine(findme, hay))
        for index, hay in enumerate(haystack)
        if tuple_match(findme, hay)
    ]
