"""
This module stores project-level path configuration for the FME log extraction
and analysis pipeline.
"""

# Author: x
# Version: 0.3
# Date: 23/07/2026


## Import Modules

import os


## Working Directories

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INPUT_ROOT = os.path.join(BASE_DIR, "input")

INPUT_SOURCES = {
    "beta": os.path.join(INPUT_ROOT, "GaOs_FME_job_logs_beta"),
    "live": os.path.join(INPUT_ROOT, "GaOs_FME_job_logs_live"),
}

OUTPUT_ROOT = os.path.join(BASE_DIR, "output")

EXTRACTED_OUTPUT_DIR = os.path.join(OUTPUT_ROOT, "extracted")
ANALYSIS_OUTPUT_DIR = os.path.join(OUTPUT_ROOT, "analysis")
PLOTS_OUTPUT_DIR = os.path.join(OUTPUT_ROOT, "plots")

EXTRACTED_OUTPUTS = {
    "beta": os.path.join(EXTRACTED_OUTPUT_DIR, "fme_log_extracted_beta.csv"),
    "live": os.path.join(EXTRACTED_OUTPUT_DIR, "fme_log_extracted_live.csv"),
}

COMBINED_EXTRACTED_CSV = os.path.join(
    EXTRACTED_OUTPUT_DIR,
    "fme_log_extracted_combined.csv",
)

ANALYSIS_ENRICHED_CSV = os.path.join(
    ANALYSIS_OUTPUT_DIR,
    "extracted_with_analysis_fields.csv",
)

SERVICE_SUMMARY_CSV = os.path.join(
    ANALYSIS_OUTPUT_DIR,
    "service_summary.csv",
)

JOB_OUTCOME_SUMMARY_CSV = os.path.join(
    ANALYSIS_OUTPUT_DIR,
    "job_outcome_summary.csv",
)

SERVICE_WEEK_SUMMARY_CSV = os.path.join(
    ANALYSIS_OUTPUT_DIR,
    "service_jobs_per_week.csv",
)


## Directory Helper

def create_output_directories():
    """Create required output directories if they do not already exist."""

    os.makedirs(EXTRACTED_OUTPUT_DIR, exist_ok=True)
    os.makedirs(ANALYSIS_OUTPUT_DIR, exist_ok=True)
    os.makedirs(PLOTS_OUTPUT_DIR, exist_ok=True)