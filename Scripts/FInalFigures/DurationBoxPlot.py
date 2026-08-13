"""

Job Duration Box Plots by Development and Deployment Period

"""

# Author: Alex Wallage
# Version: 2.1
# Date: 01/08/2026

# Enhanced with AI



## Import Modules

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

OUTPUT_FIGURE = str(
    Path(OUTPUT_DIR) / "JobDuration_Boxplots_ByPeriod_V2.png"
)

OUTPUT_STATS_CSV = str(
    Path(OUTPUT_DIR) / "JobDuration_Boxplots_ByPeriod_Stats_V2.csv"
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

PERIOD_ORDER = [
    "After Sprint 1",
    "After Sprint 2",
    "After Sprint 3",
    "Deployed",
]



## STYLE

plt.rcParams["font.family"] = "Times New Roman"

PERIOD_COLOURS = {
    "After Sprint 1": "#D6EAF8",
    "After Sprint 2": "#D5F5E3",
    "After Sprint 3": "#FCF3CF",
    "Deployed": "#D8EAD3",
}

BOX_EDGE_COLOUR = "#333333"
MEAN_MARKER_COLOUR = "#111111"
OUTLIER_COLOUR = "#999999"


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

# Remove April deployment-transition noise

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

def calculate_period_stats(values):
    """Calculate descriptive and boxplot statistics for one period."""

    values = values.dropna()

    if values.empty:

        return {
            "job_count": 0,
            "mean_sec": None,
            "median_sec": None,
            "std_sec": None,
            "coefficient_of_variation": None,
            "min_sec": None,
            "q1_sec": None,
            "q3_sec": None,
            "iqr_sec": None,
            "max_sec": None,
            "range_sec": None,
            "p05_sec": None,
            "p10_sec": None,
            "p90_sec": None,
            "p95_sec": None,
            "lower_outlier_threshold_sec": None,
            "upper_outlier_threshold_sec": None,
            "lower_outlier_count": 0,
            "upper_outlier_count": 0,
            "total_outlier_count": 0,
            "outlier_percentage": None,
            "non_outlier_min_sec": None,
            "non_outlier_max_sec": None,
        }

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    lower_threshold = q1 - 1.5 * iqr
    upper_threshold = q3 + 1.5 * iqr

    lower_outliers = values[
        values < lower_threshold
    ]

    upper_outliers = values[
        values > upper_threshold
    ]

    non_outliers = values[
        (
            values >= lower_threshold
        )
        &
        (
            values <= upper_threshold
        )
    ]

    mean_value = values.mean()
    std_value = values.std()

    if mean_value != 0:
        coefficient_of_variation = (
            std_value / mean_value
        )
    else:
        coefficient_of_variation = None

    return {
        "job_count": len(values),
        "mean_sec": mean_value,
        "median_sec": values.median(),
        "std_sec": std_value,
        "coefficient_of_variation": coefficient_of_variation,
        "min_sec": values.min(),
        "q1_sec": q1,
        "q3_sec": q3,
        "iqr_sec": iqr,
        "max_sec": values.max(),
        "range_sec": values.max() - values.min(),
        "p05_sec": values.quantile(0.05),
        "p10_sec": values.quantile(0.10),
        "p90_sec": values.quantile(0.90),
        "p95_sec": values.quantile(0.95),
        "lower_outlier_threshold_sec": lower_threshold,
        "upper_outlier_threshold_sec": upper_threshold,
        "lower_outlier_count": len(lower_outliers),
        "upper_outlier_count": len(upper_outliers),
        "total_outlier_count": len(lower_outliers) + len(upper_outliers),
        "outlier_percentage": (
            (
                len(lower_outliers)
                +
                len(upper_outliers)
            )
            /
            len(values)
        ) * 100,
        "non_outlier_min_sec": non_outliers.min() if not non_outliers.empty else None,
        "non_outlier_max_sec": non_outliers.max() if not non_outliers.empty else None,
    }


stats_records = []

for service in SERVICES:

    service_df = df[
        df["service"] == service
    ].copy()

    for period in PERIOD_ORDER:

        period_values = (
            service_df[
                service_df["comparison_period"] == period
            ]["duration_seconds"]
            .dropna()
        )

        stats = calculate_period_stats(
            period_values
        )

        record = {
            "service": service,
            "service_name": SERVICE_NAMES[service],
            "comparison_period": period,
        }

        record.update(
            stats
        )

        stats_records.append(
            record
        )


stats_df = pd.DataFrame(
    stats_records
)


# ADD BASELINE COMPARISONS

stats_df["mean_change_from_after_sprint_1_sec"] = None
stats_df["mean_pct_change_from_after_sprint_1"] = None
stats_df["mean_pct_reduction_from_after_sprint_1"] = None

stats_df["median_change_from_after_sprint_1_sec"] = None
stats_df["median_pct_change_from_after_sprint_1"] = None
stats_df["median_pct_reduction_from_after_sprint_1"] = None

stats_df["iqr_change_from_after_sprint_1_sec"] = None
stats_df["iqr_pct_change_from_after_sprint_1"] = None
stats_df["iqr_pct_reduction_from_after_sprint_1"] = None

stats_df["cv_change_from_after_sprint_1"] = None
stats_df["cv_pct_change_from_after_sprint_1"] = None
stats_df["cv_pct_reduction_from_after_sprint_1"] = None

for service in SERVICES:

    service_mask = (
        stats_df["service"] == service
    )

    baseline = stats_df[
        service_mask
        &
        (
            stats_df["comparison_period"]
            == "After Sprint 1"
        )
    ]

    if baseline.empty:
        continue

    baseline_mean = baseline["mean_sec"].iloc[0]
    baseline_median = baseline["median_sec"].iloc[0]
    baseline_iqr = baseline["iqr_sec"].iloc[0]
    baseline_cv = baseline["coefficient_of_variation"].iloc[0]

    stats_df.loc[
        service_mask,
        "mean_change_from_after_sprint_1_sec",
    ] = (
        stats_df.loc[
            service_mask,
            "mean_sec",
        ]
        -
        baseline_mean
    )

    stats_df.loc[
        service_mask,
        "median_change_from_after_sprint_1_sec",
    ] = (
        stats_df.loc[
            service_mask,
            "median_sec",
        ]
        -
        baseline_median
    )

    stats_df.loc[
        service_mask,
        "iqr_change_from_after_sprint_1_sec",
    ] = (
        stats_df.loc[
            service_mask,
            "iqr_sec",
        ]
        -
        baseline_iqr
    )

    stats_df.loc[
        service_mask,
        "cv_change_from_after_sprint_1",
    ] = (
        stats_df.loc[
            service_mask,
            "coefficient_of_variation",
        ]
        -
        baseline_cv
    )

    if baseline_mean != 0:

        stats_df.loc[
            service_mask,
            "mean_pct_change_from_after_sprint_1",
        ] = (
            (
                stats_df.loc[
                    service_mask,
                    "mean_sec",
                ]
                -
                baseline_mean
            )
            /
            baseline_mean
        ) * 100

        stats_df.loc[
            service_mask,
            "mean_pct_reduction_from_after_sprint_1",
        ] = (
            (
                baseline_mean
                -
                stats_df.loc[
                    service_mask,
                    "mean_sec",
                ]
            )
            /
            baseline_mean
        ) * 100

    if baseline_median != 0:

        stats_df.loc[
            service_mask,
            "median_pct_change_from_after_sprint_1",
        ] = (
            (
                stats_df.loc[
                    service_mask,
                    "median_sec",
                ]
                -
                baseline_median
            )
            /
            baseline_median
        ) * 100

        stats_df.loc[
            service_mask,
            "median_pct_reduction_from_after_sprint_1",
        ] = (
            (
                baseline_median
                -
                stats_df.loc[
                    service_mask,
                    "median_sec",
                ]
            )
            /
            baseline_median
        ) * 100

    if baseline_iqr != 0:

        stats_df.loc[
            service_mask,
            "iqr_pct_change_from_after_sprint_1",
        ] = (
            (
                stats_df.loc[
                    service_mask,
                    "iqr_sec",
                ]
                -
                baseline_iqr
            )
            /
            baseline_iqr
        ) * 100

        stats_df.loc[
            service_mask,
            "iqr_pct_reduction_from_after_sprint_1",
        ] = (
            (
                baseline_iqr
                -
                stats_df.loc[
                    service_mask,
                    "iqr_sec",
                ]
            )
            /
            baseline_iqr
        ) * 100

    if baseline_cv != 0:

        stats_df.loc[
            service_mask,
            "cv_pct_change_from_after_sprint_1",
        ] = (
            (
                stats_df.loc[
                    service_mask,
                    "coefficient_of_variation",
                ]
                -
                baseline_cv
            )
            /
            baseline_cv
        ) * 100

        stats_df.loc[
            service_mask,
            "cv_pct_reduction_from_after_sprint_1",
        ] = (
            (
                baseline_cv
                -
                stats_df.loc[
                    service_mask,
                    "coefficient_of_variation",
                ]
            )
            /
            baseline_cv
        ) * 100



## ROUND OUTPUT FOR READABILITY

numeric_columns = stats_df.select_dtypes(
    include=[
        "number",
    ]
).columns

stats_df[numeric_columns] = stats_df[numeric_columns].round(
    3
)


# SAVE STATS CSV

Path(
    OUTPUT_DIR
).mkdir(
    parents=True,
    exist_ok=True,
)

stats_df.to_csv(
    OUTPUT_STATS_CSV,
    index=False,
)

print(f"Statistics CSV saved: {OUTPUT_STATS_CSV}")



## FIGURE

fig, axes = plt.subplots(
    nrows=2,
    ncols=1,
    figsize=(13.5, 7.5),
    sharex=False,
)


plot_order = list(
    reversed(
        PERIOD_ORDER
    )
)

positions = list(
    range(
        1,
        len(plot_order) + 1,
    )
)

for ax, service in zip(
    axes,
    SERVICES,
):

    service_df = df[
        df["service"] == service
    ].copy()

    data_for_boxplot = []
    y_tick_labels = []

    for period in plot_order:

        period_values = (
            service_df[
                service_df["comparison_period"] == period
            ]["duration_seconds"]
            .dropna()
        )

        data_for_boxplot.append(
            period_values.tolist()
        )

        if period_values.empty:

            y_tick_labels.append(
                f"{period}\nmean n/a"
            )

        else:

            mean_value = period_values.mean()

            y_tick_labels.append(
                f"{period}\nmean {mean_value:.1f} sec"
            )

    boxplot = ax.boxplot(
        data_for_boxplot,
        vert=False,
        positions=positions,
        patch_artist=True,
        showmeans=True,
        showfliers=False,
        meanprops=dict(
            marker="D",
            markerfacecolor=MEAN_MARKER_COLOUR,
            markeredgecolor=MEAN_MARKER_COLOUR,
            markersize=4,
        ),
        medianprops=dict(
            color="#111111",
            linewidth=1.4,
        ),
        boxprops=dict(
            color=BOX_EDGE_COLOUR,
            linewidth=1.1,
        ),
        whiskerprops=dict(
            color=BOX_EDGE_COLOUR,
            linewidth=1.0,
        ),
        capprops=dict(
            color=BOX_EDGE_COLOUR,
            linewidth=1.0,
        ),
    )

    for patch, period in zip(
        boxplot["boxes"],
        plot_order,
    ):

        patch.set_facecolor(
            PERIOD_COLOURS[period]
        )

        patch.set_alpha(
            0.75
        )

    ax.set_yticks(
        positions
    )

    ax.set_yticklabels(
        y_tick_labels,
        fontsize=9,
    )

    service_max = service_df["duration_seconds"].quantile(
        0.95
    )

    ax.set_xlim(
        0,
        service_max * 1.15,
    )

    ax.set_title(
        SERVICE_NAMES[service],
        fontsize=13,
    )

    ax.text(
        -0.085,
        1.04,
        SUBPLOT_LABELS[service],
        transform=ax.transAxes,
        fontsize=16,
        fontweight="bold",
        ha="left",
        va="bottom",
    )

    ax.set_xlabel(
        "Job Duration (Seconds)",
        fontsize=11,
    )

    ax.grid(
        True,
        axis="x",
        linestyle="--",
        alpha=0.25,
    )


# LAYOUT

plt.tight_layout(
    rect=[
        0.04,
        0,
        1,
        0.98,
    ]
)


# SAVE FIGURE

plt.savefig(
    OUTPUT_FIGURE,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print(f"Figure saved: {OUTPUT_FIGURE}")
print("Job duration box plot analysis complete.")