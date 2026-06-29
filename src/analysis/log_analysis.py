"""


This module performs initial analysis on the extracted FME job log dataset.


"""

import os
import pandas as pd


def safe_bool_series(series):
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def classify_job_outcome(row):

    status = str(row.get("status", "")).upper()
    warnings = row.get("warnings")
    error_flag = row.get("error_flag")
    features_written = row.get("features_written")

    if status != "SUCCESSFUL":
        return "not_successful"

    if bool(error_flag):
        return "successful_with_errors"

    if pd.notna(warnings) and warnings > 0:
        return "successful_with_warnings"

    if pd.notna(features_written) and features_written == 0:
        return "successful_zero_output"

    return "successful_clean"


def run_analysis(
    extracted_csv,
    enriched_output_csv,
    service_summary_csv,
    job_outcome_summary_csv,
    service_week_summary_csv,
):

    print("\nStarting analysis...")
    df = pd.read_csv(extracted_csv, low_memory=False)

    df["error_flag"] = safe_bool_series(df.get("error_flag", False))
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")

    # Filter valid services only
    df = df[df["service"].notna()]
    df = df[df["service"] != "unknown"]

    # Weekly grouping
    df["job_week"] = df["start_time"].dt.to_period("W").apply(lambda r: r.start_time)

    # Core flags
    df["zero_output_flag"] = df["features_written"].fillna(0).eq(0)
    df["job_outcome"] = df.apply(classify_job_outcome, axis=1)

    # Weekly aggregation
    service_week_summary = df.groupby(
        ["job_week", "service"],
        dropna=False
    ).agg(
        job_count=("job_id", "count"),
        error_count=("error_flag", "sum")
    ).reset_index()

    # Save outputs
    os.makedirs(os.path.dirname(service_week_summary_csv), exist_ok=True)

    df.to_csv(enriched_output_csv, index=False)
    service_week_summary.to_csv(service_week_summary_csv, index=False)

    print(f"Weekly service summary saved: {service_week_summary_csv}")

    return df, service_week_summary