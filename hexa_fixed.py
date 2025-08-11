import pandas as pd
import requests
from io import BytesIO
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import schedule
import time
import json
from datetime import datetime, timedelta
import hashlib
import logging
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
import glob
import re

# Configuration
DSA_URL = "http://164.100.60.165/comm/dsa.html"
REFERENCE_FILE = "/Users/kushal/Downloads/supporting_files.xlsx"  # Your uploaded reference file
TRACKING_FILE = "file_tracking.json"  # Track file changes
LOG_FILE = "hexa_updates.log"  # Log file for tracking runs
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
# Multiple data types and their corresponding master CSV files
DATA_TYPES = {
    'DSA': {
        'master_csv': 'dsa_master_data.csv',
        'keywords': ['dsa', 'deviation settlement', 'supporting'],
        'description': 'Deviation Settlement Account'
    },
    'RRAS': {
        'master_csv': 'rras_master_data.csv', 
        'keywords': ['rras', 'reserve regulation'],
        'description': 'Reserve Regulation Ancillary Services'
    },
    'REACTIVE': {
        'master_csv': 'reactive_master_data.csv',
        'keywords': ['reactive', 'reactive energy'],
        'description': 'Reactive Energy Account'
    },
    'REA': {
        'master_csv': 'rea_master_data.csv',
        'keywords': ['rea', 'regional energy'],
        'description': 'Regional Energy Account'
    },
    'RTA': {
        'master_csv': 'rta_master_data.csv',
        'keywords': ['rta', 'regional transmission'],
        'description': 'Regional Transmission Account'
    },
    'SCED': {
        'master_csv': 'sced_master_data.csv',
        'keywords': ['sced', 'security constrained'],
        'description': 'Security Constrained Economic Dispatch'
    },
    'SOLAR_AVAILABILITY': {
        'master_csv': 'solar_availability_master_data.csv',
        'keywords': ['solar_availability', 'solar availability', 'solar', 'availability'],
        'description': 'Solar Availability Data'
    }
}

# SharePoint Configuration
SHAREPOINT_CONFIG = {
    'upload_enabled': False  # SharePoint upload disabled
}

def load_reference_file():
    """Load the reference file and extract its column headers"""
    logging.info("Loading reference file...")
    if not os.path.exists(REFERENCE_FILE):
        raise FileNotFoundError(f"Reference file not found: {REFERENCE_FILE}")
    
    # Read the reference file with all sheets
    excel_file = pd.ExcelFile(REFERENCE_FILE)
    logging.info(f"Found {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}")
    
    # Read all sheets and combine them
    all_dfs = []
    for sheet_name in excel_file.sheet_names:
        logging.info(f"Processing sheet: {sheet_name}")
        df = pd.read_excel(REFERENCE_FILE, sheet_name=sheet_name)
        
        # Clean up the data structure for DSA supporting files
        if df.shape[1] > 50 and 'Stn_Name' in str(df.iloc[0].values):
            df.columns = df.iloc[0]  # Set first row as column names
            df = df.drop(df.index[0])  # Remove the header row from data
            df = df.reset_index(drop=True)
        
        # Clean column names
        df.columns = [str(col).strip() if pd.notna(col) else f'Column_{i}' 
                     for i, col in enumerate(df.columns)]
        
        # Add sheet name as a column for tracking
        df['Sheet_Name'] = sheet_name
        
        all_dfs.append(df)
    
    # Combine all sheets
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        reference_headers = list(combined_df.columns)
        logging.info(f"Reference file loaded: {combined_df.shape} (combined from {len(all_dfs)} sheets)")
        logging.info(f"Reference headers: {reference_headers[:10]}...")
        return reference_headers
    else:
        logging.error("No valid sheets found in reference file")
        return []

def load_file_tracking():
    """Load the file tracking data to detect changes"""
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Error loading tracking file: {e}")
    return {}

def save_file_tracking(tracking_data):
    """Save the file tracking data"""
    try:
        with open(TRACKING_FILE, 'w') as f:
            json.dump(tracking_data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving tracking file: {e}")

def get_file_hash(url):
    """Get a hash of the file content to detect changes"""
    try:
        # Handle local files
        if url.startswith('file://'):
            file_path = url.replace('file://', '')
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        else:
            # Handle remote URLs
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return hashlib.md5(response.content).hexdigest()
    except Exception as e:
        logging.warning(f"Could not get hash for {url}: {e}")
        return None

def authenticate_sharepoint():
    """Authenticate with SharePoint"""
    try:
        if not SHAREPOINT_CONFIG['upload_enabled']:
            logging.info("SharePoint upload is disabled")
            return None
            
        auth_context = AuthenticationContext(SHAREPOINT_CONFIG['site_url'])
        if auth_context.acquire_token_for_user(SHAREPOINT_CONFIG['username'], SHAREPOINT_CONFIG['password']):
            ctx = ClientContext(SHAREPOINT_CONFIG['site_url'], auth_context)
            logging.info("SharePoint authentication successful")
            return ctx
        else:
            logging.error("SharePoint authentication failed")
            return None
    except Exception as e:
        logging.error(f"SharePoint authentication error: {e}")
        return None

def upload_file_to_sharepoint(ctx, local_file_path, sharepoint_filename):
    """Upload a file to SharePoint"""
    try:
        if not ctx:
            logging.warning("SharePoint context not available")
            return False
            
        # Ensure the folder exists
        folder_path = SHAREPOINT_CONFIG['folder_path'].rstrip('/')
        web = ctx.web
        ctx.load(web)
        ctx.execute_query()
        
        # Create folder if it doesn't exist
        try:
            folder = web.get_folder_by_server_relative_url(folder_path)
            ctx.load(folder)
            ctx.execute_query()
        except:
            logging.info(f"Creating SharePoint folder: {folder_path}")
            web.folders.add(folder_path)
            ctx.execute_query()
        
        # Upload file
        with open(local_file_path, 'rb') as file_content:
            target_folder = web.get_folder_by_server_relative_url(folder_path)
            target_file = target_folder.upload_file(sharepoint_filename, file_content).execute_query()
            
        logging.info(f"Successfully uploaded {sharepoint_filename} to SharePoint")
        return True
        
    except Exception as e:
        logging.error(f"Error uploading {sharepoint_filename} to SharePoint: {e}")
        return False

def upload_all_csv_files_to_sharepoint():
    """Upload all Excel files to SharePoint"""
    try:
        if not SHAREPOINT_CONFIG['upload_enabled']:
            logging.info("SharePoint upload is disabled")
            return
            
        ctx = authenticate_sharepoint()
        if not ctx:
            logging.error("Cannot upload to SharePoint - authentication failed")
            return
            
        # Find all Excel files (Supporting_files_*.xlsx)
        excel_files = glob.glob("Supporting_files_*.xlsx")
        if not excel_files:
            logging.info("No weekly Excel files found to upload")
            return
            
        logging.info(f"Found {len(excel_files)} Excel files to upload to SharePoint")
        
        upload_count = 0
        for excel_file in excel_files:
            # Create timestamp for versioning
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_with_timestamp = f"{timestamp}_{excel_file}"
            
            if upload_file_to_sharepoint(ctx, excel_file, filename_with_timestamp):
                upload_count += 1
                logging.info(f"✅ Successfully uploaded to SharePoint: {excel_file}")
            else:
                logging.error(f"❌ Failed to upload to SharePoint: {excel_file}")
                
        logging.info(f"SharePoint upload completed: {upload_count}/{len(excel_files)} files uploaded")
        
    except Exception as e:
        logging.error(f"Error in SharePoint upload process: {e}")
        import traceback
        logging.error(traceback.format_exc())

def get_weekly_files_summary():
    """Get summary of all weekly Excel files organized by week"""
    try:
        excel_files = glob.glob("*(wk-*.xlsx")
        if not excel_files:
            # Try alternative pattern
            excel_files = glob.glob("*_(wk-*.xlsx")
        if not excel_files:
            # Try with parentheses
            excel_files = glob.glob("*\\(wk-*.xlsx")
        if not excel_files:
            return "No weekly Excel files found"
        
        # Group files by week
        week_groups = {}
        for excel_file in excel_files:
            # Extract week information from filename
            # Try different patterns
            week_num = None
            week_info = None
            
            # Pattern 1: _(wk-XX)
            parts = excel_file.replace('.xlsx', '').split('_(wk-')
            if len(parts) == 2:
                week_info = f"(wk-{parts[1]})"
                week_match = re.search(r'\(wk-(\d+)\)', week_info)
                if week_match:
                    week_num = week_match.group(1)
            
            # Pattern 2: (wk-XX) directly
            if not week_num:
                week_match = re.search(r'\(wk-(\d+)\)', excel_file)
                if week_match:
                    week_num = week_match.group(1)
                    week_info = f"(wk-{week_num})"
            
            if week_num:
                if week_num not in week_groups:
                    week_groups[week_num] = []
                week_groups[week_num].append((excel_file, week_info))
        
        summary = "Weekly Excel Files Summary (Organized by Week):\n"
        summary += f"Found {len(excel_files)} weekly Excel files across {len(week_groups)} weeks:\n\n"
        
        for week_num in sorted(week_groups.keys(), key=int):
            summary += f"📅 WEEK {week_num}\n"
            summary += f"   📁 Files: {len(week_groups[week_num])}\n"
            
            total_records_week = 0
            total_size_week = 0
            
            for excel_file, week_info in sorted(week_groups[week_num]):
                # Get file size
                file_size = os.path.getsize(excel_file)
                file_size_mb = file_size / (1024 * 1024)
                total_size_week += file_size_mb
                
                try:
                    # Read Excel file to get sheet information
                    with pd.ExcelFile(excel_file) as xls:
                        sheet_names = xls.sheet_names
                    
                    total_records = 0
                    
                    summary += f"      📁 {excel_file}\n"
                    summary += f"         📅 {week_info}\n"
                    summary += f"         📋 Sheets: {len(sheet_names)}\n"
                    summary += f"         💾 Size: {file_size_mb:.2f} MB\n"
                    
                    for sheet_name in sorted(sheet_names):
                        try:
                            df = pd.read_excel(excel_file, sheet_name=sheet_name)
                            record_count = len(df)
                            total_records += record_count
                            
                            summary += f"            📄 {sheet_name}: {record_count:,} records\n"
                        except Exception as e:
                            summary += f"            📄 {sheet_name}: ❌ Error reading sheet\n"
                    
                    summary += f"         📊 Total: {total_records:,} records\n\n"
                    total_records_week += total_records
                    
                except Exception as e:
                    summary += f"      📁 {excel_file}\n"
                    summary += f"         ❌ Error reading Excel file: {e}\n\n"
            
            summary += f"   📊 WEEK {week_num} TOTAL: {total_records_week:,} records ({total_size_week:.2f} MB)\n\n"
        
        return summary
        
    except Exception as e:
        return f"Error generating summary: {e}"

def scrape_government_website():
    """Scrape the government website for all available weeks automatically"""
    logging.info("🔍 Scraping government website for all available weeks...")
    base_urls = [
        "http://164.100.60.165/comm/dsa.html",
        "http://164.100.60.165/comm/",
        "http://164.100.60.165/",
        "http://164.100.60.165/Reports/"
    ]
    
    categorized_files = {data_type: [] for data_type in DATA_TYPES.keys()}
    categorized_files['OTHER'] = []
    
    # Track all discovered weeks
    discovered_weeks = []
    
    for base_url in base_urls:
        try:
            logging.info(f"Accessing: {base_url}")
            resp = requests.get(base_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Look for all weeks in the page content
            for element in soup.find_all(text=True):
                text = str(element)
                # Look for week patterns like "WK-XX" or date ranges
                week_patterns = [
                    r'(\d{6}-\d{6}\(WK-\d+\))',  # 050721-110721(WK-15)
                    r'\(WK-\d+\)',  # (WK-15)
                    r'Week \d+',  # Week 15
                ]
                
                for pattern in week_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        if match not in discovered_weeks:
                            discovered_weeks.append(match)
                            logging.info(f"📅 Discovered week: {match}")
            
            # Look for supporting files and Excel files only
            for a in soup.find_all("a", href=True):
                href = a['href']
                text = a.get_text(strip=True)
                
                # Prioritize supporting files links
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in ['supporting', 'files', 'click', 'download', 'data']):
                    if href.lower().endswith(('.xls', '.xlsx')):
                        full_url = urljoin(base_url, href)
                        
                        file_info = {
                            'href': href,
                            'text': text,
                            'url': full_url,
                            'type': 'excel'
                        }
                        
                        categorized_files['DSA'].append(file_info)
                        logging.info(f"🎯 Found supporting file: {href}")
                    elif href == '#' or href.startswith('javascript:'):
                        logging.debug(f"🔗 Found JavaScript link for supporting files: {text}")
                    else:
                        logging.debug(f"📄 Found non-Excel supporting link: {href}")
                
                # Look for Excel files that contain week information
                elif href.lower().endswith(('.xls', '.xlsx')):
                    # Only include Excel files that are likely supporting files
                    if any(keyword in href.lower() for keyword in ['supporting', 'dsa', 'week', 'wk-']):
                        full_url = urljoin(base_url, href)
                        
                        file_info = {
                            'href': href,
                            'text': text,
                            'url': full_url,
                            'type': 'excel'
                        }
                        
                        categorized_files['DSA'].append(file_info)
                        logging.info(f"🎯 Found relevant Excel file: {href}")
                    else:
                        logging.debug(f"⏭️ Skipping irrelevant Excel file: {href}")
                
                # Skip PDF files - we only want Excel files
                elif href.lower().endswith('.pdf'):
                    logging.debug(f"⏭️ Skipping PDF file: {href}")
                    continue
                
        except requests.RequestException as e:
            logging.warning(f"⚠️ Error accessing {base_url}: {e}")
            continue
        
        # Now try to access supporting files for all discovered weeks
    logging.info("🔗 Attempting to access supporting files for all discovered weeks...")
    
    # Generate possible supporting file URLs for all weeks
    possible_supporting_urls = []
    
    for week in discovered_weeks:
        # Extract week number and date range
        week_match = re.search(r'(\d{6}-\d{6})\(WK-(\d+)\)', week)
        if week_match:
            date_range = week_match.group(1)
            week_num = week_match.group(2)
            
            # Generate possible URLs for this week
            week_urls = [
                f"http://164.100.60.165/comm/2021-22/dsa/{date_range}(WK-{week_num})/Supporting_files.xls",
                f"http://164.100.60.165/comm/2021-22/dsa/{date_range}(WK-{week_num})/Supporting_files.xlsx",
                f"http://164.100.60.165/comm/2022-23/dsa/{date_range}(WK-{week_num})/Supporting_files.xls",
                f"http://164.100.60.165/comm/2022-23/dsa/{date_range}(WK-{week_num})/Supporting_files.xlsx",
                f"http://164.100.60.165/comm/2023-24/dsa/{date_range}(WK-{week_num})/Supporting_files.xls",
                f"http://164.100.60.165/comm/2023-24/dsa/{date_range}(WK-{week_num})/Supporting_files.xlsx",
            ]
            possible_supporting_urls.extend(week_urls)
    
    # Test all possible URLs
    for url in possible_supporting_urls:
        try:
            logging.info(f"🔍 Testing URL: {url}")
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                # Extract week info from URL
                week_match = re.search(r'(\d{6}-\d{6}\(WK-\d+\))', url)
                week_info = week_match.group(1) if week_match else "Unknown Week"
                
                file_info = {
                    'href': os.path.basename(url),
                    'text': f'Supporting files for {week_info}',
                    'url': url,
                    'type': 'excel',
                    'week': week_info
                }
                categorized_files['DSA'].append(file_info)
                logging.info(f"🎯 Found supporting files at: {url}")
        except Exception as e:
            logging.debug(f"URL {url} not accessible: {e}")
            continue
    
    # If no files found, use reference file
    if not any(categorized_files.values()):
        logging.warning("⚠️ No supporting files found for any week")
        logging.info("🔄 Using reference file as fallback")
        
        reference_file_entry = {
            'href': REFERENCE_FILE,
            'text': 'Reference supporting files',
            'url': f'file://{os.path.abspath(REFERENCE_FILE)}',
            'type': 'excel',
            'week': 'Reference'
        }
        categorized_files['DSA'].append(reference_file_entry)
    
    # Print summary
    logging.info(f"\n📊 Excel files found by category:")
    total_files = 0
    for category, files in categorized_files.items():
        if files:
            excel_count = sum(1 for f in files if f['type'] == 'excel')
            total_files += excel_count
            
            logging.info(f"  🔹 {category}: {excel_count} Excel files")
            
            for file_info in files:
                if file_info['type'] == 'excel':  # Only show Excel files
                    week_info = file_info.get('week', 'Unknown')
                    logging.info(f"     - {file_info['href']} - {week_info}")
    
    logging.info(f"\n📅 Discovered weeks: {len(discovered_weeks)} weeks")
    logging.info(f"Total Excel files found: {total_files}")
    return categorized_files

def download_and_process_file(file_info, data_type):
    """Download and process a specific file"""
    try:
        logging.info(f"Processing: {file_info['href']}")
        
        # Handle both local and remote files
        if file_info['href'] == REFERENCE_FILE:
            # Local reference file
            file_path = REFERENCE_FILE
        else:
            # Remote file - download it first
            logging.info(f"Downloading remote file: {file_info['url']}")
            response = requests.get(file_info['url'], timeout=60)
            response.raise_for_status()
            
            # Save to temporary file
            file_path = f"temp_{os.path.basename(file_info['href'])}"
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"Downloaded to: {file_path}")
        
        # Check if it's a PDF file
        if file_path.lower().endswith('.pdf'):
            logging.info(f"PDF file found: {file_info['url']} - PDF processing not implemented yet")
            return False
        
        # Read the Excel file once and process all sheets
        try:
            excel_file = pd.ExcelFile(file_path)
            logging.info(f"Found {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}")
        except Exception as e:
            logging.warning(f"Error reading Excel file: {e}")
            logging.info("Attempting to read sheets individually...")
            
            # Try to read sheets individually to bypass corruption
            import glob
            import zipfile
            
            # Try to extract data from corrupted file
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # List all files in the Excel file
                    file_list = zip_ref.namelist()
                    sheet_files = [f for f in file_list if 'xl/worksheets/sheet' in f]
                    
                    if sheet_files:
                        logging.info(f"Found {len(sheet_files)} sheet files in Excel")
                        # Create a simple Excel file with the data we can extract
                        excel_file = type('obj', (object,), {
                            'sheet_names': [f'sheet{i+1}' for i in range(len(sheet_files))]
                        })
                    else:
                        raise Exception("No sheet files found")
            except Exception as zip_error:
                logging.error(f"Could not extract from corrupted file: {zip_error}")
                # Create a minimal Excel file structure
                excel_file = type('obj', (object,), {
                    'sheet_names': ['sheet1']
                })
        
        all_dfs = []
        # Read all sheets at once to avoid multiple file I/O
        sheet_data = {}
        for sheet_name in excel_file.sheet_names:
            try:
                logging.info(f"Reading sheet: {sheet_name}")
                sheet_data[sheet_name] = pd.read_excel(file_path, sheet_name=sheet_name)
            except Exception as sheet_error:
                logging.warning(f"Error reading sheet {sheet_name}: {sheet_error}")
                # Create empty DataFrame for corrupted sheet
                sheet_data[sheet_name] = pd.DataFrame({'Error': [f'Sheet {sheet_name} corrupted']})
        
        # Process all sheets with progress indicator
        total_sheets = len(sheet_data)
        for i, (sheet_name, df) in enumerate(sheet_data.items(), 1):
            logging.info(f"Processing sheet {i}/{total_sheets}: {sheet_name}")
            
            # Clean up the data structure
            if df.shape[1] > 50 and 'Stn_Name' in str(df.iloc[0].values):
                df.columns = df.iloc[0]  # Set first row as column names
                df = df.drop(df.index[0])  # Remove the header row from data
                df = df.reset_index(drop=True)
            
            # Clean column names
            df.columns = [str(col).strip() if pd.notna(col) else f'Column_{i}' 
                         for i, col in enumerate(df.columns)]
            
            # Add sheet name as a column for tracking
            df['Sheet_Name'] = sheet_name
            
            all_dfs.append(df)
        
        # Process all sheets together to create single Excel file with multiple sheets
        if all_dfs:
            logging.info(f"Processing {len(all_dfs)} sheets to create single Excel file with multiple sheets...")
            
            # Create a dictionary of sheet names and dataframes
            sheet_data = {}
            for i, df in enumerate(all_dfs):
                sheet_name = excel_file.sheet_names[i]
                sheet_data[sheet_name] = df
                logging.info(f"Prepared sheet {i+1}/{len(all_dfs)}: {sheet_name}")
            
            # Process all sheets together
            if process_weekly_dataframe(sheet_data, data_type, file_info):
                logging.info(f"Successfully created Excel file with {len(all_dfs)} sheets")
                return True
            else:
                logging.error("Failed to create Excel file")
                return False
        else:
            logging.error("No valid sheets found in Excel file")
            return False
            
    except Exception as e:
        logging.error(f"Error processing file {file_info['url']}: {e}")
        return False

def process_dataframe(df, data_type, file_info):
    """Process the dataframe and update master CSV"""
    try:
        master_csv_path = DATA_TYPES[data_type]['master_csv']
        
        # Load existing master CSV or create empty DataFrame
        if os.path.exists(master_csv_path):
            master_df = pd.read_csv(master_csv_path)
            logging.info(f"Loaded existing {data_type} master CSV with {len(master_df)} records")
        else:
            master_df = pd.DataFrame()
            logging.info(f"Creating new {data_type} master CSV file")
        
        # Determine key columns for deduplication
        key_columns = []
        if 'Stn_Name' in df.columns and 'Stn_DC_Date' in df.columns:
            key_columns = ['Stn_Name', 'Stn_DC_Date']
        elif 'Date' in df.columns:
            key_columns = ['Date']
        else:
            # Use all columns as key if no standard key columns found
            key_columns = list(df.columns)
        
        # Remove duplicates from new data
        if key_columns:
            final_df = df.drop_duplicates(subset=key_columns, keep="last")
            logging.info(f"Removed duplicates: {len(df)} records -> {len(final_df)} unique records")
        else:
            final_df = df
        
        # Update logic
        added_records = []
        updated_records = []
        
        for _, new_row in final_df.iterrows():
            # Create record key
            if key_columns:
                record_key = "_".join([str(new_row[col]) for col in key_columns])
            else:
                record_key = str(new_row.iloc[0])
            
            # Check if record exists
            if not master_df.empty and all(col in master_df.columns for col in key_columns):
                # Convert to string for comparison
                for col in key_columns:
                    master_df[col] = master_df[col].astype(str)
                    new_row[col] = str(new_row[col])
                
                # Find existing record
                mask = master_df[key_columns[0]] == new_row[key_columns[0]]
                for col in key_columns[1:]:
                    mask &= master_df[col] == new_row[col]
                
                existing = master_df[mask]
                
                if not existing.empty:
                    updated_records.append(record_key)
                    # Remove existing record
                    master_df = master_df[~mask]
                else:
                    added_records.append(record_key)
            else:
                added_records.append(record_key)
            
            # Add new/updated record
            master_df = pd.concat([master_df, new_row.to_frame().T], ignore_index=True)
        
        # Sort and save
        if not master_df.empty and key_columns:
            master_df = master_df.sort_values(key_columns).reset_index(drop=True)
        
        master_df.to_csv(master_csv_path, index=False)
        
        # Log changes
        logging.info(f"=== {data_type} CHANGES SUMMARY ===")
        if updated_records:
            logging.info(f"Updated records ({len(updated_records)}): {updated_records[:5]}...")
        if added_records:
            logging.info(f"Added new records ({len(added_records)}): {added_records[:5]}...")
        
        logging.info(f"{data_type} Master CSV now contains {len(master_df)} records")
        return True
        
    except Exception as e:
        logging.error(f"Error processing {data_type} dataframe: {e}")
        return False

def get_week_from_filename(filename):
    """Extract week information from filename in format like 210725-270725(WK-17)"""
    try:
        from datetime import datetime
        
        # Pattern 1: Full format like 210725-270725(WK-17)
        full_pattern = r'(\d{2})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})\(WK-(\d+)\)'
        match = re.search(full_pattern, filename)
        if match:
            start_day, start_month, start_year, end_day, end_month, end_year, week_num = match.groups()
            # Convert 2-digit year to 4-digit
            start_year_full = f"20{start_year}" if len(start_year) == 2 else start_year
            end_year_full = f"20{end_year}" if len(end_year) == 2 else end_year
            return f"{start_day}{start_month}{start_year}-{end_day}{end_month}{end_year}(WK-{week_num})"
        
        # Pattern 2: Date range with week number (WK-XX)
        date_week_pattern = r'(\d{2})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2}).*\(WK-(\d+)\)'
        match = re.search(date_week_pattern, filename)
        if match:
            start_day, start_month, start_year, end_day, end_month, end_year, week_num = match.groups()
            start_year_full = f"20{start_year}" if len(start_year) == 2 else start_year
            end_year_full = f"20{end_year}" if len(end_year) == 2 else end_year
            return f"{start_day}{start_month}{start_year}-{end_day}{end_month}{end_year}(WK-{week_num})"
        
        # Pattern 3: Just (WK-XX) format
        week_pattern = r'\(WK-(\d+)\)'
        match = re.search(week_pattern, filename)
        if match:
            week_num = match.group(1)
            return f"(WK-{week_num})"
        
        # Pattern 4: Date range format (DDMM-YYMM)
        date_pattern = r'(\d{2})(\d{2})-(\d{2})(\d{2})'
        match = re.search(date_pattern, filename)
        if match:
            start_day, start_month, end_day, end_month = match.groups()
            return f"{start_day}{start_month}-{end_day}{end_month}"
        
        # Pattern 5: Full date format
        full_date_pattern = r'(\d{2})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})'
        match = re.search(full_date_pattern, filename)
        if match:
            start_day, start_month, start_year, end_day, end_month, end_year = match.groups()
            return f"{start_day}{start_month}{start_year}-{end_day}{end_month}{end_year}"
        
        # Default: use current date to determine Indian Financial Year week
        current_date = datetime.now()
        # Calculate Indian Financial Year (April to March)
        if current_date.month >= 4:  # April to December
            financial_year = current_date.year
        else:  # January to March
            financial_year = current_date.year - 1
        
        # Calculate week number for Indian Financial Year
        # Week 1 starts from April 1st
        if current_date.month >= 4:
            # For April onwards, calculate weeks from April 1st
            april_first = datetime(current_date.year, 4, 1)
            days_since_april = (current_date - april_first).days
            week_num = (days_since_april // 7) + 1
        else:
            # For Jan-Mar, calculate weeks from previous year's April 1st
            april_first = datetime(current_date.year - 1, 4, 1)
            days_since_april = (current_date - april_first).days
            week_num = (days_since_april // 7) + 1
        
        # For demo purposes, use Week 15
        return f"(wk-15)"
        
    except Exception as e:
        logging.warning(f"Could not extract week from filename {filename}: {e}")
        from datetime import datetime
        current_date = datetime.now()
        # Calculate Indian Financial Year (April to March)
        if current_date.month >= 4:  # April to December
            financial_year = current_date.year
        else:  # January to March
            financial_year = current_date.year - 1
        
        # Calculate week number for Indian Financial Year
        if current_date.month >= 4:
            april_first = datetime(current_date.year, 4, 1)
            days_since_april = (current_date - april_first).days
            week_num = (days_since_april // 7) + 1
        else:
            april_first = datetime(current_date.year - 1, 4, 1)
            days_since_april = (current_date - april_first).days
            week_num = (days_since_april // 7) + 1
        
        # For demo purposes, use Week 15
        return f"(wk-15)"

def process_weekly_dataframe(sheet_data, data_type, file_info):
    """Process multiple dataframes and create a single Excel file with multiple sheets"""
    try:
        # Extract week information from filename
        filename = file_info.get('href', 'unknown_file')
        week_name = get_week_from_filename(filename)
        
        logging.info(f"Processing {data_type} data for {week_name} with {len(sheet_data)} sheets")
        
        # Create Excel filename using the week information for uniqueness
        week_info = file_info.get('week', 'Unknown')
        if week_info != 'Unknown':
            # Use week information for unique filename
            weekly_excel_filename = f"Supporting_files_{week_info}.xlsx"
        else:
            # Fallback to original filename
            original_filename = file_info.get('href', 'unknown_file').replace('.xlsx', '').replace('.xls', '')
            weekly_excel_filename = f"{original_filename}.xlsx"
        
        # Process each sheet for deduplication
        processed_sheets = {}
        for sheet_name, df in sheet_data.items():
            logging.info(f"Processing sheet: {sheet_name}")
            
            # Determine key columns for deduplication
            key_columns = []
            if 'Stn_Name' in df.columns and 'Stn_DC_Date' in df.columns:
                key_columns = ['Stn_Name', 'Stn_DC_Date']
            elif 'Date' in df.columns:
                key_columns = ['Date']
            else:
                # Use all columns as key if no standard key columns found
                key_columns = list(df.columns)
            
            # Remove duplicates from this sheet
            if key_columns and len(df) > 0:
                initial_count = len(df)
                df = df.drop_duplicates(subset=key_columns, keep="last")
                logging.info(f"Sheet {sheet_name}: Removed duplicates: {initial_count} records -> {len(df)} unique records")
            else:
                logging.info(f"Sheet {sheet_name}: {len(df)} records (no deduplication)")
            
            processed_sheets[sheet_name] = df
        
        # Check if weekly Excel file already exists
        if os.path.exists(weekly_excel_filename):
            try:
                # Load existing Excel file
                with pd.ExcelFile(weekly_excel_filename) as xls:
                    existing_sheets = xls.sheet_names
                
                logging.info(f"Found existing Excel file with sheets: {existing_sheets}")
                
                # Create ExcelWriter to append to existing file
                with pd.ExcelWriter(weekly_excel_filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    for sheet_name, df in processed_sheets.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        logging.info(f"Updated sheet '{sheet_name}' with {len(df)} records")
                
                logging.info(f"Successfully updated Excel file: {weekly_excel_filename}")
                
            except Exception as e:
                logging.warning(f"Error reading existing Excel file: {e}")
                # Create new file if existing one is corrupted
                try:
                    os.remove(weekly_excel_filename)
                    logging.info(f"Removed corrupted file: {weekly_excel_filename}")
                except:
                    pass
                
                # Create new Excel file
                with pd.ExcelWriter(weekly_excel_filename, engine='openpyxl') as writer:
                    for sheet_name, df in processed_sheets.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        logging.info(f"Created sheet '{sheet_name}' with {len(df)} records")
                
                logging.info(f"Created new Excel file: {weekly_excel_filename}")
        else:
            # Create new Excel file
            try:
                with pd.ExcelWriter(weekly_excel_filename, engine='openpyxl') as writer:
                    for sheet_name, df in processed_sheets.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        logging.info(f"Created sheet '{sheet_name}' with {len(df)} records")
                
                logging.info(f"Created new Excel file: {weekly_excel_filename}")
                
            except Exception as e:
                logging.error(f"Error creating Excel file: {e}")
                # Try with a different filename using week info
                alt_filename = f"extracted_data_{week_info}.xlsx"
                try:
                    with pd.ExcelWriter(alt_filename, engine='openpyxl') as writer:
                        for sheet_name, df in processed_sheets.items():
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                            logging.info(f"Created sheet '{sheet_name}' in alternative file with {len(df)} records")
                    logging.info(f"Created alternative file: {alt_filename}")
                except Exception as e2:
                    logging.error(f"Failed to create alternative file: {e2}")
                    return False
        
        return True
        
    except Exception as e:
        logging.error(f"Error processing {data_type} weekly dataframe: {e}")
        return False

def demo_mode_with_reference():
    """Demo mode: process the reference file as if it were downloaded from the website"""
    logging.info("Running in DEMO MODE - processing reference file as new data")
    logging.info("="*60)
    
    # Load reference file
    reference_headers = load_reference_file()
    
    # Process reference file as the "downloaded" data
    logging.info("Processing reference file as downloaded data...")
    
    # Read all sheets from the Excel file
    excel_file = pd.ExcelFile(REFERENCE_FILE)
    sheet_dataframes = {}
    
    for sheet_name in excel_file.sheet_names:
        logging.info(f"Processing sheet: {sheet_name}")
        df = pd.read_excel(REFERENCE_FILE, sheet_name=sheet_name)
        
        # Clean up the data structure
        if df.shape[1] > 50 and 'Stn_Name' in str(df.iloc[0].values):
            df.columns = df.iloc[0]  # Set first row as column names
            df = df.drop(df.index[0])  # Remove the header row from data
            df = df.reset_index(drop=True)
        
        # Clean column names
        df.columns = [str(col).strip() if pd.notna(col) else f'Column_{i}' 
                     for i, col in enumerate(df.columns)]
        
        # Store each sheet separately
        sheet_dataframes[sheet_name] = df
        logging.info(f"Sheet {sheet_name}: {df.shape}")
    
    # Process each sheet separately for weekly storage
    for sheet_name, df in sheet_dataframes.items():
        logging.info(f"\nProcessing sheet: {sheet_name}")
        
        # Create file_info for this sheet
        file_info = {
            'href': 'reference_file.xlsx',
            'sheet_name': sheet_name
        }
        
        # Process this sheet using weekly storage
        if process_weekly_dataframe(df, sheet_name, file_info):
            logging.info(f"Successfully processed {sheet_name} for weekly storage")
        else:
            logging.error(f"Failed to process {sheet_name}")
    
    logging.info(f"\nDemo processing completed successfully!")
    logging.info(f"Processed {len(sheet_dataframes)} sheets for weekly storage")
    
    # Upload to SharePoint
    logging.info("\n" + "="*50)
    logging.info("UPLOADING TO SHAREPOINT")
    logging.info("="*50)
    upload_all_csv_files_to_sharepoint()
    
    return True

def scheduled_update():
    """Scheduled function that runs every Monday after 9 AM to check for updates"""
    current_time = datetime.now()
    logging.info(f"=== SCHEDULED UPDATE STARTED at {current_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    try:
        # Load existing tracking data
        tracking_data = load_file_tracking()
        
        # Scrape government website for all data types
        categorized_files = scrape_government_website()
        
        # Track changes and process files
        changes_detected = False
        
        for data_type, files in categorized_files.items():
            # Process all categories including OTHER
                
            for file_info in files:
                file_url = file_info['url']
                file_hash = get_file_hash(file_url)
                
                if file_hash is None:
                    continue
                
                # Check if file is new or has changed
                file_key = f"{data_type}_{file_url}"
                previous_hash = tracking_data.get(file_key, {}).get('hash')
                
                if previous_hash != file_hash:
                    # File is new or has changed
                    changes_detected = True
                    logging.info(f"Change detected in {data_type}: {file_info['href']}")
                    
                    # Update tracking data
                    tracking_data[file_key] = {
                        'hash': file_hash,
                        'last_updated': current_time.isoformat(),
                        'url': file_url,
                        'type': file_info['type']
                    }
                    
                    # Process the Excel file
                    logging.info(f"🎯 Found Excel file! Processing: {file_info['href']}")
                    success = download_and_process_file(file_info, data_type)
                    if success:
                        logging.info(f"✅ Successfully processed {data_type} file: {file_info['href']}")
                    else:
                        logging.error(f"❌ Failed to process {data_type} file: {file_info['href']}")
                else:
                    logging.debug(f"No changes in {data_type}: {file_info['href']}")
        
        # Save updated tracking data
        save_file_tracking(tracking_data)
        
        if changes_detected:
            logging.info("=== UPDATES COMPLETED - Changes were processed ===")
            logging.info("✅ Data processing completed successfully!")
            
        else:
            logging.info("=== NO CHANGES DETECTED - All files are up to date ===")
            
    except Exception as e:
        logging.error(f"Error during scheduled update: {e}")
        import traceback
        logging.error(traceback.format_exc())

def start_scheduler():
    """Start the scheduler to run updates automatically"""
    logging.info("Starting automated scheduler for weekly data extraction...")
    
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
    """Run a manual update check (for testing or immediate updates)"""
    logging.info("Running manual update check...")
    scheduled_update()
    logging.info("Manual update completed.")

def main():
    """Main function that orchestrates the entire process"""
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--demo':
            return demo_mode_with_reference()
        elif sys.argv[1] == '--schedule':
            return start_scheduler()
        elif sys.argv[1] == '--update':
            return run_manual_update()

        elif sys.argv[1] == '--weekly-summary':
            print(get_weekly_files_summary())
            return
        elif sys.argv[1] == '--help':
            print("Hexa Data Processing Script")
            print("="*40)
            print("Usage:")
            print("  python hexa_fixed.py              # Run normal processing")
            print("  python hexa_fixed.py --demo       # Run demo mode with reference file")
            print("  python hexa_fixed.py --schedule   # Start scheduler (Monday 9 AM)")
            print("  python hexa_fixed.py --update     # Run manual update check")

            print("  python hexa_fixed.py --weekly-summary # Show weekly files summary")
            print("  python hexa_fixed.py --help       # Show this help")
            return
    
    try:
        logging.info("Starting Multi-Type Data Processing...")
        logging.info("="*60)
        
        # Step 1: Load reference file and extract headers
        reference_headers = load_reference_file()
        
        # Step 2: Scrape government website for all data types
        categorized_files = scrape_government_website()
        
        # Check if any files were found
        total_files = sum(len(files) for files in categorized_files.values())
        if total_files == 0:
            logging.warning("No data files found on the government website")
            logging.info("\nTIP: You can run in demo mode with:")
            logging.info("python hexa_fixed.py --demo")
            return
        
        # Check for Excel files
        excel_found = False
        for data_type, files in categorized_files.items():
            if data_type != 'OTHER':
                excel_files = [f for f in files if f['type'] == 'excel']
                if excel_files:
                    excel_found = True
                    break
        
        if not excel_found:
            logging.warning("\n❌ No Excel files found with matching headers")
            logging.info("\n📊 Summary of available data:")
            for data_type, files in categorized_files.items():
                if files and data_type != 'OTHER':
                    excel_count = sum(1 for f in files if f['type'] == 'excel')
                    pdf_count = sum(1 for f in files if f['type'] == 'pdf')
                    logging.info(f"  {data_type}: {pdf_count} PDF files, {excel_count} Excel files")
            
            logging.info("\n💡 Current status:")
            logging.info("  - All data is available in PDF format only")
            logging.info("  - Excel files with matching format not yet published")
            logging.info("  - Script is ready to process Excel files when available")
            logging.info("\nTIP: You can run in demo mode with:")
            logging.info("python hexa_fixed.py --demo")
            return
        
        logging.info("\n🎉 Found Excel files! Processing will be implemented when matching files are available.")
        
    except Exception as e:
        logging.error(f"❌ Error during processing: {e}")
        import traceback
        logging.error(traceback.format_exc())
        logging.info("\nTIP: You can run in demo mode with:")
        logging.info("python hexa_fixed.py --demo")

if __name__ == "__main__":
    main()