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
                # Find the report title/date from the table structure
                # Look for the table row containing this link
                table_row = link.find_parent('tr')
                publication_date = None
                
                if table_row:
                    # Look for table cells that contain report titles with dates
                    for cell in table_row.find_all('td'):
                        cell_text = cell.get_text(strip=True)
                        if 'DSM' in cell_text and ('period from' in cell_text or 'Accounts' in cell_text):
                            # Extract date from text like "period from 28.07.2025 to 03.08.2025"
                            import re
                            date_match = re.search(r'period from (\d{2}\.\d{2}\.\d{4})', cell_text)
                            if date_match:
                                publication_date = date_match.group(1)
                                break
                
                if publication_date:
                    try:
                        # Parse the publication date (format: DD.MM.YYYY)
                        pub_date = datetime.strptime(publication_date, '%d.%m.%Y')
                        days_since_publication = (current_date - pub_date).days
                        
                        if days_since_publication > 7:
                            logging.info(f"⏭️ Report published on {publication_date} ({days_since_publication} days ago) - skipping (older than 7 days)")
                            continue
                        else:
                            logging.info(f"✅ Report published on {publication_date} ({days_since_publication} days ago) - downloading")
                            # Download the file
                            full_url = urljoin(ERPC_BASE_URL, href)
                            
                            try:
                                logging.info(f"📥 Downloading file: {text} -> {full_url}")
                                
                                file_response = session.get(full_url, timeout=30, verify=False)
                                if file_response.status_code == 200 and len(file_response.content) > 1000:
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
                    except ValueError:
                        logging.warning(f"⚠️ Could not parse publication date '{publication_date}', skipping")
                        continue
                else:
                    logging.info("⚠️ No publication date found in webpage, skipping")
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
