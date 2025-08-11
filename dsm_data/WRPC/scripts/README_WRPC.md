# Western Regional Power Committee (WRPC) Data Extractor
A Python script for automatically extracting and processing DSM UI Account data from the Western Regional Power Committee website.

## 🎯 Features
- **Automated Web Scraping**: Scrapes WRPC website for DSM UI Account files
- **Multi-format Support**: Handles Excel (.xls, .xlsx), ZIP, and CSV files
- **ZIP File Processing**: Extracts and processes CSV files from ZIP archives
- **Intelligent File Tracking**: Tracks file changes using MD5 hashing
- **Multi-sheet Processing**: Processes Excel files with multiple sheets
- **Automated Scheduling**: Runs weekly updates automatically
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Data Cleaning**: Removes empty rows/columns and cleans data

## 📋 Prerequisites
- Python 3.8 or higher
- Internet connection to access WRPC website
- Required Python packages (see requirements_wrpc.txt)

## 🚀 Installation
1. **Clone or download the script**:
   ```bash
   # If you have the script files
   cd /path/to/script/directory
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements_wrpc.txt
   ```

3. **Verify installation**:
   ```bash
   python wrpc_extractor.py --help
   ```

## 📖 Usage

### Manual Update
Run a one-time update to extract current data:
```bash
python wrpc_extractor.py --update
```

### Automated Scheduling
Start the automated scheduler for weekly updates:
```bash
python wrpc_extractor.py --schedule
```

### Help
Show usage information:
```bash
python wrpc_extractor.py --help
```

## 📁 Output Structure

The script creates the following directory structure:

```
dsm_data/                     # Main output directory
├── WRPC/                     # Western Regional Power Committee data
│   ├── wrpc_file1_processed.xlsx
│   └── wrpc_file2_processed.xlsx
├── ERLDC/                    # Eastern Regional Load Dispatch Centre data
├── NRLDC/                    # Northern Regional Load Dispatch Centre data
└── *.xlsx                   # General processed Excel files

temp_wrpc/                    # Temporary download directory
├── temp_file1.zip
└── temp_file2.xlsx

wrpc_file_tracking.json       # File change tracking data
wrpc_extractor.log           # Detailed execution logs
```

## ⚙️ Configuration

### Website URLs
- **Base URL**: https://www.wrpc.gov.in
- **DSM UI Account Page**: https://www.wrpc.gov.in/menu/DSMUI%20Account%20_342
- **Sample File**: https://www.wrpc.gov.in/allfile/070820251025026574sum4c.zip

### Data Categories
The script categorizes files into:
- **DSM**: DSM UI Account files
- **EXCEL**: General Excel data files
- **OTHER**: Miscellaneous files

### Scheduling
- **Weekly**: Every Monday at 9:00 AM
- **Daily**: Every day at 9:00 AM (when scheduler is running)

## 🔍 How It Works

1. **Website Scraping**: Accesses WRPC website and searches for DSM UI Account files
2. **File Discovery**: Identifies Excel, ZIP, and CSV files in DSM sections
3. **Change Detection**: Compares file hashes to detect updates
4. **Download**: Downloads new or changed files
5. **Processing**: 
   - **ZIP Files**: Extracts CSV files from ZIP archives
   - **Excel Files**: Extracts data from all sheets
   - **CSV Files**: Reads directly
6. **Data Cleaning**: Removes empty rows/columns and cleans data
7. **Output**: Saves processed data as Excel files with multiple sheets

## 📊 Data Processing

### ZIP File Processing
- Extracts all CSV files from ZIP archives
- Processes each CSV file individually
- Creates separate sheets for each CSV file
- Handles encoding issues gracefully

### Excel File Processing
- Reads all sheets from Excel files
- Cleans column names and removes empty data
- Preserves original sheet structure
- Handles both .xls and .xlsx formats

### CSV File Processing
- Reads CSV files directly
- Handles various encodings
- Cleans data and removes empty rows/columns

## 🔧 File Types Supported

### Input Formats
- **ZIP Archives**: Contains CSV files (e.g., `070820251025026574sum4c.zip`)
- **Excel Files**: .xls and .xlsx formats
- **CSV Files**: Direct CSV downloads

### Output Format
- **Excel Files**: .xlsx format with multiple sheets
- **Organized Structure**: Files saved to appropriate regional directories

## 📈 Sample Data Structure

Based on the provided sample file (`070820251025026574sum4c.zip`), the script can process:
- **ACBIL_DSM-2024_Data.csv**: Contains DSM data for ACBIL
- **Multiple CSV files**: Each CSV becomes a separate sheet in the output Excel file

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
- **WRPC Data**: All WRPC files are saved to `dsm_data/WRPC/`
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
2. Verify network connectivity to WRPC website
3. Ensure all dependencies are installed correctly
4. Check file permissions in output directories

## 🔗 Related Scripts

This script works alongside other regional power committee extractors:
- **ERPC Extractor**: Eastern Regional Power Committee
- **DSM Extractor**: General DSM data processing
- **NRLDC Extractor**: Northern Regional Load Dispatch Centre

## 📄 License

This script is provided as-is for data extraction purposes. Please ensure compliance with WRPC website terms of service.
