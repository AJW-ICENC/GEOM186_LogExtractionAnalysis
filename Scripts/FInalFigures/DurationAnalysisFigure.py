"""

Job Duration Through Development and Deployment

Creates a two-panel performance analysis figure showing job
execution duration for DCAT services.

"""

# Author: Alex Wallage
# Version: 2.0
# Date: 01/08/2026

# Enhanced with AI


## Import Modules

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as pe


## CONFIGURATION

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
    f"{OUTPUT_DIR}/JobDuration_TimeSeries_V2.png"
)

LIVE_DEPLOYMENT_DATE = "2026-05-01"

# April 2026 removed because it reflects live-service setup
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

DEVELOPMENT_COLOUR = "#1F4E79"
DEPLOYED_COLOUR = "#3A7D44"

PHASE_COLOURS = {
    "Development": DEVELOPMENT_COLOUR,
    "Deployed": DEPLOYED_COLOUR,
}

SPRINT_COLOURS = {
    "Sprint 1 Development": "#D6EAF8",
    "Sprint 2 Development": "#D5F5E3",
    "Sprint 3 Development": "#FCF3CF",
}

SCATTER_ALPHA = 0.1
SCATTER_SIZE = 10

LINE_WIDTH = 3

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

df["duration_sec"] = pd.to_numeric(
    df["duration_sec"],
    errors="coerce",
)

df["duration_seconds"] = df["duration_sec"]


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
        "duration_seconds",
        "service",
        "dataset_phase",
    ]
)

df = df[
    df["duration_seconds"] > 0
].copy()

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

df["job_week"] = (
    df["start_time"]
    .dt.to_period("W")
    .apply(lambda period: period.start_time)
)

print(f"Rows retained after cleaning: {len(df):,}")


# WEEKLY SUMMARY

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
        mean_duration_sec=(
            "duration_seconds",
            "mean",
        ),
        median_duration_sec=(
            "duration_seconds",
            "median",
        ),
        job_count=(
            "job_id",
            "count",
        ),
    )
    .reset_index()
)

weekly = weekly.sort_values(
    [
        "service",
        "phase",
        "job_week",
    ]
)



# LOAD SPRINT DATES

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


# FIGURE

fig, axes = plt.subplots(
    nrows=2,
    ncols=1,
    figsize=(14, 9),
    sharex=True,
)

deployment_date = pd.Timestamp(
    LIVE_DEPLOYMENT_DATE
)

sprint_1_end = sprints.iloc[0]["end_date"]
sprint_2_end = sprints.iloc[1]["end_date"]
sprint_3_end = sprints.iloc[2]["end_date"]

performance_periods = [
    {
        "label": "After Sprint 1",
        "start": sprint_1_end,
        "end": sprint_2_end,
    },
    {
        "label": "After Sprint 2",
        "start": sprint_2_end,
        "end": sprint_3_end,
    },
    {
        "label": "After Sprint 3",
        "start": sprint_3_end,
        "end": deployment_date,
    },
]


for ax, service in zip(
    axes,
    SERVICES,
):

    service_raw = df[
        df["service"] == service
    ].copy()

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

    for period in performance_periods:

        period_jobs = service_raw[
            (service_raw["start_time"] > period["start"])
            &
            (service_raw["start_time"] <= period["end"])
        ]

        if len(period_jobs) == 0:
            continue

        period_median = (
            period_jobs["duration_seconds"]
            .median()
        )

        period_midpoint = (
            period["start"]
            +
            (
                period["end"]
                - period["start"]
            ) / 2
        )

        ax.text(
            mdates.date2num(period_midpoint),
            0.905,
            (
                f"{period['label']}\n"
                f"median {period_median:.1f} sec"
            ),
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=8,
            fontweight="bold",
            color="#333333",
            path_effects=TEXT_OUTLINE,
            zorder=6,
        )

    # Scatter points

    for phase in [
        "Development",
        "Deployed",
    ]:

        subset = service_raw[
            service_raw["phase"] == phase
        ]

        ax.scatter(
            subset["start_time"],
            subset["duration_seconds"],
            color=PHASE_COLOURS[phase],
            alpha=SCATTER_ALPHA,
            s=SCATTER_SIZE,
            zorder=1,
            label=None,
        )

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
            subset["median_duration_sec"],
            color=PHASE_COLOURS[phase],
            linewidth=LINE_WIDTH,
            marker="o",
            markersize=4,
            label=phase,
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
        mdates.date2num(deployment_date) + 20,
        0.97,
        "Live deployment",
        transform=ax.get_xaxis_transform(),
        ha="right",
        va="top",
        fontsize=8,
        color="black",
        path_effects=TEXT_OUTLINE,
        zorder=6,
    )

    deployed_jobs = service_raw[
        service_raw["phase"] == "Deployed"
    ]

    if len(deployed_jobs) > 0:

        deployed_median = (
            deployed_jobs["duration_seconds"]
            .median()
        )

        ax.text(
            mdates.date2num(deployment_date),
            0.78,
            (
                "Deployed period\n"
                f"median {deployed_median:.1f} sec"
            ),
            transform=ax.get_xaxis_transform(),
            ha="right",
            va="top",
            fontsize=8,
            fontweight="bold",
            color="black",
            path_effects=TEXT_OUTLINE,
            zorder=6,
        )

    # Axis styling

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
        "Job Duration (Seconds)",
        fontsize=11,
    )

    ax.grid(
        True,
        linestyle="--",
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
        loc="upper right",
    )


# SHARED X AXIS

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
print("Performance duration analysis complete.")