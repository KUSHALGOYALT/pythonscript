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
import time
import json
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import schedule
import sys
import glob
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
ERPC_SPECIFIC_FILE = "https://erpc.gov.in/wp-content/uploads/2025/08/DSM_Blockwise_Data_2025-07-21-2025-07-27.xlsx"
DOWNLOAD_DIR = "dsm_data"
ERLDC_DIR = "dsm_data/ERLDC"
NRLDC_DIR = "dsm_data/NRLDC"
TEMP_DIR = "temp_erpc"
FILE_TRACKING_FILE = "erpc_file_tracking.json"

# Data types for categorization
DATA_TYPES = {
    'DSA': ['dsa', 'daily', 'scheduling', 'accounting', 'supporting'],
    'REPORT': ['report', 'summary', 'analysis'],
    'NOTIFICATION': ['notification', 'circular', 'order'],
    'OTHER': ['other', 'misc']
}

def setup_directories():
    """Create necessary directories"""
    for directory in [DOWNLOAD_DIR, ERLDC_DIR, NRLDC_DIR, TEMP_DIR]:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Created directory: {directory}")

def load_file_tracking():
    """Load file tracking data"""
    if os.path.exists(FILE_TRACKING_FILE):
        try:
            with open(FILE_TRACKING_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Error loading file tracking: {e}")
    return {}

def save_file_tracking(tracking_data):
    """Save file tracking data"""
    try:
        with open(FILE_TRACKING_FILE, 'w') as f:
            json.dump(tracking_data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving file tracking: {e}")

def get_file_hash(file_path):
    """Calculate MD5 hash of a file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logging.error(f"Error calculating file hash: {e}")
        return None

def scrape_erpc_website():
    """Scrape the ERPC website for DSA data"""
    logging.info("🔍 Scraping ERPC website for DSA data...")
    
    categorized_files = {data_type: [] for data_type in DATA_TYPES.keys()}
    categorized_files['OTHER'] = []
    
    # First, add the specific DSM file
    specific_filename = "DSM_Blockwise_Data_2025-07-21-2025-07-27.xlsx"
    specific_file_info = {
        'href': specific_filename,
        'text': 'DSM Blockwise Data (2025-07-21 to 2025-07-27)',
        'url': ERPC_SPECIFIC_FILE,
        'type': 'excel'
    }
    categorized_files['DSA'].append(specific_file_info)
    logging.info(f"🎯 Added specific DSM file: {specific_filename}")
    
    try:
        logging.info(f"Accessing: {ERPC_DSA_URL}")
        resp = requests.get(ERPC_DSA_URL, timeout=30, verify=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for DSM, UI, and deviation related files
        for a in soup.find_all("a", href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # Look for DSM, UI, deviation related files
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in ['dsm', 'ui', 'deviation', 'blockwise', 'daily', 'scheduling']):
                if href.lower().endswith(('.xls', '.xlsx')):
                    full_url = urljoin(ERPC_DSA_URL, href)
                    
                    file_info = {
                        'href': href,
                        'text': text,
                        'url': full_url,
                        'type': 'excel'
                    }
                    
                    categorized_files['DSA'].append(file_info)
                    logging.info(f"🎯 Found DSM/UI Excel file: {text} -> {href}")
                elif href == '#' or href.startswith('javascript:'):
                    logging.debug(f"🔗 Found JavaScript link: {text}")
                else:
                    logging.debug(f"📄 Found non-file link: {href}")
            
            # Look for any Excel files in uploads directory
            elif 'wp-content/uploads' in href and href.lower().endswith(('.xls', '.xlsx')):
                full_url = urljoin(ERPC_DSA_URL, href)
                
                file_info = {
                    'href': href,
                    'text': text,
                    'url': full_url,
                    'type': 'excel'
                }
                
                categorized_files['DSA'].append(file_info)
                logging.info(f"🎯 Found Excel file in uploads: {href}")
                
            # Look for any Excel files
            elif href.lower().endswith(('.xls', '.xlsx')):
                full_url = urljoin(ERPC_DSA_URL, href)
                
                file_info = {
                    'href': href,
                    'text': text,
                    'url': full_url,
                    'type': 'excel'
                }
                
                categorized_files['OTHER'].append(file_info)
                logging.info(f"🎯 Found Excel file: {href}")
                
            # Skip PDF files - only process Excel files
            elif href.lower().endswith('.pdf'):
                logging.debug(f"⏭️ Skipping PDF file: {href}")
        
        # Also check for any subdirectories or additional pages
        for a in soup.find_all("a", href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # Look for DSM, UI, deviation subdirectories
            if any(keyword in href.lower() or keyword in text.lower() 
                   for keyword in ['dsm', 'ui', 'deviation', 'blockwise', 'power', 'scheduling', 'daily', 'accounting']):
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
    
    return categorized_files

def download_file(url, filename):
    """Download a file from URL"""
    try:
        logging.info(f"Downloading: {url}")
        resp = requests.get(url, timeout=60, stream=True, verify=True)
        resp.raise_for_status()
        
        file_path = os.path.join(TEMP_DIR, filename)
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
        # Determine target directory based on filename or content
        target_dir = DOWNLOAD_DIR  # Default directory
        
        # Check filename for ERLDC or NRLDC indicators
        filename_lower = original_filename.lower()
        if 'erldc' in filename_lower or 'eastern' in filename_lower:
            target_dir = ERLDC_DIR
            logging.info(f"📁 Categorizing as ERLDC data: {original_filename}")
        elif 'nrldc' in filename_lower or 'northern' in filename_lower:
            target_dir = NRLDC_DIR
            logging.info(f"📁 Categorizing as NRLDC data: {original_filename}")
        else:
            # Check content for ERLDC/NRLDC indicators
            if processed_data:
                # Define Eastern and Northern region station keywords
                eastern_stations = [
                    'bsphcl', 'dvc', 'east central railway', 'gridco', 'sikkim', 'wbsetcl', 
                    'apnrl', 'chuzachen', 'dikchu', 'gmrkel', 'jipl', 'rongnichu hep', 
                    'talcher solar', 'nvvn-bd', 'nea-bihar', 'nvvn-nepal', 'nvvn_bhutan',
                    'barh-ii', 'barh-i', 'brbcl', 'darlipali', 'fstpp', 'jsweul', 
                    'jorethang hep', 'khstpp', 'mpl', 'mtps', 'north karanpura', 'npgc', 
                    'rangit', 'teesta', 'thep', 'tstpp', 'ner', 'eastern'
                ]
                
                northern_stations = [
                    'nr', 'northern', 'nrldc', 'north'
                ]
                
                erldc_indicators = 0
                nrldc_indicators = 0
                
                for sheet_name, df in processed_data.items():
                    if not df.empty:
                        # Check sheet name for regional indicators
                        sheet_name_lower = sheet_name.lower()
                        
                        # Check for Eastern region stations in sheet name
                        if any(station in sheet_name_lower for station in eastern_stations):
                            erldc_indicators += 1
                            logging.info(f"📁 Found Eastern station in sheet name: {sheet_name}")
                        
                        # Check for Northern region stations in sheet name
                        elif any(station in sheet_name_lower for station in northern_stations):
                            nrldc_indicators += 1
                            logging.info(f"📁 Found Northern station in sheet name: {sheet_name}")
                        
                        # Check data content for station names
                        sample_data = df.head(10).astype(str).to_string().lower()
                        
                        # Check for Eastern region stations in data
                        if any(station in sample_data for station in eastern_stations):
                            erldc_indicators += 1
                            logging.info(f"📁 Found Eastern station in data: {sheet_name}")
                        
                        # Check for Northern region stations in data
                        elif any(station in sample_data for station in northern_stations):
                            nrldc_indicators += 1
                            logging.info(f"📁 Found Northern station in data: {sheet_name}")
                
                # Determine target directory based on indicators
                if erldc_indicators > nrldc_indicators:
                    target_dir = ERLDC_DIR
                    logging.info(f"📁 Content analysis: Categorizing as ERLDC data ({erldc_indicators} indicators)")
                elif nrldc_indicators > erldc_indicators:
                    target_dir = NRLDC_DIR
                    logging.info(f"📁 Content analysis: Categorizing as NRLDC data ({nrldc_indicators} indicators)")
                else:
                    logging.info(f"📁 No clear ERLDC/NRLDC indicators found, saving to main directory")
        
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

def check_for_changes(file_info, tracking_data):
    """Check if file has changed"""
    filename = file_info['href']
    current_hash = None
    
    # Check in all possible directories for existing file
    possible_paths = [
        os.path.join(DOWNLOAD_DIR, filename),
        os.path.join(ERLDC_DIR, filename),
        os.path.join(NRLDC_DIR, filename)
    ]
    
    local_path = None
    for path in possible_paths:
        if os.path.exists(path):
            local_path = path
            break
    
    if local_path:
        current_hash = get_file_hash(local_path)
    
    # Check if file has changed
    if filename in tracking_data:
        if current_hash and tracking_data[filename]['hash'] == current_hash:
            logging.info(f"📋 No changes detected in: {filename}")
            return False
        else:
            logging.info(f"🔄 Change detected in: {filename}")
            return True
    else:
        logging.info(f"🆕 New file detected: {filename}")
        return True

def download_and_process_file(file_info, data_type):
    """Download and process a single file"""
    filename = file_info['href']
    url = file_info['url']
    
    # Check for changes
    tracking_data = load_file_tracking()
    if not check_for_changes(file_info, tracking_data):
        return True
    
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
                # Update tracking
                file_hash = get_file_hash(file_path)
                if file_hash:
                    tracking_data[filename] = {
                        'hash': file_hash,
                        'last_processed': datetime.now().isoformat(),
                        'type': data_type,
                        'url': url
                    }
                    save_file_tracking(tracking_data)
                return True
    
    # Clean up temp file
    try:
        os.remove(file_path)
    except:
        pass
    
    return False

def scheduled_update():
    """Run scheduled update"""
    logging.info("🕐 Starting scheduled ERPC data update...")
    
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
        
        logging.info(f"✅ Scheduled update completed. Processed {total_processed} files.")
        
    except Exception as e:
        logging.error(f"❌ Error in scheduled update: {e}")

def start_scheduler():
    """Start the scheduler to run updates automatically"""
    logging.info("Starting automated scheduler for ERPC data extraction...")
    
    # Schedule the job to run once per week (Monday at 9:00 AM)
    schedule.every().monday.at("09:00").do(scheduled_update)
    
    # Also run once immediately when started
    schedule.every().day.at("09:00").do(scheduled_update)
    
    logging.info("Scheduler started. Updates will run:")
    logging.info("- Every Monday at 9:00 AM (weekly check)")
    logging.info("- Daily at 9:00 AM (for immediate updates)")
    logging.info("- Press Ctrl+C to stop the scheduler.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user.")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")

def run_manual_update():
    """Run manual update"""
    logging.info("🔄 Starting manual ERPC data update...")
    scheduled_update()
    logging.info("✅ Manual update completed.")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--schedule':
            setup_directories()
            start_scheduler()
        elif sys.argv[1] == '--update':
            setup_directories()
            return run_manual_update()
        elif sys.argv[1] == '--help':
            print("ERPC Data Extractor Usage:")
            print("  python erpc_extractor.py --update    # Run manual update")
            print("  python erpc_extractor.py --schedule  # Start automated scheduler")
            print("  python erpc_extractor.py --help      # Show this help")
            return
        else:
            print("Unknown argument. Use --help for usage information.")
            return
    else:
        # Default: run manual update
        setup_directories()
        return run_manual_update()

if __name__ == "__main__":
    main()
