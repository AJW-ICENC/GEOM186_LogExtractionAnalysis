"""


Semantic error extraction:
Counts true issue types rather than log lines.

"""

import os
import re
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

os.makedirs(OUTPUT_DIR, exist_ok=True)


## Regex for TRUE issues

ISSUE_PATTERN = re.compile(r"issue_found'.*?`([^`]+)`")


## Main

def main():

    print("\nRunning semantic error analysis\n")

    df = pd.read_csv(INPUT_CSV, low_memory=False)

    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df = df.dropna(subset=["start_time"])

    # Filter valid services only
    df = df[df["service"].notna()]
    df = df[df["service"] != "unknown"]

    ## Extract TRUE issues only

    def extract_issues(text):

        if pd.isna(text):
            return []

        return ISSUE_PATTERN.findall(text)

    df["issues"] = df["all_errors"].apply(extract_issues)

    # Count real issues per job
    df["true_error_count"] = df["issues"].apply(len)

    ## Weekly aggregation

    df["week"] = df["start_time"].dt.to_period("W").apply(lambda r: r.start_time)

    weekly = df.groupby("week").agg(
        job_count=("job_id", "count"),
        total_errors=("true_error_count", "sum"),
    ).reset_index()

    weekly["errors_per_job"] = weekly["total_errors"] / weekly["job_count"]

    weekly = weekly.sort_values("week").reset_index(drop=True)

    ## Linear regression

    weekly["t"] = np.arange(len(weekly))

    slope, intercept = np.polyfit(weekly["t"], weekly["errors_per_job"], 1)
    weekly["regression"] = slope * weekly["t"] + intercept

    print(f"\nRegression:")
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

    plt.title("Semantic Errors per Job per Week")
    plt.xlabel("Week")
    plt.ylabel("Errors per Job")
    plt.legend()
    plt.xticks(rotation=45)

    plt.tight_layout()

    output_plot = os.path.join(OUTPUT_DIR, "semantic_errors_per_week.png")
    plt.savefig(output_plot, dpi=300)
    plt.close()

    print(f"Saved plot: {output_plot}")

    ## Save CSV
    weekly.to_csv(os.path.join(OUTPUT_DIR, "semantic_errors_per_week.csv"), index=False)

    print("\nDone\n")


if __name__ == "__main__":
    main()