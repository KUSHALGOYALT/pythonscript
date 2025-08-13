#!/usr/bin/env python3
"""
Eastern Regional Power Committee (ERPC) Data Extractor
Extracts DSA (Daily Scheduling and Accounting) data from ERPC website
"""

import requests
import pandas as pd
import os
import logging
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('erpc_extractor.log'),
        logging.StreamHandler()
    ]
)

# Configuration
ERPC_BASE_URL = "https://erpc.gov.in"
ERPC_DSA_URL = "https://erpc.gov.in/ui-and-deviation-accts/"
DOWNLOAD_DIR = "dsm_data"
ERLDC_DIR = "dsm_data/ERLDC"

# Data types for categorization
DATA_TYPES = {
    'DSA': ['dsa', 'daily', 'scheduling', 'accounting', 'supporting'],
    'REPORT': ['report', 'summary', 'analysis'],
    'NOTIFICATION': ['notification', 'circular', 'order'],
    'OTHER': ['other', 'misc']
}

def setup_directories():
    """Create necessary directories"""
    for directory in [DOWNLOAD_DIR, ERLDC_DIR]:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Created directory: {directory}")



def scrape_erpc_website():
    """Scrape the ERPC website for DSA data"""
    logging.info("🔍 Scraping ERPC website for DSA data...")
    
    categorized_files = {data_type: [] for data_type in DATA_TYPES.keys()}
    categorized_files['OTHER'] = []
    
    try:
        logging.info(f"Accessing: {ERPC_DSA_URL}")
        resp = requests.get(ERPC_DSA_URL, timeout=30, verify=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for all Excel files
        for a in soup.find_all("a", href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # Process Excel files
            if href.lower().endswith(('.xls', '.xlsx')):
                full_url = urljoin(ERPC_DSA_URL, href)
                
                file_info = {
                    'href': href,
                    'text': text,
                    'url': full_url,
                    'type': 'excel'
                }
                
                # Categorize based on file location or content
                if 'wp-content/uploads' in href:
                    categorized_files['DSA'].append(file_info)
                    logging.info(f"🎯 Found Excel file in uploads: {text} -> {href}")
                else:
                    categorized_files['OTHER'].append(file_info)
                    logging.info(f"🎯 Found Excel file: {text} -> {href}")
                    
            # Skip non-Excel files
            elif href == '#' or href.startswith('javascript:'):
                logging.debug(f"🔗 Found JavaScript link: {text}")
            elif href.lower().endswith('.pdf'):
                logging.debug(f"⏭️ Skipping PDF file: {href}")
            else:
                logging.debug(f"📄 Found non-file link: {href}")
        
        # Also check for any subdirectories that might contain files
        for a in soup.find_all("a", href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # Look for potential subdirectories (not files)
            if not href.lower().endswith(('.xls', '.xlsx', '.pdf', '.zip')) and not href.startswith('#'):
                sub_url = urljoin(ERPC_DSA_URL, href)
                logging.info(f"🔍 Found potential subdirectory: {text} -> {sub_url}")
                
                try:
                    sub_resp = requests.get(sub_url, timeout=30, verify=True)
                    sub_resp.raise_for_status()
                    sub_soup = BeautifulSoup(sub_resp.text, "html.parser")
                    
                    # Look for files in subdirectory
                    for sub_a in sub_soup.find_all("a", href=True):
                        sub_href = sub_a['href']
                        sub_text = sub_a.get_text(strip=True)
                        
                        if sub_href.lower().endswith(('.xls', '.xlsx')):
                            sub_full_url = urljoin(sub_url, sub_href)
                            
                            file_info = {
                                'href': sub_href,
                                'text': sub_text,
                                'url': sub_full_url,
                                'type': 'excel'
                            }
                            
                            categorized_files['DSA'].append(file_info)
                            logging.info(f"🎯 Found Excel file in subdirectory: {sub_text} -> {sub_href}")
                        elif sub_href.lower().endswith('.pdf'):
                            logging.debug(f"⏭️ Skipping PDF file in subdirectory: {sub_href}")
                            
                except Exception as e:
                    logging.warning(f"⚠️ Error accessing subdirectory {sub_url}: {e}")
                    continue
                    
    except requests.RequestException as e:
        logging.error(f"❌ Error accessing ERPC website: {e}")
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
    
    # Log summary
    total_files = sum(len(files) for files in categorized_files.values())
    logging.info(f"📊 Total files found: {total_files}")
    for data_type, files in categorized_files.items():
        if files:
            logging.info(f"📁 {data_type}: {len(files)} files")
    
    # Validate that we found some files
    if total_files == 0:
        logging.warning("⚠️ No files found on ERPC website. This might indicate:")
        logging.warning("   - Website structure has changed")
        logging.warning("   - Network connectivity issues")
        logging.warning("   - No DSM data is currently available")
        logging.warning("   - Website is temporarily down")
    
    return categorized_files

def download_file(url, filename):
    """Download a file from URL"""
    try:
        logging.info(f"Downloading: {url}")
        resp = requests.get(url, timeout=60, stream=True, verify=True)
        resp.raise_for_status()
        
        file_path = os.path.join(ERLDC_DIR, filename)
        with open(file_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logging.info(f"✅ Downloaded: {filename}")
        return file_path
    except Exception as e:
        logging.error(f"❌ Error downloading {url}: {e}")
        return None

def process_excel_file(file_path, original_filename):
    """Process Excel file and extract data"""
    try:
        logging.info(f"Processing Excel file: {original_filename}")
        
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
                        logging.info(f"✅ Processed sheet '{sheet_name}' with {len(df)} rows")
                    else:
                        logging.warning(f"⚠️ Sheet '{sheet_name}' is empty after cleaning")
                else:
                    logging.warning(f"⚠️ Sheet '{sheet_name}' is empty")
                    
            except Exception as e:
                logging.error(f"❌ Error processing sheet '{sheet_name}': {e}")
                continue
        
        return processed_data
        
    except Exception as e:
        logging.error(f"❌ Error processing Excel file {file_path}: {e}")
        return None

def save_processed_data(processed_data, original_filename):
    """Save processed data to Excel file"""
    if not processed_data:
        logging.warning("No data to save")
        return None
    
    try:
        # Save all ERPC data to ERLDC directory
        target_dir = ERLDC_DIR
        logging.info(f"📁 Saving ERPC data to: {target_dir}")
        
        # Create output filename
        base_name = os.path.splitext(original_filename)[0]
        output_filename = f"{base_name}_processed.xlsx"
        output_path = os.path.join(target_dir, output_filename)
        
        # Save to Excel with multiple sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in processed_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                logging.info(f"💾 Saved sheet '{sheet_name}' with {len(df)} rows")
        
        logging.info(f"✅ Saved processed data to: {output_path}")
        return output_path
        
    except Exception as e:
        logging.error(f"❌ Error saving processed data: {e}")
        return None

def download_and_process_file(file_info, data_type):
    """Download and process a single file"""
    filename = file_info['href']
    url = file_info['url']
    
    # Download file
    file_path = download_file(url, filename)
    if not file_path:
        return False
    
    # Process based on file type
    if file_info['type'] == 'excel':
        processed_data = process_excel_file(file_path, filename)
        if processed_data:
            output_path = save_processed_data(processed_data, filename)
            if output_path:
                return True
    
    return False

def run_update():
    """Run ERPC data update"""
    logging.info("🔄 Starting ERPC data update...")
    
    try:
        # Scrape website
        categorized_files = scrape_erpc_website()
        
        # Process files
        total_processed = 0
        for data_type, files in categorized_files.items():
            if files:
                logging.info(f"Processing {data_type} files...")
                for file_info in files:
                    if download_and_process_file(file_info, data_type):
                        total_processed += 1
        
        logging.info(f"✅ Update completed. Processed {total_processed} files.")
        
    except Exception as e:
        logging.error(f"❌ Error in update: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("ERPC Data Extractor Usage:")
            print("  python erpc_extractor.py          # Run data extraction")
            print("  python erpc_extractor.py --help   # Show this help")
            return
        else:
            print("Unknown argument. Use --help for usage information.")
            return
    
    # Run data extraction
    setup_directories()
    run_update()

if __name__ == "__main__":
    main()
