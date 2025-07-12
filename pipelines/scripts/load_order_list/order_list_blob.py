"""
ORDER_LIST Blob Uploader Pipeline
Purpose: Find ORDER_LIST XLSX files from SharePoint and upload to Azure Blob Storage
This is the step BEFORE order_list_extract.py which processes files from blob storage
"""

import os
import io
import sys
import time
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

# --- repo utils path setup ----------------------------------------------------
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))  # pipelines/utils ONLY

try:
    from dotenv import load_dotenv
    # Load .env from repo root and .venv/.env if present
    load_dotenv(repo_root / ".env")
    load_dotenv(repo_root / ".venv" / ".env")
except ImportError:
    pass

# Import project utilities
import auth_helper  # noqa: E402 (from pipelines/utils/)
import logger_helper  # noqa: E402 (from pipelines/utils/)
import db_helper as db  # noqa: E402 (from pipelines/utils/)

# Create logger instance for consistent usage
logger = logger_helper.get_logger(__name__)

# ---------------- hard‑coded CONFIG (unchanged) -------------------------------


TENANT_ID     = os.getenv('AZ_TENANT_ID') or "{{ secret('AZ_TENANT_ID') }}"
CLIENT_ID     = os.getenv('BLOB_CLIENT_ID') or "{{ secret('BLOB_CLIENT_ID') }}"
CLIENT_SECRET = os.getenv('BLOB_CLIENT_SECRET') or "{{ secret('BLOB_CLIENT_SECRET') }}"
ACCOUNT_NAME  = os.getenv('BLOB_ACCOUNT_NAME') or "{{ secret('BLOB_ACCOUNT_NAME') }}"
ACCOUNT_KEY   = os.getenv('BLOB_ACCOUNT_KEY') or "{{ secret('BLOB_ACCOUNT_KEY') }}"

SOURCE_CONTAINER = "orderlist"  # Where we upload the XLSX files

# SharePoint/OneDrive Configuration

TARGET_FOLDERS = [
    ("USA CUSTOMERS",   "01TP4AHIF77VK3XMDH4BHYQUXVCLJD62AU"),
    ("AUS Customers",   "01TP4AHIHDFBKGCMAO3BA37OFF7YUYSZ2N"),
    ("_PAST Customers", "01TP4AHIGOKGHMV5XZORFYVBCXNLKAODWK"),
    ("EU CUSTOMERS",    "01TP4AHIDKQKX2RK27AVAI2LFBCG5AFIBZ"),
    ("Lorna Jane",      "01TP4AHIBRQJL52ZEX5ZB2R6KVY4W6VMHJ"),
]
DRIVE_ID = "b!Aw3US9PgWEqI3AsHsnFh4VDpZqG7xMZFvusMriy0vjlVvmF4ME5wR6vdOy90ye56"
MAX_DEPTH = 2  # Increased depth to find files in deeper folders like ROC
ORDER_LIST_FOLDER_MATCHES = ["order list", "roc"]  # Search in folders containing these terms
ORDER_LIST_FILE_MATCH = "order list (m3)"

results = []

class OrderListBlobUploader:
    """Upload ORDER_LIST XLSX files from SharePoint to Azure Blob Storage"""
    
    def __init__(self, auth_cache_key: str = "order_list_pipeline"):
        self.results = []
        self.uploaded_files = []
        self.blob_client = None
        self.headers = None
        self.auth_cache_key = auth_cache_key  # Unique cache key for this pipeline
        
    def initialize_services(self):
        """Initialize Microsoft Graph and Azure Blob Storage clients"""
        logger.info("[AUTH] Initializing authentication services...")
        
        # Get Microsoft Graph token using database-backed cache
        token = auth_helper.get_token(
            cache_key=self.auth_cache_key,  # Unique cache key for this pipeline
            db_key="dms"  # Use DMS database for token storage
        )
        if not token:
            raise Exception("Failed to acquire Microsoft Graph access token")
        
        self.headers = {"Authorization": f"Bearer {token}"}
        
        # Initialize Azure Blob Storage client
        blob_svc = BlobServiceClient(
            account_url=f"https://{ACCOUNT_NAME}.blob.core.windows.net",
            credential=ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET),
        )
        self.blob_client = blob_svc.get_container_client(SOURCE_CONTAINER)
        
        logger.info("[SUCCESS] Services initialized successfully")
    
    def search_for_order_list_files(self, drive_id: str, folder_id: str, region: str, parent_name: str, subfolder_name: str):
        """Search for ORDER_LIST XLSX files in a specific folder"""
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}/children"
        
        try:
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            items = resp.json().get("value", [])
            
            for item in items:
                name = item.get("name", "")
                if (name.lower().endswith(".xlsx") and ORDER_LIST_FILE_MATCH in name.lower()):
                    
                    file_info = {
                        "Region": region,
                        "Parent": parent_name,
                        "Subfolder": subfolder_name,
                        "FileName": name,
                        "FileURL": item.get("webUrl", ""),
                        "DownloadURL": item.get("@microsoft.graph.downloadUrl"),
                        "ItemId": item.get("id"),
                        "Size": item.get("size", 0),
                        "LastModified": item.get("lastModifiedDateTime")
                    }
                    
                    self.results.append(file_info)
                    logger.info(f"[FOUND] ORDER_LIST file: {name} in {region}/{subfolder_name}")
                    # Find ALL matching files in folder (no break statement)
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Error accessing folder {folder_id}: {e}")
    
    def find_and_accumulate_files(self, drive_id: str, region_name: str, parent_id: str, depth: int = 0):
        """Recursively find ORDER_LIST folders and files"""
        if depth >= MAX_DEPTH:
            return
            
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{parent_id}/children"
        
        try:
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            items = resp.json().get("value", [])
            
            for item in items:
                if "folder" in item:
                    folder_name = item["name"]
                    parent_name = item.get('parentReference', {}).get('name', '?')
                    
                    # Check if folder name contains any of the target terms
                    folder_matches = any(match_term in folder_name.lower() for match_term in ORDER_LIST_FOLDER_MATCHES)
                    
                    if folder_matches:
                        logger.info(f"[SEARCH] Searching in ORDER_LIST folder: {region_name}/{folder_name}")
                        self.search_for_order_list_files(drive_id, item['id'], region_name, parent_name, folder_name)
                    
                    # Continue recursive search
                    self.find_and_accumulate_files(drive_id, region_name, item['id'], depth + 1)
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Error searching folder {parent_id}: {e}")
    
    def download_and_upload_file(self, file_info: Dict) -> Dict:
        """Download file from SharePoint and upload to Azure Blob Storage"""
        start_time = time.time()
        
        try:
            # Generate blob name directly in container (no subfolders)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            # Use just the filename (no region prefix)
            blob_name = file_info['FileName']
            
            # Check if file already exists in blob storage (for logging purposes)
            file_exists = False
            try:
                blob_props = self.blob_client.get_blob_client(blob_name).get_blob_properties()
                file_exists = True
                logger.info(f"[REPLACE] File exists, will overwrite: {blob_name}")
            except:
                logger.info(f"[NEW] New file will be uploaded: {blob_name}")
            
            # Download file from SharePoint
            logger.info(f"[DOWNLOAD] Downloading: {file_info['FileName']}")
            download_resp = requests.get(file_info['DownloadURL'], headers=self.headers)
            download_resp.raise_for_status()
            
            # Upload to Azure Blob Storage
            logger.info(f"[UPLOAD] Uploading to blob storage: {blob_name}")
            blob_client = self.blob_client.get_blob_client(blob_name)
            blob_client.upload_blob(
                download_resp.content,
                overwrite=True,
                metadata={
                    'source_region': file_info['Region'],
                    'source_folder': file_info['Subfolder'],
                    'upload_timestamp': timestamp,
                    'source_url': file_info['FileURL'],
                    'file_size': str(file_info['Size'])
                }
            )
            
            elapsed = time.time() - start_time
            size_mb = file_info['Size'] / (1024 * 1024) if file_info['Size'] else 0
            
            logger.info(f"[SUCCESS] Successfully uploaded: {blob_name} ({size_mb:.2f} MB in {elapsed:.2f}s)")
            
            return {
                'success': True,
                'file_info': file_info,
                'blob_name': blob_name,
                'size_mb': size_mb,
                'elapsed': elapsed
            }
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to upload {file_info['FileName']}: {e}")
            return {
                'success': False,
                'file_info': file_info,
                'blob_name': blob_name if 'blob_name' in locals() else 'unknown',
                'error': str(e),
                'elapsed': time.time() - start_time
            }
    
    def process_all_files(self):
        """Find all ORDER_LIST files and upload them to blob storage"""
        logger.info("[START] Starting ORDER_LIST file discovery and upload process")
        
        # Initialize services
        self.initialize_services()
        
        # Find all ORDER_LIST files
        logger.info("[SEARCH] Searching for ORDER_LIST files across all regions...")
        for region, folder_id in TARGET_FOLDERS:
            logger.info(f"[REGION] Searching region: {region}")
            self.find_and_accumulate_files(DRIVE_ID, region, folder_id, depth=0)
        
        if not self.results:
            logger.warning("[WARN] No matching ORDER_LIST files found")
            return {'files_found': 0, 'files_uploaded': 0, 'success_rate': 0}
        
        logger.info(f"[FOUND] Found {len(self.results)} ORDER_LIST files")
        
        # Upload files to blob storage
        logger.info("[UPLOAD] Starting file uploads to Azure Blob Storage...")
        for file_info in self.results:
            result = self.download_and_upload_file(file_info)
            self.uploaded_files.append(result)
        
        # Generate summary report
        successful_uploads = [r for r in self.uploaded_files if r['success']]
        failed_uploads = [r for r in self.uploaded_files if not r['success']]
        
        total_size_mb = sum(r.get('size_mb', 0) for r in successful_uploads)
        total_time = sum(r.get('elapsed', 0) for r in self.uploaded_files)
        success_rate = len(successful_uploads) / len(self.uploaded_files) * 100 if self.uploaded_files else 0
        
        logger.info("[SUMMARY] UPLOAD SUMMARY")
        logger.info("-" * 50)
        logger.info(f"Files found: {len(self.results)}")
        logger.info(f"Successful uploads: {len(successful_uploads)}")
        logger.info(f"Failed uploads: {len(failed_uploads)}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Total size: {total_size_mb:.2f} MB")
        logger.info(f"Total time: {total_time:.2f}s")
        
        if failed_uploads:
            logger.warning("[FAILURES] Failed uploads:")
            for failure in failed_uploads:
                logger.warning(f"  - {failure['file_info']['FileName']}: {failure.get('error', 'Unknown error')}")
        
        return {
            'files_found': len(self.results),
            'files_uploaded': len(successful_uploads),
            'success_rate': success_rate,
            'total_size_mb': total_size_mb,
            'results': self.uploaded_files
        }


def main():
    """Main execution function"""
    try:
        uploader = OrderListBlobUploader()
        summary = uploader.process_all_files()
        
        if summary['success_rate'] == 100:
            logger.info("[SUCCESS] All ORDER_LIST files successfully uploaded to blob storage!")
        elif summary['success_rate'] > 0:
            logger.warning(f"[PARTIAL] Partial success: {summary['success_rate']:.1f}% of files uploaded")
        else:
            logger.error("[FAIL] No files were successfully uploaded")
            
        return summary
        
    except Exception as e:
        logger.error(f"[CRASH] Pipeline failed: {e}")
        raise
        

if __name__ == "__main__":
    main()
