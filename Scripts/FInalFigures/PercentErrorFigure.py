"""
Failure and Error Rate Reduction Analysis

"""

# Author: Alex Wallage
# Version: 1.0
# Date: 01/08/2026

# Enhanced with AI


# Import Modules
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


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
    f"{OUTPUT_DIR}/FailureError_RateReduction_ByPeriod_V1.png"
)

SUMMARY_OUTPUT_CSV = (
    f"{OUTPUT_DIR}/FailureError_RateReduction_Summary_V1.csv"
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

METRIC_COLOURS = {
    "Failure rate": "#8A4F4F",
    "Error-job rate": "#4F6D7A",
}

METRIC_MARKERS = {
    "Failure rate": "o",
    "Error-job rate": "s",
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

df["failed_job_flag"] = (
    df["translation_status"] == "FAILED"
)

df["error_job_flag"] = (
    df["error_count"] > 0
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


## PERIOD DEFINITIONS

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


# SUMMARY STATISTICS

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

summary["failure_rate"] = (
    summary["failed_jobs"]
    / summary["job_count"]
)

summary["error_job_rate"] = (
    summary["jobs_with_errors"]
    / summary["job_count"]
)


# PERCENTAGE RATE REDUCTION FROM BASELINE

summary["failure_rate_pct_reduction"] = None
summary["error_job_rate_pct_reduction"] = None

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

    baseline_failure_rate = (
        baseline_row["failure_rate"]
        .iloc[0]
    )

    baseline_error_job_rate = (
        baseline_row["error_job_rate"]
        .iloc[0]
    )

    if baseline_failure_rate > 0:

        summary.loc[
            service_mask,
            "failure_rate_pct_reduction",
        ] = (
            (
                baseline_failure_rate
                -
                summary.loc[
                    service_mask,
                    "failure_rate",
                ]
            )
            /
            baseline_failure_rate
        ) * 100

    if baseline_error_job_rate > 0:

        summary.loc[
            service_mask,
            "error_job_rate_pct_reduction",
        ] = (
            (
                baseline_error_job_rate
                -
                summary.loc[
                    service_mask,
                    "error_job_rate",
                ]
            )
            /
            baseline_error_job_rate
        ) * 100


percentage_columns = [
    "failure_rate_pct_reduction",
    "error_job_rate_pct_reduction",
]

for column in percentage_columns:
    summary[column] = pd.to_numeric(
        summary[column],
        errors="coerce",
    )


# SAVE SUMMARY TABLE

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


## PLOT

fig, axes = plt.subplots(
    nrows=2,
    ncols=1,
    figsize=(11.5, 7.5),
    sharex=True,
)

x_positions = list(
    range(len(PERIOD_ORDER))
)

x_labels = [
    PERIOD_LABELS[period]
    for period in PERIOD_ORDER
]

metrics = [
    {
        "name": "Failure rate",
        "column": "failure_rate_pct_reduction",
    },
    {
        "name": "Error-job rate",
        "column": "error_job_rate_pct_reduction",
    },
]

for ax, service in zip(
    axes,
    SERVICES,
):

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

    for metric in metrics:

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
                    period_row[metric["column"]].iloc[0]
                )

        ax.plot(
            x_positions,
            y_values,
            color=METRIC_COLOURS[metric["name"]],
            marker=METRIC_MARKERS[metric["name"]],
            linewidth=LINE_WIDTH,
            markersize=MARKER_SIZE,
            label=metric["name"],
        )

        for x_position, y_value in zip(
            x_positions,
            y_values,
        ):

            if pd.isna(y_value):
                continue

            vertical_offset = 2.0

            if y_value < 0:
                vertical_offset = -3.0

            ax.text(
                x_position,
                y_value + vertical_offset,
                f"{y_value:+.1f}%",
                ha="center",
                va="bottom" if y_value >= 0 else "top",
                fontsize=8,
                fontweight="bold",
                color=METRIC_COLOURS[metric["name"]],
            )

    ax.axhline(
        0,
        color="#333333",
        linewidth=1.0,
    )

    ax.set_title(
        SERVICE_NAMES[service],
        fontsize=13,
    )

    ax.set_ylabel(
        "Reduction relative to\nAfter Sprint 1 baseline (%)",
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

axes[-1].set_xticks(
    x_positions
)

axes[-1].set_xticklabels(
    x_labels,
    fontsize=10,
)

axes[-1].set_xlabel(
    "Comparison Period",
    fontsize=11,
)


# LAYOUT

plt.tight_layout(
    rect=[
        0,
        0,
        1,
        0.98,
    ]
)


## SAVE

plt.savefig(
    OUTPUT_FIGURE,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print(f"Figure saved: {OUTPUT_FIGURE}")
print("Failure and error rate reduction analysis complete.")