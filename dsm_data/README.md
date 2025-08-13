# DSM Data Analysis Project

A comprehensive data analysis project for Demand Side Management (DSM) data from multiple Regional Power Committees in India.

## 🏢 Regional Power Committees

This project covers data from three major Regional Power Committees:

### 1. **WRPC** - Western Regional Power Committee
- **Location**: Mumbai, Maharashtra
- **Coverage**: Western India (Maharashtra, Gujarat, Madhya Pradesh, etc.)
- **Data**: DSM financial and operational metrics

### 2. **ERLDC** - Eastern Regional Load Dispatch Centre
- **Location**: Kolkata, West Bengal
- **Coverage**: Eastern India (West Bengal, Bihar, Jharkhand, etc.)
- **Data**: Power generation and load dispatch data

### 3. **NRLDC** - Northern Regional Load Dispatch Centre
- **Location**: Delhi
- **Coverage**: Northern India (Delhi, Haryana, Punjab, etc.)
- **Data**: Northern region power management data

## 📁 Project Structure

```
dsm_data/
├── README.md                 # This file
├── cron_setup.md            # Automated data collection setup
├── WRPC/                    # Western region scripts
│   ├── data/               # WRPC data directory (created when needed)
│   └── scripts/
│       ├── wrpc_extractor.py
│       ├── requirements_wrpc.txt
│       └── README.md
├── ERLDC/                   # Eastern region scripts
│   └── scripts/
│       ├── erpc_extractor.py
│       ├── requirements_erpc.txt
│       └── README_ERPC.md
└── NRLDC/                   # Northern region scripts
    └── scripts/
        ├── dsm_extractor.py
        ├── requirements_nrldc.txt
        └── README_NRLDC.md
```

## 📊 Available Data

### WRPC Data (Western Region)
- **Ready for new data collection**
- **Will process CSV files from WRPC website**
- **Generates comprehensive analysis reports**
- **Supports multiple power plants and constituents**

## 🛠️ Usage

### For WRPC Data
```bash
cd dsm_data/WRPC/scripts
pip install -r requirements_wrpc.txt
python wrpc_extractor.py
```

### For ERLDC Data
```bash
cd dsm_data/ERLDC/scripts
pip install -r requirements_erpc.txt
python erpc_extractor.py
```

### For NRLDC Data
```bash
cd dsm_data/NRLDC/scripts
pip install -r requirements_nrldc.txt
python dsm_extractor.py
```

## 📈 Data Analysis

Each extractor provides:
- **Individual CSV files** for each constituent
- **Summary reports** with key metrics
- **Analysis reports** with insights
- **Financial calculations** and deviations
- **Time-based trends** and patterns

## 🔧 Features

- **🌐 Web Download**: Attempts to fetch fresh data from official websites
- **📊 Data Processing**: Comprehensive data validation and analysis
- **📈 Analytics**: Detailed insights and performance metrics
- **🔄 Automation**: Can be scheduled for regular data collection
- **📋 Validation**: Ensures data quality and structure

## 📋 Data Fields

Common fields across all regions:
- **Date & Time**: Timestamp information
- **Power Generation**: Actual vs Scheduled MWH
- **Frequency**: Grid frequency measurements
- **Deviations**: Calculated deviations and percentages
- **Financial Data**: DSM amounts, rates, and charges
- **Performance Metrics**: Efficiency and compliance data

## 🔍 Troubleshooting

### Common Issues
1. **No Data Found**: Check if source files are available
2. **Download Failures**: Websites may require authentication
3. **Processing Errors**: Verify file formats and structure

### Solutions
- Use manual download instructions provided by extractors
- Check file permissions and dependencies
- Verify data source availability

## 📞 Support

For issues with specific regions:
- **WRPC**: Check `WRPC/scripts/README.md`
- **ERLDC**: Check `ERLDC/scripts/README_ERPC.md`
- **NRLDC**: Check `NRLDC/scripts/README_NRLDC.md`

## 📄 License

This project is designed for data analysis and research purposes related to power sector management in India.

## 🎯 Purpose

This project aims to:
- Provide comprehensive DSM data analysis
- Enable power sector performance monitoring
- Support regulatory compliance analysis
- Facilitate research and policy development
- Improve power grid efficiency understanding
