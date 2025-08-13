#!/usr/bin/env python3
"""
WRPC (Western Regional Power Committee) Data Extractor
Dynamically extracts and processes DSM (Demand Side Management) data from CSV files.
Can also download fresh data from the WRPC website.
"""

import os
import glob
import logging
import pandas as pd
import requests
import zipfile
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wrpc_extractor.log')
    ]
)

# Constants
WRPC_DATA_DIR = "../data"
OUTPUT_DIR = "../data"
WRPC_BASE_URL = "https://www.wrpc.gov.in"
WRPC_DSM_URL = "https://www.wrpc.gov.in/menu/DSMUI%20Account%20_342"

# Browser-like headers for web requests
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
    """Create necessary directories"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(WRPC_DATA_DIR, exist_ok=True)
    logging.info(f"✅ Created directory: {OUTPUT_DIR}")
    logging.info(f"✅ Created directory: {WRPC_DATA_DIR}")

def get_session():
    """Create and configure a requests session with browser-like behavior"""
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    return session

def download_from_wrpc_website():
    """Download DSM data files from the WRPC website"""
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
        
        # Look for download links or file references
        download_links = []
        downloaded_files = []
        
        # Method 1: Look for direct file links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(ext in href.lower() for ext in ['.zip', '.xlsx', '.xls', '.csv']):
                download_links.append(href)
                logging.info(f"📎 Found file link: {href}")
        
        # Method 2: Look for common file patterns in the page
        content_text = response.text
        file_patterns = [
            r'[a-zA-Z0-9_-]+\.zip',
            r'[a-zA-Z0-9_-]+\.xlsx',
            r'[a-zA-Z0-9_-]+\.csv'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content_text)
            for match in matches:
                if match not in download_links:
                    download_links.append(match)
                    logging.info(f"📎 Found file pattern: {match}")
        
        if not download_links:
            logging.warning("⚠️ No direct download links found on the page")
            logging.info("🔍 Attempting alternative download methods...")
            
            # Try to find files using common patterns and date-based URLs
            current_date = datetime.now()
            date_patterns = [
                f"{current_date.strftime('%d%m%Y')}*.zip",
                f"{current_date.strftime('%Y%m%d')}*.zip",
                f"{current_date.strftime('%d%m%Y')}*sum*.zip",
                f"{current_date.strftime('%Y%m%d')}*sum*.zip"
            ]
            
            # Try common file paths
            common_paths = [
                "/allfile/",
                "/files/",
                "/data/",
                "/downloads/",
                "/dsm/"
            ]
            
            for path in common_paths:
                for pattern in date_patterns:
                    try:
                        test_url = f"{WRPC_BASE_URL}{path}{pattern}"
                        logging.info(f"🔍 Testing: {test_url}")
                        response = session.get(test_url, timeout=10, verify=True)
                        
                        if response.status_code == 200 and len(response.content) > 1000:
                            filename = pattern.replace('*', 'test')
                            file_path = os.path.join(WRPC_DATA_DIR, filename)
                            with open(file_path, 'wb') as f:
                                f.write(response.content)
                            
                            logging.info(f"✅ Found and downloaded: {filename}")
                            downloaded_files.append(file_path)
                            break
                            
                    except Exception as e:
                        logging.debug(f"⚠️ Failed to access {test_url}: {e}")
                        continue
            
            if not downloaded_files:
                logging.warning("⚠️ No files found using alternative methods")
                logging.info("💡 The website might require authentication or use dynamic content")
                return False
        
        # Try to download files
        downloaded_files = []
        for file_link in download_links[:5]:  # Limit to first 5 files
            try:
                # Try different URL combinations
                possible_urls = [
                    urljoin(WRPC_BASE_URL, file_link),
                    urljoin(WRPC_DSM_URL, file_link),
                    f"{WRPC_BASE_URL}/allfile/{file_link}",
                    f"{WRPC_BASE_URL}/files/{file_link}",
                    f"{WRPC_BASE_URL}/downloads/{file_link}"
                ]
                
                for url in possible_urls:
                    try:
                        logging.info(f"⬇️ Attempting to download: {url}")
                        file_response = session.get(url, timeout=30, verify=True)
                        
                        if file_response.status_code == 200 and len(file_response.content) > 1000:
                            # Save the file
                            file_path = os.path.join(WRPC_DATA_DIR, file_link)
                            with open(file_path, 'wb') as f:
                                f.write(file_response.content)
                            
                            logging.info(f"✅ Downloaded: {file_link} ({len(file_response.content)} bytes)")
                            downloaded_files.append(file_path)
                            
                            # If it's a ZIP file, extract it
                            if file_link.lower().endswith('.zip'):
                                try:
                                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                                        zip_ref.extractall(WRPC_DATA_DIR)
                                        logging.info(f"📦 Extracted ZIP file: {file_link}")
                                except Exception as e:
                                    logging.warning(f"⚠️ Failed to extract ZIP: {e}")
                            
                            break  # Successfully downloaded, move to next file
                            
                    except Exception as e:
                        logging.debug(f"⚠️ Failed to download from {url}: {e}")
                        continue
                        
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
    """Validate if CSV file has the expected DSM structure"""
    try:
        # Read first few lines to check structure
        df_sample = pd.read_csv(file_path, nrows=5)
        
        # Check for required columns
        required_columns = [
            'Date', 'Time', 'Block', 'Freq(Hz)', 'Constituents',
            'Actual (MWH)', 'Schedule (MWH)', 'SRAS (MWH)',
            'Deviation(MWH)', 'Deviation (%)', 'DSM Payable (Rs.)',
            'DSM Receivable (Rs.)', 'Normal Rate (p/Kwh)',
            'Gen Variable Charges (p/Kwh)', 'HPDAM Ref. Rate (p/Kwh)',
            'HPDAM Normal Rate (p/Kwh)'
        ]
        
        missing_columns = [col for col in required_columns if col not in df_sample.columns]
        
        if missing_columns:
            logging.warning(f"⚠️ Missing columns in {os.path.basename(file_path)}: {missing_columns}")
            return False
        
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
    """Process a single CSV file and extract insights"""
    try:
        filename = os.path.basename(file_path)
        constituent = extract_constituent_name(file_path)
        
        logging.info(f"📊 Processing: {filename}")
        
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Basic data validation
        if df.empty:
            logging.warning(f"⚠️ Empty file: {filename}")
            return None
        
        # Convert date and time columns
        df['Date'] = pd.to_datetime(df['Date'])
        df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'])
        
        # Convert numeric columns
        numeric_columns = [
            'Freq(Hz)', 'Actual (MWH)', 'Schedule (MWH)', 'SRAS (MWH)',
            'Deviation(MWH)', 'Deviation (%)', 'DSM Payable (Rs.)',
            'DSM Receivable (Rs.)', 'Normal Rate (p/Kwh)',
            'Gen Variable Charges (p/Kwh)', 'HPDAM Ref. Rate (p/Kwh)',
            'HPDAM Normal Rate (p/Kwh)'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate additional metrics
        df['Total_DSM_Amount'] = df['DSM Payable (Rs.)'] + df['DSM Receivable (Rs.)']
        df['Deviation_Absolute'] = abs(df['Deviation(MWH)'])
        
        # Extract insights
        insights = {
            'constituent': constituent,
            'filename': filename,
            'total_records': len(df),
            'date_range': {
                'start': df['Date'].min().strftime('%Y-%m-%d'),
                'end': df['Date'].max().strftime('%Y-%m-%d')
            },
            'total_actual_mwh': df['Actual (MWH)'].sum(),
            'total_schedule_mwh': df['Schedule (MWH)'].sum(),
            'total_deviation_mwh': df['Deviation(MWH)'].sum(),
            'total_dsm_payable': df['DSM Payable (Rs.)'].sum(),
            'total_dsm_receivable': df['DSM Receivable (Rs.)'].sum(),
            'total_dsm_amount': df['Total_DSM_Amount'].sum(),
            'avg_frequency': df['Freq(Hz)'].mean(),
            'max_deviation': df['Deviation_Absolute'].max(),
            'avg_deviation_percent': df['Deviation (%)'].mean(),
            'blocks_with_deviation': len(df[df['Deviation(MWH)'] != 0]),
            'blocks_with_dsm_payable': len(df[df['DSM Payable (Rs.)'] > 0]),
            'blocks_with_dsm_receivable': len(df[df['DSM Receivable (Rs.)'] > 0])
        }
        
        # Save processed data
        output_filename = f"{constituent}_processed.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        df.to_csv(output_path, index=False)
        
        logging.info(f"💾 Saved processed data: {output_filename}")
        
        return insights
        
    except Exception as e:
        logging.error(f"❌ Error processing {os.path.basename(file_path)}: {e}")
        return None

def generate_summary_report(all_insights):
    """Generate a summary report from all processed files"""
    if not all_insights:
        logging.warning("⚠️ No insights to generate report")
        return
    
    # Create summary DataFrame
    summary_data = []
    for insight in all_insights:
        if insight:
            summary_data.append({
                'Constituent': insight['constituent'],
                'Total_Records': insight['total_records'],
                'Date_Start': insight['date_range']['start'],
                'Date_End': insight['date_range']['end'],
                'Total_Actual_MWH': round(insight['total_actual_mwh'], 2),
                'Total_Schedule_MWH': round(insight['total_schedule_mwh'], 2),
                'Total_Deviation_MWH': round(insight['total_deviation_mwh'], 2),
                'Total_DSM_Payable_Rs': round(insight['total_dsm_payable'], 2),
                'Total_DSM_Receivable_Rs': round(insight['total_dsm_receivable'], 2),
                'Total_DSM_Amount_Rs': round(insight['total_dsm_amount'], 2),
                'Avg_Frequency_Hz': round(insight['avg_frequency'], 2),
                'Max_Deviation_MWH': round(insight['max_deviation'], 2),
                'Avg_Deviation_Percent': round(insight['avg_deviation_percent'], 2),
                'Blocks_with_Deviation': insight['blocks_with_deviation'],
                'Blocks_with_DSM_Payable': insight['blocks_with_dsm_payable'],
                'Blocks_with_DSM_Receivable': insight['blocks_with_dsm_receivable']
            })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        
        # Save summary report
        summary_path = os.path.join(OUTPUT_DIR, "WRPC_Summary_Report.csv")
        summary_df.to_csv(summary_path, index=False)
        
        # Generate additional analysis
        analysis_path = os.path.join(OUTPUT_DIR, "WRPC_Analysis_Report.txt")
        with open(analysis_path, 'w') as f:
            f.write("WRPC DSM Data Analysis Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total Constituents Analyzed: {len(summary_data)}\n")
            f.write(f"Total Records Processed: {summary_df['Total_Records'].sum()}\n")
            f.write(f"Date Range: {summary_df['Date_Start'].min()} to {summary_df['Date_End'].max()}\n\n")
            
            f.write("Top 5 Constituents by Total DSM Amount:\n")
            top_dsm = summary_df.nlargest(5, 'Total_DSM_Amount_Rs')
            for _, row in top_dsm.iterrows():
                f.write(f"  {row['Constituent']}: ₹{row['Total_DSM_Amount_Rs']:,.2f}\n")
            
            f.write(f"\nTop 5 Constituents by Deviation:\n")
            top_deviation = summary_df.nlargest(5, 'Total_Deviation_MWH')
            for _, row in top_deviation.iterrows():
                f.write(f"  {row['Constituent']}: {row['Total_Deviation_MWH']:,.2f} MWH\n")
            
            f.write(f"\nAverage Frequency Across All Constituents: {summary_df['Avg_Frequency_Hz'].mean():.2f} Hz\n")
            f.write(f"Total DSM Amount Across All Constituents: ₹{summary_df['Total_DSM_Amount_Rs'].sum():,.2f}\n")
        
        logging.info(f"📊 Generated summary report: {summary_path}")
        logging.info(f"📊 Generated analysis report: {analysis_path}")
        
        return summary_df
    
    return None

def main():
    """Main function to run the WRPC data extraction"""
    logging.info("🔄 Starting WRPC data extraction...")
    
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
            logging.info("   4. Place the files in: dsm_data/WRPC/")
            logging.info("   5. Run this script again")
            logging.info("💡 Alternatively, check if you have processed data in: processed_data/")
            return
    
    # Process each file
    all_insights = []
    processed_count = 0
    
    for file_path in csv_files:
        # Validate file structure
        if validate_csv_structure(file_path):
            insights = process_csv_file(file_path)
            if insights:
                all_insights.append(insights)
                processed_count += 1
        else:
            logging.warning(f"⚠️ Skipping invalid file: {os.path.basename(file_path)}")
    
    # Generate summary report
    if all_insights:
        summary_df = generate_summary_report(all_insights)
        
        logging.info(f"✅ WRPC extraction completed successfully!")
        logging.info(f"📊 Processed {processed_count} files out of {len(csv_files)} total files")
        logging.info(f"📁 Output files saved in: {OUTPUT_DIR}")
        
        if summary_df is not None:
            logging.info(f"📈 Total DSM amount across all constituents: ₹{summary_df['Total_DSM_Amount_Rs'].sum():,.2f}")
    else:
        logging.error("❌ No files were successfully processed")

if __name__ == "__main__":
    main()
