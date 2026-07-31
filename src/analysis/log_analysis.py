"""
This module performs initial analysis on the extracted FME job log dataset.

Job outcome analysis uses the authoritative FME translation summary fields:

- translation_status
- error_count
- warning_count
- features_output

Diagnostic ERROR/WARN text is retained in the extracted dataset but is not used
as the primary source for analysis.
"""

import os
import pandas as pd


def classify_job_outcome(row):
    """Classify each FME job using extracted translation summary metrics."""

    status = str(row.get("translation_status", "")).upper()

    errors = row.get("error_count", 0)
    warnings = row.get("warning_count", 0)
    features_output = row.get("features_output", 0)

    if pd.isna(errors):
        errors = 0

    if pd.isna(warnings):
        warnings = 0

    if pd.isna(features_output):
        features_output = 0

    if status == "FAILED":
        return "failed"

    if status != "SUCCESSFUL":
        return "unknown_or_not_successful"

    if errors > 0:
        return "successful_with_errors"

    if warnings > 0:
        return "successful_with_warnings"

    if features_output == 0:
        return "successful_zero_output"

    return "successful_clean"


def run_analysis(
    extracted_csv,
    enriched_output_csv,
    service_summary_csv,
    job_outcome_summary_csv,
    service_week_summary_csv,
):
    """Run analysis and write enriched and summary CSV outputs."""

    print("\nStarting analysis...")

    df = pd.read_csv(extracted_csv, low_memory=False)

    ## Ensure required columns exist

    required_columns = [
        "translation_status",
        "error_count",
        "warning_count",
        "features_output",
        "features_written",
        "start_time",
        "service",
        "job_id",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = None

    ## Type conversion

    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")

    for column in [
        "error_count",
        "warning_count",
        "features_output",
        "features_written",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["error_count"] = df["error_count"].fillna(0).astype(int)
    df["warning_count"] = df["warning_count"].fillna(0).astype(int)

    ## Clean status

    df["translation_status"] = (
        df["translation_status"]
        .astype(str)
        .str.upper()
        .replace({"NAN": None, "NONE": None})
    )

    ## Filter valid services only

    df = df[df["service"].notna()]
    df = df[df["service"] != "unknown"]

    ## Weekly grouping

    df["job_week"] = df["start_time"].dt.to_period("W").apply(
        lambda period: period.start_time if pd.notna(period) else pd.NaT
    )

    ## Core analysis flags

    df["failed_job_flag"] = df["translation_status"].eq("FAILED")
    df["successful_job_flag"] = df["translation_status"].eq("SUCCESSFUL")
    df["error_flag"] = df["error_count"].gt(0)
    df["warning_flag"] = df["warning_count"].gt(0)
    df["zero_output_flag"] = df["features_output"].fillna(0).eq(0)

    df["job_outcome"] = df.apply(classify_job_outcome, axis=1)

    ## Service-level summary

    service_summary = (
        df.groupby("service", dropna=False)
        .agg(
            job_count=("job_id", "count"),
            successful_jobs=("successful_job_flag", "sum"),
            failed_jobs=("failed_job_flag", "sum"),
            jobs_with_errors=("error_flag", "sum"),
            jobs_with_warnings=("warning_flag", "sum"),
            zero_output_jobs=("zero_output_flag", "sum"),
            total_errors=("error_count", "sum"),
            total_warnings=("warning_count", "sum"),
            mean_errors_per_job=("error_count", "mean"),
            mean_warnings_per_job=("warning_count", "mean"),
        )
        .reset_index()
    )

    service_summary["failure_rate"] = (
        service_summary["failed_jobs"] / service_summary["job_count"]
    )

    service_summary["error_job_rate"] = (
        service_summary["jobs_with_errors"] / service_summary["job_count"]
    )

    service_summary["warning_job_rate"] = (
        service_summary["jobs_with_warnings"] / service_summary["job_count"]
    )

    ## Job outcome summary

    job_outcome_summary = (
        df.groupby(["service", "job_outcome"], dropna=False)
        .agg(
            job_count=("job_id", "count"),
            total_errors=("error_count", "sum"),
            total_warnings=("warning_count", "sum"),
        )
        .reset_index()
    )

    ## Weekly aggregation

    service_week_summary = (
        df.groupby(
            ["job_week", "service"],
            dropna=False,
        )
        .agg(
            job_count=("job_id", "count"),
            successful_jobs=("successful_job_flag", "sum"),
            failed_jobs=("failed_job_flag", "sum"),
            jobs_with_errors=("error_flag", "sum"),
            jobs_with_warnings=("warning_flag", "sum"),
            zero_output_jobs=("zero_output_flag", "sum"),
            total_errors=("error_count", "sum"),
            total_warnings=("warning_count", "sum"),
            mean_errors_per_job=("error_count", "mean"),
            mean_warnings_per_job=("warning_count", "mean"),
        )
        .reset_index()
    )

    service_week_summary["failure_rate"] = (
        service_week_summary["failed_jobs"] / service_week_summary["job_count"]
    )

    service_week_summary["error_job_rate"] = (
        service_week_summary["jobs_with_errors"] / service_week_summary["job_count"]
    )

    service_week_summary["warning_job_rate"] = (
        service_week_summary["jobs_with_warnings"] / service_week_summary["job_count"]
    )

    ## Save outputs

    os.makedirs(os.path.dirname(enriched_output_csv), exist_ok=True)
    os.makedirs(os.path.dirname(service_summary_csv), exist_ok=True)
    os.makedirs(os.path.dirname(job_outcome_summary_csv), exist_ok=True)
    os.makedirs(os.path.dirname(service_week_summary_csv), exist_ok=True)

    df.to_csv(enriched_output_csv, index=False)
    service_summary.to_csv(service_summary_csv, index=False)
    job_outcome_summary.to_csv(job_outcome_summary_csv, index=False)
    service_week_summary.to_csv(service_week_summary_csv, index=False)

    print(f"Enriched dataset saved: {enriched_output_csv}")
    print(f"Service summary saved: {service_summary_csv}")
    print(f"Job outcome summary saved: {job_outcome_summary_csv}")
    print(f"Weekly service summary saved: {service_week_summary_csv}")

    return df, service_week_summary