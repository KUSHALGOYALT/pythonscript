#!/usr/bin/env python3
import os
import sys
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from openpyxl import load_workbook, Workbook

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('erpc_extractor.log'),
        logging.StreamHandler()
    ]
)

ERPC_BASE_URL = "https://erpc.gov.in"
ERPC_UI_URL = "https://erpc.gov.in/ui-and-deviation-accts/"
ERPC_DIR = "../data"

def setup_directories():
    os.makedirs(ERPC_DIR, exist_ok=True)
    logging.info(f"✅ Created directory: {ERPC_DIR}")

def download_dsm_blockwise_files():
    """Download DSM blockwise data files from the UI and deviation accounts page for past 7 days"""
    logging.info("🔍 Downloading DSM blockwise data files for past 7 days...")
    
    try:
        # Get the UI and deviation accounts page with better error handling
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        response = session.get(ERPC_UI_URL, timeout=30, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        downloaded_files = []
        current_date = datetime.now()
        
        # Check for files published in the past 7 days
        # We'll download all DSM blockwise files and check their publication dates
        logging.info("🔍 Looking for DSM blockwise files published in the past 7 days...")
        
        # Look for DSM blockwise data files and their publication dates
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Check if it's a DSM blockwise data file
            if 'DSM_Blockwise_Data_' in href or 'DSM_Blockwise_Data_' in text:
                # Download the file first to check its actual publish date
                full_url = urljoin(ERPC_BASE_URL, href)
                
                try:
                    logging.info(f"📥 Checking file: {text} -> {full_url}")
                    
                    file_response = session.get(full_url, timeout=30, verify=False)
                    if file_response.status_code == 200 and len(file_response.content) > 1000:
                        # Check the file's actual publish date from HTTP headers
                        last_modified = file_response.headers.get('Last-Modified')
                        if last_modified:
                            try:
                                from email.utils import parsedate_to_datetime
                                file_date = parsedate_to_datetime(last_modified)
                                days_old = (current_date - file_date).days
                                
                                if days_old <= 7:
                                    logging.info(f"✅ File published {days_old} days ago - downloading")
                                    
                                    # Extract filename from URL or use text
                                    if href.endswith(('.xlsx', '.xls', '.csv')):
                                        filename = os.path.basename(urlparse(href).path)
                                    else:
                                        filename = f"DSM_Blockwise_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                                    
                                    file_path = os.path.join(ERPC_DIR, filename)
                                    with open(file_path, 'wb') as f:
                                        f.write(file_response.content)
                                    
                                    logging.info(f"✅ Successfully downloaded: {filename} ({len(file_response.content)} bytes)")
                                    downloaded_files.append({
                                        'url': full_url,
                                        'filename': filename,
                                        'text': text
                                    })
                                else:
                                    logging.info(f"⏭️ File published {days_old} days ago - skipping (older than 7 days)")
                                    continue
                            except:
                                # If we can't parse the date, assume it's recent and download
                                logging.info("⚠️ Could not parse file publish date, downloading anyway")
                                
                                # Extract filename from URL or use text
                                if href.endswith(('.xlsx', '.xls', '.csv')):
                                    filename = os.path.basename(urlparse(href).path)
                                else:
                                    filename = f"DSM_Blockwise_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                                
                                file_path = os.path.join(ERPC_DIR, filename)
                                with open(file_path, 'wb') as f:
                                    f.write(file_response.content)
                                
                                logging.info(f"✅ Successfully downloaded: {filename} ({len(file_response.content)} bytes)")
                                downloaded_files.append({
                                    'url': full_url,
                                    'filename': filename,
                                    'text': text
                                })
                        else:
                            # No last-modified header, assume it's recent and download
                            logging.info("⚠️ No publish date found in headers, downloading anyway")
                            
                            # Extract filename from URL or use text
                            if href.endswith(('.xlsx', '.xls', '.csv')):
                                filename = os.path.basename(urlparse(href).path)
                            else:
                                filename = f"DSM_Blockwise_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                            
                            file_path = os.path.join(ERPC_DIR, filename)
                            with open(file_path, 'wb') as f:
                                f.write(file_response.content)
                            
                            logging.info(f"✅ Successfully downloaded: {filename} ({len(file_response.content)} bytes)")
                            downloaded_files.append({
                                'url': full_url,
                                'filename': filename,
                                'text': text
                            })
                        
                except Exception as e:
                    logging.error(f"❌ Error downloading {text}: {e}")
                    continue
        
        return downloaded_files
        
    except Exception as e:
        logging.error(f"❌ Error accessing UI and deviation accounts page: {e}")
        return []

def run_update():
    """Main update function"""
    logging.info("🔄 Starting ERPC data update...")
    
    setup_directories()
    
    # Download DSM blockwise files
    downloaded_files = download_dsm_blockwise_files()
    
    if downloaded_files:
        logging.info(f"✅ Successfully downloaded {len(downloaded_files)} DSM blockwise data files")
        for file_info in downloaded_files:
            logging.info(f"   - {file_info['filename']} ({file_info['text']})")
    else:
        logging.warning("⚠️ No DSM blockwise data files found or downloaded")
    
    logging.info("✅ ERPC data update completed")

def main():
    run_update()

if __name__ == "__main__":
    main()
