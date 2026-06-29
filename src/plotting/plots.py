"""


This module creates initial figures from the extracted and analysed FME log dataset.


"""

# Author: x
# Version: 0.1
# Date: 29/06/2026


## Import Modules

import os
import pandas as pd
import matplotlib.pyplot as plt


## Plot Helpers

def save_plot(output_path):
    """Save current matplotlib figure."""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


## Plotting Runner

def run_plots(enriched_csv, service_summary_csv, plots_output_dir):
    """Generate initial plots from analysed FME log data."""

    print("\nStarting plotting...")

    dataframe = pd.read_csv(enriched_csv)
    service_summary = pd.read_csv(service_summary_csv)

    os.makedirs(plots_output_dir, exist_ok=True)

    ## Plot 1: Job count by service

    if "service" in service_summary.columns and "job_count" in service_summary.columns:

        plt.figure(figsize=(10, 6))
        plt.bar(service_summary["service"].astype(str), service_summary["job_count"])
        plt.title("FME Job Count by Service")
        plt.xlabel("Service")
        plt.ylabel("Job Count")
        plt.xticks(rotation=45, ha="right")

        output_path = os.path.join(plots_output_dir, "job_count_by_service.png")
        save_plot(output_path)

        print(f"Plot saved: {output_path}")

    ## Plot 2: Average duration by service

    if "service" in service_summary.columns and "mean_duration_sec" in service_summary.columns:

        plot_data = service_summary.dropna(subset=["mean_duration_sec"])

        if not plot_data.empty:

            plt.figure(figsize=(10, 6))
            plt.bar(plot_data["service"].astype(str), plot_data["mean_duration_sec"])
            plt.title("Mean FME Job Duration by Service")
            plt.xlabel("Service")
            plt.ylabel("Mean Duration (seconds)")
            plt.xticks(rotation=45, ha="right")

            output_path = os.path.join(plots_output_dir, "average_duration_by_service.png")
            save_plot(output_path)

            print(f"Plot saved: {output_path}")

    ## Plot 3: Warning count distribution

    if "warnings" in dataframe.columns:

        warning_data = pd.to_numeric(dataframe["warnings"], errors="coerce").dropna()

        if not warning_data.empty:

            plt.figure(figsize=(10, 6))
            plt.hist(warning_data, bins=20)
            plt.title("Distribution of Warning Counts")
            plt.xlabel("Warning Count")
            plt.ylabel("Frequency")

            output_path = os.path.join(plots_output_dir, "warning_count_distribution.png")
            save_plot(output_path)

            print(f"Plot saved: {output_path}")

    ## Plot 4: Duration distribution

    if "duration_sec" in dataframe.columns:

        duration_data = pd.to_numeric(dataframe["duration_sec"], errors="coerce").dropna()

        if not duration_data.empty:

            plt.figure(figsize=(10, 6))
            plt.hist(duration_data, bins=40)
            plt.title("Distribution of FME Job Durations")
            plt.xlabel("Duration (seconds)")
            plt.ylabel("Frequency")

            output_path = os.path.join(plots_output_dir, "duration_distribution.png")
            save_plot(output_path)

            print(f"Plot saved: {output_path}")

    print("Plotting complete.")