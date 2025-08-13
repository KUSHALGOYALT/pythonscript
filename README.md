# DSM Data Extraction Scripts

This repository contains three data extraction scripts for different regional power committees in India.

## Scripts

### 1. WRPC Extractor (`dsm_data/WRPC/scripts/wrpc_extractor.py`)
- **Purpose**: Extracts DSM (Deviation Settlement Mechanism) data from Western Regional Power Committee
- **Features**: 
  - Downloads data for past 7 days
  - Handles dynamic file patterns
  - Processes CSV files with flexible column structure
- **Usage**: `python wrpc_extractor.py`

### 2. ERPC Extractor (`dsm_data/ERLDC/scripts/erpc_extractor.py`)
- **Purpose**: Extracts data from Eastern Regional Power Committee
- **Features**:
  - Downloads historical files for past 7 days
  - Scrapes website for current files
  - Processes Excel files
- **Usage**: `python erpc_extractor.py`

### 3. NRLDC Extractor (`dsm_data/NRLDC/scripts/dsa_extractor.py`)
- **Purpose**: Extracts DSA (Deviation Settlement Account) data from Northern Regional Load Dispatch Centre
- **Features**:
  - Downloads historical files for past 7 days
  - Processes supporting files from DSA directories
  - Handles Excel files
- **Usage**: `python dsa_extractor.py`

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Navigate to the script directory:
   ```bash
   cd dsm_data/[WRPC|ERLDC|NRLDC]/scripts
   ```

3. Run the script:
   ```bash
   python [script_name].py
   ```

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- openpyxl
- pandas (for some scripts)

## Output

All scripts create a `data/` directory and save extracted files there. The scripts will:
- Download files from respective websites
- Process and clean the data
- Save processed files in the data directory
- Generate extraction reports
