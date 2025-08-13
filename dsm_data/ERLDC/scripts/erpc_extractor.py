#!/usr/bin/env python3
import os
import sys
import logging
import requests
import re
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

def extract_report_date_from_text(text):
    """Extract report date from text like '2025/08/13'"""
    # Look for date pattern YYYY/MM/DD at the end of the text
    date_pattern = r'(\d{4}/\d{2}/\d{2})$'
    match = re.search(date_pattern, text)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y/%m/%d')
        except ValueError:
            return None
    return None

def is_within_past_7_days(report_date):
    """Check if report date is within the past 7 days"""
    if not report_date:
        return False
    
    current_date = datetime.now()
    days_difference = (current_date - report_date).days
    
    logging.info(f"📅 Report date: {report_date.strftime('%Y-%m-%d')}")
    logging.info(f"📅 Current date: {current_date.strftime('%Y-%m-%d')}")
    logging.info(f"📅 Days difference: {days_difference}")
    
    return 0 <= days_difference <= 7

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
        
        # Look for table rows that contain file information
        table_rows = soup.find_all('tr')
        logging.info(f"📊 Found {len(table_rows)} table rows")
        
        for row in table_rows:
            # Get all cells in the row
            cells = row.find_all('td')
            if len(cells) >= 3:  # Need description, date, and download columns
                # Get the description text (first cell)
                description_cell = cells[0]
                description_text = description_cell.get_text(strip=True)
                
                # Get the report date (second cell)
                date_cell = cells[1]
                date_text = date_cell.get_text(strip=True)
                
                # Extract report date from the date cell
                report_date = extract_report_date_from_text(date_text)
                
                if report_date:
                    logging.info(f"📅 Found file with report date: {description_text[:80]}...")
                    
                    # Check if report date is within past 7 days
                    if is_within_past_7_days(report_date):
                        logging.info(f"✅ Report date is within past 7 days - looking for download links")
                        
                        # Look for download links in this row
                        download_links = row.find_all('a', href=True)
                        
                        for link in download_links:
                            href = link['href']
                            link_text = link.get_text(strip=True)
                            
                            # Check if it's a download link
                            if 'download' in link_text.lower() or 'data file' in link_text.lower():
                                # Skip PDF files
                                if href.lower().endswith('.pdf') or link_text.lower().endswith('.pdf'):
                                    logging.info(f"⏭️ Skipping PDF file: {link_text}")
                                    continue
                                
                                # Download the file
                                full_url = urljoin(ERPC_BASE_URL, href)
                                
                                try:
                                    logging.info(f"📥 Downloading: {link_text} -> {full_url}")
                                    
                                    file_response = session.get(full_url, timeout=30, verify=False)
                                    if file_response.status_code == 200 and len(file_response.content) > 1000:
                                        # Extract filename from URL or use description
                                        if href.endswith(('.xlsx', '.xls', '.csv')):
                                            filename = os.path.basename(urlparse(href).path)
                                        else:
                                            # Create filename from description and date
                                            safe_description = re.sub(r'[^\w\s-]', '', description_text[:50])
                                            filename = f"DSM_{safe_description}_{report_date.strftime('%Y%m%d')}.xlsx"
                                        
                                        file_path = os.path.join(ERPC_DIR, filename)
                                        with open(file_path, 'wb') as f:
                                            f.write(file_response.content)
                                        
                                        logging.info(f"✅ Successfully downloaded: {filename} ({len(file_response.content)} bytes)")
                                        downloaded_files.append({
                                            'url': full_url,
                                            'filename': filename,
                                            'description': description_text,
                                            'report_date': report_date.strftime('%Y-%m-%d')
                                        })
                                    else:
                                        logging.warning(f"⚠️ Failed to download {link_text}: Status {file_response.status_code}")
                                        
                                except Exception as e:
                                    logging.error(f"❌ Error downloading {link_text}: {e}")
                                    continue
                    else:
                        logging.info(f"⏭️ Report date is older than 7 days - skipping")
                else:
                    # No report date found, skip this row
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
            logging.info(f"   - {file_info['filename']} (Report Date: {file_info['report_date']})")
    else:
        logging.warning("⚠️ No DSM blockwise data files found or downloaded")
    
    logging.info("✅ ERPC data update completed")

def main():
    run_update()

if __name__ == "__main__":
    main()
