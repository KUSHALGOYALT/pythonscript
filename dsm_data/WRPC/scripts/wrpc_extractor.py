#!/usr/bin/env python3
import os
import glob
import logging
import requests
import zipfile
import re
import csv
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wrpc_extractor.log')
    ]
)

WRPC_DATA_DIR = "../data"
OUTPUT_DIR = "../data"
WRPC_BASE_URL = "https://www.wrpc.gov.in"
WRPC_DSM_URL = "https://www.wrpc.gov.in/menu/DSMUI%20Account%20_342"

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}

def create_directories():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(WRPC_DATA_DIR, exist_ok=True)
    logging.info(f"✅ Created directory: {OUTPUT_DIR}")
    logging.info(f"✅ Created directory: {WRPC_DATA_DIR}")

def get_session():
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    return session

def load_learned_patterns():
    pattern_file = os.path.join(WRPC_DATA_DIR, "successful_patterns.txt")
    patterns = []
    
    try:
        if os.path.exists(pattern_file):
            with open(pattern_file, 'r') as f:
                patterns = [line.strip() for line in f.readlines() if line.strip()]
            logging.info(f"📚 Loaded {len(patterns)} learned patterns")
    except Exception as e:
        logging.debug(f"Could not load patterns: {e}")
    
    return patterns

def save_successful_pattern(pattern):
    try:
        pattern_file = os.path.join(WRPC_DATA_DIR, "successful_patterns.txt")
        
        existing_patterns = []
        if os.path.exists(pattern_file):
            with open(pattern_file, 'r') as f:
                existing_patterns = [line.strip() for line in f.readlines() if line.strip()]
        
        if pattern not in existing_patterns:
            existing_patterns.append(pattern)
            
            if len(existing_patterns) > 50:
                existing_patterns = existing_patterns[-50:]
            
            with open(pattern_file, 'w') as f:
                for p in existing_patterns:
                    f.write(f"{p}\n")
            
            logging.info(f"📚 Learned new successful pattern: {pattern}")
        
    except Exception as e:
        logging.debug(f"Could not save pattern: {e}")

def generate_dynamic_time_patterns():
    patterns = []
    
    learned_patterns = load_learned_patterns()
    
    if learned_patterns:
        for pattern in learned_patterns:
            if len(pattern) >= 14:
                patterns.append(pattern)
            elif len(pattern) >= 8:
                patterns.extend(generate_common_times_for_date(pattern))
    
    if not patterns:
        patterns = generate_systematic_time_patterns()
    
    return patterns

def generate_common_times_for_date(date_pattern):
    times = []
    
    for hour in range(24):
        for minute in range(60):
            time_str = f"{hour:02d}{minute:02d}000000"
            times.append(f"{date_pattern}{time_str}")
    
    return times

def generate_systematic_time_patterns():
    patterns = []
    
    for hour in range(24):
        for minute in range(60):
            patterns.append(f"{hour:02d}{minute:02d}000000")
    
    return patterns

def detect_new_columns(file_path):
    """Detect and log all columns in the file for dynamic processing"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            if not header:
                return []
            
            # Log all columns found in the file
            logging.info(f"📋 All columns in {os.path.basename(file_path)}: {header}")
            
            # Save all columns for future reference and analysis
            save_column_patterns(header, header)
            
            return header  # Return all columns for dynamic processing
            
    except Exception as e:
        logging.debug(f"Could not detect columns: {e}")
        return []

def save_column_patterns(all_columns, new_columns):
    """Save all column patterns for dynamic analysis"""
    try:
        column_file = os.path.join(WRPC_DATA_DIR, "column_patterns.txt")
        
        # Read existing patterns
        existing_patterns = set()
        if os.path.exists(column_file):
            with open(column_file, 'r') as f:
                existing_patterns = set(line.strip() for line in f.readlines())
        
        # Add all new columns (not just "new" ones)
        all_patterns = existing_patterns.union(set(all_columns))
        
        # Save updated patterns
        with open(column_file, 'w') as f:
            for pattern in sorted(all_patterns):
                f.write(f"{pattern}\n")
        
        logging.info(f"📝 Updated column patterns file with {len(all_columns)} total columns")
        
    except Exception as e:
        logging.debug(f"Could not save column patterns: {e}")

def download_from_wrpc_website():
    """Download DSM data files from the WRPC website - Simple approach"""
    logging.info("🌐 Attempting to download data from WRPC website...")
    
    session = get_session()
    
    try:
        # Try to access the DSM page
        logging.info(f"🔍 Accessing: {WRPC_DSM_URL}")
        response = session.get(WRPC_DSM_URL, timeout=30, verify=True)
        
        if response.status_code != 200:
            logging.error(f"❌ Failed to access WRPC website. Status code: {response.status_code}")
            return False
        
        logging.info("✅ Successfully accessed WRPC website")
        
        # Parse the page content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for any ZIP files in the page content
        download_links = []
        downloaded_files = []
        
        # Method 1: Look for direct file links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.zip' in href.lower():
                download_links.append(href)
                logging.info(f"📎 Found ZIP file link: {href}")
        
        # Method 2: Look for any ZIP file patterns in the page text
        content_text = response.text
        # Find any pattern that looks like: allfile/[anything].zip
        zip_patterns = [
            r'allfile/[a-zA-Z0-9_-]+\.zip',  # allfile/ + anything + .zip
            r'[a-zA-Z0-9_-]+\.zip',  # any .zip file
            r'\d{8,20}[a-zA-Z0-9_-]*\.zip',  # numbers + anything + .zip
        ]
        
        for pattern in zip_patterns:
            matches = re.findall(pattern, content_text)
            for match in matches:
                if match not in download_links:
                    download_links.append(match)
                    logging.info(f"📎 Found ZIP file pattern: {match}")
        
        # Method 3: Try to download files from found links
        for file_link in download_links:
            try:
                # Construct full URL
                if file_link.startswith('http'):
                    file_url = file_link
                elif file_link.startswith('allfile/'):
                    file_url = f"{WRPC_BASE_URL}/{file_link}"
                else:
                    file_url = f"{WRPC_BASE_URL}/allfile/{file_link}"
                
                logging.info(f"📥 Attempting to download: {file_url}")
                file_response = session.get(file_url, timeout=30, verify=True)
                
                if file_response.status_code == 200 and len(file_response.content) > 1000:
                    # Extract filename from URL
                    filename = os.path.basename(urlparse(file_url).path)
                    if not filename:
                        filename = f"downloaded_file_{len(downloaded_files)}.zip"
                    
                    file_path = os.path.join(WRPC_DATA_DIR, filename)
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_response.content)
                    
                    logging.info(f"✅ Successfully downloaded: {filename} ({len(file_response.content)} bytes)")
                    downloaded_files.append(file_path)
                    
                    # Process the downloaded ZIP file
                    process_zip_file(file_path)
                
            except Exception as e:
                logging.warning(f"⚠️ Error downloading {file_link}: {e}")
                continue
        
        # Method 4: Try dynamic file patterns for recent dates
        if not downloaded_files:
            logging.info("🔍 Trying dynamic file patterns for recent dates...")
            current_date = datetime.now()
            
            # Try last 7 days
            for days_back in range(7):
                test_date = current_date - timedelta(days=days_back)
                date_str = test_date.strftime('%d%m%Y')
                
                # Smart approach: Scrape website to find actual file timestamps
                logging.info(f"🔍 Smart scraping for actual file timestamps on {date_str}...")
                
                # Try to access the DSM page to find actual files
                try:
                    logging.info(f"🌐 Accessing WRPC website to find actual files...")
                    response = session.get(WRPC_DSM_URL, timeout=30, verify=True)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for any ZIP files with our date pattern
                        found_files = []
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if '.zip' in href.lower() and date_str in href:
                                found_files.append(href)
                                logging.info(f"🎯 Found file with date {date_str}: {href}")
                        
                        # Also check page content for file patterns
                        content_text = response.text
                        import re
                        
                        # Look for ZIP file patterns in the page content
                        zip_patterns = re.findall(rf'{date_str}\d{{8,14}}\.zip', content_text)
                        for pattern in zip_patterns:
                            if pattern not in found_files:
                                found_files.append(pattern)
                                logging.info(f"🎯 Found file pattern in content: {pattern}")
                        
                        # Download found files
                        for file_pattern in found_files:
                            # Extract the actual timestamp from the filename
                            if date_str in file_pattern:
                                # Try different URL paths for the file
                                possible_urls = [
                                    f"{WRPC_BASE_URL}/allfile/{file_pattern}",
                                    f"{WRPC_BASE_URL}/uploads/{file_pattern}",
                                    f"{WRPC_BASE_URL}/files/{file_pattern}",
                                    f"{WRPC_BASE_URL}/data/{file_pattern}"
                                ]
                                
                                for url in possible_urls:
                                    try:
                                        logging.debug(f"🔍 Testing found file: {url}")
                                        file_response = session.get(url, timeout=10, verify=True)
                                        
                                        if file_response.status_code == 200 and len(file_response.content) > 1000:
                                            file_path = os.path.join(WRPC_DATA_DIR, file_pattern)
                                            with open(file_path, 'wb') as f:
                                                f.write(file_response.content)
                                            
                                            logging.info(f"✅ Successfully downloaded: {file_pattern} ({len(file_response.content)} bytes)")
                                            downloaded_files.append(file_path)
                                            process_zip_file(file_path)
                                            
                                            # Learn this successful pattern for future use
                                            save_successful_pattern(file_pattern.replace(date_str, ''))
                                            
                                            break  # Found this file, try next one
                                            
                                    except Exception as e:
                                        logging.debug(f"⚠️ Failed to access {url}: {e}")
                                        continue
                        
                        if found_files:
                            logging.info(f"🎯 Found {len(found_files)} files with date {date_str}")
                        else:
                            logging.info(f"📭 No files found with date {date_str} on website")
                    
                except Exception as e:
                    logging.warning(f"⚠️ Error scraping website: {e}")
                
                # If we found files for this date, move to next date
                if any(f"{date_str}" in f for f in downloaded_files):
                    break
        
        if downloaded_files:
            logging.info(f"✅ Successfully downloaded {len(downloaded_files)} files")
            return True
        else:
            logging.warning("⚠️ No ZIP files were found or downloaded")
            logging.info("💡 The website might require authentication or use dynamic content")
            return False
        
        # Try to download files from found links
        for file_link in download_links:
            try:
                # Construct full URL
                if file_link.startswith('http'):
                    file_url = file_link
                else:
                    file_url = urljoin(WRPC_BASE_URL, file_link)
                
                logging.info(f"📥 Downloading: {file_url}")
                file_response = session.get(file_url, timeout=30, verify=True)
                
                if file_response.status_code == 200 and len(file_response.content) > 1000:
                    # Extract filename from URL
                    filename = os.path.basename(urlparse(file_url).path)
                    if not filename:
                        filename = f"downloaded_file_{len(downloaded_files)}.zip"
                    
                    file_path = os.path.join(WRPC_DATA_DIR, filename)
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_response.content)
                    
                    logging.info(f"✅ Downloaded: {filename} ({len(file_response.content)} bytes)")
                    downloaded_files.append(file_path)
                
            except Exception as e:
                logging.warning(f"⚠️ Error processing {file_link}: {e}")
                continue
        
        if downloaded_files:
            logging.info(f"✅ Successfully downloaded {len(downloaded_files)} files")
            
            # Learn from successful downloads for future runs
            successful_patterns = []
            for file_path in downloaded_files:
                filename = os.path.basename(file_path)
                # Look for any sum*.zip pattern
                if 'sum' in filename and '.zip' in filename:
                    # Extract the time pattern from successful download
                    for ext in ['sum4.zip', 'sum3a.zip', 'sum3.zip', 'sum2.zip', 'sum1.zip']:
                        if ext in filename:
                            time_part = filename.replace(ext, '')
                            if len(time_part) >= 8:  # At least date part
                                successful_patterns.append(time_part)
                            break
            
            if successful_patterns:
                logging.info(f"📚 Learned successful patterns: {successful_patterns[:3]}...")
                # Save patterns for future reference using the new function
                for pattern in successful_patterns:
                    save_successful_pattern(pattern)
          
            return True
        else:
            logging.warning("⚠️ No files were successfully downloaded")
            logging.info("💡 The website might require authentication or use dynamic content")
            return False
        
        # Try to download files from found links
        for file_link in download_links:
            try:
                # Construct full URL
                if file_link.startswith('http'):
                    file_url = file_link
                else:
                    file_url = urljoin(WRPC_BASE_URL, file_link)
                
                logging.info(f"📥 Downloading: {file_url}")
                file_response = session.get(file_url, timeout=30, verify=True)
                
                if file_response.status_code == 200 and len(file_response.content) > 1000:
                    # Extract filename from URL
                    filename = os.path.basename(urlparse(file_url).path)
                    if not filename:
                        filename = f"downloaded_file_{len(downloaded_files)}.zip"
                    
                    file_path = os.path.join(WRPC_DATA_DIR, filename)
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_response.content)
                    
                    logging.info(f"✅ Downloaded: {filename} ({len(file_response.content)} bytes)")
                    downloaded_files.append(file_path)
                
            except Exception as e:
                logging.warning(f"⚠️ Error processing {file_link}: {e}")
                continue
        
        if downloaded_files:
            logging.info(f"✅ Successfully downloaded {len(downloaded_files)} files")
            return True
        else:
            logging.warning("⚠️ No files were successfully downloaded")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error accessing WRPC website: {e}")
        return False

def get_csv_files():
    """Get all CSV files in the WRPC data directory"""
    csv_pattern = os.path.join(WRPC_DATA_DIR, "**/*.csv")
    csv_files = glob.glob(csv_pattern, recursive=True)
    
    # Filter out empty files, schedule files, and already processed files
    valid_files = []
    for file_path in csv_files:
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # Skip empty files, schedule files, and already processed files
        if (file_size > 0 and 
            "schedule" not in filename.lower() and
            "_processed" not in filename and
            "Summary_Report" not in filename):
            valid_files.append(file_path)
    
    logging.info(f"📁 Found {len(valid_files)} valid CSV files")
    return valid_files

def validate_csv_structure(file_path):
    """Validate if CSV file has basic structure - Fully dynamic validation"""
    try:
        # Read first few lines to check structure
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            if not header:
                logging.warning(f"⚠️ Empty file: {os.path.basename(file_path)}")
                return False
            
            # Check if file has at least some data rows
            try:
                first_data_row = next(reader, None)
                if not first_data_row:
                    logging.warning(f"⚠️ No data rows in {os.path.basename(file_path)}")
                    return False
            except:
                logging.warning(f"⚠️ Cannot read data from {os.path.basename(file_path)}")
                return False
            
            # Log the columns found for transparency
            logging.info(f"📊 File structure: {os.path.basename(file_path)} - Found {len(header)} columns")
            logging.info(f"📋 Columns: {', '.join(header[:5])}{'...' if len(header) > 5 else ''}")
            
            # Any CSV with headers and data is considered valid
            return True
        
    except Exception as e:
        logging.error(f"❌ Error validating {os.path.basename(file_path)}: {e}")
        return False

def extract_constituent_name(file_path):
    """Extract constituent name from filename"""
    filename = os.path.basename(file_path)
    
    # Remove common suffixes
    name = filename.replace('_DSM-2024_Data.csv', '')
    name = name.replace('_DSM-2024_Data', '')
    
    return name

def process_csv_file(file_path):
    """Process a single CSV file with dynamic column handling"""
    try:
        filename = os.path.basename(file_path)
        constituent = extract_constituent_name(file_path)
        
        logging.info(f"📊 Processing: {filename}")
        
        # Read the CSV file to check if it's valid
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            if len(rows) <= 1:  # Only header or empty
                logging.warning(f"⚠️ Empty file: {filename}")
                return None
        
        # Detect and log all columns for dynamic processing
        all_columns = detect_new_columns(file_path)
        
        # Copy file to output directory with original structure preserved
        output_filename = f"{constituent}_extracted.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        with open(file_path, 'r', encoding='utf-8') as source:
            with open(output_path, 'w', encoding='utf-8', newline='') as target:
                target.write(source.read())
        
        logging.info(f"💾 Extracted data: {output_filename}")
        logging.info(f"📋 Preserved {len(all_columns)} columns: {', '.join(all_columns[:3])}{'...' if len(all_columns) > 3 else ''}")
        
        return {
            'constituent': constituent,
            'filename': filename,
            'output_file': output_filename,
            'total_records': len(rows) - 1,  # Exclude header
            'columns': all_columns,
            'column_count': len(all_columns)
        }
        
    except Exception as e:
        logging.error(f"❌ Error processing {os.path.basename(file_path)}: {e}")
        return None

def process_zip_file(file_path):
    """Process a ZIP file and extract its contents"""
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # List contents
            file_list = zip_ref.namelist()
            logging.info(f"📦 ZIP contents: {file_list}")
            
            # Extract all files
            zip_ref.extractall(WRPC_DATA_DIR)
            logging.info(f"✅ Extracted {len(file_list)} files from ZIP")
            
            return file_list
            
    except Exception as e:
        logging.error(f"❌ Error processing ZIP file: {e}")
        return []

def generate_simple_report(processed_files):
    """Generate a dynamic report of processed files"""
    if not processed_files:
        logging.warning("⚠️ No files to report")
        return
    
    # Create dynamic report
    report_path = os.path.join(OUTPUT_DIR, "WRPC_Extraction_Report.txt")
    with open(report_path, 'w') as f:
        f.write("WRPC Dynamic Data Extraction Report\n")
        f.write("=" * 45 + "\n\n")
        
        f.write(f"Total Files Processed: {len(processed_files)}\n")
        f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Processing Mode: Dynamic (No fixed column requirements)\n\n")
        
        f.write("Processed Files:\n")
        f.write("-" * 20 + "\n")
        for file_info in processed_files:
            if file_info:
                f.write(f"• {file_info['constituent']}: {file_info['total_records']} records, {file_info['column_count']} columns\n")
                f.write(f"  Output: {file_info['output_file']}\n")
                f.write(f"  Columns: {', '.join(file_info['columns'][:5])}{'...' if len(file_info['columns']) > 5 else ''}\n\n")
        
        f.write(f"\nTotal Records Extracted: {sum(f['total_records'] for f in processed_files if f)}\n")
        f.write(f"Total Columns Discovered: {len(set().union(*[set(f['columns']) for f in processed_files if f]))}\n")
        f.write(f"\nNote: All files processed with original column structure preserved\n")
    
    logging.info(f"📊 Generated dynamic extraction report: {report_path}")

def main():
    """Main function to run the WRPC dynamic data extraction"""
    logging.info("🔄 Starting WRPC dynamic data extraction...")
    
    # Create directories
    create_directories()
    
    # Get all CSV files
    csv_files = get_csv_files()
    
    if not csv_files:
        logging.warning("⚠️ No CSV files found in WRPC data directory")
        logging.info("🌐 Attempting to download fresh data from WRPC website...")
        
        # Try to download from website
        download_success = download_from_wrpc_website()
        
        if download_success:
            # Process any downloaded ZIP files
            zip_files = glob.glob(os.path.join(WRPC_DATA_DIR, "*.zip"))
            for zip_file in zip_files:
                process_zip_file(zip_file)
            
            # Re-check for CSV files after download
            csv_files = get_csv_files()
            if not csv_files:
                logging.error("❌ Still no CSV files found after download attempt")
                logging.info("💡 The website might require authentication or the data format has changed")
                return
        else:
            logging.error("❌ Failed to download data from WRPC website")
            logging.info("💡 The website might require authentication or use dynamic content")
            logging.info("💡 Manual download instructions:")
            logging.info("   1. Visit: https://www.wrpc.gov.in/menu/DSMUI%20Account%20_342")
            logging.info("   2. Look for download links or file attachments")
            logging.info("   3. Download CSV or ZIP files")
            logging.info("   4. Place the files in: dsm_data/WRPC/data/")
            logging.info("   5. Run this script again")
            return
    
    # Process each file with dynamic column handling
    processed_files = []
    processed_count = 0
    
    for file_path in csv_files:
        # Validate basic file structure (any CSV with headers and data)
        if validate_csv_structure(file_path):
            file_info = process_csv_file(file_path)
            if file_info:
                processed_files.append(file_info)
                processed_count += 1
        else:
            logging.warning(f"⚠️ Skipping invalid file: {os.path.basename(file_path)}")
    
    # Generate dynamic report
    if processed_files:
        generate_simple_report(processed_files)
        
        logging.info(f"✅ WRPC dynamic extraction completed successfully!")
        logging.info(f"📊 Processed {processed_count} files out of {len(csv_files)} total files")
        logging.info(f"📁 Output files saved in: {OUTPUT_DIR}")
        logging.info(f"📈 Total records extracted: {sum(f['total_records'] for f in processed_files)}")
        logging.info(f"🔍 Total unique columns discovered: {len(set().union(*[set(f['columns']) for f in processed_files if f]))}")
    else:
        logging.error("❌ No files were successfully processed")

if __name__ == "__main__":
    main()
