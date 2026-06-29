"""


This is the main entry point for the FME log extraction and analysis pipeline.


"""

# Author: x
# Version: 0.2
# Date: 29/06/2026


## Import Modules

import os
import argparse
import pandas as pd

from utils.config import (
    INPUT_SOURCES,
    EXTRACTED_OUTPUTS,
    COMBINED_EXTRACTED_CSV,
    ANALYSIS_ENRICHED_CSV,
    SERVICE_SUMMARY_CSV,
    JOB_OUTCOME_SUMMARY_CSV,
    SERVICE_MONTH_SUMMARY_CSV,
    PLOTS_OUTPUT_DIR,
    create_output_directories,
)

from extraction.log_extractor import run_extraction
from analysis.log_analysis import run_analysis
from plotting.plots import run_plots


## Argument Handling

def parse_arguments():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description="Run the FME log extraction and analysis pipeline."
    )

    parser.add_argument(
        "--phase",
        choices=["beta", "live", "all"],
        default="all",
        help="Select which log source to process. Default is all."
    )

    parser.add_argument(
        "--force-extract",
        action="store_true",
        help="Force extraction even if extracted CSV files already exist."
    )

    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Run extraction and analysis but skip plot generation."
    )

    return parser.parse_args()


## Pipeline Helpers

def get_selected_phases(phase_argument):
    """Return selected dataset phases based on command line argument."""

    if phase_argument == "all":
        return ["beta", "live"]

    return [phase_argument]


def load_or_extract_phase(phase, force_extract=False):
    """Load cached extraction output or run extraction for one phase."""

    input_root = INPUT_SOURCES[phase]
    output_file = EXTRACTED_OUTPUTS[phase]

    if os.path.exists(output_file) and not force_extract:
        print(f"\nUsing cached extraction for {phase}: {output_file}")
        dataframe = pd.read_csv(output_file)

        if "dataset_phase" not in dataframe.columns:
            dataframe["dataset_phase"] = phase

        return dataframe

    dataframe = run_extraction(
        input_root=input_root,
        output_file=output_file,
        dataset_phase=phase,
    )

    return dataframe


def combine_extracted_outputs(dataframes, output_file):
    """Combine extracted dataframes into one CSV."""

    valid_dataframes = [
        dataframe for dataframe in dataframes
        if dataframe is not None and not dataframe.empty
    ]

    if not valid_dataframes:
        raise ValueError("No extracted data available to combine.")

    combined = pd.concat(valid_dataframes, ignore_index=True)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    combined.to_csv(output_file, index=False)

    print(f"\nCombined extracted dataset saved: {output_file}")
    print(f"Combined row count: {len(combined)}")

    return combined


## Main Function

def main():
    """Run the full FME log extraction and analysis pipeline."""

    args = parse_arguments()

    print("\nGEOM186 - FME Log Extraction and Analysis")
    print("-----------------------------------------")
    print(f"Selected phase: {args.phase}")
    print(f"Force extraction: {args.force_extract}")
    print(f"Skip plots: {args.skip_plots}\n")

    create_output_directories()

    selected_phases = get_selected_phases(args.phase)

    extracted_dataframes = []

    for phase in selected_phases:
        dataframe = load_or_extract_phase(
            phase=phase,
            force_extract=args.force_extract,
        )

        if dataframe is not None and not dataframe.empty:
            extracted_dataframes.append(dataframe)

    combine_extracted_outputs(
        dataframes=extracted_dataframes,
        output_file=COMBINED_EXTRACTED_CSV,
    )


    run_analysis(
        extracted_csv=COMBINED_EXTRACTED_CSV,
        enriched_output_csv=ANALYSIS_ENRICHED_CSV,
        service_summary_csv=SERVICE_SUMMARY_CSV,
        job_outcome_summary_csv=JOB_OUTCOME_SUMMARY_CSV,
        service_week_summary_csv=SERVICE_MONTH_SUMMARY_CSV,
    )


    if not args.skip_plots:
        run_plots(
            enriched_csv=ANALYSIS_ENRICHED_CSV,
            service_summary_csv=SERVICE_SUMMARY_CSV,
            service_week_summary_csv=SERVICE_MONTH_SUMMARY_CSV,
            plots_output_dir=PLOTS_OUTPUT_DIR,
        )


    print("\nPipeline complete.\n")


if __name__ == "__main__":
    main()