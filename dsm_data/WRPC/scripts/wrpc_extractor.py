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
        logging.FileHandler('wrpc_extractor.log')
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
    logging.info("🚀 Starting WRPC data extraction for past 7 days...")
    
    # Create data directory
    os.makedirs(WRPC_DATA_DIR, exist_ok=True)
    
    driver = setup_chrome_driver()
    if not driver:
        return False
    
    try:
        logging.info(f"🌐 Accessing WRPC website...")
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
        logging.info(f"📄 Page loaded successfully")
        
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
        
        # Show summary by date
        logging.info("📊 Summary by date:")
        for date_str in date_patterns:
            date_files = [f for f in found_files if date_str in f]
            if date_files:
                count = len(date_files)
                logging.info(f"  📅 {date_str}: {count} files")
                for file in date_files[:3]:  # Show first 3 files
                    logging.info(f"    - {file}")
            else:
                logging.info(f"  📅 {date_str}: 0 files")
        
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
