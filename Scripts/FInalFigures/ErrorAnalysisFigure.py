"""

Failure and Error Frequency Through Development and Deployment

"""

#Author: Alex Wallage
# Version: 1.0
# Date: 01/08/2026

# Enhanced with AI


## Import Modules
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as pe


# CONFIGURATION

INPUT_CSV = (
    r"output/analysis/extracted_with_analysis_fields.csv"
)

DATES_CSV = (
    r"static/dates.csv"
)

OUTPUT_DIR = (
    r"plots/performance_analysis"
)

OUTPUT_FIGURE = (
    f"{OUTPUT_DIR}/FailureError_TimeSeries_V1.png"
)

LIVE_DEPLOYMENT_DATE = "2026-05-01"


EXCLUDE_START = "2026-04-01"
EXCLUDE_END = "2026-04-30"

SERVICES = [
    "data_registration",
    "overlap_assessment",
]

SERVICE_NAMES = {
    "data_registration": "Data Registration",
    "overlap_assessment": "Overlap Assessment",
}

SUBPLOT_LABELS = {
    "data_registration": "A",
    "overlap_assessment": "B",
}

PHASE_LABELS = {
    "beta": "Development",
    "live": "Deployed",
}


# STYLE

plt.rcParams["font.family"] = "Times New Roman"

FAILED_COLOUR = "#8A4F4F"
ERROR_COLOUR = "#4F6D7A"

SPRINT_COLOURS = {
    "Sprint 1 Development": "#D6EAF8",
    "Sprint 2 Development": "#D5F5E3",
    "Sprint 3 Development": "#FCF3CF",
}

LINE_WIDTH = 2.4
MARKER_SIZE = 5

TEXT_OUTLINE = [
    pe.withStroke(
        linewidth=3,
        foreground="white",
    )
]


## LOAD DATA

df = pd.read_csv(
    INPUT_CSV,
    low_memory=False,
)

df["start_time"] = pd.to_datetime(
    df["start_time"],
    errors="coerce",
)

df["error_count"] = pd.to_numeric(
    df["error_count"],
    errors="coerce",
).fillna(0)


if "translation_status" not in df.columns:
    df["translation_status"] = df.get(
        "status",
        None,
    )

df["translation_status"] = (
    df["translation_status"]
    .astype(str)
    .str.upper()
)


## CLEAN DATA

df = df[
    df["service"].isin(SERVICES)
].copy()

df = df[
    df["dataset_phase"].isin(["beta", "live"])
].copy()

df = df.dropna(
    subset=[
        "start_time",
        "service",
        "dataset_phase",
    ]
)


df = df[
    ~(
        (df["start_time"] >= pd.Timestamp(EXCLUDE_START))
        &
        (df["start_time"] <= pd.Timestamp(EXCLUDE_END))
    )
].copy()

df["phase"] = df["dataset_phase"].replace(
    PHASE_LABELS
)

df["failed_job_flag"] = (
    df["translation_status"] == "FAILED"
)

df["error_job_flag"] = (
    df["error_count"] > 0
)

df["job_week"] = (
    df["start_time"]
    .dt.to_period("W")
    .apply(lambda period: period.start_time)
)

print(f"Rows retained after cleaning: {len(df):,}")



## WEEKLY SUMMARY

weekly = (
    df.groupby(
        [
            "service",
            "phase",
            "job_week",
        ],
        dropna=False,
    )
    .agg(
        job_count=(
            "job_id",
            "count",
        ),
        failed_jobs=(
            "failed_job_flag",
            "sum",
        ),
        jobs_with_errors=(
            "error_job_flag",
            "sum",
        ),
        total_errors=(
            "error_count",
            "sum",
        ),
    )
    .reset_index()
)

weekly["failure_rate"] = (
    weekly["failed_jobs"]
    / weekly["job_count"]
)

weekly["error_job_rate"] = (
    weekly["jobs_with_errors"]
    / weekly["job_count"]
)

weekly = weekly.sort_values(
    [
        "service",
        "phase",
        "job_week",
    ]
)


## LOAD SPRINT DATES

dates = pd.read_csv(
    DATES_CSV
)

dates["start_date"] = pd.to_datetime(
    dates["start_date"],
    dayfirst=True,
    errors="coerce",
)

dates["end_date"] = pd.to_datetime(
    dates["end_date"],
    dayfirst=True,
    errors="coerce",
)

sprints = dates[
    dates["Title"].isin(
        [
            "Sprint 1 Development",
            "Sprint 2 Development",
            "Sprint 3 Development",
        ]
    )
].copy()

sprints = sprints.dropna(
    subset=[
        "start_date",
        "end_date",
    ]
)

sprints = sprints.sort_values(
    "end_date"
).reset_index(
    drop=True
)


## FIGURE

fig, axes = plt.subplots(
    nrows=2,
    ncols=1,
    figsize=(14, 9),
    sharex=True,
)

deployment_date = pd.Timestamp(
    LIVE_DEPLOYMENT_DATE
)

for ax, service in zip(
    axes,
    SERVICES,
):

    service_weekly = weekly[
        weekly["service"] == service
    ].copy()


    for _, sprint in sprints.iterrows():

        ax.axvspan(
            sprint["start_date"],
            sprint["end_date"],
            color=SPRINT_COLOURS.get(
                sprint["Title"],
                "lightgrey",
            ),
            alpha=0.35,
            zorder=0,
        )

        sprint_midpoint = (
            sprint["start_date"]
            +
            (
                sprint["end_date"]
                - sprint["start_date"]
            ) / 2
        )

        sprint_label = (
            sprint["Title"]
            .replace(
                " Development",
                "",
            )
        )

        ax.text(
            mdates.date2num(sprint_midpoint),
            0.97,
            sprint_label,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=8,
            fontweight="bold",
            color="dimgray",
            path_effects=TEXT_OUTLINE,
            zorder=5,
        )

    # Development/deployed weekly series

    for phase in [
        "Development",
        "Deployed",
    ]:

        subset = service_weekly[
            service_weekly["phase"] == phase
        ].copy()

        if subset.empty:
            continue

        ax.plot(
            subset["job_week"],
            subset["failed_jobs"],
            color=FAILED_COLOUR,
            linewidth=LINE_WIDTH,
            marker="o",
            markersize=MARKER_SIZE,
            label=f"{phase}: failed jobs",
            zorder=4,
        )

        ax.plot(
            subset["job_week"],
            subset["jobs_with_errors"],
            color=ERROR_COLOUR,
            linewidth=LINE_WIDTH,
            marker="s",
            markersize=MARKER_SIZE,
            linestyle="--",
            label=f"{phase}: jobs with errors",
            zorder=4,
        )

    # Live deployment marker

    ax.axvline(
        deployment_date,
        color="black",
        linestyle="--",
        linewidth=1.6,
        zorder=5,
    )

    ax.text(
        mdates.date2num(deployment_date),
        0.97,
        "Live deployment",
        transform=ax.get_xaxis_transform(),
        rotation=90,
        ha="right",
        va="top",
        fontsize=8,
        color="black",
        path_effects=TEXT_OUTLINE,
        zorder=6,
    )

    ax.set_title(
        SERVICE_NAMES[service],
        fontsize=13,
    )

    ax.text(
        -0.045,
        1.02,
        SUBPLOT_LABELS[service],
        transform=ax.transAxes,
        fontsize=16,
        fontweight="bold",
        ha="left",
        va="bottom",
    )

    ax.set_ylabel(
        "Weekly Job Count",
        fontsize=11,
    )

    ax.grid(
        True,
        axis="y",
        linestyle="--",
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
        loc="upper right",
        fontsize=8,
    )



axes[-1].set_xlabel(
    "Date",
    fontsize=11,
)

axes[-1].xaxis.set_major_locator(
    mdates.MonthLocator()
)

axes[-1].xaxis.set_major_formatter(
    mdates.DateFormatter("%b %Y")
)

plt.xticks(
    rotation=45,
)


# LAYOUT

plt.tight_layout(
    rect=[
        0,
        0,
        1,
        0.95,
    ]
)


# SAVE

Path(
    OUTPUT_DIR
).mkdir(
    parents=True,
    exist_ok=True,
)

plt.savefig(
    OUTPUT_FIGURE,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print(f"Figure saved: {OUTPUT_FIGURE}")
print("Failure and error time-series analysis complete.")