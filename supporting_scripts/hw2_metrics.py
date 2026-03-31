import pandas as pd


def _get_swe_datetime_and_value_columns(swe_df):
    """Return datetime and SWE value column names from a SNOTEL DataFrame."""
    datetime_col = "datetime" if "datetime" in swe_df.columns else "Date"

    if "WTEQ" in swe_df.columns:
        value_col = "WTEQ"
    elif "Snow Water Equivalent (m) Start of Day Values" in swe_df.columns:
        value_col = "Snow Water Equivalent (m) Start of Day Values"
    else:
        raise KeyError(
            "Could not find SWE value column. Expected 'WTEQ' or "
            "'Snow Water Equivalent (m) Start of Day Values'."
        )

    return datetime_col, value_col


def summarize_april1_swe_streamflow(
    snotel_data,
    cleaned,
    site_code="546_ID_SNTL",
    target_date="2025-04-01",
):
    """Summarize April 1 SWE and streamflow by year and for a target date.

    Parameters
    ----------
    snotel_data : dict[str, pandas.DataFrame]
        Dictionary keyed by SNOTEL site code.
    cleaned : pandas.DataFrame
        Streamflow DataFrame with DateTimeIndex and 'flow_cms' column.
    site_code : str, default '546_ID_SNTL'
        SNOTEL station code.
    target_date : str, default '2025-04-01'
        Date to report SWE and streamflow values for.

    Returns
    -------
    summary_by_year : pandas.DataFrame
        Index = year, columns = ['swe_april1', 'streamflow_april1_cms'].
    target_values : dict
        Dictionary with SWE and streamflow for target_date.
    """
    if site_code not in snotel_data:
        raise KeyError(f"Site code {site_code} not found in snotel_data.")

    swe_df = snotel_data[site_code].copy()
    datetime_col, swe_value_col = _get_swe_datetime_and_value_columns(swe_df)

    swe_df[datetime_col] = pd.to_datetime(swe_df[datetime_col], errors="coerce")
    swe_df[swe_value_col] = pd.to_numeric(swe_df[swe_value_col], errors="coerce")

    swe_april1 = swe_df[
        (swe_df[datetime_col].dt.month == 4) & (swe_df[datetime_col].dt.day == 1)
    ].copy()
    swe_april1["year"] = swe_april1[datetime_col].dt.year

    swe_by_year = swe_april1.groupby("year")[swe_value_col].mean()

    flow_df = cleaned.copy()
    flow_df.index = pd.to_datetime(flow_df.index, errors="coerce")
    flow_df["flow_cms"] = pd.to_numeric(flow_df["flow_cms"], errors="coerce")

    flow_april1 = flow_df[(flow_df.index.month == 4) & (flow_df.index.day == 1)].copy()
    flow_april1["year"] = flow_april1.index.year

    flow_by_year = flow_april1.groupby("year")["flow_cms"].mean()

    summary_by_year = pd.concat(
        [swe_by_year.rename("swe_april1"), flow_by_year.rename("streamflow_april1_cms")],
        axis=1,
    ).sort_index()

    target_ts = pd.Timestamp(target_date)
    target_year = target_ts.year

    target_values = {
        "site_code": site_code,
        "target_date": target_ts.strftime("%Y-%m-%d"),
        "swe_april1": summary_by_year.loc[target_year, "swe_april1"]
        if target_year in summary_by_year.index
        else pd.NA,
        "streamflow_april1_cms": summary_by_year.loc[target_year, "streamflow_april1_cms"]
        if target_year in summary_by_year.index
        else pd.NA,
        "swe_april1_average_all_years": summary_by_year["swe_april1"].mean(),
        "streamflow_april1_average_all_years_cms": summary_by_year[
            "streamflow_april1_cms"
        ].mean(),
    }

    print(f"April 1 summary for site {site_code}")
    print(summary_by_year)
    print("\nRequested date values:")
    print(target_values)

    return summary_by_year, target_values
