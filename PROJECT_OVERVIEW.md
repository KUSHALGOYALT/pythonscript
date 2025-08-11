# Regional Power Committee Data Extraction System - Project Overview

## 🎯 System Architecture

This project implements a comprehensive data extraction system for collecting DSM (Daily Scheduling and Accounting) data from three major regional power committees in India. The system is designed with modularity, scalability, and maintainability in mind.

## 📊 System Components

### 1. **ERLDC (Eastern Regional Load Dispatch Centre)**
- **Purpose**: Extracts DSM Blockwise Data from Eastern region
- **Data Source**: https://erpc.gov.in
- **File Types**: Excel (.xlsx) files with multiple sheets
- **Data Content**: Power station data, scheduling information, deviation charges
- **Processing**: Multi-sheet Excel processing with data cleaning

### 2. **NRLDC (Northern Regional Load Dispatch Centre)**
- **Purpose**: Extracts DSM data from Northern region
- **Data Source**: Northern region power committee websites
- **File Types**: Excel (.xls, .xlsx) files
- **Data Content**: Power scheduling data, station performance metrics
- **Processing**: Excel file processing with regional categorization

### 3. **WRPC (Western Regional Power Committee)**
- **Purpose**: Extracts DSM UI Account data from Western region
- **Data Source**: https://www.wrpc.gov.in
- **File Types**: ZIP archives containing CSV files
- **Data Content**: 95+ power station datasets, regional exchanges
- **Processing**: ZIP extraction, CSV processing, multi-station data handling

## 🏗️ Directory Structure

```
Script/
├── dsm_data/                    # Main data repository
│   ├── ERLDC/                   # Eastern Regional Load Dispatch Centre
│   │   ├── scripts/             # ERLDC extraction system
│   │   │   ├── erpc_extractor.py      # Main extraction script
│   │   │   ├── requirements_erpc.txt  # Python dependencies
│   │   │   └── README_ERPC.md         # ERLDC documentation
│   │   └── data/                # ERLDC processed data
│   │       └── *.xlsx           # Processed Excel files
│   ├── NRLDC/                   # Northern Regional Load Dispatch Centre
│   │   ├── scripts/             # NRLDC extraction system
│   │   │   ├── dsm_extractor.py       # Main extraction script
│   │   │   ├── requirements_nrldc.txt # Python dependencies
│   │   │   └── README_NRLDC.md        # NRLDC documentation
│   │   └── data/                # NRLDC processed data
│   │       └── *.xlsx           # Processed Excel files
│   └── WRPC/                    # Western Regional Power Committee
│       ├── scripts/             # WRPC extraction system
│       │   ├── wrpc_extractor.py      # Main extraction script
│       │   ├── requirements_wrpc.txt  # Python dependencies
│       │   └── README_WRPC.md         # WRPC documentation
│       └── data/                # WRPC processed data
│           └── *.xlsx           # Processed Excel files
├── README.md                    # Main project documentation
├── PROJECT_OVERVIEW.md          # This file - system overview
├── requirements.txt             # Main project dependencies
├── .gitignore                   # Git ignore rules
└── .git/                        # Git repository
```

## 🔧 Technical Architecture

### Core Components

#### 1. **Web Scraping Engine**
- **Technology**: BeautifulSoup4, Requests
- **Functionality**: Intelligent website parsing and file discovery
- **Features**: Dynamic link discovery, subdirectory exploration
- **Error Handling**: Network resilience, timeout management

#### 2. **File Processing Engine**
- **Technology**: Pandas, OpenPyXL, XLRD
- **Functionality**: Multi-format file processing
- **Features**: Excel multi-sheet processing, ZIP extraction, CSV handling
- **Data Cleaning**: Empty row/column removal, column standardization

#### 3. **Change Detection System**
- **Technology**: MD5 hashing, JSON tracking
- **Functionality**: File change detection and version control
- **Features**: Duplicate prevention, incremental updates
- **Storage**: JSON-based tracking files

#### 4. **Scheduling System**
- **Technology**: Schedule library
- **Functionality**: Automated execution scheduling
- **Features**: Weekly updates, daily checks, manual triggers
- **Configuration**: Flexible scheduling options

### Data Flow Architecture

```
1. Website Discovery → 2. File Detection → 3. Change Check → 4. Download → 5. Process → 6. Save → 7. Log
```

#### Step-by-Step Process:
1. **Website Discovery**: Scrape regional power committee websites
2. **File Detection**: Identify relevant data files (Excel, ZIP, CSV)
3. **Change Check**: Compare file hashes with previous versions
4. **Download**: Download new or changed files
5. **Process**: Extract and clean data from files
6. **Save**: Save processed data to regional folders
7. **Log**: Record all operations for monitoring

## 📊 Data Processing Pipeline

### Input Processing
- **Excel Files**: Multi-sheet extraction with data validation
- **ZIP Archives**: Automatic extraction of contained files
- **CSV Files**: Direct processing with encoding handling
- **Data Validation**: Type checking, format validation

### Data Cleaning
- **Empty Data Removal**: Automatic removal of empty rows/columns
- **Column Standardization**: Consistent column naming
- **Data Type Conversion**: Proper data type assignment
- **Duplicate Detection**: Automatic duplicate removal

### Output Generation
- **Excel Files**: Multi-sheet Excel output with original structure
- **File Naming**: Timestamped naming for version control
- **Organization**: Regional folder structure for easy access
- **Metadata**: Processing information and timestamps

## 🔄 Automation Features

### Scheduling System
- **Weekly Updates**: Every Monday at 9:00 AM
- **Daily Checks**: Every day at 9:00 AM (when running)
- **Manual Triggers**: On-demand execution with `--update` flag
- **Flexible Configuration**: Customizable scheduling options

### Monitoring and Logging
- **Comprehensive Logging**: Detailed operation tracking
- **Error Reporting**: Structured error messages
- **Performance Metrics**: Processing time and file size tracking
- **Status Monitoring**: Real-time operation status

### Error Handling
- **Network Resilience**: Automatic retry mechanisms
- **File Corruption**: Graceful handling of corrupted files
- **Encoding Issues**: Multi-encoding support
- **Missing Data**: Robust error recovery

## 🎯 Regional Specific Features

### ERLDC (Eastern Region)
- **Website**: https://erpc.gov.in
- **Data Type**: DSM Blockwise Data
- **File Format**: Excel (.xlsx) with multiple sheets
- **Processing**: Eastern region station categorization
- **Output**: Organized Excel files with regional data

### NRLDC (Northern Region)
- **Website**: Northern region power committee sites
- **Data Type**: DSM scheduling data
- **File Format**: Excel (.xls, .xlsx)
- **Processing**: Northern region station categorization
- **Output**: Regional Excel files with scheduling data

### WRPC (Western Region)
- **Website**: https://www.wrpc.gov.in
- **Data Type**: DSM UI Account data
- **File Format**: ZIP archives containing CSV files
- **Processing**: 95+ power station datasets
- **Output**: Comprehensive Excel files with multi-station data

## 🔧 Configuration Management

### Environment Configuration
- **Base URLs**: Regional website URLs
- **File Patterns**: File naming and extension patterns
- **Processing Options**: Data cleaning and validation settings
- **Scheduling**: Update frequency and timing

### File Tracking
- **Hash Storage**: MD5 hashes for change detection
- **Version Control**: Timestamped file naming
- **History Tracking**: Processing history and metadata
- **Duplicate Prevention**: Automatic duplicate detection

## 📈 Performance Characteristics

### Processing Capacity
- **File Size**: Handles files up to 100MB+
- **Data Volume**: Processes thousands of data points
- **Concurrent Processing**: Sequential processing for stability
- **Memory Usage**: Efficient memory management

### Network Efficiency
- **Change Detection**: Only downloads changed files
- **Compression Support**: Handles compressed archives
- **Timeout Management**: Configurable network timeouts
- **Retry Logic**: Automatic retry for failed downloads

### Storage Optimization
- **Incremental Updates**: Only stores new/changed data
- **File Organization**: Regional folder structure
- **Cleanup**: Automatic temporary file cleanup
- **Version Control**: Timestamped file naming

## 🚀 Deployment and Usage

### Installation
```bash
# Clone repository
git clone [repository-url]
cd Script

# Install main dependencies
pip install -r requirements.txt

# Install regional dependencies
cd dsm_data/ERLDC/scripts && pip install -r requirements_erpc.txt
cd dsm_data/NRLDC/scripts && pip install -r requirements_nrldc.txt
cd dsm_data/WRPC/scripts && pip install -r requirements_wrpc.txt
```

### Usage Examples
```bash
# Manual extraction for each region
cd dsm_data/ERLDC/scripts && python erpc_extractor.py --update
cd dsm_data/NRLDC/scripts && python dsm_extractor.py --update
cd dsm_data/WRPC/scripts && python wrpc_extractor.py --update

# Automated scheduling
python [extractor_name].py --schedule
```

### Monitoring
```bash
# View logs
tail -f [extractor_name].log

# Check data files
ls -la dsm_data/[REGION]/data/

# Verify processing
python [extractor_name].py --help
```

## 🔮 Future Enhancements

### Planned Features
- **Additional Regions**: Support for more regional power committees
- **API Integration**: RESTful API for data access
- **Real-time Streaming**: Live data streaming capabilities
- **Advanced Analytics**: Built-in data analysis tools
- **Web Dashboard**: Web-based monitoring interface

### Technical Improvements
- **Parallel Processing**: Concurrent file processing
- **Database Integration**: SQL database for data storage
- **Cloud Deployment**: Cloud-based deployment options
- **Containerization**: Docker containerization
- **CI/CD Pipeline**: Automated testing and deployment

## 📞 Support and Maintenance

### Documentation
- **Regional READMEs**: Detailed documentation for each region
- **API Documentation**: Code documentation and examples
- **Troubleshooting Guides**: Common issues and solutions
- **Best Practices**: Usage guidelines and recommendations

### Maintenance
- **Regular Updates**: Dependency and security updates
- **Performance Monitoring**: System performance tracking
- **Error Tracking**: Comprehensive error logging and analysis
- **User Support**: Technical support and assistance

---

**This system provides a robust, scalable, and maintainable solution for automated data extraction from regional power committees across India.**
