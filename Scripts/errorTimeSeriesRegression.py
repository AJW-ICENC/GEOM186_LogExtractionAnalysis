"""


Custom analysis script:
Errors per job per week with linear regression trend.

Uses:
output/analysis/extracted_with_analysis_fields.csv

"""

# Author: Alex Wallage
# Version: 0.2
# Date: 29/06/2026


## Imports

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


## Paths

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_CSV = os.path.join(
    BASE_DIR,
    "output",
    "analysis",
    "extracted_with_analysis_fields.csv",
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output",
    "custom_scripts",
)

OUTPUT_CSV = os.path.join(
    OUTPUT_DIR,
    "errors_per_job_per_week.csv",
)

OUTPUT_PLOT = os.path.join(
    OUTPUT_DIR,
    "errors_per_job_per_week_regression.png",
)


## Main

def main():

    print("\nRunning: Errors per Job per Week (Linear Regression)\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ## Load

    df = pd.read_csv(INPUT_CSV, low_memory=False)

    ## Ensure correct types

    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["error_count"] = pd.to_numeric(df["error_count"], errors="coerce")

    ## Filter

    df = df.dropna(subset=["start_time"])
    df = df[df["service"].notna()]
    df = df[df["service"] != "unknown"]

    ## --- IMPORTANT: true error count used ---
    df["error_count"] = df["error_count"].fillna(0)

    ## Weekly aggregation

    df["week"] = df["start_time"].dt.to_period("W").apply(lambda r: r.start_time)

    weekly = df.groupby("week").agg(
        job_count=("job_id", "count"),
        total_errors=("error_count", "sum"),
    ).reset_index()

    ## Errors per job (correct metric)

    weekly["errors_per_job"] = weekly["total_errors"] / weekly["job_count"]

    ## Sort

    weekly = weekly.sort_values("week")
    weekly = weekly.reset_index(drop=True)

    ## Save CSV

    weekly.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved CSV: {OUTPUT_CSV}")

    ## --- Linear regression (NOT rolling) ---

    weekly["time_index"] = np.arange(len(weekly))

    x = weekly["time_index"].values
    y = weekly["errors_per_job"].values

    slope, intercept = np.polyfit(x, y, 1)

    weekly["regression"] = slope * x + intercept

    print("\nLinear regression:")
    print(f"errors_per_job = {slope:.6f} * t + {intercept:.6f}")

    ## Plot

    plt.figure(figsize=(11, 6))

    plt.plot(
        weekly["week"],
        weekly["errors_per_job"],
        marker="o",
        label="Errors per job",
    )

    plt.plot(
        weekly["week"],
        weekly["regression"],
        linestyle="--",
        label="Linear trend",
    )

    plt.title("Errors per Job per Week (Linear Trend)")
    plt.xlabel("Week")
    plt.ylabel("Errors per Job")
    plt.legend()
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=300)
    plt.close()

    print(f"Saved plot: {OUTPUT_PLOT}")

    ## Debug sanity output (important)

    print("\nSanity check (error_count distribution):")
    print(df["error_count"].describe())


if __name__ == "__main__":
    main()