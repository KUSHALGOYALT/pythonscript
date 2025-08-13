#!/usr/bin/env python3
import os
import time
import logging
import requests
import zipfile
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('selenium_extractor.log')
    ]
)

WRPC_DATA_DIR = "../data"
WRPC_BASE_URL = "https://www.wrpc.gov.in"
WRPC_DSM_URL = "https://www.wrpc.gov.in/menu/DSMUI%20Account%20_342"

def setup_chrome_driver():
    """Setup Chrome driver with headless options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"❌ Failed to setup Chrome driver: {e}")
        logging.info("💡 Please install Chrome and ChromeDriver")
        return None

def extract_past_7_days_data():
    """Extract data for the past 7 days from current date using Selenium"""
    logging.info("🚀 Starting Selenium-based extraction for past 7 days...")
    
    # Create data directory
    os.makedirs(WRPC_DATA_DIR, exist_ok=True)
    
    driver = setup_chrome_driver()
    if not driver:
        return False
    
    try:
        logging.info(f"🌐 Accessing: {WRPC_DSM_URL}")
        driver.get(WRPC_DSM_URL)
        
        # Wait for page to load
        logging.info("⏳ Waiting for page to load...")
        time.sleep(5)
        
        # Wait for JavaScript content to load
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            logging.warning("⚠️ Timeout waiting for page to load completely")
        
        # Get the page source after JavaScript execution
        page_source = driver.page_source
        logging.info(f"📄 Page loaded, content length: {len(page_source)} bytes")
        
        # Save the full page source for debugging
        with open(os.path.join(WRPC_DATA_DIR, "full_page_source.html"), 'w', encoding='utf-8') as f:
            f.write(page_source)
        logging.info("💾 Saved full page source")
        
        # Generate date patterns for past 7 days
        current_date = datetime.now()
        date_patterns = []
        
        for days_back in range(7):
            test_date = current_date - timedelta(days=days_back)
            date_str = test_date.strftime('%d%m%Y')
            date_patterns.append(date_str)
            logging.info(f"📅 Looking for date: {date_str} ({test_date.strftime('%Y-%m-%d')})")
        
        # Look for files for each date
        found_files = []
        downloaded_files = []
        
        for date_str in date_patterns:
            logging.info(f"🔍 Searching for files with date: {date_str}")
            
            # Look for files with this specific date
            date_pattern = rf'{date_str}\d{{8,14}}\.zip'
            matches = re.findall(date_pattern, page_source, re.IGNORECASE)
            
            for match in matches:
                if match not in found_files:
                    found_files.append(match)
                    logging.info(f"🎯 Found file for {date_str}: {match}")
                    
                    # Try to download the file
                    try:
                        file_url = f"{WRPC_BASE_URL}/allfile/{match}"
                        logging.info(f"📥 Downloading: {match}")
                        response = requests.get(file_url, timeout=30)
                        
                        if response.status_code == 200 and len(response.content) > 1000:
                            file_path = os.path.join(WRPC_DATA_DIR, match)
                            with open(file_path, 'wb') as f:
                                f.write(response.content)
                            
                            logging.info(f"✅ Successfully downloaded: {match} ({len(response.content)} bytes)")
                            downloaded_files.append(file_path)
                        else:
                            logging.warning(f"⚠️ Failed to download {match}: Status {response.status_code}")
                            
                    except Exception as e:
                        logging.warning(f"⚠️ Error downloading {match}: {e}")
        
        # Also look for any ZIP files and categorize them by date
        all_zip_files = re.findall(r'[^"\']*\.zip[^"\']*', page_source, re.IGNORECASE)
        logging.info(f"📦 Found {len(all_zip_files)} total ZIP files")
        
        # Categorize ZIP files by date
        files_by_date = {}
        for zip_file in all_zip_files:
            for date_str in date_patterns:
                if date_str in zip_file:
                    if date_str not in files_by_date:
                        files_by_date[date_str] = []
                    files_by_date[date_str].append(zip_file)
                    break
        
        # Show summary by date
        logging.info("📊 Summary by date:")
        for date_str in date_patterns:
            if date_str in files_by_date:
                count = len(files_by_date[date_str])
                logging.info(f"  📅 {date_str}: {count} files")
                for file in files_by_date[date_str][:3]:  # Show first 3 files
                    logging.info(f"    - {file}")
            else:
                logging.info(f"  📅 {date_str}: 0 files")
        
        # Look for any links on the page
        links = driver.find_elements(By.TAG_NAME, "a")
        logging.info(f"🔗 Found {len(links)} links on the page")
        
        # Check for links with ZIP files
        zip_links = []
        for link in links:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                if href and '.zip' in href.lower():
                    zip_links.append({'href': href, 'text': text})
                    logging.info(f"🔗 Found ZIP link: {text} -> {href}")
                    
            except Exception as e:
                continue
        
        # Also check for any download buttons or file lists
        try:
            # Look for download buttons
            download_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Download') or contains(text(), 'download')]")
            logging.info(f"📥 Found {len(download_buttons)} download buttons")
            
            for button in download_buttons:
                try:
                    text = button.text.strip()
                    logging.info(f"📥 Download button: {text}")
                except:
                    continue
                    
        except Exception as e:
            logging.debug(f"Could not find download buttons: {e}")
        
        # Check for any file lists or tables
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            logging.info(f"📊 Found {len(tables)} tables")
            
            for i, table in enumerate(tables):
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    logging.info(f"📊 Table {i+1}: {len(rows)} rows")
                    
                    for row in rows[:5]:  # Show first 5 rows
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            row_text = " | ".join([cell.text.strip() for cell in cells if cell.text.strip()])
                            if row_text:
                                logging.info(f"  Row: {row_text}")
                        except:
                            continue
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            logging.debug(f"Could not find tables: {e}")
        
        if downloaded_files:
            logging.info(f"✅ Successfully downloaded {len(downloaded_files)} files for past 7 days")
            logging.info("📁 Downloaded files:")
            for file_path in downloaded_files:
                logging.info(f"  - {os.path.basename(file_path)}")
            return True
        else:
            logging.warning("⚠️ No files downloaded for past 7 days")
            logging.info("💡 The files might be in a different location or require authentication")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error during extraction: {e}")
        return False
        
    finally:
        driver.quit()
        logging.info("🔚 Browser closed")

if __name__ == "__main__":
    extract_past_7_days_data()
