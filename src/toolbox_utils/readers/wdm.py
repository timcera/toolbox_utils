"""
Pure python WDM file reader.
"""

from datetime import datetime

import numpy as np
import pandas as pd

# look up attributes NAME, data type (Integer; Real; String) and data length by attribute number
attrinfo = {
    1: ("TSTYPE", "S", 4),
    2: ("STAID", "S", 16),
    11: ("DAREA", "R", 1),
    17: ("TCODE", "I", 1),
    27: ("TSBYR", "I", 1),
    28: ("TSBMO", "I", 1),
    29: ("TSBDY", "I", 1),
    30: ("TSBHR", "I", 1),
    32: ("TFILL", "R", 1),
    33: ("TSSTEP", "I", 1),
    34: ("TGROUP", "I", 1),
    45: ("STNAM", "S", 48),
    83: ("COMPFG", "I", 1),
    84: ("TSFORM", "I", 1),
    85: ("VBTIME", "I", 1),
    444: ("A444", "S", 12),
    443: ("A443", "S", 12),
    22: ("DCODE", "I", 1),
    10: ("DESCRP", "S", 80),
    7: ("ELEV", "R", 1),
    8: ("LATDEG", "R", 1),
    9: ("LNGDEG", "R", 1),
    288: ("SCENARIO", "S", 8),
    289: ("CONSTITUENT", "S", 8),
    290: ("LOCATION", "S", 8),
}

freq = {
    7: "100YS",
    6: "YS",
    5: "MS",
    4: "D",
    3: "H",
    2: "min",
    1: "S",
}  # pandas date_range() frequency by TCODE, TGROUP


def wdm_extract(wdmfile, *idsn):
    """Extract DSN from WDM file."""
    idsn = [int(i) for i in idsn]

    iarray = np.fromfile(wdmfile, dtype=np.int32)
    farray = np.fromfile(wdmfile, dtype=np.float32)

    if iarray[0] != -998:
        raise ValueError("Not a WDM file, magic number is not -990. Stopping!")

    nrecords = iarray[28]  # first record is File Definition Record
    ntimeseries = iarray[31]

    dsnlist = [
        index
        for index in range(512, nrecords * 512, 512)
        if (
            not (
                iarray[index] == iarray[index + 1] == iarray[index + 2] == 0
                and iarray[index + 3]
            )
            and iarray[index + 5] == 1
        )
    ]
    if len(dsnlist) != ntimeseries:
        print("PROGRAM ERROR, wrong number of DSN records found")

    retdf = pd.DataFrame()

    for index in dsnlist:
        # get layout information for TimeSeries Dataset frame
        dsn = iarray[index + 4]

        if dsn not in idsn:
            continue
        psa = iarray[index + 9]

        if psa > 0:
            sacnt = iarray[index + psa - 1]
        pdat = iarray[index + 10]
        pdatv = iarray[index + 11]

        # get attributes
        dattr = {
            "TSBDY": 1,
            "TSBHR": 1,
            "TSBMO": 1,
            "TSBYR": 1900,
            "TFILL": -999.0,
        }  # preset defaults

        for i in range(psa + 1, psa + 1 + 2 * sacnt, 2):
            iarray_id = iarray[index + i]
            ptr = iarray[index + i + 1] - 1 + index

            if iarray_id not in attrinfo:
                print(
                    "PROGRAM ERROR: ATTRIBUTE INDEX not found",
                    iarray_id,
                    "Attribute pointer",
                    iarray[index + i + 1],
                )

                continue

            name, atype, length = attrinfo[iarray_id]

            if atype == "I":
                dattr[name] = iarray[ptr]
            elif atype == "R":
                dattr[name] = farray[ptr]
            else:
                dattr[name] = "".join(
                    [itostr(iarray[k]) for k in range(ptr, ptr + length // 4)]
                ).strip()

        # Get timeseries timebase data
        records = []

        for i in range(pdat + 1, pdatv - 1):
            if a_record := iarray[index + i]:
                records.append(splitposition(a_record))

        if not records:
            continue  # WDM preallocated, but nothing saved here yet

        srec, soffset = records[0]
        start = splitdate(iarray[srec * 512 + soffset])

        # calculate number of data points in each group, tindex is final index
        # for storage
        tgroup = dattr["TGROUP"]
        tstep = dattr["TSSTEP"]
        tcode = dattr["TCODE"]
        cindex = pd.date_range(start=start, periods=len(records) + 1, freq=freq[tgroup])
        tindex = pd.date_range(
            start=start, end=cindex[-1], freq=str(tstep) + freq[tcode]
        )
        counts = np.diff(np.searchsorted(tindex, cindex))

        # Get timeseries data
        floats = np.zeros(sum(counts), dtype=np.float32)
        findex = 0

        for (rec, offset), count in zip(records, counts):
            findex = getfloats(iarray, farray, floats, findex, rec, offset, count)

        series = pd.DataFrame(floats[:findex], index=tindex[:findex])
        series = series[series[0] != dattr["TFILL"]]
        series.columns = [f"{wdmfile}_{dsn}"]
        retdf = retdf.join(series, how="outer")

    return retdf


def todatetime(year=1900, month=1, day=1, hour=0):
    """takes yr,mo,dy,hr information then returns its datetime64"""

    return (
        datetime(year, month, day, 23) + pd.Timedelta(1, "h")
        if hour == 24
        else datetime(year, month, day, hour)
    )


def splitdate(datwrd):
    """splits WDM compressed datetime int32 DATWRD into year, month, day, hour
    -> datetime64"""
    year = int((datwrd / 16384) % 131072)
    month = int((datwrd / 1024) % 16)
    day = int((datwrd / 32) % 32)
    hour = int(datwrd % 32)

    return todatetime(year, month, day, hour)


def splitposition(recoffset):
    """splits int32 into (record, offset), converting to Python zero based
    indexing"""

    return ((recoffset >> 9) - 1, (recoffset & 511) - 1)


def itostr(i):
    """Convert integer to string."""

    return chr(i & 255) + chr(i >> 8 & 255) + chr(i >> 16 & 255) + chr(i >> 24 & 255)


def getfloats(iarray, farray, floats, findex, rec, offset, count):
    index = rec * 512 + offset + 1
    stop = (rec + 1) * 512
    cntr = 0

    while cntr < count and findex < len(floats):
        if index >= stop:
            rec = (
                iarray[rec * 512 + 3] - 1
            )  # 3 is forward data pointer, -1 is python indexing
            index = rec * 512 + 4  # 4 is index of start of new data
            stop = (rec + 1) * 512

        control_word = iarray[index]  # control word, don't need most of it here
        nval = control_word >> 16

        index += 1

        if control_word >> 5 & 0x3:  # comp from control word, x
            for _ in range(nval):
                if findex >= len(floats):
                    return findex
                floats[findex] = farray[index]
                findex += 1
            index += 1
        else:
            for k in range(nval):
                if findex >= len(floats):
                    return findex
                floats[findex] = farray[index + k]
                findex += 1
            index += nval
        cntr += nval

    return findex
