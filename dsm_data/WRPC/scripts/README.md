# WRPC Data Extractor

A comprehensive tool for extracting and analyzing DSM (Demand Side Management) data from the Western Regional Power Committee (WRPC).

## 🚀 Features

- **🌐 Web Download**: Attempts to download fresh data from WRPC website
- **📊 Data Processing**: Processes CSV files with comprehensive analytics
- **📈 Analysis**: Generates detailed reports and insights
- **🔄 Dynamic**: Automatically discovers and processes files
- **📋 Validation**: Ensures data quality and structure

## 📁 Project Structure

```
dsm_data/WRPC/
├── scripts/
│   ├── wrpc_extractor.py      # Main extractor script
│   ├── requirements_wrpc.txt  # Python dependencies
│   └── README.md             # This file
└── data/                     # Processed data and reports
    ├── *.csv                 # Individual constituent data
    ├── WRPC_Summary_Report.csv
    └── WRPC_Analysis_Report.txt
```

## 🛠️ Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_wrpc.txt
   ```

2. **Run the Extractor**:
   ```bash
   cd scripts
   python wrpc_extractor.py
   ```

## 📊 Available Data

### Current Dataset (July 21-27, 2025)
- **25 Power Plants** analyzed
- **16,800 Total Records** processed
- **₹169,539,983.61** total DSM amount
- **7 Days** of continuous data
- **96 Time Blocks** per day (15-minute intervals)

### Key Metrics
- Actual vs Scheduled MWH
- Frequency measurements (Hz)
- Deviation calculations
- DSM Payable/Receivable amounts
- Rate information (p/Kwh)

## 🏆 Top Performers

### By DSM Amount
1. **GADARWARA-I**: ₹16,764,556.90
2. **SOLAPUR**: ₹12,632,845.18
3. **VSTPS I**: ₹11,946,147.07

### By Deviation
1. **TAPS-II**: 1,660.05 MWH
2. **SASAN**: 1,297.51 MWH
3. **KAPS**: 972.21 MWH

## 🔧 How It Works

1. **File Discovery**: Automatically finds CSV files
2. **Data Validation**: Checks file structure and content
3. **Processing**: Converts data types and calculates metrics
4. **Analysis**: Generates insights and summary reports
5. **Output**: Creates processed files in `../data/`

## 📋 Output Files

- **Individual CSV Files**: One per constituent with enhanced data
- **Summary Report**: Comprehensive overview of all constituents
- **Analysis Report**: Human-readable insights and statistics

## 🌐 Web Download

The extractor can attempt to download fresh data from:
- **URL**: https://www.wrpc.gov.in/menu/DSMUI%20Account%20_342
- **Fallback**: Provides manual download instructions if automatic fails

## 📈 Data Analysis

Each constituent file includes:
- Power generation metrics
- Financial calculations
- Deviation analysis
- Time-based trends
- Performance indicators

## 🔍 Troubleshooting

### No Files Found
- Check if CSV files are in the correct directory
- Ensure files have proper structure
- Try manual download from WRPC website

### Download Issues
- Website may require authentication
- Use manual download instructions provided
- Contact WRPC for official access

## 📞 Support

For issues or questions:
1. Check the error messages in the console
2. Verify file structure and permissions
3. Ensure all dependencies are installed

## 📄 License

This tool is designed for data analysis and research purposes.
