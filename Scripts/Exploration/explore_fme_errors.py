"""


Exploratory script for understanding FME log error reporting.

Purpose:
    - Identify how FME logs represent failures, warnings,
      validation findings and diagnostic output.
    - Create datasets for manual review before defining
      analytical error metrics.

Inputs:
    output/analysis/extracted_with_analysis_fields.csv

Outputs:
    output/error_exploration/

"""

# Author: Alex Wallage
# Version: 1

## Enhanced by AI


## Imports

import os
import pandas as pd


## Paths

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)


INPUT_CSV = os.path.join(
    BASE_DIR,
    "output",
    "analysis",
    "extracted_with_analysis_fields.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output",
    "error_exploration"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

TOP_ERROR_JOBS = os.path.join(
    OUTPUT_DIR,
    "top_error_jobs.csv"
)

FAILED_JOBS = os.path.join(
    OUTPUT_DIR,
    "failed_jobs.csv"
)

WARNING_JOBS = os.path.join(
    OUTPUT_DIR,
    "warning_jobs.csv"
)

UNIQUE_MESSAGES = os.path.join(
    OUTPUT_DIR,
    "unique_error_messages.csv"
)

FULL_EXAMPLES = os.path.join(
    OUTPUT_DIR,
    "full_error_examples.csv"
)


## Main

def main():

    print("\nLoading dataset...\n")

    df = pd.read_csv(INPUT_CSV)

    
    ## Basic statistics
    

    print("Rows:", len(df))

    if "status" in df.columns:
        print("\nStatus distribution:\n")
        print(df["status"].value_counts(dropna=False))

    if "warnings" in df.columns:
        print("\nWarning distribution:\n")
        print(df["warnings"].describe())

    if "error_count" in df.columns:
        print("\nError count distribution:\n")
        print(df["error_count"].describe())

    
    ## Top error-count jobs
    

    top_jobs = df.sort_values(
        "error_count",
        ascending=False
    )

    top_jobs = top_jobs[
        [
            "job_id",
            "service",
            "workspace",
            "status",
            "warnings",
            "error_count",
            "start_time",
        ]
    ]

    top_jobs.head(200).to_csv(
        TOP_ERROR_JOBS,
        index=False
    )

    print("Saved:", TOP_ERROR_JOBS)

    
    ## Failed jobs
    

    failed_jobs = df[
        df["status"].astype(str).str.upper() != "SUCCESSFUL"
    ]

    failed_jobs.to_csv(
        FAILED_JOBS,
        index=False
    )

    print("Saved:", FAILED_JOBS)

    
    ## Jobs with warnings
    

    warning_jobs = df[
        pd.to_numeric(
            df["warnings"],
            errors="coerce"
        ).fillna(0) > 0
    ]

    warning_jobs.to_csv(
        WARNING_JOBS,
        index=False
    )

    print("Saved:", WARNING_JOBS)

    
    ## Unique messages
    

    if "all_errors" in df.columns:

        records = []

        for _, row in df.iterrows():

            text = row.get("all_errors")

            if pd.isna(text):
                continue

            messages = [
                m.strip()
                for m in str(text).split("|")
                if m.strip()
            ]

            for msg in messages:

                records.append(
                    {
                        "job_id": row["job_id"],
                        "service": row["service"],
                        "status": row["status"],
                        "message": msg
                    }
                )

        messages_df = pd.DataFrame(records)

        if len(messages_df):

            summary = messages_df.groupby(
                "message"
            ).agg(
                count=("message", "count"),
                example_job=("job_id", "first"),
                example_service=("service", "first")
            )

            summary = (
                summary
                .reset_index()
                .sort_values(
                    "count",
                    ascending=False
                )
            )

            summary.to_csv(
                UNIQUE_MESSAGES,
                index=False
            )

            print("Saved:", UNIQUE_MESSAGES)

    
    ## Full examples
    

    example_fields = [
        "job_id",
        "service",
        "workspace",
        "start_time",
        "status",
        "warnings",
        "error_count",
        "all_errors",
        "raw_excerpt"
    ]

    existing_fields = [
        f
        for f in example_fields
        if f in df.columns
    ]

    examples = (
        df
        .sort_values(
            "error_count",
            ascending=False
        )
        .head(50)
    )

    examples[existing_fields].to_csv(
        FULL_EXAMPLES,
        index=False
    )

    print("Saved:", FULL_EXAMPLES)

    print("\nExploration complete.\n")


if __name__ == "__main__":
    main()