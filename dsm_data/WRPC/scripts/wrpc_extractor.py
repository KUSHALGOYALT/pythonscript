#!/usr/bin/env python3
"""
Western Regional Power Committee (WRPC) Data Extractor
Extracts and processes DSM UI Account data from WRPC website
"""

import os
import sys
import logging
import requests
import pandas as pd
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import zipfile
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wrpc_extractor.log'),
        logging.StreamHandler()
    ]
)

# Configuration
WRPC_BASE_URL = "https://www.wrpc.gov.in"
WRPC_DSM_URL = "https://www.wrpc.gov.in/menu/DSMUI%20Account%20_342"
WRPC_SAMPLE_FILE = "https://www.wrpc.gov.in/allfile/070820251025026574sum4c.zip"
DOWNLOAD_DIR = "dsm_data"
WRPC_DIR = "dsm_data/WRPC"

# Data types for categorization
DATA_TYPES = {
    'DSM': ['dsm', 'daily', 'scheduling', 'accounting', 'ui'],
    'EXCEL': ['excel', 'spreadsheet', 'data'],
    'OTHER': ['other', 'misc']
}

def setup_directories():
    """Create necessary directories"""
    for directory in [DOWNLOAD_DIR, WRPC_DIR]:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Created directory: {directory}")



def scrape_wrpc_website():
    """Scrape the WRPC website for DSM data"""
    logging.info("🔍 Scraping WRPC website for DSM data...")
    
    categorized_files = {data_type: [] for data_type in DATA_TYPES.keys()}
    categorized_files['OTHER'] = []
    
    # First, add the sample DSM file
    sample_filename = "070820251025026574sum4c.zip"
    sample_file_info = {
        'href': sample_filename,
        'text': 'WRPC DSM UI Account Data Sample',
        'url': WRPC_SAMPLE_FILE,
        'type': 'zip'
    }
    categorized_files['DSM'].append(sample_file_info)
    logging.info(f"🎯 Added sample WRPC DSM file: {sample_filename}")
    
    try:
        logging.info(f"Accessing: {WRPC_DSM_URL}")
        resp = requests.get(WRPC_DSM_URL, timeout=30, verify=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for DSM, UI, and account related files
        for a in soup.find_all("a", href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # Look for DSM, UI, account related files
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in ['dsm', 'ui', 'account', 'daily', 'scheduling']):
                if href.lower().endswith(('.xls', '.xlsx', '.zip', '.csv')):
                    full_url = urljoin(WRPC_DSM_URL, href)
                    
                    file_info = {
                        'href': href,
                        'text': text,
                        'url': full_url,
                        'type': 'excel' if href.lower().endswith(('.xls', '.xlsx')) else 'zip' if href.lower().endswith('.zip') else 'csv'
                    }
                    
                    categorized_files['DSM'].append(file_info)
                    logging.info(f"🎯 Found WRPC DSM file: {text} -> {href}")
                elif href == '#' or href.startswith('javascript:'):
                    logging.debug(f"🔗 Found JavaScript link: {text}")
                else:
                    logging.debug(f"📄 Found non-file link: {href}")
            
            # Look for any downloadable files
            elif href.lower().endswith(('.xls', '.xlsx', '.zip', '.csv')):
                full_url = urljoin(WRPC_DSM_URL, href)
                
                file_info = {
                    'href': href,
                    'text': text,
                    'url': full_url,
                    'type': 'excel' if href.lower().endswith(('.xls', '.xlsx')) else 'zip' if href.lower().endswith('.zip') else 'csv'
                }
                
                categorized_files['OTHER'].append(file_info)
                logging.info(f"📄 Found other WRPC file: {text} -> {href}")
        
        # Also check for any subdirectories or additional pages
        for a in soup.find_all("a", href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # Look for potential subdirectories
            if any(keyword in text.lower() for keyword in ['download', 'data', 'file', 'dsm', 'ui']):
                if not href.lower().endswith(('.xls', '.xlsx', '.zip', '.csv', '.pdf')):
                    try:
                        sub_url = urljoin(WRPC_DSM_URL, href)
                        logging.info(f"🔍 Found potential subdirectory: {text} -> {sub_url}")
                        
                        sub_resp = requests.get(sub_url, timeout=30, verify=True)
                        sub_resp.raise_for_status()
                        sub_soup = BeautifulSoup(sub_resp.text, "html.parser")
                        
                        for sub_a in sub_soup.find_all("a", href=True):
                            sub_href = sub_a['href']
                            sub_text = sub_a.get_text(strip=True)
                            
                            if sub_href.lower().endswith(('.xls', '.xlsx', '.zip', '.csv')):
                                sub_full_url = urljoin(sub_url, sub_href)
                                
                                file_info = {
                                    'href': sub_href,
                                    'text': sub_text,
                                    'url': sub_full_url,
                                    'type': 'excel' if sub_href.lower().endswith(('.xls', '.xlsx')) else 'zip' if sub_href.lower().endswith('.zip') else 'csv'
                                }
                                
                                categorized_files['DSM'].append(file_info)
                                logging.info(f"🎯 Found WRPC file in subdirectory: {sub_text} -> {sub_href}")
                            elif sub_href.lower().endswith('.pdf'):
                                logging.debug(f"⏭️ Skipping PDF file in subdirectory: {sub_href}")
                                
                    except Exception as e:
                        logging.warning(f"⚠️ Error accessing subdirectory {href}: {e}")
                        continue
        
        # Summary
        total_files = sum(len(files) for files in categorized_files.values())
        logging.info(f"📊 Found {total_files} files on WRPC website:")
        for data_type, files in categorized_files.items():
            if files:
                logging.info(f"  - {data_type}: {len(files)} files")
        
        return categorized_files
        
    except requests.RequestException as e:
        logging.error(f"❌ Error accessing WRPC website: {e}")
        return categorized_files

def download_file(url, filename):
    """Download a file from URL"""
    try:
        logging.info(f"📥 Downloading: {filename}")
        
        resp = requests.get(url, timeout=60, stream=True, verify=True)
        resp.raise_for_status()
        
        file_path = os.path.join(WRPC_DIR, filename)
        
        with open(file_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logging.info(f"✅ Downloaded: {filename}")
        return file_path
        
    except Exception as e:
        logging.error(f"❌ Error downloading {filename}: {e}")
        return None

def process_zip_file(file_path, original_filename):
    """Process ZIP file containing CSV data"""
    try:
        logging.info(f"📦 Processing ZIP file: {file_path}")
        
        processed_data = {}
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # List all files in the ZIP
            file_list = zip_ref.namelist()
            logging.info(f"📋 Files in ZIP: {file_list}")
            
            for file_name in file_list:
                if file_name.lower().endswith('.csv'):
                    try:
                        logging.info(f"📄 Processing CSV file: {file_name}")
                        
                        # Read CSV from ZIP
                        with zip_ref.open(file_name) as csv_file:
                            df = pd.read_csv(csv_file, encoding='utf-8', on_bad_lines='skip')
                        
                        if not df.empty:
                            # Clean column names
                            df.columns = df.columns.str.strip()
                            
                            # Remove completely empty rows and columns
                            df = df.dropna(how='all').dropna(axis=1, how='all')
                            
                            if not df.empty:
                                sheet_name = os.path.splitext(file_name)[0]
                                processed_data[sheet_name] = df
                                logging.info(f"✅ Processed CSV '{sheet_name}' with {len(df)} rows and {len(df.columns)} columns")
                                
                                # Show first few rows for preview
                                logging.info(f"📊 Preview of CSV '{sheet_name}':")
                                logging.info(f"Columns: {list(df.columns)}")
                                logging.info(f"First 3 rows:\n{df.head(3)}")
                            else:
                                logging.warning(f"⚠️ CSV '{file_name}' is empty after cleaning")
                        else:
                            logging.warning(f"⚠️ CSV '{file_name}' is empty")
                            
                    except Exception as e:
                        logging.error(f"❌ Error processing CSV '{file_name}': {e}")
                        continue
                        
        return processed_data
        
    except Exception as e:
        logging.error(f"❌ Error processing ZIP file {file_path}: {e}")
        return None

def process_excel_file(file_path, original_filename):
    """Process Excel file"""
    try:
        logging.info(f"📊 Processing Excel file: {file_path}")
        
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
                        logging.info(f"First 3 rows:\n{df.head(3)}")
                        
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
        # Determine target directory - WRPC data goes to WRPC directory
        target_dir = WRPC_DIR
        logging.info(f"📁 Saving WRPC data to: {target_dir}")
        
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
    processed_data = None
    if file_info['type'] == 'zip':
        processed_data = process_zip_file(file_path, filename)
    elif file_info['type'] == 'excel':
        processed_data = process_excel_file(file_path, filename)
    elif file_info['type'] == 'csv':
        # For CSV files, read directly
        try:
            df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
            if not df.empty:
                df.columns = df.columns.str.strip()
                df = df.dropna(how='all').dropna(axis=1, how='all')
                if not df.empty:
                    processed_data = {'CSV_Data': df}
                    logging.info(f"✅ Processed CSV file with {len(df)} rows")
        except Exception as e:
            logging.error(f"❌ Error processing CSV file: {e}")
    
    if processed_data:
        output_path = save_processed_data(processed_data, filename)
        if output_path:
            return True
    
    return False

def run_update():
    """Run WRPC data update"""
    logging.info("🔄 Starting WRPC data update...")
    
    try:
        # Ensure directories exist
        setup_directories()
        
        # Scrape website
        categorized_files = scrape_wrpc_website()
        
        # Process files
        total_processed = 0
        for data_type, files in categorized_files.items():
            if files:
                logging.info(f"📁 Processing {data_type} files...")
                for file_info in files:
                    if download_and_process_file(file_info, data_type):
                        total_processed += 1
        
        logging.info(f"✅ WRPC update completed. Processed {total_processed} files.")
        
    except Exception as e:
        logging.error(f"❌ Error in update: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("WRPC Data Extractor Usage:")
            print("  python wrpc_extractor.py          # Run data extraction")
            print("  python wrpc_extractor.py --help   # Show this help")
        else:
            print("Unknown option. Use --help for usage information.")
    else:
        # Run data extraction
        run_update()

if __name__ == "__main__":
    main()
