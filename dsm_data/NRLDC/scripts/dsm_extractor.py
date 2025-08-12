#!/usr/bin/env python3
"""
DSM Blockwise Data Extractor for Northern Regional Power Committee (NRPC)
Extracts DSM data from NRPC website
"""

import requests
import pandas as pd
import os
import logging
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dsm_extractor.log'),
        logging.StreamHandler()
    ]
)

# Configuration
NRPC_BASE_URL = "http://164.100.60.165/comm/dsa.html"
DOWNLOAD_DIR = "dsm_data"
NRLDC_DIR = "dsm_data/NRLDC"

def setup_directories():
    """Create necessary directories"""
    for directory in [DOWNLOAD_DIR, NRLDC_DIR]:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Created directory: {directory}")

def get_latest_dsm_file_url():
    """Get the latest DSM file URL from NRPC website"""
    try:
        logging.info(f"Fetching NRPC website: {NRPC_BASE_URL}")
        
        # Fetch the main page
        response = requests.get(NRPC_BASE_URL, timeout=30)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the dropdown with week options
        week_options = []
        select_element = soup.find('select', {'name': 'wk'})
        
        if select_element:
            for option in select_element.find_all('option'):
                value = option.get('value')
                if value and 'WK-' in value:
                    week_options.append(value)
                    logging.info(f"Found week option: {value}")
        
        if week_options:
            # Look for the most recent 2021 data (since the URL should be 2021-22)
            # Filter for dates that end with '21' (year 2021)
            week_2021_options = [week for week in week_options if week.split('-')[0].endswith('21')]
            
            if week_2021_options:
                latest_week = week_2021_options[0]  # Get the first (most recent) 2021 week
                logging.info(f"Selected latest 2021 week: {latest_week}")
            else:
                # Fallback to the first option if no 2021 data found
                latest_week = week_options[0]
                logging.info(f"No 2021 data found, using latest week: {latest_week}")
            
            # Construct the DSM file URL based on the pattern
            # Pattern: 164.100.60.165/comm/2021-22/dsa/210725-270725(WK-17)/Supporting_files.xls
            # Extract year from the week pattern (e.g., 210725 -> 2021)
            week_start = latest_week.split('-')[0]
            
            # The date format is DDMMYY, so extract year from the last 2 digits
            # For example: 210725 -> 21 (year 2021)
            year_suffix = week_start[4:6]  # Extract year from date like 210725 -> 21
            
            # Based on the URL pattern: 164.100.60.165/comm/2021-22/dsa/210725-270725(WK-17)/Supporting_files.xls
            # The date 210725 is July 21, 2021, and the FY is 2021-22
            # So the financial year starts in the same year as the date
            fy_start = 2000 + int(year_suffix)
            fy_end = fy_start + 1
            
            dsm_url = f"http://164.100.60.165/comm/{fy_start}-{str(fy_end)[2:]}/dsa/{latest_week}/Supporting_files.xls"
            logging.info(f"Constructed DSM URL: {dsm_url}")
            
            return dsm_url
        else:
            logging.warning("No week options found on NRPC website")
            return None
            
    except Exception as e:
        logging.error(f"❌ Error fetching NRPC website: {e}")
        return None

def download_dsm_file(file_url):
    """Download the DSM file"""
    try:
        logging.info(f"Downloading DSM file: {file_url}")
        
        # Download the file
        resp = requests.get(file_url, timeout=60, stream=True)
        resp.raise_for_status()
        
        # Extract filename from URL
        filename = file_url.split('/')[-1]
        if not filename or '.' not in filename:
            filename = f"DSM_NRPC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls"
        
        file_path = os.path.join(NRLDC_DIR, filename)
        
        with open(file_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logging.info(f"✅ Downloaded: {filename}")
        return file_path
        
    except Exception as e:
        logging.error(f"❌ Error downloading DSM file: {e}")
        return None

def process_dsm_file(file_path):
    """Process the DSM Excel file"""
    try:
        logging.info(f"Processing DSM file: {file_path}")
        
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        logging.info(f"Found {len(sheet_names)} sheets: {sheet_names}")
        
        # Process each sheet
        processed_data = {}
        for sheet_name in sheet_names:
            try:
                logging.info(f"Reading sheet: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                if not df.empty:
                    # Clean column names
                    df.columns = df.columns.str.strip()
                    
                    # Remove completely empty rows and columns
                    df = df.dropna(how='all').dropna(axis=1, how='all')
                    
                    if not df.empty:
                        processed_data[sheet_name] = df
                        logging.info(f"✅ Processed sheet '{sheet_name}' with {len(df)} rows and {len(df.columns)} columns")
                        
                        # Show first few rows for preview
                        logging.info(f"📊 Preview of sheet '{sheet_name}':")
                        logging.info(f"Columns: {list(df.columns)}")
                        if len(df) > 0:
                            logging.info(f"First row: {df.iloc[0].to_dict()}")
                    else:
                        logging.warning(f"Sheet '{sheet_name}' is empty after cleaning")
                else:
                    logging.warning(f"Sheet '{sheet_name}' is empty")
                    
            except Exception as e:
                logging.error(f"❌ Error processing sheet '{sheet_name}': {e}")
                continue
        
        return processed_data
        
    except Exception as e:
        logging.error(f"❌ Error processing DSM file: {e}")
        return None

def save_processed_data(processed_data):
    """Save processed data to Excel file"""
    if not processed_data:
        logging.warning("No data to save")
        return None
    
    try:
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"DSM_NRPC_processed_{timestamp}.xlsx"
        output_path = os.path.join(NRLDC_DIR, output_filename)
        
        # Save to Excel with multiple sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in processed_data.items():
                # Clean sheet name for Excel (remove invalid characters)
                clean_sheet_name = re.sub(r'[\\/*?:\[\]]', '_', sheet_name)
                df.to_excel(writer, sheet_name=clean_sheet_name, index=False)
        
        logging.info(f"✅ Saved processed data to: {output_path}")
        return output_path
        
    except Exception as e:
        logging.error(f"❌ Error saving processed data: {e}")
        return None

def main():
    """Main function"""
    try:
        logging.info("🚀 Starting NRPC DSM data extraction...")
        
        # Setup directories
        setup_directories()
        
        # Get latest DSM file URL
        dsm_url = get_latest_dsm_file_url()
        if not dsm_url:
            logging.error("❌ Could not find DSM file URL")
            return
        
        # Download the file
        file_path = download_dsm_file(dsm_url)
        if not file_path:
            logging.error("❌ Could not download DSM file")
            return
        
        # Process the file
        processed_data = process_dsm_file(file_path)
        if not processed_data:
            logging.error("❌ Could not process DSM file")
            return
        
        # Save processed data
        output_path = save_processed_data(processed_data)
        if output_path:
            logging.info("🎉 NRPC DSM data extraction completed successfully!")
        else:
            logging.error("❌ Could not save processed data")
            
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
