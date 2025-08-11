# Northern Regional Load Dispatch Centre (NRLDC) Data Extractor
A Python script for automatically extracting and processing DSM data from the Northern Regional Load Dispatch Centre.

## 🎯 Features
- **Automated Web Scraping**: Scrapes NRLDC website for DSM data
- **Multi-format Support**: Handles Excel (.xls, .xlsx) files
- **Intelligent File Tracking**: Tracks file changes using MD5 hashing
- **Multi-sheet Processing**: Processes Excel files with multiple sheets
- **Automated Scheduling**: Runs weekly updates automatically
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Data Cleaning**: Removes empty rows/columns and cleans data

## 📋 Prerequisites
- Python 3.8 or higher
- Internet connection to access NRLDC website
- Required Python packages (see requirements_nrldc.txt)

## 🚀 Installation
1. **Navigate to the NRLDC scripts directory**:
   ```bash
   cd dsm_data/NRLDC/scripts
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements_nrldc.txt
   ```

3. **Verify installation**:
   ```bash
   python dsm_extractor.py --help
   ```

## 📖 Usage

### Manual Update
Run a one-time update to extract current data:
```bash
python dsm_extractor.py --update
```

### Automated Scheduling
Start the automated scheduler for weekly updates:
```bash
python dsm_extractor.py --schedule
```

### Help
Show usage information:
```bash
python dsm_extractor.py --help
```

## 📁 Output Structure

The script creates the following directory structure:

```
dsm_data/
├── NRLDC/                      # Northern Regional Load Dispatch Centre data
│   ├── scripts/                # Script files
│   │   ├── dsm_extractor.py
│   │   ├── requirements_nrldc.txt
│   │   └── README_NRLDC.md
│   └── *.xlsx                  # Processed Excel files
├── ERLDC/                      # Eastern Regional Load Dispatch Centre data
└── WRPC/                       # Western Regional Power Committee data
```

## ⚙️ Configuration

### Website URLs
- **Base URL**: https://nrldc.in
- **DSM Data**: Various DSM data sources

### Data Categories
The script categorizes files into:
- **DSM**: DSM data files
- **EXCEL**: General Excel data files
- **OTHER**: Miscellaneous files

### Scheduling
- **Weekly**: Every Monday at 9:00 AM
- **Daily**: Every day at 9:00 AM (when scheduler is running)

## 🔍 How It Works

1. **Website Scraping**: Accesses NRLDC website and searches for DSM files
2. **File Discovery**: Identifies Excel files in DSM sections
3. **Change Detection**: Compares file hashes to detect updates
4. **Download**: Downloads new or changed files
5. **Processing**: Extracts data from all sheets
6. **Data Cleaning**: Removes empty rows/columns and cleans data
7. **Output**: Saves processed data as Excel files with multiple sheets

## 📊 Data Processing

### Excel File Processing
- Reads all sheets from Excel files
- Cleans column names and removes empty data
- Preserves original sheet structure
- Handles both .xls and .xlsx formats

## 🔧 File Types Supported

### Input Formats
- **Excel Files**: .xls and .xlsx formats

### Output Format
- **Excel Files**: .xlsx format with multiple sheets
- **Organized Structure**: Files saved to appropriate regional directories

## 🚨 Error Handling

- **Network Errors**: Retries and continues with other files
- **Corrupted Files**: Logs errors and skips problematic files
- **Encoding Issues**: Handles various character encodings
- **Missing Files**: Gracefully handles 404 errors

## 📝 Logging

The script provides detailed logging:
- **File Discovery**: Shows which files were found
- **Download Progress**: Tracks download status
- **Processing Details**: Shows data cleaning and processing steps
- **Error Reporting**: Detailed error messages for troubleshooting

## 🔄 Automation

### Scheduled Updates
- **Weekly Schedule**: Every Monday at 9:00 AM
- **Daily Check**: Every day at 9:00 AM when running
- **Change Detection**: Only processes new or changed files
- **File Tracking**: Maintains history of processed files

### Manual Updates
- **One-time Processing**: Run `--update` for immediate processing
- **Selective Processing**: Can process specific files or all files
- **Force Processing**: Can override change detection if needed

## 📊 Data Organization

### Regional Classification
- **NRLDC Data**: All NRLDC files are saved to `dsm_data/NRLDC/`
- **Consistent Naming**: Files are named with timestamps for uniqueness
- **Structured Output**: Each file type is processed appropriately

### File Naming Convention
- **Original Name**: Preserved from source
- **Timestamp**: Added for uniqueness
- **Processed Suffix**: `_processed.xlsx` for output files

## 🔍 Troubleshooting

### Common Issues
1. **Network Timeout**: Increase timeout values in configuration
2. **File Not Found**: Check if URLs are still valid
3. **Encoding Errors**: Script handles most encoding issues automatically
4. **Permission Errors**: Ensure write permissions to output directories

### Debug Mode
Enable debug logging by modifying the logging level in the script:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## 📞 Support

For issues or questions:
1. Check the log files for detailed error messages
2. Verify network connectivity to NRLDC website
3. Ensure all dependencies are installed correctly
4. Check file permissions in output directories

## 🔗 Related Scripts

This script works alongside other regional power committee extractors:
- **ERPC Extractor**: Eastern Regional Power Committee
- **WRPC Extractor**: Western Regional Power Committee

## 📄 License

This script is provided as-is for data extraction purposes. Please ensure compliance with NRLDC website terms of service.
