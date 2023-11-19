"""hspfbintoolbox to read HSPF binary files."""

import datetime
import struct
import sys

try:
    from typing import Literal
except ImportError:
    from typing import Literal

import pandas as pd

from .. import tsutils

code2intervalmap = {5: "yearly", 4: "monthly", 3: "daily", 2: "bivl"}

interval2codemap = {"yearly": 5, "monthly": 4, "daily": 3, "bivl": 2}

code2freqmap = {5: "A", 4: "M", 3: "D", 2: None}


_LOCAL_DOCSTRINGS = {
    "hbnfilename": """hbnfilename: str
        The HSPF binary output file.  This file must have been created from
        a completed model run."""
}


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


def _get_data(binfilename, interval="daily", labels=None, catalog_only=True):
    """Underlying function to read from the binary file.  Used by
    'extract', 'catalog'.
    """
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
                    f"""The label '{label}' has the wrong number of entries.
                    """
                )
            )

        # replace empty fields with None
        # operation,lue_number,group,variable
        words = [None if (i in ("", "None")) else i for i in label]

        # first word must be a valid operation type or None
        if words[0] is not None:
            # force uppercase before comparison
            words[0] = words[0].upper()
            if words[0] not in testem:
                raise ValueError(
                    tsutils.error_wrapper(
                        f"""Operation type must be one of 'PERLND', 'IMPLND',
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
                            f"""The land use element must be an integer from
                            1 to 999 inclusive, instead of {luenum}.
                            """
                        )
                    )
        else:
            luelist = [None]

        # third word must be a valid group name or None
        if words[2] is not None:
            words[2] = words[2].upper()
            if words[2] not in testem[words[0]]:
                raise ValueError(
                    tsutils.error_wrapper(
                        f"""The {words[0]} operation type only allows the
                        variable groups: {testem[words[0]][:-1]}, instead you
                        gave {words[2]}.
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

    # Now read through the binary file and collect the data matching the labels
    with open(binfilename, "rb") as binfp:
        labeltest = set()
        vnames = {}
        ndates = set()
        # read first byte - must be hex FD (decimal 253) for valid file.
        magicbyte = binfp.read(1)
        if magicbyte != b"\xfd":
            # not a valid HSPF binary file
            raise ValueError(
                tsutils.error_wrapper(
                    f"""{binfilename} is not a valid HSPF binary output file
                    (.hbn),  The first byte must be FD hexadecimal, but it was
                    {magicbyte}.
                    """
                )
            )

        # loop through each record
        while True:
            # reinitialize counter for record length - used to compute skip at
            # end
            recpos = 0

            # read first four bytes to get record length bitfield
            try:
                reclen1, reclen2, reclen3, reclen = struct.unpack("4B", binfp.read(4))
                recpos += 4
            except struct.error:
                # End of file.
                break

            # get record leader - next 24 bytes
            rectype, optype, lue, group = struct.unpack("I8sI8s", binfp.read(24))
            recpos += 24

            # clean up
            rectype = int(rectype)
            lue = int(lue)
            optype = optype.strip()
            group = group.strip()

            if rectype == 0:
                # header record - collect variable names for this
                # operation and group

                # parse reclen bitfield to get actual remaining length
                # the " - 24 " subtracts the 24 bytes already read
                reclen1 = int(reclen1 / 4)
                reclen2 = reclen2 * 64 + reclen1
                reclen3 = reclen3 * 16384 + reclen2
                reclen = reclen * 4194304 + reclen3 - 24

                # loop through rest of record
                slen = 0
                while slen < reclen:
                    # read single 4B word for length of next variable name
                    length = struct.unpack("I", binfp.read(4))[0]

                    # read the variable name
                    variable_name = struct.unpack(f"{length}s", binfp.read(length))[0]

                    # add variable name to the set for this operation
                    # why a set instead of a list? There should never be
                    # a duplicate anyway
                    vnames.setdefault((lue, group), []).append(variable_name)

                    # update how far along the record we are
                    slen += length + 4
                    recpos += length + 4

            elif rectype == 1:
                # Data record

                # record should contain a value for each variable name for this
                # operation and group
                numvals = len(vnames[(lue, group)])

                (_, level, year, month, day, hour, minute) = struct.unpack(
                    "7I", binfp.read(28)
                )
                recpos += 28

                vals = struct.unpack(f"{numvals}f", binfp.read(4 * numvals))
                recpos += 4 * numvals

                delta = datetime.timedelta(hours=0)
                if hour == 24:
                    hour = 0

                ndate = datetime.datetime(year, month, day, hour, minute) + delta

                #  Go through labels to see if these values need to be
                #  collected
                for i, vname in enumerate(vnames[(lue, group)]):
                    tmpkey = (
                        optype.decode("ascii"),
                        lue,
                        group.decode("ascii"),
                        vname.decode("ascii"),
                        level,
                    )

                    for lbl in lablist:
                        res = tuple_search(tmpkey, [lbl])
                        if not res:
                            continue
                        labeltest.add(tuple(lbl))
                        nres = res[0][1]
                        ndates.add(ndate)
                        if catalog_only is False:
                            if intervalcode == level:
                                collect_dict.setdefault(nres, []).append(vals[i])
                        else:
                            collect_dict[nres] = level
            else:
                # there was a problem with unexpected record length
                # back up almost all the way and try again
                binfp.seek(-31, 1)

            # calculate and skip to the end of the variable-length back pointer
            reccnt = recpos * 4 + 1
            if reccnt >= 256**2:
                skbytes = 3
            elif reccnt >= 256:
                skbytes = 2
            else:
                skbytes = 1
            binfp.read(skbytes)

    if not collect_dict:
        raise ValueError(
            tsutils.error_wrapper(
                f"""The label specifications below matched no records in the
                binary file.

                {lablist}
                """
            )
        )

    ndates = sorted(list(ndates))

    if catalog_only is False:
        for lbl in lablist:
            if tuple(lbl) not in labeltest:
                sys.stderr.write(
                    tsutils.error_wrapper(
                        f"""Warning: The label '{lbl}' matched no records in
                        the binary file.
                        """
                    )
                )
    else:
        for key in collect_dict:
            delta = ndates[1] - ndates[0] if key[4] == 2 else code2freqmap[key[4]]
            collect_dict[key] = (
                pd.Period(ndates[0], freq=delta),
                pd.Period(ndates[-1], freq=delta),
            )

    return ndates, collect_dict


def hbn_extract(
    hbnfilename: str,
    interval: Literal["yearly", "monthly", "daily", "bivl"],
    *labels,
    sort_columns: bool = False,
):
    """Returns a DataFrame from a HSPF binary output file."""
    interval = interval.lower()

    if interval not in ("bivl", "daily", "monthly", "yearly"):
        raise ValueError(
            tsutils.error_wrapper(
                f"""The "interval" argument must be one of "bivl", "daily",
                "monthly", or "yearly".  You supplied "{interval}".
                """
            )
        )

    index, data = _get_data(hbnfilename, interval, labels, catalog_only=False)
    skeys = list(data.keys())
    if sort_columns:
        skeys.sort(key=lambda tup: tup[1:])

    result = pd.DataFrame(
        pd.concat(
            [pd.Series(data[i], index=index) for i in skeys], sort=False, axis=1
        ).reindex(pd.Index(index))
    )
    columns = [f"{i[0]}_{i[1]}_{i[3]}".replace(" ", "-") for i in skeys]
    result.columns = columns
    if interval == "bivl":
        result.index = result.index.to_period(result.index[1] - result.index[0])
    else:
        result.index = result.index.to_period()
    result.index.name = "Datetime"

    return result
