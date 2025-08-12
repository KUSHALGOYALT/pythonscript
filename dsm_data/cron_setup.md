# Cron Setup Guide for DSM Data Extraction

## Overview
This guide shows how to set up cron jobs to automatically run the data extraction scripts at scheduled times.

## Scripts Available
- **ERLDC**: `dsm_data/ERLDC/scripts/erpc_extractor.py`
- **NRLDC**: `dsm_data/NRLDC/scripts/dsm_extractor.py`
- **WRPC**: `dsm_data/WRPC/scripts/wrpc_extractor.py`

## Cron Job Examples

### Run all scripts daily at 9:00 AM
```bash
0 9 * * * cd /path/to/your/project && python dsm_data/ERLDC/scripts/erpc_extractor.py
0 9 * * * cd /path/to/your/project && python dsm_data/NRLDC/scripts/dsm_extractor.py
0 9 * * * cd /path/to/your/project && python dsm_data/WRPC/scripts/wrpc_extractor.py
```

### Run weekly on Monday at 9:00 AM
```bash
0 9 * * 1 cd /path/to/your/project && python dsm_data/ERLDC/scripts/erpc_extractor.py
0 9 * * 1 cd /path/to/your/project && python dsm_data/NRLDC/scripts/dsm_extractor.py
0 9 * * 1 cd /path/to/your/project && python dsm_data/WRPC/scripts/wrpc_extractor.py
```

### Run every 6 hours
```bash
0 */6 * * * cd /path/to/your/project && python dsm_data/ERLDC/scripts/erpc_extractor.py
0 */6 * * * cd /path/to/your/project && python dsm_data/NRLDC/scripts/dsm_extractor.py
0 */6 * * * cd /path/to/your/project && python dsm_data/WRPC/scripts/wrpc_extractor.py
```

## How to Set Up Cron Jobs

### 1. Open crontab editor
```bash
crontab -e
```

### 2. Add your cron jobs
Add the desired cron job lines to the file.

### 3. Save and exit
The cron jobs will be automatically activated.

## Cron Format
```
minute hour day month day_of_week command
```

### Examples:
- `0 9 * * *` = Every day at 9:00 AM
- `0 9 * * 1` = Every Monday at 9:00 AM
- `0 */6 * * *` = Every 6 hours
- `0 9,15 * * *` = Every day at 9:00 AM and 3:00 PM

## Important Notes

1. **Replace `/path/to/your/project`** with the actual path to your project directory
2. **Ensure Python environment** is properly set up with all required dependencies
3. **Check logs** in the respective script directories for any errors
4. **Test manually first** by running the scripts directly before setting up cron

## Log Files
Each script creates its own log file:
- `erpc_extractor.log` (ERLDC)
- `dsm_extractor.log` (NRLDC)
- `wrpc_extractor.log` (WRPC)

## Manual Testing
Before setting up cron, test the scripts manually:
```bash
cd /path/to/your/project
python dsm_data/ERLDC/scripts/erpc_extractor.py
python dsm_data/NRLDC/scripts/dsm_extractor.py
python dsm_data/WRPC/scripts/wrpc_extractor.py
```
