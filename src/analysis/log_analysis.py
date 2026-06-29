"""


This module performs initial analysis on the extracted FME job log dataset.


"""

# Author: x
# Version: 0.1
# Date: 28/05/2026


## Import Modules

import os
import pandas as pd


## Utility Functions

def safe_bool_series(series):
    """Convert mixed boolean-like values to boolean."""

    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def classify_job_outcome(row):
    """Classify job outcome using extracted fields."""

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


## Analysis Runner

def run_analysis(extracted_csv, enriched_output_csv, service_summary_csv, job_outcome_summary_csv):
    """Run initial analysis on extracted FME log records."""

    print("\nStarting analysis...")
    print(f"Input file: {extracted_csv}")

    dataframe = pd.read_csv(extracted_csv)

    ## Type handling

    if "error_flag" in dataframe.columns:
        dataframe["error_flag"] = safe_bool_series(dataframe["error_flag"])
    else:
        dataframe["error_flag"] = False

    numeric_columns = [
        "duration_sec",
        "duration_calculated",
        "warnings",
        "features_read",
        "features_written",
        "features_output",
        "peak_memory_kb",
        "current_memory_kb",
        "log_line_count",
        "error_count",
        "warning_text_count",
        "max_geometry_processed",
        "max_geometry_total",
    ]

    for column in numeric_columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    ## Derived fields

    dataframe["zero_output_flag"] = dataframe["features_written"].fillna(0).eq(0)

    dataframe["has_warning_flag"] = dataframe["warnings"].fillna(0).gt(0)

    dataframe["has_warning_text_flag"] = dataframe["warning_text_count"].fillna(0).gt(0)

    dataframe["has_error_text_flag"] = dataframe["error_count"].fillna(0).gt(0)

    dataframe["job_outcome"] = dataframe.apply(classify_job_outcome, axis=1)

    dataframe["duration_difference_sec"] = (
        dataframe["duration_calculated"] - dataframe["duration_sec"]
    )

    dataframe["parse_note_flag"] = dataframe["parse_notes"].fillna("").ne("")

    ## Service summary

    service_summary = dataframe.groupby("service", dropna=False).agg(
        job_count=("job_id", "count"),
        mean_duration_sec=("duration_sec", "mean"),
        median_duration_sec=("duration_sec", "median"),
        max_duration_sec=("duration_sec", "max"),
        mean_duration_calculated=("duration_calculated", "mean"),
        mean_peak_memory_kb=("peak_memory_kb", "mean"),
        max_peak_memory_kb=("peak_memory_kb", "max"),
        total_features_read=("features_read", "sum"),
        total_features_written=("features_written", "sum"),
        error_flag_count=("error_flag", "sum"),
        warning_job_count=("has_warning_flag", "sum"),
        zero_output_count=("zero_output_flag", "sum"),
        parse_note_count=("parse_note_flag", "sum"),
    ).reset_index()

    ## Outcome summary

    outcome_summary = dataframe.groupby("job_outcome", dropna=False).agg(
        job_count=("job_id", "count"),
        mean_duration_sec=("duration_sec", "mean"),
        max_duration_sec=("duration_sec", "max"),
        mean_peak_memory_kb=("peak_memory_kb", "mean"),
    ).reset_index()

    ## Save outputs

    os.makedirs(os.path.dirname(enriched_output_csv), exist_ok=True)

    dataframe.to_csv(enriched_output_csv, index=False)
    service_summary.to_csv(service_summary_csv, index=False)
    outcome_summary.to_csv(job_outcome_summary_csv, index=False)

    print(f"Enriched dataset saved: {enriched_output_csv}")
    print(f"Service summary saved: {service_summary_csv}")
    print(f"Job outcome summary saved: {job_outcome_summary_csv}")

    return dataframe, service_summary, outcome_summary