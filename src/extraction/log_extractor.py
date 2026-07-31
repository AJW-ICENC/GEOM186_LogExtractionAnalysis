"""
This module extracts meta information from FME job logs as part of the
Gaps and Overlaps beta/live testing period.

Error and warning counts are extracted primarily from the FME translation
summary line, for example:

Translation FAILED with 3 error(s) and 12 warning(s) (0 feature(s) output)

Individual ERROR and WARN lines are retained only as diagnostic text fields.
"""

# Author: Alex Wallage
# Version: 4
# Date: 23/07/2026

## Enhanced by AI


## Import Modules

import os
import re
import pandas as pd
from datetime import datetime


## Regex Patterns

patterns = {
    # command line
    "job_id": re.compile(r"--FME_JOB_ID'\s*`([^`]+)`|--FME_JOB_ID\s+`([^`]+)`"),
    "automation": re.compile(r"--FME_AUTOMATION_NAME'\s*`([^`]+)`|--FME_AUTOMATION_NAME\s+`([^`]+)`"),

    # workspace
    "workspace_cfg": re.compile(r"FME_MF_NAME is '([^']+\.fmw)'"),
    "workspace_cmd": re.compile(r"`([^`]+\.fmw)`"),

    # execution
    "start_time": re.compile(r"System Time:\s+(\d{14})"),
    "duration": re.compile(r"FME Session Duration:\s+([\d\.]+)\s+seconds"),

    # Authoritative FME translation summary
    "translation_summary": re.compile(
        r"Translation\s+(?:was\s+)?(SUCCESSFUL|FAILED)\s+with\s+"
        r"(\d+)\s+error\(s\)\s+and\s+"
        r"(\d+)\s+warning\(s\)\s+"
        r"\((\d+)\s+feature\(s\)\s+output\)",
        re.IGNORECASE,
    ),

    # Fallback where count summary is not present
    "translation_status": re.compile(
        r"Translation\s+(?:was\s+)?(SUCCESSFUL|FAILED)",
        re.IGNORECASE,
    ),

    # timestamps
    "timestamp": re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"),

    # process / memory
    "peak_memory": re.compile(r"peak process memory usage:\s*(\d+)\s*kB", re.IGNORECASE),
    "current_memory": re.compile(r"current process memory usage:\s*(\d+)\s*kB", re.IGNORECASE),
    "process_id": re.compile(r"ProcessID:\s*(\d+)"),

    # environment
    "fme_version": re.compile(r"Current FME version:\s*FME\s+([\d\.]+)"),
    "workspace_saved_version": re.compile(r"Workspace was last saved in FME version:\s*FME\s+(.+)"),
    "machine": re.compile(r"Machine host name is:\s+(.+)"),
    "os": re.compile(r"Operating System:\s+(.+)"),
    "platform": re.compile(r"FME Platform:\s+(.+)"),
    "locale": re.compile(r"OS Locale Name\s*:\s+(.+)"),
    "locale_encoding": re.compile(r"OS Locale Encoding\s*:\s+(.+)"),
    "process_encoding": re.compile(r"Process Encoding\s*:\s+(.+)"),
    "fme_api_version": re.compile(r"FME API version:\s+'([^']+)'"),
    "engine": re.compile(r"--FME_ENGINE'\s*`([^`]+)`|--FME_ENGINE\s+`([^`]+)`"),
    "user": re.compile(r"--FME_SERVER_RUNTIME_USER'\s*`([^`]+)`|--FME_SERVER_RUNTIME_USER\s+`([^`]+)`"),

    # system resources
    "disk_space_gb": re.compile(r"System Status:\s+([\d\.]+)\s+GB of disk space available"),
    "physical_memory_gb": re.compile(r"System Status:\s+([\d\.]+)\s+GB of physical memory available"),
    "virtual_memory_gb": re.compile(r"System Status:\s+([\d\.]+)\s+GB of virtual memory available"),

    # data context
    "dmd_id": re.compile(r"DMD ID is\s+(\d+)"),
    "source_path": re.compile(r"(Data_In[\\/][^`'\s]+)"),
    "source_dataset_path": re.compile(r"--SourceDataset_PATH_3'\s*`([^`]+)`|--SourceDataset_PATH_3\s+`([^`]+)`"),
    "source_textline": re.compile(r"--SourceDataset_TEXTLINE'\s*`([^`]+)`|--SourceDataset_TEXTLINE\s+`([^`]+)`"),
    "log_filename_arg": re.compile(r"-LOG_FILENAME'\s*`([^`]+)`|-LOG_FILENAME\s+`([^`]+)`"),
    "file_name": re.compile(r"([A-Z]{2}\d{6}\.\d{3})"),
    "load_file": re.compile(r"([0-9]+_[A-Z0-9]+_LOAD\.txt)"),

    # database context
    "dest_mssql_spatial": re.compile(r"--DestDataset_MSSQL_SPATIAL(?:_\d+)?'\s*`([^`]+)`|--DestDataset_MSSQL_SPATIAL(?:_\d+)?\s+`([^`]+)`"),
    "source_mssql_spatial": re.compile(r"--SourceDataset_MSSQL_SPATIAL(?:_\d+)?'\s*`([^`]+)`|--SourceDataset_MSSQL_SPATIAL(?:_\d+)?\s+`([^`]+)`"),
    "source_sqlserver_jdbc": re.compile(r"--SourceDataset_SQLSERVER_JDBC(?:_\d+)?'\s*`([^`]+)`|--SourceDataset_SQLSERVER_JDBC(?:_\d+)?\s+`([^`]+)`"),
    "source_mssql_ado": re.compile(r"--SourceDataset_MSSQL_ADO'\s*`([^`]+)`|--SourceDataset_MSSQL_ADO\s+`([^`]+)`"),
    "dest_mssql_ado": re.compile(r"--DestDataset_MSSQL_ADO'\s*`([^`]+)`|--DestDataset_MSSQL_ADO\s+`([^`]+)`"),

    # processing
    "modification": re.compile(r"Modification type is (?:a\s*)?(.+?)\."),
    "join_success": re.compile(r"Input successfully joined with DB"),
    "registered_at": re.compile(r"Registered at\s+(.+?)\."),

    # validation
    "geometry_ok": re.compile(r"Geometry contains no errors"),
    "attribution_ok": re.compile(r"All attribution is accounted for"),
    "catcov": re.compile(r"(\d+)\s+polygon\(s\)\s+with CATCOV"),

    # feature metrics
    "features_read": re.compile(r"Total Features Read\s+(\d+)"),
    "features_written": re.compile(r"Total Features Written\s+(\d+)"),
    "done_reading": re.compile(r"Done reading\s+(\d+)\s+features"),
    "database_read_complete": re.compile(r"Database read complete\. Retrieved\s+(.+?)\s+feature\(s\)"),
    "geometry_processed": re.compile(r"Processed\s+(\d+)\s+of\s+(\d+)\s+features"),

    # diagnostic errors / warnings only
    "error_line": re.compile(r"\|ERROR\s*\|(.+)", re.IGNORECASE),
    "warn_line": re.compile(r"\|WARN\s*\|(.+)", re.IGNORECASE),
}


## Utility Functions

def get_first_group(match):
    """Return the first populated regex group."""

    if not match:
        return None

    for group in match.groups():
        if group:
            return group.strip()

    return None


def infer_service(workspace):
    """Infer service type from workspace name."""

    if not workspace:
        return None, "low"

    name = workspace.lower()

    if "overlap" in name:
        return "overlap_assessment", "high"

    if "registration" in name:
        return "data_registration", "high"

    if "maintenance" in name:
        return "maintenance", "high"

    return "unknown", "low"


def parse_time(timestr):
    """Parse FME system time."""

    try:
        return datetime.strptime(timestr, "%Y%m%d%H%M%S")
    except Exception:
        return None


def parse_log_timestamp(timestr):
    """Parse standard log timestamp."""

    try:
        return datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def extract_version_from_workspace(workspace):
    """Extract model version from workspace name where possible."""

    if not workspace:
        return None

    match = re.search(r"_v_([0-9_]+)", workspace)

    if match:
        return "v_" + match.group(1)

    return None


def extract_cell_name_from_file_name(file_name):
    """Extract cell name from ENC file where possible."""

    if not file_name:
        return None

    return file_name.split(".")[0]


def extract_job_id_from_source_file(source_file):
    """Fallback job ID extraction from filename."""

    file_name = os.path.basename(source_file)
    match = re.search(r"job_(\d+)\.log", file_name)

    if match:
        return match.group(1)

    return None


## Parser

def parse_log(file_path):
    """Parse a single FME log file into one structured record."""

    record = {
        "source_file": file_path,
        "dataset_phase": None,

        "job_id": None,
        "automation": None,
        "workspace": None,
        "workspace_version": None,
        "service": None,
        "service_confidence": None,

        "start_time": None,
        "end_time": None,
        "duration_sec": None,
        "duration_calculated": None,

        # New primary outcome fields
        "translation_status": None,
        "error_count": 0,
        "warning_count": 0,
        "features_output": None,
        "translation_summary_found": False,

        # Backwards-compatible aliases
        "status": None,
        "warnings": 0,
        "error_flag": False,

        "fme_version": None,
        "workspace_saved_version": None,
        "machine": None,
        "operating_system": None,
        "platform": None,
        "locale": None,
        "locale_encoding": None,
        "process_encoding": None,
        "fme_api_version": None,
        "engine": None,
        "user": None,

        "disk_space_gb": None,
        "physical_memory_gb": None,
        "virtual_memory_gb": None,

        "dmd_id": None,
        "source_path": None,
        "source_dataset_path": None,
        "source_textline": None,
        "log_filename_arg": None,
        "file_name": None,
        "cell_name": None,
        "load_file": None,

        "dest_mssql_spatial": None,
        "source_mssql_spatial": None,
        "source_sqlserver_jdbc": None,
        "source_mssql_ado": None,
        "dest_mssql_ado": None,

        "modification_type": None,
        "registered_at": None,
        "db_join_success": False,

        "geometry_ok": False,
        "attribution_ok": False,
        "catcov_count": None,

        "features_read": None,
        "features_written": None,
        "done_reading_features": None,
        "max_geometry_processed": None,
        "max_geometry_total": None,

        "peak_memory_kb": None,
        "current_memory_kb": None,
        "process_id": None,

        # Diagnostic text fields only
        "first_error_message": None,
        "all_errors": None,
        "diagnostic_error_line_count": 0,

        "all_warnings_text": None,
        "diagnostic_warning_line_count": 0,

        "log_line_count": 0,
        "last_timestamp_raw": None,

        "parse_status": "success",
        "parse_notes": "",

        "raw_excerpt": None,
    }

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()

        lines = content.splitlines()

        record["log_line_count"] = len(lines)
        record["raw_excerpt"] = content[:2000]

        timestamps = []
        diagnostic_errors = []
        diagnostic_warnings = []
        peak_memory_values = []
        current_memory_values = []
        geometry_processed_values = []
        geometry_total_values = []

        ## Command-line extraction

        for key in [
            "job_id",
            "automation",
            "engine",
            "user",
            "source_dataset_path",
            "source_textline",
            "log_filename_arg",
            "dest_mssql_spatial",
            "source_mssql_spatial",
            "source_sqlserver_jdbc",
            "source_mssql_ado",
            "dest_mssql_ado",
        ]:
            match = patterns[key].search(content)
            value = get_first_group(match)

            if value:
                record[key] = value

        ## Job ID fallback

        if not record["job_id"]:
            record["job_id"] = extract_job_id_from_source_file(file_path)

            if record["job_id"]:
                record["parse_notes"] += "job_id_from_filename; "

        ## Workspace extraction

        match = patterns["workspace_cfg"].search(content)

        if match:
            record["workspace"] = match.group(1).strip()
        else:
            matches = patterns["workspace_cmd"].findall(content)

            if matches:
                record["workspace"] = os.path.basename(matches[-1])

        ## Line-by-line extraction

        for line in lines:

            timestamp_match = patterns["timestamp"].match(line)

            if timestamp_match:
                timestamps.append(timestamp_match.group(1))

            ## Authoritative translation summary

            summary_match = patterns["translation_summary"].search(line)

            if summary_match:
                record["translation_summary_found"] = True
                record["translation_status"] = summary_match.group(1).upper()
                record["error_count"] = int(summary_match.group(2))
                record["warning_count"] = int(summary_match.group(3))
                record["features_output"] = int(summary_match.group(4))

                # Backwards-compatible aliases
                record["status"] = record["translation_status"]
                record["warnings"] = record["warning_count"]
                record["error_flag"] = record["error_count"] > 0

                continue

            ## Fallback translation status

            status_match = patterns["translation_status"].search(line)

            if status_match and not record["translation_status"]:
                record["translation_status"] = status_match.group(1).upper()
                record["status"] = record["translation_status"]

            ## Other extraction patterns

            for key, pattern in patterns.items():

                if key in [
                    "job_id",
                    "automation",
                    "workspace_cfg",
                    "workspace_cmd",
                    "timestamp",
                    "translation_summary",
                    "translation_status",
                    "engine",
                    "user",
                    "source_dataset_path",
                    "source_textline",
                    "log_filename_arg",
                    "dest_mssql_spatial",
                    "source_mssql_spatial",
                    "source_sqlserver_jdbc",
                    "source_mssql_ado",
                    "dest_mssql_ado",
                ]:
                    continue

                match = pattern.search(line)

                if not match:
                    continue

                if key == "start_time":
                    record["start_time"] = parse_time(match.group(1))

                elif key == "duration":
                    record["duration_sec"] = float(match.group(1))

                elif key == "features_read":
                    record["features_read"] = int(match.group(1))

                elif key == "features_written":
                    record["features_written"] = int(match.group(1))

                elif key == "done_reading":
                    record["done_reading_features"] = int(match.group(1))

                elif key == "geometry_processed":
                    processed = int(match.group(1))
                    total = int(match.group(2))

                    geometry_processed_values.append(processed)
                    geometry_total_values.append(total)

                elif key == "catcov":
                    record["catcov_count"] = int(match.group(1))

                elif key == "peak_memory":
                    peak_memory_values.append(int(match.group(1)))

                elif key == "current_memory":
                    current_memory_values.append(int(match.group(1)))

                elif key == "process_id":
                    record["process_id"] = match.group(1)

                elif key == "error_line":
                    diagnostic_errors.append(match.group(1).strip())

                elif key == "warn_line":
                    diagnostic_warnings.append(match.group(1).strip())

                elif key == "join_success":
                    record["db_join_success"] = True

                elif key == "geometry_ok":
                    record["geometry_ok"] = True

                elif key == "attribution_ok":
                    record["attribution_ok"] = True

                elif key == "modification":
                    record["modification_type"] = match.group(1).strip()

                elif key == "registered_at":
                    record["registered_at"] = match.group(1).strip()

                elif key == "file_name":
                    record["file_name"] = match.group(1).strip()

                elif key == "load_file":
                    record["load_file"] = match.group(1).strip()

                elif key == "source_path":
                    record["source_path"] = match.group(1).strip()

                elif key == "fme_version":
                    record["fme_version"] = match.group(1).strip()

                elif key == "workspace_saved_version":
                    record["workspace_saved_version"] = match.group(1).strip()

                elif key == "machine":
                    record["machine"] = match.group(1).strip()

                elif key == "os":
                    record["operating_system"] = match.group(1).strip()

                elif key == "platform":
                    record["platform"] = match.group(1).strip()

                elif key == "locale":
                    record["locale"] = match.group(1).strip()

                elif key == "locale_encoding":
                    record["locale_encoding"] = match.group(1).strip()

                elif key == "process_encoding":
                    record["process_encoding"] = match.group(1).strip()

                elif key == "fme_api_version":
                    record["fme_api_version"] = match.group(1).strip()

                elif key == "disk_space_gb":
                    record["disk_space_gb"] = float(match.group(1))

                elif key == "physical_memory_gb":
                    record["physical_memory_gb"] = float(match.group(1))

                elif key == "virtual_memory_gb":
                    record["virtual_memory_gb"] = float(match.group(1))

                elif key == "dmd_id":
                    record["dmd_id"] = match.group(1).strip()

        ## End time extraction

        if timestamps:
            record["last_timestamp_raw"] = timestamps[-1]
            record["end_time"] = parse_log_timestamp(timestamps[-1])

        ## Calculated duration

        if record["start_time"] and record["end_time"]:
            record["duration_calculated"] = (
                record["end_time"] - record["start_time"]
            ).total_seconds()

        ## Memory metrics

        if peak_memory_values:
            record["peak_memory_kb"] = max(peak_memory_values)

        if current_memory_values:
            record["current_memory_kb"] = max(current_memory_values)

        ## Geometry metrics

        if geometry_processed_values:
            record["max_geometry_processed"] = max(geometry_processed_values)

        if geometry_total_values:
            record["max_geometry_total"] = max(geometry_total_values)

        ## Diagnostic error/warning aggregation

        if diagnostic_errors:
            record["first_error_message"] = diagnostic_errors[0]
            record["all_errors"] = " | ".join(diagnostic_errors)
            record["diagnostic_error_line_count"] = len(diagnostic_errors)

        if diagnostic_warnings:
            record["all_warnings_text"] = " | ".join(diagnostic_warnings)
            record["diagnostic_warning_line_count"] = len(diagnostic_warnings)

        ## Fallback if no translation summary is available

        if not record["translation_summary_found"]:
            record["parse_notes"] += "missing_translation_summary; "

            if record["translation_status"]:
                record["status"] = record["translation_status"]

            # Only use diagnostic ERROR lines as a fallback where the
            # authoritative FME summary line is absent.
            if record["error_count"] == 0 and diagnostic_errors:
                record["error_count"] = len(diagnostic_errors)
                record["error_flag"] = True
                record["parse_notes"] += "error_count_from_diagnostic_lines; "

            if record["warning_count"] == 0 and diagnostic_warnings:
                record["warning_count"] = len(diagnostic_warnings)
                record["warnings"] = record["warning_count"]
                record["parse_notes"] += "warning_count_from_diagnostic_lines; "

        ## Derived fields

        record["workspace_version"] = extract_version_from_workspace(record["workspace"])
        record["cell_name"] = extract_cell_name_from_file_name(record["file_name"])

        service, confidence = infer_service(record.get("workspace"))

        record["service"] = service
        record["service_confidence"] = confidence

        ## Final backwards-compatible flags

        record["status"] = record["translation_status"]
        record["warnings"] = record["warning_count"]
        record["error_flag"] = record["error_count"] > 0

        ## Validation

        if not record["job_id"]:
            record["parse_notes"] += "missing_job_id; "

        if not record["workspace"]:
            record["parse_notes"] += "missing_workspace; "

        if not record["end_time"]:
            record["parse_notes"] += "missing_end_time; "

        if not record["translation_status"]:
            record["parse_notes"] += "missing_translation_status; "

        return record

    except Exception as error:
        record["parse_status"] = "failed"
        record["parse_notes"] = str(error)

        return record


## Extraction Runner

def run_extraction(input_root, output_file, dataset_phase):
    """Run extraction across all FME log files for a given dataset phase."""

    all_records = []
    file_count = 0

    print("\nStarting extraction...")
    print(f"Dataset phase: {dataset_phase}")
    print(f"Input directory: {input_root}")
    print(f"Output file: {output_file}\n")

    for root, dirs, files in os.walk(input_root):
        for file in files:

            if file.endswith(".log"):

                file_path = os.path.join(root, file)
                record = parse_log(file_path)

                record["dataset_phase"] = dataset_phase

                all_records.append(record)
                file_count += 1

                if file_count % 1000 == 0:
                    print(f"Processed {file_count} log files...")

    print(f"\nTotal logs processed for {dataset_phase}: {file_count}")

    if file_count == 0:
        print(f"No log files found for {dataset_phase}. This source will be skipped.")
        return pd.DataFrame()

    dataframe = pd.DataFrame(all_records)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    dataframe.to_csv(output_file, index=False)

    print(f"Extraction complete: {output_file}")

    return dataframe