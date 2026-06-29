"""


This is the main entry point for the FME log extraction and analysis pipeline.


"""

# Author: x
# Version: 0.1
# Date: 28/05/2026


## Import Modules

from utils.config import (
    INPUT_ROOT,
    EXTRACTED_CSV,
    ANALYSIS_ENRICHED_CSV,
    SERVICE_SUMMARY_CSV,
    JOB_OUTCOME_SUMMARY_CSV,
    PLOTS_OUTPUT_DIR,
    create_output_directories,
)

from extraction.log_extractor import run_extraction
from analysis.log_analysis import run_analysis
from plotting.plots import run_plots


## Main Function

def main():
    """Run the full FME log extraction and analysis pipeline."""

    print("\nGEOM186 - FME Log Extraction and Analysis")
    print("-----------------------------------------\n")

    create_output_directories()

    run_extraction(
        input_root=INPUT_ROOT,
        output_file=EXTRACTED_CSV,
    )

    run_analysis(
        extracted_csv=EXTRACTED_CSV,
        enriched_output_csv=ANALYSIS_ENRICHED_CSV,
        service_summary_csv=SERVICE_SUMMARY_CSV,
        job_outcome_summary_csv=JOB_OUTCOME_SUMMARY_CSV,
    )

    run_plots(
        enriched_csv=ANALYSIS_ENRICHED_CSV,
        service_summary_csv=SERVICE_SUMMARY_CSV,
        plots_output_dir=PLOTS_OUTPUT_DIR,
    )

    print("\nPipeline complete.\n")


if __name__ == "__main__":
    main()
