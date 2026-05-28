"""


This script extracts meta information from FME job logs as part of the gaps and overlaps beta testing period


"""

# Author: x
# Version: 0.1
# Date: 28/05/2026


## Import Modules

import os
import re
import pandas as pd
from datetime import datetime


## Working Directories

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_ROOT = os.path.join(BASE_DIR, "input", "GaOs_FME_job_logs_beta")
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "fme_log_extracted.csv")



## regex patterns


patterns = {
    "job_id": re.compile(r'--FME_JOB_ID\s+(\d+)'),
    "automation": re.compile(r'--FME_SERVER_JOBHISTORY_AUTOMATION_NAME\s+(.+)'),
    "workspace": re.compile(r'([A-Za-z0-9_]+\.fmw)'),
    "start_time": re.compile(r'System Time:\s+(\d{14})'),
    "duration": re.compile(r'FME Session Duration:\s+([\d\.]+)\s+seconds'),
    "status": re.compile(r'Translation was (\w+)'),
    "warnings": re.compile(r'(\d+)\s+warning\(s\)'),
    "fme_version": re.compile(r'FME\s+([\d\.]+)'),
    "machine": re.compile(r'Machine name is\s+(.+)'),
    "engine": re.compile(r'Running on\s+(.+)'),
    "user": re.compile(r'User Name:\s+(.+)'),

    "dmd_id": re.compile(r'DMD ID is\s+(\d+)'),
    "source_path": re.compile(r'Data_In[\\/].+'),
    "file_name": re.compile(r'([A-Z]{2}\d{6}\.\d{3})'),

    "modification": re.compile(r'Modification type is a?\s*(.+)\.'),
    "join_success": re.compile(r'Input successfully joined with DB'),

    "geometry_ok": re.compile(r'Geometry contains no errors'),
    "attribution_ok": re.compile(r'All attribution is accounted for'),
    "catcov": re.compile(r'(\d+)\s+polygon\(s\) with CATCOV'),

    "features_read": re.compile(r'Total Features Read\s+(\d+)'),
    "features_written": re.compile(r'Total Features Written\s+(\d+)'),

    "error": re.compile(r'ERROR:\s*(.+)'),
}



## Utility Functions

def infer_service(job_name):
    """Infer service type from job name"""
    if not job_name:
        return None, "low"

    name = job_name.lower()

    if "overlap" in name:
        return "overlap_assessment", "high"
    elif "registration" in name:
        return "data_registration", "high"
    else:
        return "unknown", "low"


def parse_time(timestr):
    try:
        return datetime.strptime(timestr, "%Y%m%d%H%M%S")
    except:
        return None



## Parser

def parse_log(file_path):
    record = {
        "source_file": file_path,
        "job_id": None,
        "automation": None,
        "workspace": None,
        "service": None,
        "service_confidence": None,
        "start_time": None,
        "duration_sec": None,
        "status": None,
        "warnings": None,

        "fme_version": None,
        "machine": None,
        "engine": None,
        "user": None,

        "dmd_id": None,
        "source_path": None,
        "file_name": None,

        "modification_type": None,
        "db_join_success": False,

        "geometry_ok": False,
        "attribution_ok": False,
        "catcov_count": None,

        "features_read": None,
        "features_written": None,

        "error_flag": False,
        "error_message": None,

        "parse_status": "success",
        "parse_notes": None,

        "raw_excerpt": None,
    }

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        record["raw_excerpt"] = "".join(lines[:50])

        for line in lines:
            for key, pattern in patterns.items():
                match = pattern.search(line)

                if match:
                    value = match.group(1) if match.groups() else match.group(0)

                    if key == "start_time":
                        record["start_time"] = parse_time(value)
                    elif key == "duration":
                        record["duration_sec"] = float(value)
                    elif key == "warnings":
                        record["warnings"] = int(value)
                    elif key == "features_read":
                        record["features_read"] = int(value)
                    elif key == "features_written":
                        record["features_written"] = int(value)
                    elif key == "catcov":
                        record["catcov_count"] = int(value)
                    elif key == "error":
                        record["error_flag"] = True
                        record["error_message"] = value
                    elif key == "join_success":
                        record["db_join_success"] = True
                    elif key == "geometry_ok":
                        record["geometry_ok"] = True
                    elif key == "attribution_ok":
                        record["attribution_ok"] = True
                    elif key == "modification":
                        record["modification_type"] = value.strip()
                    else:
                        record[key] = value.strip()

        service, confidence = infer_service(record.get("automation"))
        record["service"] = service
        record["service_confidence"] = confidence

        return record

    except Exception as e:
        record["parse_status"] = "failed"
        record["parse_notes"] = str(e)
        return record


## Main Function

def main():
    all_records = []
    file_count = 0

    print(f"\nBASE DIR: {BASE_DIR}")
    print(f"INPUT DIR: {INPUT_ROOT}")
    print(f"OUTPUT FILE: {OUTPUT_FILE}\n")

    for root, dirs, files in os.walk(INPUT_ROOT):
        for file in files:
            if file.endswith(".log"):
                file_path = os.path.join(root, file)

                record = parse_log(file_path)
                all_records.append(record)

                file_count += 1

                # Progress reporting at scale
                if file_count % 1000 == 0:
                    print(f"Processed {file_count} log files...")

    print(f"\n📊 Total logs processed: {file_count}")

    if file_count == 0:
        print("No log files found — check input path.")
        return

    df = pd.DataFrame(all_records)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nExtraction complete: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
