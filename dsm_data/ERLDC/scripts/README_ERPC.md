# Eastern Regional Power Committee (ERPC) Data Extractor
A Python script for automatically extracting and processing DSA (Daily Scheduling and Accounting) data from the Eastern Regional Power Committee website.
## 🎯 Features
- **Automated Web Scraping**: Scrapes ERPC website for DSA-related files
- **Excel-only Support**: Handles Excel (.xls, .xlsx) files only
- **Intelligent File Tracking**: Tracks file changes using MD5 hashing
- **Multi-sheet Processing**: Processes Excel files with multiple sheets
- **Automated Scheduling**: Runs weekly updates automatically
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Data Cleaning**: Removes empty rows/columns and cleans data
## 📋 Prerequisites
- Python 3.8 or higher
- Internet connection to access ERPC website
- Required Python packages (see requirements_erpc.txt)
## 🚀 Installation
1. **Clone or download the script**:
   ```bash
   # If you have the script files
   cd /path/to/script/directory
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements_erpc.txt
   ```
3. **Verify installation**:
   ```bash
   python erpc_extractor.py --help
   ```

## 📖 Usage

### Run Data Extraction
Extract current data from ERPC website:
```bash
python erpc_extractor.py
```

### Help
Show usage information:
```bash
python erpc_extractor.py --help
```

## 📁 Output Structure

The script creates the following directory structure:

```
dsm_data/                     # Main output directory
├── ERLDC/                    # Eastern Regional Load Dispatch Centre data
│   ├── erldc_file1_processed.xlsx
│   └── erldc_file2_processed.xlsx
├── NRLDC/                    # Northern Regional Load Dispatch Centre data
│   ├── nrldc_file1_processed.xlsx
│   └── nrldc_file2_processed.xlsx
├── file1_processed.xlsx      # General processed Excel files
└── file2_processed.xlsx

temp_erpc/                    # Temporary download directory
├── temp_file1.xls
└── temp_file2.xlsx

erpc_file_tracking.json       # File change tracking data
erpc_extractor.log           # Detailed execution logs
```

### File Categorization
The script automatically categorizes files into ERLDC or NRLDC directories based on:
- **Filename analysis**: Checks for "erldc", "eastern", "nrldc", or "northern" in the filename
- **Content analysis**: Examines column names and data content for regional indicators
- **Default location**: Files without clear indicators are saved to the main directory

## ⚙️ Configuration

### Website URLs
- **Base URL**: http://erpc.gov.in
- **DSA Page**: http://erpc.gov.in/dsa.html

### Data Categories
The script categorizes files into:
- **DSA**: Daily Scheduling and Accounting Excel files
- **EXCEL**: General Excel data files
- **OTHER**: Miscellaneous Excel files



## 🔍 How It Works

1. **Website Scraping**: Accesses ERPC website and searches for DSA-related files
2. **File Discovery**: Identifies Excel files in DSA sections
3. **Change Detection**: Compares file hashes to detect updates
4. **Download**: Downloads new or changed files
5. **Processing**: Extracts data from Excel files (all sheets)
6. **Data Cleaning**: Removes empty rows/columns and cleans data
7. **Output**: Saves processed data as Excel files with multiple sheets

## 📊 Data Processing

### Excel File Processing
- Reads all sheets from Excel files
- Cleans column names and removes empty data
- Preserves original sheet structure
- Handles both .xls and .xlsx formats

### File Tracking
- Uses MD5 hashing to detect file changes
- Tracks processing history in JSON format
- Prevents duplicate processing of unchanged files

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Check internet connection
   - Verify ERPC website accessibility
   - Check firewall settings

2. **File Download Issues**:
   - Check available disk space
   - Verify write permissions in output directory
   - Check file size limits

3. **Processing Errors**:
   - Ensure all dependencies are installed
   - Check Excel file format compatibility
   - Review log files for specific error messages

### Log Files
- **erpc_extractor.log**: Contains detailed execution logs
- Check for ERROR level messages for troubleshooting
- INFO level messages show normal operation

## 🔧 Customization

### Modifying Data Types
Edit the `DATA_TYPES` dictionary in the script to change file categorization:

```python
DATA_TYPES = {
    'DSA': ['dsa', 'daily', 'scheduling', 'accounting', 'supporting'],
    'REPORT': ['report', 'summary', 'analysis'],
    'NOTIFICATION': ['notification', 'circular', 'order'],
    'OTHER': ['other', 'misc']
}
```



## 📈 Monitoring

### Log Monitoring
Monitor the log file for:
- File discovery and download status
- Processing progress and errors

### File Tracking
Check `erpc_file_tracking.json` for:
- List of processed files
- Last processing timestamps
- File change history

## 🔒 Security Considerations

- Script only downloads publicly available files
- No authentication required for ERPC website
- Temporary files are automatically cleaned up
- No sensitive data is stored or transmitted

## 📞 Support

For issues or questions:
1. Check the log files for error messages
2. Verify website accessibility
3. Ensure all dependencies are properly installed
4. Review this README for troubleshooting steps

## 📄 License

This script is provided as-is for educational and research purposes. Please ensure compliance with ERPC website terms of service when using this tool.

---

**Note**: This script is designed to work with the current ERPC website structure. Website changes may require script updates.
