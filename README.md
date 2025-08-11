# Regional Power Committee Data Extraction System

A comprehensive Python-based data extraction system for automatically collecting and processing DSM (Daily Scheduling and Accounting) data from various Regional Power Committees across India.

## 🎯 Overview

This system provides automated data extraction from three major regional power committees:
- **ERLDC**: Eastern Regional Load Dispatch Centre
- **NRLDC**: Northern Regional Load Dispatch Centre  
- **WRPC**: Western Regional Power Committee

## 📁 Project Structure

```
Script/
├── dsm_data/                    # Main data directory
│   ├── ERLDC/                   # Eastern Regional Load Dispatch Centre
│   │   ├── scripts/             # ERLDC extraction scripts
│   │   │   ├── erpc_extractor.py
│   │   │   ├── requirements_erpc.txt
│   │   │   └── README_ERPC.md
│   │   └── data/                # ERLDC processed data files
│   ├── NRLDC/                   # Northern Regional Load Dispatch Centre
│   │   ├── scripts/             # NRLDC extraction scripts
│   │   │   ├── dsm_extractor.py
│   │   │   ├── requirements_nrldc.txt
│   │   │   └── README_NRLDC.md
│   │   └── data/                # NRLDC processed data files
│   └── WRPC/                    # Western Regional Power Committee
│       ├── scripts/             # WRPC extraction scripts
│       │   ├── wrpc_extractor.py
│       │   ├── requirements_wrpc.txt
│       │   └── README_WRPC.md
│       └── data/                # WRPC processed data files
├── README.md                    # This file - main documentation
├── requirements.txt             # Main project dependencies
├── .gitignore                   # Git ignore rules
└── .git/                        # Git repository
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Regional Extractors

**For Eastern Region (ERLDC):**
```bash
cd dsm_data/ERLDC/scripts
pip install -r requirements_erpc.txt
python erpc_extractor.py --update
```

**For Northern Region (NRLDC):**
```bash
cd dsm_data/NRLDC/scripts
pip install -r requirements_nrldc.txt
python dsm_extractor.py --update
```

**For Western Region (WRPC):**
```bash
cd dsm_data/WRPC/scripts
pip install -r requirements_wrpc.txt
python wrpc_extractor.py --update
```

## 🎯 Features

### Core Capabilities
- **Automated Web Scraping**: Intelligent scraping of regional power committee websites
- **Multi-format Support**: Handles Excel (.xls, .xlsx), ZIP, and CSV files
- **Intelligent File Tracking**: MD5 hash-based change detection
- **Multi-sheet Processing**: Processes Excel files with multiple sheets
- **Automated Scheduling**: Weekly automated updates
- **Comprehensive Logging**: Detailed operation tracking
- **Data Cleaning**: Automatic data validation and cleaning

### Regional Specific Features

#### ERLDC (Eastern Region)
- Extracts DSM Blockwise Data from ERPC website
- Processes multiple Excel sheets with power station data
- Categorizes data by Eastern region stations
- Handles weekly data updates

#### NRLDC (Northern Region)
- Extracts DSM data from Northern region sources
- Processes Excel files with power scheduling data
- Organizes data by Northern region stations
- Automated weekly data collection

#### WRPC (Western Region)
- Extracts DSM UI Account data from WRPC website
- Processes ZIP archives containing CSV files
- Handles complex multi-station data structures
- Extracts 95+ power station datasets

## 📊 Data Organization

### File Structure
Each regional folder contains:
- **Scripts**: Python extractors, requirements, and documentation
- **Data**: Processed Excel files with multiple sheets
- **Logs**: Operation logs (generated during execution)

### Data Categories
- **DSM Data**: Daily Scheduling and Accounting information
- **Power Station Data**: Individual station performance metrics
- **Regional Exchanges**: Inter-regional power transfer data
- **Scheduling Data**: Power scheduling and deviation information

## ⚙️ Configuration

### Scheduling
- **Weekly Updates**: Every Monday at 9:00 AM
- **Daily Checks**: Every day at 9:00 AM (when running)
- **Manual Updates**: On-demand execution with `--update` flag

### File Tracking
- **Change Detection**: MD5 hash comparison
- **Duplicate Prevention**: Automatic duplicate detection
- **Version Control**: Timestamped file naming

## 🔧 Technical Details

### Supported File Formats
- **Input**: Excel (.xls, .xlsx), ZIP archives, CSV files
- **Output**: Excel (.xlsx) with multiple sheets
- **Logs**: Text-based logging with timestamps

### Error Handling
- **Network Resilience**: Automatic retry mechanisms
- **File Corruption**: Graceful handling of corrupted files
- **Encoding Issues**: Multi-encoding support
- **Missing Data**: Robust error recovery

## 📝 Usage Examples

### Manual Data Extraction
```bash
# Extract ERLDC data
cd dsm_data/ERLDC/scripts
python erpc_extractor.py --update

# Extract NRLDC data  
cd dsm_data/NRLDC/scripts
python dsm_extractor.py --update

# Extract WRPC data
cd dsm_data/WRPC/scripts
python wrpc_extractor.py --update
```

### Automated Scheduling
```bash
# Start automated scheduler for any region
python [extractor_name].py --schedule
```

### Help and Documentation
```bash
# Get help for any extractor
python [extractor_name].py --help
```

## 🔍 Monitoring and Logs

### Log Files
- Each extractor generates detailed logs
- Logs include file discovery, processing, and error information
- Timestamped entries for easy tracking

### Data Validation
- Automatic data quality checks
- Empty row/column removal
- Column name cleaning and standardization
- Data type validation

## 🚨 Troubleshooting

### Common Issues
1. **Network Connectivity**: Check internet connection
2. **File Permissions**: Ensure write access to data directories
3. **Dependencies**: Verify all Python packages are installed
4. **Website Changes**: Regional websites may update their structure

### Debug Mode
Enable detailed logging by modifying the logging level in each script:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## 📞 Support

For issues or questions:
1. Check the log files for detailed error messages
2. Verify network connectivity to regional websites
3. Ensure all dependencies are installed correctly
4. Check file permissions in data directories

## 🔗 Related Documentation

- **ERLDC**: See `dsm_data/ERLDC/scripts/README_ERPC.md`
- **NRLDC**: See `dsm_data/NRLDC/scripts/README_NRLDC.md`
- **WRPC**: See `dsm_data/WRPC/scripts/README_WRPC.md`

## 📄 License

This system is provided as-is for data extraction purposes. Please ensure compliance with respective regional power committee website terms of service.

## 🎯 Future Enhancements

- Additional regional power committees
- Enhanced data visualization
- API integration capabilities
- Real-time data streaming
- Advanced analytics features
