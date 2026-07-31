"""


Extract and inspect error behaviour from FME log dataset.

Produces:
- Unique error messages
- Jobs with most errors
- Expanded error table


"""

# Author: Alex Wallage
# Version: 1
# Date: 29/06/2026


## Imports

import os
import pandas as pd


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
    "error_diagnostics",
)

UNIQUE_ERRORS_CSV = os.path.join(OUTPUT_DIR, "unique_errors.csv")
TOP_JOBS_CSV = os.path.join(OUTPUT_DIR, "jobs_with_most_errors.csv")
EXPANDED_ERRORS_CSV = os.path.join(OUTPUT_DIR, "expanded_errors.csv")


## Main

def main():

    print("\nRunning error diagnostics extraction\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load dataset
    df = pd.read_csv(INPUT_CSV, low_memory=False)

    # Ensure fields exist
    if "all_errors" not in df.columns:
        raise Exception("Column 'all_errors' not found in dataset")

    df["error_count"] = pd.to_numeric(df["error_count"], errors="coerce").fillna(0)

    # Filter real error rows
    df_errors = df[df["error_count"] > 0].copy()

    print(f"Total jobs with errors: {len(df_errors)}")

    ## --------------------------------------------------
    ## Expand errors (split multiple errors per job)
    ## --------------------------------------------------

    df_errors["error_list"] = df_errors["all_errors"].fillna("").str.split(r"\s*\|\s*")

    expanded = df_errors.explode("error_list")

    expanded = expanded.rename(columns={"error_list": "error_text"})

    expanded = expanded[
        expanded["error_text"].notna() &
        (expanded["error_text"].str.strip() != "")
    ]

    ## --------------------------------------------------
    ## Unique error summary
    ## --------------------------------------------------

    unique_errors = expanded.groupby("error_text").agg(
        count=("error_text", "count"),
        example_job_id=("job_id", "first"),
    ).reset_index()

    unique_errors = unique_errors.sort_values("count", ascending=False)

    unique_errors.to_csv(UNIQUE_ERRORS_CSV, index=False)
    print(f"Saved: {UNIQUE_ERRORS_CSV}")

    ## --------------------------------------------------
    ## Top jobs with most errors
    ## --------------------------------------------------

    top_jobs = df_errors.sort_values("error_count", ascending=False)[
        ["job_id", "error_count", "service", "start_time"]
    ]

    top_jobs = top_jobs.head(50)

    top_jobs.to_csv(TOP_JOBS_CSV, index=False)
    print(f"Saved: {TOP_JOBS_CSV}")

    ## --------------------------------------------------
    ## Expanded error table (use this for analysis/chat)
    ## --------------------------------------------------

    expanded_subset = expanded[
        ["job_id", "service", "error_text"]
    ].copy()

    expanded_subset.to_csv(EXPANDED_ERRORS_CSV, index=False)
    print(f"Saved: {EXPANDED_ERRORS_CSV}")

    print("\nDone.\n")


if __name__ == "__main__":
    main()