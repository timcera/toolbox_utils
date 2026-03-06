import pandas as pd
from pandas.testing import assert_frame_equal

from toolbox_utils import tsutils


def test_period_timestamp_bivl():
    # RCHRES    14  HYDR     ROVOL
    interval = "bivl"

    period = tsutils.common_kwds(f"tests/data_bivl.hbn,{interval},,14,,ROVOL").astype(
        "float64"
    )
    out = pd.read_csv(
        f"tests/data_period.{interval}.csv",
        index_col=0,
        parse_dates=True,
    )
    out.index = out.index.to_period()
    assert_frame_equal(
        period.reset_index(drop=True), out.reset_index(drop=True), check_exact=False
    )

    out = pd.read_csv(
        f"tests/data_start.{interval}.csv",
        index_col=0,
        parse_dates=True,
    )
    assert_frame_equal(
        period.to_timestamp(how="start").reset_index(drop=True),
        tsutils.asbestfreq(out).reset_index(drop=True),
        check_exact=False,
    )

    out = pd.read_csv(
        f"tests/data_end.{interval}.csv",
        index_col=0,
        parse_dates=True,
    )
    assert_frame_equal(
        period.to_timestamp(how="end").reset_index(drop=True),
        tsutils.asbestfreq(out).reset_index(drop=True),
        check_exact=False,
    )


def test_period_timestamp_daily():
    # RCHRES    14  HYDR     ROVOL
    interval = "daily"
    period = tsutils.common_kwds(f"tests/data_bivl.hbn,{interval},,14,,ROVOL").astype(
        "float64"
    )
    assert_frame_equal(
        period.reset_index(drop=True),
        pd.read_csv(f"tests/data_period.{interval}.csv", index_col=0, parse_dates=True)
        .to_period()
        .reset_index(drop=True),
        check_exact=False,
    )
    assert_frame_equal(
        period.to_timestamp(how="start").reset_index(drop=True),
        tsutils.asbestfreq(
            pd.read_csv(
                f"tests/data_start.{interval}.csv",
                index_col=0,
                parse_dates=True,
            )
        ).reset_index(drop=True),
        check_exact=False,
    )
    assert_frame_equal(
        period.to_timestamp(how="end").reset_index(drop=True),
        tsutils.asbestfreq(
            pd.read_csv(
                f"tests/data_end.{interval}.csv",
                index_col=0,
                parse_dates=True,
            )
        ).reset_index(drop=True),
        check_exact=False,
    )


def test_period_timestamp_monthly():
    # RCHRES    14  HYDR     ROVOL
    interval = "monthly"
    period = tsutils.common_kwds(f"tests/data_bivl.hbn,{interval},,14,,ROVOL").astype(
        "float64"
    )
    assert_frame_equal(
        period.reset_index(drop=True),
        pd.read_csv(f"tests/data_period.{interval}.csv", index_col=0, parse_dates=True)
        .to_period()
        .reset_index(drop=True),
        check_exact=False,
    )
    assert_frame_equal(
        period.to_timestamp(how="start").reset_index(drop=True),
        tsutils.asbestfreq(
            pd.read_csv(
                f"tests/data_start.{interval}.csv",
                index_col=0,
                parse_dates=True,
            )
        ).reset_index(drop=True),
        check_exact=False,
    )
    assert_frame_equal(
        tsutils.asbestfreq(period.to_timestamp(how="end")).reset_index(drop=True),
        tsutils.asbestfreq(
            pd.read_csv(
                f"tests/data_end.{interval}.csv",
                index_col=0,
                parse_dates=True,
            )
        ).reset_index(drop=True),
        check_exact=False,
    )


def test_period_timestamp_yearly():
    interval = "yearly"
    # PERLND   905  PWATER   AGWET
    period = tsutils.common_kwds(
        f"tests/data_yearly.hbn,{interval},,905,,AGWET"
    ).astype("float64")
    assert_frame_equal(
        period.reset_index(drop=True),
        pd.read_csv(f"tests/data_period.{interval}.csv", index_col=0, parse_dates=True)
        .to_period()
        .reset_index(drop=True),
        check_exact=False,
    )
    assert_frame_equal(
        period.to_timestamp(how="start").reset_index(drop=True),
        tsutils.asbestfreq(
            pd.read_csv(
                f"tests/data_start.{interval}.csv",
                index_col=0,
                parse_dates=True,
            )
        ).reset_index(drop=True),
        check_exact=False,
    )
    assert_frame_equal(
        tsutils.asbestfreq(period.to_timestamp(how="end")).reset_index(drop=True),
        tsutils.asbestfreq(
            pd.read_csv(
                f"tests/data_end.{interval}.csv",
                index_col=0,
                parse_dates=True,
            )
        ).reset_index(drop=True),
        check_exact=False,
    )
