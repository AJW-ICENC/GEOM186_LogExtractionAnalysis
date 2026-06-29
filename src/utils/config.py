"""


This module stores project-level path configuration for the FME log extraction and analysis pipeline.


"""

# Author: x
# Version: 0.1
# Date: 28/05/2026


## Import Modules

import os


## Working Directories

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INPUT_ROOT = os.path.join(BASE_DIR, "input", "GaOs_FME_job_logs_beta")

OUTPUT_ROOT = os.path.join(BASE_DIR, "output")

EXTRACTED_OUTPUT_DIR = os.path.join(OUTPUT_ROOT, "extracted")
ANALYSIS_OUTPUT_DIR = os.path.join(OUTPUT_ROOT, "analysis")
PLOTS_OUTPUT_DIR = os.path.join(OUTPUT_ROOT, "plots")

EXTRACTED_CSV = os.path.join(EXTRACTED_OUTPUT_DIR, "fme_log_extracted.csv")

ANALYSIS_ENRICHED_CSV = os.path.join(
    ANALYSIS_OUTPUT_DIR,
    "extracted_with_analysis_fields.csv"
)

SERVICE_SUMMARY_CSV = os.path.join(
    ANALYSIS_OUTPUT_DIR,
    "service_summary.csv"
)

JOB_OUTCOME_SUMMARY_CSV = os.path.join(
    ANALYSIS_OUTPUT_DIR,
    "job_outcome_summary.csv"
)


## Directory Helper

def create_output_directories():
    """Create required output directories if they do not already exist."""

    os.makedirs(EXTRACTED_OUTPUT_DIR, exist_ok=True)
    os.makedirs(ANALYSIS_OUTPUT_DIR, exist_ok=True)
    os.makedirs(PLOTS_OUTPUT_DIR, exist_ok=True)