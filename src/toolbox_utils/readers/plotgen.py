"""For reading HSPF plotgen files."""

import datetime

import pandas as pd

_END_OF_HEADER = 25


def plotgen_extract(filename):
    """Reads HSPF PLTGEN files and creates a DataFrame."""
    foundcols = False
    cols = []
    lst = []
    with open(filename, encoding="ascii") as fpointer:
        for i, line in enumerate(fpointer):
            if i < _END_OF_HEADER:
                if "LINTYP" in line:
                    foundcols = True
                elif line[5:].startswith("Time series"):
                    foundcols = False
                elif foundcols:
                    if header := line[4:30].strip():
                        cols.append(header)
                    else:
                        foundcols = False

            if i > _END_OF_HEADER:
                year, month, day, hour, minute = line[4:22].split()

                if int(hour) == 24:
                    day = [
                        datetime.datetime(int(year), int(month), int(day), tzinfo=None)
                        + datetime.timedelta(days=1)
                    ]
                else:
                    day = [
                        datetime.datetime(
                            int(year),
                            int(month),
                            int(day),
                            int(hour),
                            int(minute),
                            tzinfo=None,
                        )
                    ]
                data = [float(x) for x in line[23:].split()]
                lst.append(day + data)

    pgdf = pd.DataFrame(lst)
    pgdf.columns = ["Datetime"] + cols
    pgdf = pgdf.set_index(["Datetime"])
    pgdf.index = pd.DatetimeIndex(pgdf.index)

    return pgdf
