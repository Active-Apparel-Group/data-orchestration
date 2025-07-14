# ORDER_LIST Extract‑only Pipeline – matches original complete.py speed
# ---------------------------------------------------------------------
# * 1‑to‑1 refactor of complete.py *minus* all transform / comparison steps
# * Landing tables now follow x<BASENAME>_ORDER_LIST_RAW convention
# * Row‑count validation after each BULK INSERT
# * All constants, credentials, helper imports kept verbatim so nothing
#   else in your repo changes.
# * ENHANCED: Robust retry logic and explicit Excel engine specification

import os, io, re, sys, time, csv, warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional
import random

import pandas as pd
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient, generate_container_sas, ContainerSasPermissions

# --- suppress openpyxl chatter ------------------------------------------------
warnings.filterwarnings(
    "ignore", message="Data Validation extension is not supported and will be removed"
)

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
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

try:
    from dotenv import load_dotenv
    # Load .env from repo root and .venv/.env if present
    load_dotenv(repo_root / ".env")
    load_dotenv(repo_root / ".venv" / ".env")
except ImportError:
    pass

import db_helper                 # noqa: E402
import schema_helper             # noqa: E402
import logger_helper             # noqa: E402

# Create logger instance for consistent usage
logger = logger_helper.get_logger(__name__)

# ---------------- hard‑coded CONFIG (unchanged) -------------------------------


TENANT_ID     = os.getenv('AZ_TENANT_ID') or "{{ secret('AZ_TENANT_ID') }}"
CLIENT_ID     = os.getenv('BLOB_CLIENT_ID') or "{{ secret('BLOB_CLIENT_ID') }}"
CLIENT_SECRET = os.getenv('BLOB_CLIENT_SECRET') or "{{ secret('BLOB_CLIENT_SECRET') }}"
ACCOUNT_NAME  = os.getenv('BLOB_ACCOUNT_NAME') or "{{ secret('BLOB_ACCOUNT_NAME') }}"
ACCOUNT_KEY   = os.getenv('BLOB_ACCOUNT_KEY') or "{{ secret('BLOB_ACCOUNT_KEY') }}"

SOURCE_CONTAINER = "orderlist"
TARGET_CONTAINER = "orderlistcsv"

DB_KEY            = "orders"
OVERWRITE_DB      = True
MAX_WORKERS       = 4  # keep sequential if you suspect throttling

# ---------------- RETRY CONFIGURATION ----------------------------------------
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2.0  # Base delay in seconds
RETRY_BACKOFF_MULTIPLIER = 2.0  # Exponential backoff
JITTER_MAX = 1.0  # Random jitter to avoid thundering herd

# ---------------- blob client --------------------------------------------------
# MOVED TO MAIN FUNCTION - Don't initialize at module level!

# ---------------- enhanced helpers ---------------------------------------------

def get_blob_clients():
    """Initialize blob clients when needed - not at module level"""
    blob_svc = BlobServiceClient(
        account_url=f"https://{ACCOUNT_NAME}.blob.core.windows.net",
        credential=ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET),
    )
    
    src_client = blob_svc.get_container_client(SOURCE_CONTAINER)
    trg_client = blob_svc.get_container_client(TARGET_CONTAINER)
    return blob_svc, src_client, trg_client

def safe_table_name(xlsx_name: str) -> str:
    name = re.sub(r"\.xls[x]?$", "", xlsx_name, flags=re.I)
    name = name.replace("(M3)", "").replace("'", "")
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return f"x{name}_RAW"

def validate_excel_file(xlsx_bytes: bytes, filename: str) -> bool:
    """Validate that the downloaded file is a valid Excel file"""
    try:
        # Check file size
        if len(xlsx_bytes) < 1024:  # Less than 1KB is suspicious
            logger.warning(f"File {filename} is suspiciously small: {len(xlsx_bytes)} bytes")
            return False
        
        # Check Excel file signature
        excel_signatures = [
            b'PK\x03\x04',  # Modern Excel (.xlsx)
            b'\xd0\xcf\x11\xe0',  # Legacy Excel (.xls)
        ]
        
        file_start = xlsx_bytes[:8]
        if not any(file_start.startswith(sig) for sig in excel_signatures):
            logger.warning(f"File {filename} does not have valid Excel signature")
            return False
        
        # Try to create ExcelFile object with explicit engine
        try:
            excel_file = pd.ExcelFile(io.BytesIO(xlsx_bytes), engine='openpyxl')
            sheet_names = excel_file.sheet_names
            if not sheet_names:
                logger.warning(f"File {filename} has no sheets")
                return False
            logger.info(f"File {filename} validation passed: {len(sheet_names)} sheets found")
            return True
        except Exception as e:
            logger.warning(f"File {filename} failed ExcelFile validation: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error validating file {filename}: {e}")
        return False

def best_sheet_with_retry(xlsx_bytes: bytes, filename: str) -> str:
    """Get best sheet with retry and explicit engine specification"""
    for attempt in range(MAX_RETRIES):
        try:
            # Always use openpyxl engine explicitly for .xlsx files
            engine = 'openpyxl' if filename.lower().endswith('.xlsx') else 'xlrd'
            
            xls = pd.ExcelFile(io.BytesIO(xlsx_bytes), engine=engine)
            sheet_names = xls.sheet_names
            
            # Look for MASTER sheet first
            if "MASTER" in sheet_names:
                logger.info(f"Using MASTER sheet from {filename}")
                return "MASTER"
            
            # Otherwise use first sheet
            best_sheet = sheet_names[0]
            logger.info(f"Using first sheet '{best_sheet}' from {filename}")
            return best_sheet
            
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {filename}: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY_BASE * (RETRY_BACKOFF_MULTIPLIER ** attempt)
                jitter = random.uniform(0, JITTER_MAX)
                sleep_time = delay + jitter
                logger.info(f"Retrying {filename} in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Failed to determine best sheet for {filename} after {MAX_RETRIES} attempts")
                raise

def download_blob_with_retry(blob_name: str, src_client) -> bytes:
    """Download blob with retry logic and validation"""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Downloading {blob_name} (attempt {attempt + 1}/{MAX_RETRIES})")
            
            blob_client = src_client.get_blob_client(blob_name)
            data = blob_client.download_blob().readall()
            
            # Validate the downloaded file
            if validate_excel_file(data, blob_name):
                logger.info(f"Successfully downloaded and validated {blob_name}: {len(data):,} bytes")
                return data
            else:
                raise ValueError(f"Downloaded file {blob_name} failed validation")
                
        except Exception as e:
            logger.warning(f"Download attempt {attempt + 1}/{MAX_RETRIES} failed for {blob_name}: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY_BASE * (RETRY_BACKOFF_MULTIPLIER ** attempt)
                jitter = random.uniform(0, JITTER_MAX)
                sleep_time = delay + jitter
                logger.info(f"Retrying download of {blob_name} in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Failed to download {blob_name} after {MAX_RETRIES} attempts")
                raise

def read_excel_with_retry(xlsx_bytes: bytes, sheet_name: str, filename: str) -> pd.DataFrame:
    """Read Excel with retry logic and explicit engine specification"""
    for attempt in range(MAX_RETRIES):
        try:
            # Always specify engine explicitly
            engine = 'openpyxl' if filename.lower().endswith('.xlsx') else 'xlrd'
            
            logger.info(f"Reading Excel {filename} sheet '{sheet_name}' with {engine} engine (attempt {attempt + 1})")
            
            df = pd.read_excel(
                io.BytesIO(xlsx_bytes), 
                sheet_name=sheet_name, 
                dtype=str, 
                na_filter=False,
                engine=engine  # Explicit engine specification
            )
            
            logger.info(f"Successfully read {filename}: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.warning(f"Excel read attempt {attempt + 1}/{MAX_RETRIES} failed for {filename}: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY_BASE * (RETRY_BACKOFF_MULTIPLIER ** attempt)
                jitter = random.uniform(0, JITTER_MAX)
                sleep_time = delay + jitter
                logger.info(f"Retrying Excel read of {filename} in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Failed to read Excel {filename} after {MAX_RETRIES} attempts")
                raise

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DataFrame with enhanced validation"""
    original_rows = len(df)
    original_cols = len(df.columns)
    
    # Filter valid columns (exclude unnamed/empty columns)
    cols = [c for c in df.columns if c and not str(c).lower().startswith("unnamed")]
    df = df[cols]
    
    # Clean column names
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in cols]
    
    # Remove completely empty rows
    df = df.dropna(how="all")
    
    # Remove rows where all values are empty strings
    df = df.loc[~df.apply(lambda r: r.astype(str).str.strip().eq("").all(), axis=1)]
    
    logger.info(f"DataFrame cleaning: {original_rows}→{len(df)} rows, {original_cols}→{len(df.columns)} columns")
    return df

# ---------------- external DATA‑SOURCE once per run ---------------------------

def ensure_external_ds() -> None:
    conn = db_helper.get_connection(DB_KEY)
    cur  = conn.cursor()

    start  = datetime.now(timezone.utc) - timedelta(minutes=10)
    expiry = start + timedelta(hours=2)
    sas = generate_container_sas(
        account_name   = ACCOUNT_NAME,
        container_name = TARGET_CONTAINER,
        account_key    = ACCOUNT_KEY,
        permission     = ContainerSasPermissions(read=True, list=True),
        start          = start,
        expiry         = expiry,
    )

    cur.execute("""
        IF EXISTS (SELECT 1 FROM sys.external_data_sources WHERE name='CsvBlobSrc')
            DROP EXTERNAL DATA SOURCE CsvBlobSrc;
        IF EXISTS (SELECT 1 FROM sys.database_scoped_credentials WHERE name='AzureBlobCred')
            DROP DATABASE SCOPED CREDENTIAL AzureBlobCred;
    """)

    cur.execute(f"""
        CREATE DATABASE SCOPED CREDENTIAL AzureBlobCred
        WITH IDENTITY='SHARED ACCESS SIGNATURE', SECRET='{sas}';
        CREATE EXTERNAL DATA SOURCE CsvBlobSrc
        WITH (TYPE=BLOB_STORAGE,
              LOCATION='https://{ACCOUNT_NAME}.blob.core.windows.net/{TARGET_CONTAINER}',
              CREDENTIAL=AzureBlobCred);
    """)
    conn.commit()
    cur.close(); conn.close()

# ---------------- core loader --------------------------------------------------

def bulk_load(df: pd.DataFrame, table: str, trg_client) -> int:
    """Bulk load with enhanced error handling"""
    conn = db_helper.get_connection(DB_KEY)
    cur  = conn.cursor()

    try:
        if OVERWRITE_DB:
            cur.execute(f"IF OBJECT_ID('dbo.{table}','U') IS NOT NULL DROP TABLE dbo.{table}")
            conn.commit()

        cols_sql, schema = schema_helper.generate_table_schema(df)
        cur.execute(f"CREATE TABLE dbo.{table} ({', '.join(cols_sql)})")
        conn.commit()

        df_sql = schema_helper.convert_df_for_sql(df, schema)

        csv_buf = io.StringIO()
        df_sql.to_csv(csv_buf, index=False, quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n', encoding='utf-8')
        blob_name = f"csv_temp/{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Upload CSV with retry
        for attempt in range(MAX_RETRIES):
            try:
                trg_client.get_blob_client(blob_name).upload_blob(
                    csv_buf.getvalue().encode('utf-8-sig'), 
                    overwrite=True
                )
                break
            except Exception as e:
                logger.warning(f"CSV upload attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_BASE * (attempt + 1))
                else:
                    raise

        cur.execute(f"""
            BULK INSERT dbo.{table}
            FROM '{blob_name}'
            WITH (DATA_SOURCE='CsvBlobSrc', FORMAT='CSV', FIRSTROW=2,
                  FIELDTERMINATOR=',', ROWTERMINATOR='0x0a', TABLOCK)
        """)
        conn.commit()
        
        cur.execute(f"SELECT COUNT(*) FROM dbo.{table}")
        rows = cur.fetchone()[0]

        # Log successful bulk insert
        logger.info(f"[{table}] BULK INSERT: {rows:,} rows loaded from {blob_name}")

        return rows
        
    finally:
        cur.close()
        conn.close()

# ---------------- enhanced per‑file pipeline --------------------------------

def process_blob(blob_name: str, src_client, trg_client) -> Dict:
    """Enhanced process_blob with comprehensive retry and error handling"""
    start = time.time()
    
    try:
        logger.info(f"Processing blob: {blob_name}")
        
        # Download with retry and validation
        data = download_blob_with_retry(blob_name, src_client)
        
        # Get best sheet with retry
        best_sheet = best_sheet_with_retry(data, blob_name)
        
        # Read Excel with retry and explicit engine
        df = read_excel_with_retry(data, best_sheet, blob_name)
        
        # Clean DataFrame
        df = clean_df(df)
        
        # Add metadata columns
        df['_SOURCE_FILE'] = blob_name
        df['_EXTRACTED_AT'] = datetime.now(timezone.utc)

        # Generate table name
        table = safe_table_name(blob_name)
        
        # Load to database with retry
        loaded = bulk_load(df, table, trg_client)

        processing_time = time.time() - start
        
        result = {
            'file': blob_name,
            'table': table,
            'rows_src': len(df),
            'rows_db': loaded,
            'match': len(df) == loaded,
            'elapsed': processing_time,
            'success': True
        }
        
        if result['match']:
            logger.info(f"✅ {blob_name} → {table}: {loaded:,} rows in {processing_time:.1f}s")
        else:
            logger.warning(f"⚠️ {blob_name} → {table}: Row count mismatch ({len(df)} vs {loaded})")
            
        return result

    except Exception as e:
        processing_time = time.time() - start
        logger.error(f"❌ Failed to process {blob_name}: {e}")
        
        return {
            'file': blob_name,
            'table': safe_table_name(blob_name),
            'rows_src': 0,
            'rows_db': 0,
            'match': False,
            'elapsed': processing_time,
            'success': False,
            'error': str(e)
        }

# ---------------- driver ------------------------------------------------------

def main():
    """ORDER_LIST Extract Phase: Blob storage → SQL tables with enhanced reliability"""
    
    try:
        # Get blob clients (lazy initialization for better performance)
        blob_svc, src_client, trg_client = get_blob_clients()
        
        logger.info("[*] ORDER_LIST - RAW Landing Pipeline (extract-only)")
        logger.info("=" * 60)
        logger.info(f"Retry configuration: {MAX_RETRIES} attempts, {RETRY_DELAY_BASE}s base delay")
        
        ensure_external_ds()

        # Get list of Excel files
        blobs = [b.name for b in src_client.list_blobs() if b.name.lower().endswith(('.xlsx', '.xls'))]
        logger.info(f"Found {len(blobs)} Excel files to process")
        
        # Process files sequentially with enhanced error handling
        results = []
        successful_files = 0
        failed_files = 0
        
        for i, blob_name in enumerate(blobs, 1):
            logger.info(f"[{i}/{len(blobs)}] Processing: {blob_name}")
            
            result = process_blob(blob_name, src_client, trg_client)
            results.append(result)
            
            if result['success'] and result['match']:
                successful_files += 1
            else:
                failed_files += 1
                
            # Progress update every 10 files
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(blobs)} files processed ({successful_files} success, {failed_files} failed)")

        # Calculate final statistics
        total_rows = sum(r['rows_db'] for r in results if r['success'])
        total_time = sum(r['elapsed'] for r in results)
        success_rate = (successful_files / len(results) * 100) if results else 0

        # Final report
        if failed_files == 0:
            status = "✅ COMPLETED SUCCESSFULLY"
        elif successful_files > 0:
            status = f"⚠️ COMPLETED WITH {failed_files} FAILURES"
        else:
            status = "❌ FAILED - NO FILES PROCESSED"
            
        logger.info(status)
        logger.info(f"Files processed: {len(results)}")
        logger.info(f"Successful     : {successful_files}")
        logger.info(f"Failed         : {failed_files}")
        logger.info(f"Success rate   : {success_rate:.1f}%")
        logger.info(f"Rows loaded    : {total_rows:,}")
        logger.info(f"Total time     : {total_time:.2f}s")
        
        if total_time > 0 and total_rows > 0:
            logger.info(f"Throughput     : {total_rows/total_time:,.0f} rows/s")

        # Detailed file report
        logger.info("\nDetailed Results:")
        logger.info("File | Src | DB | Match | Status | Secs")
        logger.info("-" * 60)
        for r in results:
            status_icon = "✅" if r['success'] and r['match'] else "❌"
            error_msg = f" ({r.get('error', 'Unknown error')})" if not r['success'] else ""
            logger.info(f"{status_icon} {r['file']} | {r['rows_src']} | {r['rows_db']} | {r['match']} | {r['elapsed']:.1f}s{error_msg}")

        return {
            'files_processed': len(results),
            'success_count': successful_files,
            'failed_count': failed_files,
            'success_rate': success_rate,
            'total_rows': total_rows,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR in main(): {e}")
        raise

if __name__ == "__main__":
    main()