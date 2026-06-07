"""hspfbintoolbox to read HSPF binary files."""

import datetime
import struct
import sys
from typing import Literal

import pandas as pd

from .. import tsutils
from ..utils import pandas_offset_by_version
from . import utils

code2intervalmap = {5: "yearly", 4: "monthly", 3: "daily", 2: "bivl"}

interval2codemap = {"yearly": 5, "monthly": 4, "daily": 3, "bivl": 2}

code2freqmap = {
    5: pandas_offset_by_version("YE"),
    4: pandas_offset_by_version("ME"),
    3: "D",
    2: None,
}


_LOCAL_DOCSTRINGS = {
    "hbnfilename": """hbnfilename: str
        The HSPF binary output file.  This file must have been created from
        a completed model run."""
}


def _get_data(binfilename, interval="daily", labels=None, catalog_only=True):
    """Underlying function to read from the binary file.  Used by
    'extract', 'catalog'.
    """
    # Normalize interval code
    try:
        intervalcode = interval2codemap[interval.lower()]
    except AttributeError:
        intervalcode = None

    lablist = utils.normalize_labels(labels)
    lablist = [i + [intervalcode] for i in lablist]

    collect_dict = {}
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
                    f"""
                    {binfilename} is not a valid HSPF binary output file
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
                if level == interval2codemap["bivl"]:
                    delta = datetime.timedelta(hours=hour) + datetime.timedelta(
                        minutes=minute
                    )

                ndate = datetime.datetime(year, month, day) + delta

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
                        res = utils.tuple_search(tmpkey, [lbl])
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
                f"""
                The label specifications below matched no records in the binary
                file.

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
                        f"""
                        Warning: The label '{lbl}' matched no records in the
                        binary file.
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
                f"""
                The "interval" argument must be one of "bivl", "daily",
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
