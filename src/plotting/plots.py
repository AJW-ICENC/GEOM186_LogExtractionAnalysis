"""
This module creates figures from analysed FME log data.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


def save_plot(output_path):
    """Save the current matplotlib figure."""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def load_project_dates():
    """Load project milestone dates from static/dates.csv if available."""

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dates_path = os.path.join(base_dir, "static", "dates.csv")

    if not os.path.exists(dates_path):
        print(f"Project dates file not found: {dates_path}")
        return pd.DataFrame(columns=["date", "Title"])

    df = pd.read_csv(dates_path)

    if "start_date" not in df.columns:
        print("Project dates file does not contain a start_date column.")
        return pd.DataFrame(columns=["date", "Title"])

    df["date"] = pd.to_datetime(df["start_date"], dayfirst=True, errors="coerce")

    return df.dropna(subset=["date"])


def add_project_milestones(dates_df):
    """Add project milestone lines to a plot."""

    if dates_df is None or dates_df.empty:
        return

    ymax = plt.ylim()[1] * 0.95

    for _, row in dates_df.iterrows():

        title = row.get("Title", "")

        plt.axvline(row["date"], linestyle="--")
        plt.text(
            row["date"],
            ymax,
            title,
            rotation=90,
            verticalalignment="top",
        )


def plot_jobs_per_week(service_week_summary, dates_df, output_path):
    """Plot number of FME jobs per week by service."""

    plt.figure(figsize=(12, 7))

    for service, group in service_week_summary.groupby("service"):
        group = group.sort_values("job_week")

        plt.plot(
            group["job_week"],
            group["job_count"],
            marker="o",
            label=service,
        )

    add_project_milestones(dates_df)

    plt.title("FME Jobs per Week by Service")
    plt.xlabel("Week")
    plt.ylabel("Job Count")
    plt.legend()
    plt.xticks(rotation=45)

    save_plot(output_path)


def plot_errors_per_week(service_week_summary, dates_df, output_path):
    """Plot total FME-reported errors per week by service."""

    plt.figure(figsize=(12, 7))

    for service, group in service_week_summary.groupby("service"):
        group = group.sort_values("job_week")

        plt.plot(
            group["job_week"],
            group["total_errors"],
            marker="o",
            label=service,
        )

    add_project_milestones(dates_df)

    plt.title("FME Errors per Week by Service")
    plt.xlabel("Week")
    plt.ylabel("Total FME-Reported Errors")
    plt.legend()
    plt.xticks(rotation=45)

    save_plot(output_path)


def plot_warnings_per_week(service_week_summary, dates_df, output_path):
    """Plot total FME-reported warnings per week by service."""

    plt.figure(figsize=(12, 7))

    for service, group in service_week_summary.groupby("service"):
        group = group.sort_values("job_week")

        plt.plot(
            group["job_week"],
            group["total_warnings"],
            marker="o",
            label=service,
        )

    add_project_milestones(dates_df)

    plt.title("FME Warnings per Week by Service")
    plt.xlabel("Week")
    plt.ylabel("Total FME-Reported Warnings")
    plt.legend()
    plt.xticks(rotation=45)

    save_plot(output_path)


def plot_failed_jobs_per_week(service_week_summary, dates_df, output_path):
    """Plot failed FME jobs per week by service."""

    plt.figure(figsize=(12, 7))

    for service, group in service_week_summary.groupby("service"):
        group = group.sort_values("job_week")

        plt.plot(
            group["job_week"],
            group["failed_jobs"],
            marker="o",
            label=service,
        )

    add_project_milestones(dates_df)

    plt.title("Failed FME Jobs per Week by Service")
    plt.xlabel("Week")
    plt.ylabel("Failed Jobs")
    plt.legend()
    plt.xticks(rotation=45)

    save_plot(output_path)


def plot_failure_rate_per_week(service_week_summary, dates_df, output_path):
    """Plot weekly failure rate by service."""

    plt.figure(figsize=(12, 7))

    for service, group in service_week_summary.groupby("service"):
        group = group.sort_values("job_week")

        plt.plot(
            group["job_week"],
            group["failure_rate"],
            marker="o",
            label=service,
        )

    add_project_milestones(dates_df)

    plt.title("FME Job Failure Rate per Week by Service")
    plt.xlabel("Week")
    plt.ylabel("Failure Rate")
    plt.legend()
    plt.xticks(rotation=45)

    save_plot(output_path)


def run_plots(
    enriched_csv,
    service_summary_csv,
    service_week_summary_csv,
    plots_output_dir,
):
    """Run all plots from the weekly service summary dataset."""

    print("\nStarting plotting...")

    service_week_summary = pd.read_csv(service_week_summary_csv, low_memory=False)

    # Clean
    service_week_summary = service_week_summary.dropna(
        subset=["service", "job_week"]
    )

    service_week_summary["job_week"] = pd.to_datetime(
        service_week_summary["job_week"],
        errors="coerce",
    )

    service_week_summary = service_week_summary.dropna(subset=["job_week"])

    # Ensure expected numeric columns exist
    for column in [
        "job_count",
        "total_errors",
        "total_warnings",
        "failed_jobs",
        "failure_rate",
    ]:
        if column not in service_week_summary.columns:
            service_week_summary[column] = 0

        service_week_summary[column] = pd.to_numeric(
            service_week_summary[column],
            errors="coerce",
        ).fillna(0)

    dates_df = load_project_dates()

    plot_jobs_per_week(
        service_week_summary,
        dates_df,
        os.path.join(plots_output_dir, "jobs_per_week.png"),
    )

    print("Jobs per week plot saved")

    plot_errors_per_week(
        service_week_summary,
        dates_df,
        os.path.join(plots_output_dir, "errors_per_week.png"),
    )

    print("Errors per week plot saved")

    plot_warnings_per_week(
        service_week_summary,
        dates_df,
        os.path.join(plots_output_dir, "warnings_per_week.png"),
    )

    print("Warnings per week plot saved")

    plot_failed_jobs_per_week(
        service_week_summary,
        dates_df,
        os.path.join(plots_output_dir, "failed_jobs_per_week.png"),
    )

    print("Failed jobs per week plot saved")

    plot_failure_rate_per_week(
        service_week_summary,
        dates_df,
        os.path.join(plots_output_dir, "failure_rate_per_week.png"),
    )

    print("Failure rate per week plot saved")

    print("Plotting complete.")