# GEOM186 - FME Log Extraction and Analysis
*As part of the Applied Project (GEOM186) for an MSc in GIS at the University of Exeter*

---

## Overview

This project provides a Python-based pipeline for extracting, structuring, and analysing FME Flow job logs generated during the beta testing of the **Data Coverage and Assessment Tool (DCAT)**.

The primary objective is to transform thousands of raw, semi-structured log files into a structured dataset that supports quantitative and qualitative analysis for the dissertation **Results** section.

---

## Introduction

FME Flow job logs contain detailed diagnostic information on the execution of DCAT workflows, including:

- Execution metadata (job ID, timestamps, duration)
- Workflow context (workspace name, automation, service type)
- Data processing metrics (features read/written)
- Validation results (geometry, attribution)
- System performance (memory usage, processing time)
- Error and warning messages

However, these logs are stored as unstructured text files, making direct analysis impractical.

This codebase solves that problem by:

1. Extracting key information from each log
2. Structuring it into a tabular dataset (CSV)
3. Supporting downstream analysis to evaluate system performance, reliability, and behaviour

---

## Project Structure

```
project_root/
│
├── input/
│   └── GaOs_FME_job_logs_beta/
│       └── {grouped_by_thousands}/
│           └── job_{jobid}.log
│
├── output/
│   └── fme_log_extracted.csv
│
├── src/
│   └── ExtractFMETestLogs.py
│
└── README.md
```

---

## Methodology

### Phase 1: Log Extraction

The extraction script processes all `.log` files and captures:

#### Execution Metadata
- Job ID
- Start Time
- End Time (derived from log timestamps)
- Duration (reported and calculated)
- Status (e.g. SUCCESSFUL)
- Warning count

#### Workflow Context
- Automation name
- Workspace (FME model)
- Derived service type (e.g. registration, overlap assessment)

#### Data Context
- DMD ID
- Source file paths
- ENC file identifiers

#### Processing Results
- Features read
- Features written
- Modification type (e.g. new cell, update, cancellation)
- Join success indicators

#### Validation Outputs
- Geometry validation status
- Attribution validation status
- CATCOV counts

#### Performance Metrics
- Peak memory usage
- Process ID
- Log line count (proxy for complexity)

#### Errors
- Error flag (boolean)
- First error message
- All error messages (aggregated)

#### Traceability
- Raw log excerpt (for debugging and validation)
- Source file path

---

### Phase 2: Data Structuring

All extracted records are written to:
