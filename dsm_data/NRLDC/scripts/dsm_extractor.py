#!/usr/bin/env python3
"""
DSM Blockwise Data Extractor
Extracts specific DSM data from ERPC website
"""

import requests
import pandas as pd
import os
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dsm_extractor.log'),
        logging.StreamHandler()
    ]
)

# Configuration
DSM_FILE_URL = "https://erpc.gov.in/wp-content/uploads/2025/08/DSM_Blockwise_Data_2025-07-21-2025-07-27.xlsx"
DOWNLOAD_DIR = "dsm_data"
ERLDC_DIR = "dsm_data/ERLDC"
NRLDC_DIR = "dsm_data/NRLDC"
TEMP_DIR = "temp_dsm"

def setup_directories():
    """Create necessary directories"""
    for directory in [DOWNLOAD_DIR, ERLDC_DIR, NRLDC_DIR, TEMP_DIR]:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Created directory: {directory}")

def download_dsm_file():
    """Download the DSM file"""
    try:
        logging.info(f"Downloading DSM file: {DSM_FILE_URL}")
        
        # Download the file
        resp = requests.get(DSM_FILE_URL, timeout=60, stream=True, verify=True)
        resp.raise_for_status()
        
        # Save to temp directory
        filename = "DSM_Blockwise_Data_2025-07-21-2025-07-27.xlsx"
        file_path = os.path.join(TEMP_DIR, filename)
        
        with open(file_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logging.info(f"✅ Downloaded: {filename}")
        return file_path
        
    except Exception as e:
        logging.error(f"❌ Error downloading DSM file: {e}")
        return None

def process_dsm_file(file_path):
    """Process the DSM Excel file"""
    try:
        logging.info(f"Processing DSM file: {file_path}")
        
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
        logging.error(f"❌ Error processing DSM file {file_path}: {e}")
        return None

def save_processed_data(processed_data):
    """Save processed data to Excel file"""
    if not processed_data:
        logging.warning("No data to save")
        return None
    
    try:
        # Determine target directory based on content analysis
        target_dir = DOWNLOAD_DIR  # Default directory
        
        # Analyze content to determine if it's ERLDC or NRLDC data
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
            
            # Check all sheets for regional indicators
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
                # Default to main directory if no clear indicators
                logging.info(f"📁 No clear ERLDC/NRLDC indicators found, saving to main directory")
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"DSM_Blockwise_Data_processed_{timestamp}.xlsx"
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

def main():
    """Main function"""
    logging.info("🚀 Starting DSM Blockwise Data extraction...")
    
    # Setup directories
    setup_directories()
    
    # Download the DSM file
    file_path = download_dsm_file()
    if not file_path:
        logging.error("❌ Failed to download DSM file")
        return
    
    # Process the file
    processed_data = process_dsm_file(file_path)
    if not processed_data:
        logging.error("❌ Failed to process DSM file")
        return
    
    # Save processed data
    output_path = save_processed_data(processed_data)
    if output_path:
        logging.info("✅ DSM data extraction completed successfully!")
        logging.info(f"📁 Output file: {output_path}")
    else:
        logging.error("❌ Failed to save processed data")
    
    # Clean up temp file
    try:
        os.remove(file_path)
        logging.info("🧹 Cleaned up temporary file")
    except:
        pass

if __name__ == "__main__":
    main()
