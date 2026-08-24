"""

Performance Reduction Over Development and Deployment

"""

# Author: Alex Wallage
# Version: 2.0
# Date: 01/08/2026

# Enhanced with AI



# Import Modules

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


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

MEMORY_OUTPUT_FIGURE = (
    f"{OUTPUT_DIR}/PeakMemory_PercentageReduction_ByPeriod_V2.png"
)

DURATION_OUTPUT_FIGURE = (
    f"{OUTPUT_DIR}/JobDuration_PercentageReduction_ByPeriod_V2.png"
)

SUMMARY_OUTPUT_CSV = (
    f"{OUTPUT_DIR}/Performance_PercentageReduction_Summary_V2.csv"
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

PHASE_LABELS = {
    "beta": "Development",
    "live": "Deployed",
}

PERIOD_ORDER = [
    "After Sprint 1",
    "After Sprint 2",
    "After Sprint 3",
    "Deployed",
]

PERIOD_LABELS = {
    "After Sprint 1": "After\nSprint 1",
    "After Sprint 2": "After\nSprint 2",
    "After Sprint 3": "After\nSprint 3",
    "Deployed": "Deployed",
}

BASELINE_PERIOD = "After Sprint 1"


## STYLE

plt.rcParams["font.family"] = "Times New Roman"

SERVICE_COLOURS = {
    "data_registration": "#4F6D7A",
    "overlap_assessment": "#7A6F4F",
}

SERVICE_MARKERS = {
    "data_registration": "o",
    "overlap_assessment": "s",
}

LINE_WIDTH = 2.4
MARKER_SIZE = 7


## LOAD DATA

df = pd.read_csv(
    INPUT_CSV,
    low_memory=False,
)

df["start_time"] = pd.to_datetime(
    df["start_time"],
    errors="coerce",
)

df["peak_memory_kb"] = pd.to_numeric(
    df["peak_memory_kb"],
    errors="coerce",
)

df["duration_sec"] = pd.to_numeric(
    df["duration_sec"],
    errors="coerce",
)


df["peak_memory_mb"] = (
    df["peak_memory_kb"] / 1024
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
        "peak_memory_mb",
        "duration_seconds",
        "service",
        "dataset_phase",
    ]
)

df = df[
    df["peak_memory_mb"] > 0
].copy()

df = df[
    df["duration_seconds"] > 0
].copy()

df = df[
    ~(
        (
            df["start_time"] >= pd.Timestamp(EXCLUDE_START)
        )
        &
        (
            df["start_time"] <= pd.Timestamp(EXCLUDE_END)
        )
    )
].copy()

df["phase"] = df["dataset_phase"].replace(
    PHASE_LABELS
)

print(f"Rows retained after cleaning: {len(df):,}")


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


# PERIOD DEFINITIONS

deployment_date = pd.Timestamp(
    LIVE_DEPLOYMENT_DATE
)

sprint_1_end = sprints.iloc[0]["end_date"]
sprint_2_end = sprints.iloc[1]["end_date"]
sprint_3_end = sprints.iloc[2]["end_date"]

periods = [
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
    {
        "label": "Deployed",
        "start": deployment_date,
        "end": df["start_time"].max(),
    },
]


# ASSIGN PERIODS

def assign_period(row):
    """Assign each job to a post-sprint or deployed comparison period."""

    job_time = row["start_time"]

    for period in periods:
        if (
            job_time > period["start"]
            and job_time <= period["end"]
        ):
            return period["label"]

    return None


df["comparison_period"] = df.apply(
    assign_period,
    axis=1,
)

df = df.dropna(
    subset=[
        "comparison_period",
    ]
).copy()

df["comparison_period"] = pd.Categorical(
    df["comparison_period"],
    categories=PERIOD_ORDER,
    ordered=True,
)


## SUMMARY STATISTICS

summary = (
    df.groupby(
        [
            "service",
            "comparison_period",
        ],
        observed=False,
    )
    .agg(
        job_count=(
            "job_id",
            "count",
        ),
        mean_peak_memory_mb=(
            "peak_memory_mb",
            "mean",
        ),
        median_peak_memory_mb=(
            "peak_memory_mb",
            "median",
        ),
        std_peak_memory_mb=(
            "peak_memory_mb",
            "std",
        ),
        mean_duration_sec=(
            "duration_seconds",
            "mean",
        ),
        median_duration_sec=(
            "duration_seconds",
            "median",
        ),
        std_duration_sec=(
            "duration_seconds",
            "std",
        ),
    )
    .reset_index()
)

summary["memory_cv"] = (
    summary["std_peak_memory_mb"]
    / summary["mean_peak_memory_mb"]
)

summary["duration_cv"] = (
    summary["std_duration_sec"]
    / summary["mean_duration_sec"]
)


# PERCENTAGE REDUCTION FROM BASELINE

summary["memory_mean_pct_reduction"] = None
summary["memory_median_pct_reduction"] = None
summary["duration_mean_pct_reduction"] = None
summary["duration_median_pct_reduction"] = None

for service in SERVICES:

    service_mask = summary["service"] == service

    baseline_row = summary[
        service_mask
        &
        (
            summary["comparison_period"].astype(str)
            == BASELINE_PERIOD
        )
    ]

    if baseline_row.empty:
        continue

    baseline_mean_memory = (
        baseline_row["mean_peak_memory_mb"]
        .iloc[0]
    )

    baseline_median_memory = (
        baseline_row["median_peak_memory_mb"]
        .iloc[0]
    )

    baseline_mean_duration = (
        baseline_row["mean_duration_sec"]
        .iloc[0]
    )

    baseline_median_duration = (
        baseline_row["median_duration_sec"]
        .iloc[0]
    )


    summary.loc[
        service_mask,
        "memory_mean_pct_reduction",
    ] = (
        (
            baseline_mean_memory
            -
            summary.loc[
                service_mask,
                "mean_peak_memory_mb",
            ]
        )
        /
        baseline_mean_memory
    ) * 100

    summary.loc[
        service_mask,
        "memory_median_pct_reduction",
    ] = (
        (
            baseline_median_memory
            -
            summary.loc[
                service_mask,
                "median_peak_memory_mb",
            ]
        )
        /
        baseline_median_memory
    ) * 100

    summary.loc[
        service_mask,
        "duration_mean_pct_reduction",
    ] = (
        (
            baseline_mean_duration
            -
            summary.loc[
                service_mask,
                "mean_duration_sec",
            ]
        )
        /
        baseline_mean_duration
    ) * 100

    summary.loc[
        service_mask,
        "duration_median_pct_reduction",
    ] = (
        (
            baseline_median_duration
            -
            summary.loc[
                service_mask,
                "median_duration_sec",
            ]
        )
        /
        baseline_median_duration
    ) * 100


percentage_columns = [
    "memory_mean_pct_reduction",
    "memory_median_pct_reduction",
    "duration_mean_pct_reduction",
    "duration_median_pct_reduction",
]

for column in percentage_columns:
    summary[column] = pd.to_numeric(
        summary[column],
        errors="coerce",
    )


## SAVE SUMMARY TABLE

Path(
    OUTPUT_DIR
).mkdir(
    parents=True,
    exist_ok=True,
)

summary.to_csv(
    SUMMARY_OUTPUT_CSV,
    index=False,
)

print(f"Summary table saved: {SUMMARY_OUTPUT_CSV}")


# PLOT HELPER

def plot_reduction_line_figure(
    metric_column,
    output_figure,
    y_label,
    value_suffix="%",
):
    """Create a sequential line chart showing percentage reduction."""

    fig, ax = plt.subplots(
        figsize=(11.5, 6.5)
    )

    x_positions = list(
        range(len(PERIOD_ORDER))
    )

    x_labels = [
        PERIOD_LABELS[period]
        for period in PERIOD_ORDER
    ]

    for service in SERVICES:

        service_summary = summary[
            summary["service"] == service
        ].copy()

        service_summary["comparison_period"] = pd.Categorical(
            service_summary["comparison_period"],
            categories=PERIOD_ORDER,
            ordered=True,
        )

        service_summary = service_summary.sort_values(
            "comparison_period"
        )

        y_values = []

        for period in PERIOD_ORDER:

            period_row = service_summary[
                service_summary["comparison_period"].astype(str)
                == period
            ]

            if period_row.empty:
                y_values.append(None)
            else:
                y_values.append(
                    period_row[metric_column].iloc[0]
                )

        ax.plot(
            x_positions,
            y_values,
            color=SERVICE_COLOURS[service],
            marker=SERVICE_MARKERS[service],
            linewidth=LINE_WIDTH,
            markersize=MARKER_SIZE,
            label=SERVICE_NAMES[service],
        )

        for x_position, y_value in zip(
            x_positions,
            y_values,
        ):

            if pd.isna(y_value):
                continue

            vertical_offset = 1.2

            if y_value < 0:
                vertical_offset = -2.2

            ax.text(
                x_position,
                y_value + vertical_offset,
                f"{y_value:+.1f}{value_suffix}",
                ha="center",
                va="bottom" if y_value >= 0 else "top",
                fontsize=9,
                fontweight="bold",
                color=SERVICE_COLOURS[service],
            )

    ax.axhline(
        0,
        color="#333333",
        linewidth=1.0,
    )

    ax.set_xticks(
        x_positions
    )

    ax.set_xticklabels(
        x_labels,
        fontsize=10,
    )

    ax.set_ylabel(
        y_label,
        fontsize=11,
    )

    ax.set_xlabel(
        "Comparison Period",
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
        loc="best",
    )

    y_min = (
        summary[metric_column]
        .min()
    )

    y_max = (
        summary[metric_column]
        .max()
    )

    y_range = y_max - y_min

    if y_range == 0:
        y_range = 5

    ax.set_ylim(
        y_min - y_range * 0.25,
        y_max + y_range * 0.25,
    )

    plt.tight_layout()

    plt.savefig(
        output_figure,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Figure saved: {output_figure}")


## FIGURE 1: PEAK MEMORY PERCENTAGE REDUCTION

plot_reduction_line_figure(
    metric_column="memory_mean_pct_reduction",
    output_figure=MEMORY_OUTPUT_FIGURE,
    y_label=(
        "Percentage Reduction in Mean Peak Process Memory Usage (%)"
    ),
)


## FIGURE 2: JOB DURATION PERCENTAGE REDUCTION

plot_reduction_line_figure(
    metric_column="duration_median_pct_reduction",
    output_figure=DURATION_OUTPUT_FIGURE,
    y_label=(
        "Percentage Reduction in Median Job Duration (%)"
    ),
)

print("Performance percentage reduction analysis complete.")