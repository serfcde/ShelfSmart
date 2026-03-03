# 📦 ShelfSmart

> **Smart shelf inventory analytics and data pipeline system built with Python.**

ShelfSmart is a Python-based inventory intelligence platform designed to collect, process, analyze, and visualize shelf-level stock data. It combines a structured data pipeline with analytical scripts and secure storage practices to give teams actionable insights into inventory health, trends, and anomalies.

---

## 🗂️ Project Structure

```
ShelfSmart/
├── src/                    # Core source code and business logic
├── data_hub/               # Processed and transformed data
├── raw_data/               # Raw ingested data before processing
├── logs/                   # Application and pipeline execution logs
├── assests/                # Static assets (images, configs, templates)
├── app.py                  # Main application entry point
├── pipeline.md             # Pipeline architecture and workflow documentation
├── dataset.md              # Dataset schema and field descriptions
├── analytical_scripts.md   # Guide to available analytical scripts
└── security_storage.md     # Security policies and storage configuration
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/serfcde/ShelfSmart.git
cd ShelfSmart

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py
```

---

## 📖 Section Overview

### `src/`
Contains the core application modules including data ingestion handlers, transformation logic, and utility functions that power the ShelfSmart pipeline end-to-end.

### `data_hub/`
Acts as the central warehouse for cleaned and structured data outputs — serving as the bridge between raw ingestion and downstream analytics or reporting.

### `raw_data/`
Stores unprocessed, source-level inventory data as ingested from external feeds or manual uploads, preserved in its original form for traceability and reprocessing.

### `logs/`
Captures timestamped runtime logs, pipeline execution traces, and error reports to support debugging, auditing, and system monitoring.

### `assests/`
Holds supporting static files such as configuration templates, reference images, and report layouts used across the application.

### `app.py`
The main entry point of the ShelfSmart application — initializes the pipeline, connects components, and orchestrates the full data flow from ingestion to output.

### `pipeline.md`
Documents the end-to-end data pipeline architecture, describing each stage from raw data ingestion through transformation, analysis, and final storage.

### `dataset.md`
Provides detailed schema documentation including field names, data types, expected value ranges, and descriptions for all datasets used in the system.

### `analytical_scripts.md`
A reference guide to all available analytical scripts — covering their purpose, input requirements, usage instructions, and expected output formats.

### `security_storage.md`
Outlines the security guidelines and storage configuration policies governing data access controls, retention rules, and safe handling of sensitive inventory records.

---

## 🛠️ Tech Stack

- **Language:** Python 100%
- **Architecture:** Modular pipeline with separation of raw, processed, and analytical layers
- **Logging:** File-based structured logging via the `logs/` directory

