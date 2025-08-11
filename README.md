# 🚀 Automated DSA Data Extraction System

A Python-based automation system for extracting and processing weekly DSA (Deviation Settlement Account) data from government websites.

## 📋 Overview

This system automatically:
- 🔍 **Discovers** new weekly data from government websites
- 📥 **Downloads** Excel files with DSA data
- 🔄 **Processes** data into organized Excel files
- 📊 **Organizes** files by week with unique naming
- ⏰ **Monitors** continuously for updates

## 🎯 Features

### ✅ **Fully Automated**
- Automatic week detection using regex patterns
- Continuous monitoring every 6 hours
- Smart change detection using file hashing
- Automatic file processing and organization

### 📊 **Data Processing**
- Extracts 16+ sheets from each Excel file
- Removes duplicate records automatically
- Maintains original data structure
- Creates unique filenames per week

### 🔄 **Update Management**
- Detects new weeks automatically
- Updates existing week data when changes occur
- Maintains data integrity with deduplication
- Comprehensive logging and tracking

## 📁 File Structure

```
Pythonscriptforextracting/
├── hexa_fixed.py                    # Main automation script
├── requirements.txt                 # Python dependencies
├── hexa_updates.log                # Detailed activity logs
├── Supporting_files_*.xlsx         # Extracted weekly data files
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Run Manual Update**
```bash
python hexa_fixed.py --update
```

### 3. **Start Automation**
```bash
python hexa_fixed.py --schedule
```

## 📊 Output Files

### **File Naming Convention**
- `Supporting_files_070725-130725(WK-15).xlsx`
- `Supporting_files_210725-270725(WK-17).xlsx`

### **Data Structure**
Each Excel file contains 16 sheets:
- `DC_Stations` - Station data
- `Solar_availability` - Solar availability data
- `Drl_Sch_States` - State schedule data
- `Act_Inj_Gen_Stations` - Generation station data
- `Act_Drl_States` - State data
- `Frequency` - Frequency data
- `GS_Stations` - GS station data
- `Deviation_Charges` - Deviation charges
- `Normal_Rate` - Normal rate data
- `Contract_Rate` - Contract rate data
- And 6 more sheets...

## ⚙️ Configuration

### **Automation Schedule**
- **Every Monday at 9:00 AM** - Weekly check for new data
- **Daily at 9:00 AM** - Immediate updates when started
- **Manual updates** - Run anytime with `python hexa_fixed.py --update`

### **Data Sources**
- Government website: `http://164.100.60.165/comm/dsa.html`
- Multiple financial years: 2021-22, 2022-23, 2023-24
- Supporting files for each week

## 📝 Usage Examples

### **Check Current Status**
```bash
python hexa_fixed.py --update
```

### **Start Continuous Monitoring**
```bash
python hexa_fixed.py --schedule
```

### **View Logs**
```bash
tail -f hexa_updates.log
```

## 🔧 Technical Details

### **Key Functions**
- `scrape_government_website()` - Discovers weeks and files
- `download_and_process_file()` - Downloads and processes Excel files
- `process_weekly_dataframe()` - Creates organized Excel output
- `scheduled_update()` - Main automation loop

### **Change Detection**
- Uses MD5 hashing to detect file changes
- Tracks file modifications in `file_tracking.json`
- Prevents unnecessary downloads

### **Error Handling**
- Robust error recovery for corrupted files
- Automatic retry mechanisms
- Comprehensive logging

## 📈 Monitoring

### **Log File: `hexa_updates.log`**
- Discovery logs: `📅 Discovered week: 210725-270725(WK-17)`
- Processing logs: `🎯 Found supporting file: Supporting_files.xls`
- Update logs: `✅ Successfully updated Excel file`
- Error logs: `❌ Failed to process file`

### **File Tracking: `file_tracking.json`**
- File hashes for change detection
- Last update timestamps
- Processing history

## 🎯 Use Cases

### **Scenario 1: New Week Published**
1. Government publishes Week 18 data
2. Script detects new week (Monday 9:00 AM check)
3. Downloads `Supporting_files.xls` for Week 18
4. Creates `Supporting_files_280725-030825(WK-18).xlsx`
5. Logs successful processing

### **Scenario 2: Existing Week Updated**
1. Government updates Week 15 data
2. Script detects hash change
3. Downloads updated file
4. Replaces existing `Supporting_files_070725-130725(WK-15).xlsx`
5. Logs update completion

## 🔒 Security & Performance

### **Security Features**
- Secure file handling
- Error logging without sensitive data
- Robust authentication handling

### **Performance Optimizations**
- Efficient file processing
- Smart change detection
- Minimal network usage

## 📞 Support

### **Troubleshooting**
- Check `hexa_updates.log` for detailed error information
- Verify internet connectivity
- Ensure proper file permissions

### **Common Issues**
1. **Authentication Failed** - Check network connectivity
2. **File Corruption** - Script automatically recreates files
3. **No New Data** - Normal when no updates are available

## 🚀 Future Enhancements

- [ ] Email notifications for new data
- [ ] Web dashboard for monitoring
- [ ] API endpoints for data access
- [ ] Advanced analytics integration

## 📄 License

This project is developed for Hexa Climate internal use.

## 👨‍💻 Author

**Kushal Goyal** - `kushal.goyal@hexaclimate.com`

---

**🎉 Your automated DSA data extraction system is ready to use!**
