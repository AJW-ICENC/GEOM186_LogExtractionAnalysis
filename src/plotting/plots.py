"""


This module creates figures from analysed FME log data.


"""

import os
import pandas as pd
import matplotlib.pyplot as plt


def save_plot(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def load_project_dates():

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dates_path = os.path.join(base_dir, "static", "dates.csv")

    df = pd.read_csv(dates_path)

    # Use start_date only, UK format
    df["date"] = pd.to_datetime(df["start_date"], dayfirst=True, errors="coerce")

    return df.dropna(subset=["date"])


def plot_jobs_per_week(service_week_summary, dates_df, output_path):

    plt.figure(figsize=(12, 7))

    for service, group in service_week_summary.groupby("service"):
        group = group.sort_values("job_week")

        plt.plot(
            group["job_week"],
            group["job_count"],
            marker="o",
            label=service,
        )

    # Add milestone lines
    ymax = plt.ylim()[1] * 0.95

    for _, row in dates_df.iterrows():
        plt.axvline(row["date"], linestyle="--")
        plt.text(row["date"], ymax, row["Title"], rotation=90)

    plt.title("FME Jobs per Week by Service")
    plt.xlabel("Week")
    plt.ylabel("Job Count")
    plt.legend()
    plt.xticks(rotation=45)

    save_plot(output_path)


def plot_errors_per_week(service_week_summary, dates_df, output_path):

    plt.figure(figsize=(12, 7))

    for service, group in service_week_summary.groupby("service"):
        group = group.sort_values("job_week")

        plt.plot(
            group["job_week"],
            group["error_count"],
            marker="o",
            label=service,
        )

    ymax = plt.ylim()[1] * 0.95

    for _, row in dates_df.iterrows():
        plt.axvline(row["date"], linestyle="--")
        plt.text(row["date"], ymax, row["Title"], rotation=90)

    plt.title("FME Errors per Week by Service")
    plt.xlabel("Week")
    plt.ylabel("Error Count")
    plt.legend()
    plt.xticks(rotation=45)

    save_plot(output_path)


def run_plots(
    enriched_csv,
    service_summary_csv,
    service_week_summary_csv,
    plots_output_dir,
):

    print("\nStarting plotting...")

    service_week_summary = pd.read_csv(service_week_summary_csv, low_memory=False)

    # Clean
    service_week_summary = service_week_summary.dropna(subset=["service", "job_week"])

    service_week_summary["job_week"] = pd.to_datetime(service_week_summary["job_week"])

    dates_df = load_project_dates()

    # Jobs per week plot
    plot_jobs_per_week(
        service_week_summary,
        dates_df,
        os.path.join(plots_output_dir, "jobs_per_week.png"),
    )

    print("Jobs per week plot saved")

    # Errors per week plot
    plot_errors_per_week(
        service_week_summary,
        dates_df,
        os.path.join(plots_output_dir, "errors_per_week.png"),
    )

    print("Errors per week plot saved")

    print("Plotting complete.")