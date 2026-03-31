import pandas as pd
import matplotlib.pyplot as plt


DEFAULT_MONTHS = [
    ("April", 4),
    ("May", 5),
    ("June", 6),
    ("July", 7),
    ("August", 8),
    ("September", 9),
]


def plot_peak_swe_by_month(snotel_data, site_code, months=None):
    """Plot monthly peak SWE by year for a given SNOTEL site."""
    if months is None:
        months = DEFAULT_MONTHS

    swe_df = snotel_data[site_code].copy()
    swe_df["datetime"] = pd.to_datetime(swe_df["datetime"])
    swe_df["year"] = swe_df["datetime"].dt.year
    swe_df["month"] = swe_df["datetime"].dt.month
    swe_df["WTEQ"] = pd.to_numeric(swe_df["WTEQ"], errors="coerce")
    swe_df["WTEQ_mm"] = swe_df["WTEQ"] * 25.4

    fig, axs = plt.subplots(2, 3, figsize=(15, 10), sharex=True, sharey=True)
    axs = axs.flatten()

    peak_series = []
    for _, month_num in months:
        s = swe_df[swe_df["month"] == month_num].groupby("year")["WTEQ_mm"].max()
        peak_series.append(s)

    all_vals = pd.concat(peak_series).dropna()
    ymin = all_vals.min()
    ymax = all_vals.max()

    for i, (month_name, month_num) in enumerate(months):
        ax = axs[i]
        month_peak_by_year = swe_df[swe_df["month"] == month_num].groupby("year")["WTEQ_mm"].max()

        ax.plot(month_peak_by_year.index, month_peak_by_year.values, color="tab:green", linewidth=2)
        ax.set_title(month_name)
        ax.set_ylim(ymin, ymax)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Year")
        ax.set_ylabel("Peak SWE (mm)")

    plt.suptitle("Peak SWE by Year (Apr-Sep) at SNOTEL: " + site_code, fontsize=14)
    plt.tight_layout()
    plt.show()


def plot_monthly_streamflow(cleaned, usgs_gage_id, months=None):
    """Plot monthly mean streamflow by year for Apr-Sep."""
    if months is None:
        months = DEFAULT_MONTHS

    fig, axs = plt.subplots(2, 3, figsize=(15, 10), sharex=True, sharey=True)
    axs = axs.flatten()

    plot_df = cleaned.copy()
    plot_df["year"] = plot_df.index.year
    plot_df["month"] = plot_df.index.month

    monthly_series = []
    for _, month_num in months:
        s = plot_df[plot_df["month"] == month_num].groupby("year")["flow_cms"].mean()
        monthly_series.append(s)

    all_vals = pd.concat(monthly_series).dropna()
    ymin = all_vals.min()
    ymax = all_vals.max()

    for i, (month_name, month_num) in enumerate(months):
        ax = axs[i]
        month_mean_by_year = plot_df[plot_df["month"] == month_num].groupby("year")["flow_cms"].mean()

        ax.plot(month_mean_by_year.index, month_mean_by_year.values, color="tab:blue", linewidth=2)
        ax.set_title(month_name)
        ax.set_ylim(ymin, ymax)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Year")
        ax.set_ylabel("Average Streamflow (cms)")

    plt.suptitle(
        "Average Monthly Streamflow by Year (Apr-Sep) at USGS gage: " + usgs_gage_id,
        fontsize=14,
    )
    plt.tight_layout()
    plt.show()


def plot_streamflow_swe_overlay(cleaned, snotel_data, site_code, usgs_gage_id, months=None):
    """Overlay monthly streamflow means and SWE peaks by year in 6 panels."""
    if months is None:
        months = DEFAULT_MONTHS

    flow_df = cleaned.copy()
    flow_df["year"] = flow_df.index.year
    flow_df["month"] = flow_df.index.month

    swe_df = snotel_data[site_code].copy()
    swe_df["datetime"] = pd.to_datetime(swe_df["datetime"])
    swe_df["year"] = swe_df["datetime"].dt.year
    swe_df["month"] = swe_df["datetime"].dt.month
    swe_df["WTEQ"] = pd.to_numeric(swe_df["WTEQ"], errors="coerce")
    swe_df["WTEQ_mm"] = swe_df["WTEQ"] * 25.4

    flow_monthly = {}
    swe_monthly = {}
    for month_name, month_num in months:
        flow_monthly[month_name] = flow_df[flow_df["month"] == month_num].groupby("year")["flow_cms"].mean()
        swe_monthly[month_name] = swe_df[swe_df["month"] == month_num].groupby("year")["WTEQ_mm"].max()

    all_flow = pd.concat(flow_monthly.values()).dropna()
    all_swe = pd.concat(swe_monthly.values()).dropna()
    all_years = pd.Index(
        sorted(
            set(
                pd.concat([s.index.to_series() for s in flow_monthly.values()]).tolist()
                + pd.concat([s.index.to_series() for s in swe_monthly.values()]).tolist()
            )
        )
    )

    x_min = int(all_years.min())
    x_max = int(all_years.max())
    flow_ymin, flow_ymax = float(all_flow.min()), float(all_flow.max())
    swe_ymin, swe_ymax = float(all_swe.min()), float(all_swe.max())

    fig, axs = plt.subplots(2, 3, figsize=(16, 10), sharex=True)
    axs = axs.flatten()

    for i, (month_name, month_num) in enumerate(months):
        ax = axs[i]
        ax2 = ax.twinx()

        flow_series = flow_monthly[month_name]
        swe_series = swe_monthly[month_name]

        ax.plot(flow_series.index, flow_series.values, color="tab:blue", linewidth=2, label="Avg Streamflow")
        ax2.plot(swe_series.index, swe_series.values, color="tab:green", linewidth=2, label="Peak SWE")

        ax.set_title(month_name)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(flow_ymin, flow_ymax)
        ax2.set_ylim(swe_ymin, swe_ymax)
        ax.set_xlabel("Year")
        ax.set_ylabel("Avg Streamflow (cms)", color="tab:blue")
        ax2.set_ylabel("Peak SWE (mm)", color="tab:green")
        ax.tick_params(axis="y", labelcolor="tab:blue")
        ax2.tick_params(axis="y", labelcolor="tab:green")
        ax.grid(True, alpha=0.3)

    lines = [
        plt.Line2D([0], [0], color="tab:blue", lw=2),
        plt.Line2D([0], [0], color="tab:green", lw=2),
    ]
    labels = ["Avg Streamflow (cms)", "Peak SWE (mm)"]
    fig.legend(lines, labels, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.01))

    plt.suptitle(
        "Overlay of Streamflow and SWE by Year (Apr-Sep) at USGS "
        + usgs_gage_id
        + " / SNOTEL "
        + site_code,
        fontsize=14,
    )
    plt.tight_layout()
    plt.show()
