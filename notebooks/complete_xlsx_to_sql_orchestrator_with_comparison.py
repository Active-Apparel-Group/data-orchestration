import os, io, re, sys
import pandas as pd
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
from pathlib import Path
import warnings
from datetime import datetime, timedelta
import csv
import tempfile
import time

# Hide irrelevant openpyxl warnings
warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed")

# --- repo utils path setup ----------------------------------------------------
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

# Add utils to path for db_helper
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

try:
    from dotenv import load_dotenv
    # Load .env from repo root and .venv/.env if present
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    load_dotenv(repo_root / ".env")
    load_dotenv(repo_root / ".venv" / ".env")
except ImportError:
    pass

import db_helper                 # noqa: E402
import schema_helper             # noqa: E402
import logger_helper             # noqa: E402

# Create logger instance for consistent usage
logger = logger_helper.get_logger(__name__)

# ─── CONFIG ───────────────────────────────────────────────────────────────────

tenant_id     = os.getenv('AZ_TENANT_ID') or "{{ secret('AZ_TENANT_ID') }}"
client_id     = os.getenv('BLOB_CLIENT_ID') or "{{ secret('BLOB_CLIENT_ID') }}"
client_secret = os.getenv('BLOB_CLIENT_SECRET') or "{{ secret('BLOB_CLIENT_SECRET') }}"
account_name  = os.getenv('BLOB_ACCOUNT_NAME') or "{{ secret('BLOB_ACCOUNT_NAME') }}"
account_key   = os.getenv('BLOB_ACCOUNT_KEY') or "{{ secret('BLOB_ACCOUNT_KEY') }}"

# Container configuration
source_container = 'orderlist'        # XLSX files
target_container = 'orderlistcsv'     # CSV files

# Processing options
PROCESS_ALL_XLSX = True               # Set to False to process single file
SINGLE_XLSX_FILE = "AESCAPE ORDER LIST (M3).xlsx"  # Only used if PROCESS_ALL_XLSX = False
OVERWRITE_CSV = True                  # Overwrite CSV files if they already exist
OVERWRITE_DB_TABLES = True            # Overwrite database tables if they exist
AUTO_CONFIRM = True                   # Skip manual confirmation prompts
COMPARE_WITH_INCUMBENT = True         # Compare with incumbent tables

# Performance and analysis settings
CHUNK_SIZE = 500  # Larger chunks with optimized schema
CREATE_EXCEPTION_LOG = True  # Save failed files to CSV
CREATE_SCHEMA_ANALYSIS = True  # Analyze column differences across files

# Database configuration
db_key = "orders"  # Database key from config.yaml

# ─── INIT CLIENTS ─────────────────────────────────────────────────────────────
blob_svc = BlobServiceClient(
    account_url=f"https://{account_name}.blob.core.windows.net",
    credential=ClientSecretCredential(tenant_id, client_id, client_secret)
)

# ─── UTILITY FUNCTIONS ────────────────────────────────────────────────────────

def clean_filename_for_csv(xlsx_name: str) -> str:
    """Convert XLSX filename to CSV filename with proper cleaning"""
    csv_name = xlsx_name.replace('.xlsx', '.csv').replace('.XLSX', '.csv')
    csv_name = csv_name.replace('(M3)', '')  # Remove (M3) patterns
    csv_name = csv_name.replace('  ', ' ')   # Remove double spaces
    csv_name = csv_name.strip()              # Remove leading/trailing spaces
    return csv_name

def clean_table_name(fn: str) -> str:
    """Clean table name for SQL Server"""
    name = re.sub(r"\.csv$", "", fn, flags=re.IGNORECASE)  # Remove .csv extension
    name = name.replace("(M3)", "")
    name = name.replace(" ", "_").replace("'", "")
    name = re.sub(r"_+$", "", name)
    
    # Add leading 'x' to table name (current tables)
    name = "x" + name
    return name

def get_incumbent_table_name(current_table_name: str) -> str:
    """Get incumbent table name by removing 'x' prefix and checking for underscore suffix"""
    if current_table_name.startswith('x'):
        base_name = current_table_name[1:]  # Remove 'x' prefix
        return base_name + "_"  # Add underscore suffix for incumbent
    return None


# --- All schema/type inference now handled by schema_helper ---

# ─── BLOB SETUP FUNCTIONS ─────────────────────────────────────────────────────

def setup_blob_data_source_with_sas(cursor, conn, account_name: str, container: str) -> bool:
    """Set up external data source for Azure Blob Storage using SAS token with user delegation key"""
    try:
        print(f"  🔧 Setting up blob data source with SAS token...")
        from azure.storage.blob import generate_container_sas, ContainerSasPermissions

        ACCOUNT_KEY = account_key
        start_time  = datetime.utcnow() - timedelta(minutes=10) # avoid clock skew
        expiry_time = start_time + timedelta(hours=2)           # tight window

        sas_token = generate_container_sas(
            account_name      = account_name,
            container_name    = container,
            account_key       = ACCOUNT_KEY,        # <-- account key, not user delegation
            permission        = ContainerSasPermissions(read=True, list=True),
            expiry            = expiry_time,
            start             = start_time
        )
        print("  🔑 SAS starts with:", sas_token[:20])

        # Clean up old credentials and data sources
        cleanup_sql = """
        IF EXISTS (SELECT * FROM sys.external_data_sources WHERE name = 'CsvBlobSrc')
        DROP EXTERNAL DATA SOURCE CsvBlobSrc;
        
        IF EXISTS (SELECT * FROM sys.database_credentials WHERE name = 'AzureBlobCred')
        DROP DATABASE SCOPED CREDENTIAL AzureBlobCred;
        """
        
        cursor.execute(cleanup_sql)
        
        # Create database scoped credential with SAS
        credential_sql = f"""
        CREATE DATABASE SCOPED CREDENTIAL AzureBlobCred
        WITH IDENTITY = 'SHARED ACCESS SIGNATURE',
             SECRET = '{sas_token}'
        """
        
        cursor.execute(credential_sql)
        
        # Create external data source with credential
        data_source_sql = f"""
        CREATE EXTERNAL DATA SOURCE CsvBlobSrc
        WITH (
            TYPE = BLOB_STORAGE,
            LOCATION = 'https://{account_name}.blob.core.windows.net/{container}',
            CREDENTIAL = AzureBlobCred
        )
        """
        
        cursor.execute(data_source_sql)
        conn.commit()
        
        print(f"  ✅ Blob data source with SAS token configured successfully")
        return True
        
    except Exception as e:
        print(f"  ⚠️ Could not set up SAS-based blob data source: {e}")
        print(f"  🔄 Will fall back to traditional insert.")
        return False

# ─── COLUMN COMPARISON FUNCTIONS ───────────────────────────────────────────────

def compare_with_incumbent_table(current_table: str, incumbent_table: str, db_key: str) -> dict:
    """Compare current table columns with incumbent table columns"""
    try:
        conn = db_helper.get_connection(db_key)
        
        # Check if incumbent table exists
        check_query = """
        SELECT COUNT(*) as table_count
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
        """
        
        incumbent_exists = pd.read_sql_query(check_query, conn, params=[incumbent_table])
        
        if incumbent_exists['table_count'].iloc[0] == 0:
            conn.close()
            return {
                'incumbent_exists': False,
                'comparison_possible': False,
                'message': f"Incumbent table '{incumbent_table}' does not exist"
            }
        
        # Get columns for both tables
        column_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        
        current_columns = pd.read_sql_query(column_query, conn, params=[current_table])
        incumbent_columns = pd.read_sql_query(column_query, conn, params=[incumbent_table])
        
        conn.close()
        
        # Analyze differences
        # Normalize columns for comparison
        def normalize_col(col):
            return re.sub(r'\s+', ' ', str(col)).strip()

        current_col_names_raw = set(current_columns['COLUMN_NAME'])
        incumbent_col_names_raw = set(incumbent_columns['COLUMN_NAME'])
        current_col_names = set([normalize_col(c) for c in current_col_names_raw])
        incumbent_col_names = set([normalize_col(c) for c in incumbent_col_names_raw])

        matching_columns = current_col_names & incumbent_col_names
        new_columns = current_col_names - incumbent_col_names
        missing_columns = incumbent_col_names - current_col_names

        # Check for data type differences (on normalized names)
        modified_columns = []
        for col in matching_columns:
            # Find original names for type comparison
            cur_col = next((c for c in current_col_names_raw if normalize_col(c) == col), col)
            inc_col = next((c for c in incumbent_col_names_raw if normalize_col(c) == col), col)
            current_info = current_columns[current_columns['COLUMN_NAME'] == cur_col].iloc[0]
            incumbent_info = incumbent_columns[incumbent_columns['COLUMN_NAME'] == inc_col].iloc[0]
            current_type = f"{current_info['DATA_TYPE']}"
            incumbent_type = f"{incumbent_info['DATA_TYPE']}"
            if current_info['CHARACTER_MAXIMUM_LENGTH']:
                current_type += f"({current_info['CHARACTER_MAXIMUM_LENGTH']})"
            if incumbent_info['CHARACTER_MAXIMUM_LENGTH']:
                incumbent_type += f"({incumbent_info['CHARACTER_MAXIMUM_LENGTH']})"
            if current_type != incumbent_type:
                modified_columns.append({
                    'column_name': col,
                    'current_type': current_type,
                    'incumbent_type': incumbent_type
                })

        # Calculate accuracy
        total_unique_columns = len(current_col_names | incumbent_col_names)
        matching_score = len(matching_columns) / total_unique_columns * 100 if total_unique_columns > 0 else 100

        return {
            'incumbent_exists': True,
            'comparison_possible': True,
            'current_column_count': len(current_col_names),
            'incumbent_column_count': len(incumbent_col_names),
            'matching_columns': len(matching_columns),
            'new_columns': list(new_columns),
            'missing_columns': list(missing_columns),
            'modified_columns': modified_columns,
            'accuracy_score': matching_score,
            'message': f"Comparison completed: {matching_score:.1f}% column match"
        }
        
    except Exception as e:
        return {
            'incumbent_exists': False,
            'comparison_possible': False,
            'error': str(e),
            'message': f"Error comparing with incumbent: {e}"
        }

# ─── MAIN PROCESSING FUNCTIONS ─────────────────────────────────────────────────

def process_single_xlsx_file(xlsx_blob_name: str) -> dict:
    """Process a single XLSX file through the complete pipeline"""
    
    # Start timing
    start_time = time.time()
    
def process_single_xlsx_file(xlsx_blob_name: str) -> dict:
    """Process a single XLSX file through the complete pipeline"""
    
    # Start timing
    start_time = time.time()
    
    try:
        # Generate names
        csv_name = clean_filename_for_csv(xlsx_blob_name)
        table_name = clean_table_name(csv_name)
        incumbent_table_name = get_incumbent_table_name(table_name)
        
        print(f"  🎯 CSV target: {csv_name}")
        print(f"  🎯 Table target: {table_name}")
        if incumbent_table_name:
            print(f"  🎯 Incumbent table: {incumbent_table_name}")
        
        # Step 1: Download and analyze XLSX
        step1_start = time.time()
        print(f"  📥 Step 1: Downloading and analyzing XLSX...")
        
        source_client = blob_svc.get_container_client(source_container)
        xlsx_blob_client = source_client.get_blob_client(xlsx_blob_name)
        xlsx_data = xlsx_blob_client.download_blob().readall()
        
        step1_time = time.time() - step1_start
        print(f"  ✅ Downloaded {len(xlsx_data):,} bytes in {step1_time:.2f}s")
        
        # Analyze Excel sheets
        print(f"  🔍 Found {get_sheet_count(xlsx_data)} sheet(s), selected: {get_best_sheet(xlsx_data)}")
        sheet_info = analyze_excel_sheets(xlsx_data)
        for sheet_name, info in list(sheet_info.items())[:4]:  # Show first 4 sheets
            if 'error' not in info:
                status = "✅" if info['has_data'] else "⚠️ "
                print(f"    {status} {sheet_name}: {info['rows']:,} rows, {info['columns']} columns")
        
        # Step 2: Convert XLSX to CSV
        step2_start = time.time()
        print(f"  🔄 Step 2: Converting XLSX to CSV...")
        
        best_sheet = get_best_sheet(xlsx_data)
        df = pd.read_excel(io.BytesIO(xlsx_data), sheet_name=best_sheet, dtype=str)
        
        # No special case: Keep all columns for LORNA JANE ORDER LIST (do not trim at 'ORDER TYPE')
        # (Reverted per new requirements)

        # --- COLUMN NORMALIZATION FUNCTION ---
        def normalize_col(col):
            return re.sub(r'\s+', ' ', str(col)).strip()

        # Clean and filter columns:
        # 1. Flatten column names (replace newlines/carriage returns with space)
        # 2. Remove columns with no heading or 'Unnamed:'
        # 3. Normalize all whitespace to single space
        clean_cols = []
        for col in df.columns:
            col_flat = str(col).replace('\r', ' ').replace('\n', ' ')
            col_norm = normalize_col(col_flat)
            if not col_norm or col_norm.lower().startswith('unnamed:'):
                continue
            clean_cols.append(col_norm)
        # Set DataFrame columns to normalized names
        df.columns = [normalize_col(str(col).replace('\r', ' ').replace('\n', ' ')) for col in df.columns]
        df = df[clean_cols]

        # Drop blank rows (all columns empty or NaN)
        df = df.dropna(how='all')
        df = df[~(df.apply(lambda row: row.astype(str).str.strip().eq('').all(), axis=1))]

        step2_time = time.time() - step2_start
        print(f"  ✅ Converted to CSV: {len(df):,} rows, {len(df.columns)} columns ({get_csv_size(df):,} bytes)")
        
        # --- FINAL VALIDATION: Check all columns exist in ORDERS_UNIFIED (with normalization) ---
        orders_unified_comparison = None
        try:
            with db_helper.get_connection(db_key) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT TOP 1 * FROM ORDERS_UNIFIED")
                orders_unified_cols_raw = [desc[0] for desc in cursor.description]
            # Normalize ORDERS_UNIFIED columns
            orders_unified_cols = [normalize_col(c) for c in list(orders_unified_cols_raw)]
            df_col_norm = [normalize_col(col) for col in list(df.columns)]
            missing_in_orders_unified = [col for col, norm_col in zip(list(df.columns), df_col_norm) if norm_col not in orders_unified_cols]
            new_columns_in_orders_unified = [col for col in orders_unified_cols if col not in df_col_norm]

            # Calculate match percentage
            orders_unified_match = 100 * (1 - len(missing_in_orders_unified) / len(df_col_norm)) if df_col_norm else 100

            # Store comparison results
            orders_unified_comparison = {
                'match_percent': orders_unified_match,
                'missing_columns': missing_in_orders_unified,
                'new_columns': new_columns_in_orders_unified,
                'total_columns': len(df_col_norm),
                'orders_unified_total_columns': len(orders_unified_cols)
            }

            if missing_in_orders_unified:
                print(f"    ⚠️ Columns not found in ORDERS_UNIFIED: {missing_in_orders_unified}")
                print(f"    📊 ORDERS_UNIFIED match: {orders_unified_match:.1f}%")
            else:
                print(f"    ✅ All columns present in ORDERS_UNIFIED for merge.")
                print(f"    📊 ORDERS_UNIFIED match: 100.0%")
        except Exception as e:
            print(f"    ⚠️ Could not validate against ORDERS_UNIFIED: {e}")
            orders_unified_comparison = {
                'match_percent': 0,
                'missing_columns': [],
                'new_columns': [],
                'total_columns': len(df.columns),
                'orders_unified_total_columns': 0,
                'error': str(e)
            }
        
        # Step 3: Upload CSV to blob storage  
        step3_start = time.time()
        print(f"  📤 Step 3: Uploading CSV to blob storage...")
        
        csv_uploaded = upload_csv_to_target_container(csv_name, df)
        
        step3_time = time.time() - step3_start
        print(f"  ✅ CSV uploaded in {step3_time:.2f}s")
        
        # Step 4: Load data to SQL Server
        step4_start = time.time()
        print(f"  💾 Step 4: Loading data to SQL Server...")
        
        db_result = load_dataframe_to_sql_optimized(df, table_name, db_key)
        
        step4_time = time.time() - step4_start
        
        if db_result['success']:
            print(f"  ✅ Database load successful using {db_result['method']}")
            print(f"    📊 Loaded {db_result['rows_loaded']:,} rows, {db_result['columns_count']} columns")
        else:
            print(f"  ❌ Database load failed: {db_result.get('error', 'Unknown error')}")
            
        # Step 5: Verify table integrity
        step5_start = time.time()
        print(f"  🔍 Step 5: Verifying table integrity...")
        
        integrity_result = verify_table_integrity(table_name, df, db_key)
        
        step5_time = time.time() - step5_start
        print(f"  ✅ Integrity check: {integrity_result['accuracy']:.1f}% accuracy")
        print(f"    📊 Rows: {integrity_result['db_rows']}/{integrity_result['source_rows']}")
        print(f"    📋 Columns: {integrity_result['db_columns']}/{integrity_result['source_columns']}")
        
        # Step 6: Compare with incumbent (if enabled and exists)
        comparison_result = None
        step6_time = 0
        
        if COMPARE_WITH_INCUMBENT and incumbent_table_name:
            step6_start = time.time()
            print(f"  📊 Step 6: Comparing with incumbent table...")
            
            comparison_result = compare_with_incumbent_table(table_name, incumbent_table_name, db_key)
            
            step6_time = time.time() - step6_start
            
            if comparison_result['comparison_possible']:
                print(f"  ✅ Column comparison: {comparison_result['accuracy_score']:.1f}% match")
                print(f"    ➕ New columns: {len(comparison_result['new_columns'])}")
                print(f"    ➖ Missing columns: {len(comparison_result['missing_columns'])}")
                print(f"    🔄 Modified columns: {len(comparison_result['modified_columns'])}")
            else:
                print(f"  ⚠️  {comparison_result['message']}")
        
        # Calculate total time
        total_time = time.time() - start_time
        
        print(f"  🎉 PROCESSING COMPLETE: {xlsx_blob_name}")
        print(f"  ⏱️ Total time: {total_time:.2f}s")
        
        # --- CSV OUTPUT SAFEGUARD ---
        # Ensure per-file results are always written to CSV, even if DB load fails
        try:
            import csv
            import os
            csv_temp_dir = os.path.join(os.path.dirname(__file__), 'csv_temp')
            os.makedirs(csv_temp_dir, exist_ok=True)
            result_csv_path = os.path.join(csv_temp_dir, f'orchestration_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            # Write a single-row CSV for this file (append if exists)
            fieldnames = [
                'xlsx_file', 'csv_file', 'table_name', 'incumbent_table', 'status', 'sheets_analyzed', 'best_sheet',
                'rows_processed', 'columns_processed', 'db_load_method', 'db_load_success', 'integrity_accuracy',
                'orders_unified_match', 'orders_unified_missing', 'orders_unified_new', 'orders_unified_total_columns',
                'comparison_accuracy', 'comparison_new', 'comparison_missing', 'comparison_modified', 'timing_total'
            ]
            def safe_join(val):
                if isinstance(val, list):
                    return ';'.join([str(x) for x in val])
                return str(val) if val is not None else ''
            row = {
                'xlsx_file': xlsx_blob_name,
                'csv_file': csv_name,
                'table_name': table_name,
                'incumbent_table': incumbent_table_name,
                'status': 'SUCCESS',
                'sheets_analyzed': len(sheet_info),
                'best_sheet': best_sheet,
                'rows_processed': len(df),
                'columns_processed': len(df.columns),
                'db_load_method': db_result.get('method', 'N/A'),
                'db_load_success': db_result['success'],
                'integrity_accuracy': integrity_result['accuracy'],
                'orders_unified_match': orders_unified_comparison['match_percent'] if orders_unified_comparison else '',
                'orders_unified_missing': safe_join(orders_unified_comparison['missing_columns']) if orders_unified_comparison else '',
                'orders_unified_new': safe_join(orders_unified_comparison['new_columns']) if orders_unified_comparison else '',
                'orders_unified_total_columns': orders_unified_comparison['orders_unified_total_columns'] if orders_unified_comparison else '',
                'comparison_accuracy': comparison_result['accuracy_score'] if comparison_result else '',
                'comparison_new': safe_join(comparison_result['new_columns']) if comparison_result else '',
                'comparison_missing': safe_join(comparison_result['missing_columns']) if comparison_result else '',
                'comparison_modified': safe_join(comparison_result['modified_columns']) if comparison_result else '',
                'timing_total': total_time
            }
            write_header = not os.path.exists(result_csv_path)
            with open(result_csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                writer.writerow(row)
            print(f"  💾 Per-file results written to: {result_csv_path}")
        except Exception as csv_e:
            print(f"  ⚠️ Could not write per-file CSV results: {csv_e}")

        return {
            'xlsx_file': xlsx_blob_name,
            'csv_file': csv_name,
            'table_name': table_name,
            'incumbent_table': incumbent_table_name,
            'status': 'SUCCESS',
            'sheets_analyzed': len(sheet_info),
            'best_sheet': best_sheet,
            'rows_processed': len(df),
            'columns_processed': len(df.columns),
            'db_load_method': db_result.get('method', 'N/A'),
            'db_load_success': db_result['success'],
            'integrity_accuracy': integrity_result['accuracy'],
            'comparison_result': comparison_result,
            'orders_unified_comparison': orders_unified_comparison,
            'timing': {
                'step1_download': step1_time,
                'step2_conversion': step2_time,
                'step3_upload': step3_time,
                'step4_database': step4_time,
                'step5_integrity': step5_time,
                'step6_comparison': step6_time,
                'total_time': total_time
            }
        }
        
    except Exception as e:
        total_time = time.time() - start_time
        print(f"  ❌ PROCESSING FAILED: {xlsx_blob_name}")
        print(f"  ❌ Error: {e}")
        
        # --- CSV OUTPUT SAFEGUARD ON FAILURE ---
        try:
            import csv
            import os
            csv_temp_dir = os.path.join(os.path.dirname(__file__), 'csv_temp')
            os.makedirs(csv_temp_dir, exist_ok=True)
            result_csv_path = os.path.join(csv_temp_dir, f'orchestration_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            fieldnames = [
                'xlsx_file', 'csv_file', 'table_name', 'incumbent_table', 'status', 'sheets_analyzed', 'best_sheet',
                'rows_processed', 'columns_processed', 'db_load_method', 'db_load_success', 'integrity_accuracy',
                'orders_unified_match', 'orders_unified_missing', 'orders_unified_new', 'orders_unified_total_columns',
                'comparison_accuracy', 'comparison_new', 'comparison_missing', 'comparison_modified', 'timing_total', 'error'
            ]
            def safe_join(val):
                if isinstance(val, list):
                    return ';'.join([str(x) for x in val])
                return str(val) if val is not None else ''
            row = {
                'xlsx_file': xlsx_blob_name,
                'csv_file': csv_name if 'csv_name' in locals() else 'unknown',
                'table_name': table_name if 'table_name' in locals() else 'unknown',
                'incumbent_table': incumbent_table_name if 'incumbent_table_name' in locals() else None,
                'status': 'FAILED',
                'sheets_analyzed': len(sheet_info) if 'sheet_info' in locals() else '',
                'best_sheet': best_sheet if 'best_sheet' in locals() else '',
                'rows_processed': len(df) if 'df' in locals() else '',
                'columns_processed': len(df.columns) if 'df' in locals() else '',
                'db_load_method': db_result.get('method', 'N/A') if 'db_result' in locals() else '',
                'db_load_success': db_result['success'] if 'db_result' in locals() and 'success' in db_result else '',
                'integrity_accuracy': integrity_result['accuracy'] if 'integrity_result' in locals() and 'accuracy' in integrity_result else '',
                'orders_unified_match': orders_unified_comparison['match_percent'] if 'orders_unified_comparison' in locals() and orders_unified_comparison else '',
                'orders_unified_missing': safe_join(orders_unified_comparison['missing_columns']) if 'orders_unified_comparison' in locals() and orders_unified_comparison else '',
                'orders_unified_new': safe_join(orders_unified_comparison['new_columns']) if 'orders_unified_comparison' in locals() and orders_unified_comparison else '',
                'orders_unified_total_columns': orders_unified_comparison['orders_unified_total_columns'] if 'orders_unified_comparison' in locals() and orders_unified_comparison else '',
                'comparison_accuracy': comparison_result['accuracy_score'] if 'comparison_result' in locals() and comparison_result else '',
                'comparison_new': safe_join(comparison_result['new_columns']) if 'comparison_result' in locals() and comparison_result else '',
                'comparison_missing': safe_join(comparison_result['missing_columns']) if 'comparison_result' in locals() and comparison_result else '',
                'comparison_modified': safe_join(comparison_result['modified_columns']) if 'comparison_result' in locals() and comparison_result else '',
                'timing_total': total_time,
                'error': str(e)
            }
            write_header = not os.path.exists(result_csv_path)
            with open(result_csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                writer.writerow(row)
            print(f"  💾 Per-file results written to: {result_csv_path}")
        except Exception as csv_e:
            print(f"  ⚠️ Could not write per-file CSV results: {csv_e}")

        return {
            'xlsx_file': xlsx_blob_name,
            'csv_file': csv_name if 'csv_name' in locals() else 'unknown',
            'table_name': table_name if 'table_name' in locals() else 'unknown',
            'incumbent_table': incumbent_table_name if 'incumbent_table_name' in locals() else None,
            'status': 'FAILED',
            'error': str(e),
            'timing': {
                'total_time': total_time
            }
        }

# ─── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def get_sheet_count(xlsx_data: bytes) -> int:
    """Get number of sheets in Excel file"""
    try:
        excel_file = pd.ExcelFile(io.BytesIO(xlsx_data))
        return len(excel_file.sheet_names)
    except:
        return 0

def get_best_sheet(xlsx_data: bytes) -> str:
    """Get the best sheet to convert (usually the one with most data)"""
    try:
        excel_file = pd.ExcelFile(io.BytesIO(xlsx_data))
        sheet_names = excel_file.sheet_names
        
        # Look for MASTER sheet first
        for sheet in sheet_names:
            if 'MASTER' in sheet.upper():
                return sheet
        
        # Otherwise return first sheet
        return sheet_names[0] if sheet_names else 0
    except:
        return 0

def analyze_excel_sheets(xlsx_data: bytes) -> dict:
    """Analyze all sheets in Excel file"""
    try:
        excel_file = pd.ExcelFile(io.BytesIO(xlsx_data))
        sheet_info = {}
        
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(io.BytesIO(xlsx_data), sheet_name=sheet_name)
                sheet_info[sheet_name] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'has_data': len(df) > 0
                }
            except Exception as e:
                sheet_info[sheet_name] = {
                    'rows': 0,
                    'columns': 0,
                    'has_data': False,
                    'error': str(e)
                }
        
        return sheet_info
    except:
        return {}

def get_csv_size(df: pd.DataFrame) -> int:
    """Estimate CSV size in bytes"""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return len(csv_buffer.getvalue().encode('utf-8'))

def upload_csv_to_target_container(csv_name: str, df: pd.DataFrame) -> bool:
    """Upload DataFrame as CSV to target container"""
    try:
        # Save local copy to notebooks/csv_temp
        import os
        os.makedirs('notebooks/csv_temp', exist_ok=True)
        local_csv_path = os.path.join('notebooks/csv_temp', csv_name)
        df.to_csv(local_csv_path, index=False, encoding='utf-8-sig')
        print(f"    💾 Local CSV saved: {local_csv_path}")

        # (Optional) Still upload to blob if needed
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_data = csv_buffer.getvalue().encode('utf-8-sig')
        target_client = blob_svc.get_container_client(target_container)
        blob_client = target_client.get_blob_client(csv_name)
        blob_client.upload_blob(csv_data, overwrite=OVERWRITE_CSV)
        return True
    except Exception as e:
        print(f"    ❌ CSV upload failed: {e}")
        return False

def verify_table_integrity(table_name: str, source_df: pd.DataFrame, db_key: str) -> dict:
    """Verify table integrity by comparing row and column counts"""
    try:
        conn = db_helper.get_connection(db_key)
        
        # Get row count
        row_query = f"SELECT COUNT(*) as row_count FROM dbo.{table_name}"
        row_result = pd.read_sql_query(row_query, conn)
        db_rows = row_result['row_count'].iloc[0]
        
        # Get column count
        col_query = f"""
        SELECT COUNT(*) as col_count 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table_name}'
        """
        col_result = pd.read_sql_query(col_query, conn)
        db_columns = col_result['col_count'].iloc[0]
        
        conn.close()
        
        source_rows = len(source_df)
        source_columns = len(source_df.columns)
        
        row_accuracy = (db_rows / source_rows * 100) if source_rows > 0 else 100
        col_accuracy = (db_columns / source_columns * 100) if source_columns > 0 else 100
        overall_accuracy = (row_accuracy + col_accuracy) / 2
        
        return {
            'db_rows': db_rows,
            'source_rows': source_rows,
            'db_columns': db_columns,
            'source_columns': source_columns,
            'row_accuracy': row_accuracy,
            'column_accuracy': col_accuracy,
            'accuracy': overall_accuracy
        }
        
    except Exception as e:
        return {
            'db_rows': 0,
            'source_rows': len(source_df),
            'db_columns': 0,
            'source_columns': len(source_df.columns),
            'accuracy': 0,
            'error': str(e)
        }

# ─── IMPORT THE OPTIMIZED LOADER ───────────────────────────────────────────────

def load_dataframe_to_sql_optimized(df: pd.DataFrame, table_name: str, db_key: str) -> dict:
    """Load DataFrame to SQL using smart column sizing + Azure Blob BULK INSERT for maximum performance"""
    conn = None
    cursor = None
    blob_name = None
    staging_table = None
    
    try:
        print(f"    🔌 Creating fresh database connection...")
        conn = db_helper.get_connection(db_key)
        conn.timeout = 60  # Longer timeout for bulk operations
        cursor = conn.cursor()

        # Drop table if exists and OVERWRITE_DB_TABLES is True
        if OVERWRITE_DB_TABLES:
            print(f"    🗑️ Dropping existing table if exists...")
            drop_sql = f"IF OBJECT_ID('dbo.{table_name}', 'U') IS NOT NULL DROP TABLE dbo.{table_name}"
            cursor.execute(drop_sql)
            conn.commit()
            print(f"    ✅ Table drop completed")

        # Use schema_helper to generate schema and convert DataFrame
        print(f"    🔧 Inferring schema for {len(df.columns)} columns using schema_helper...")
        columns_sql, schema_info = schema_helper.generate_table_schema(df)
        print(f"    🏗️ Creating table with inferred schema...")
        create_sql = f"CREATE TABLE dbo.{table_name} ({', '.join(columns_sql)})"
        cursor.execute(create_sql)
        conn.commit()
        print(f"    ✅ Table created with inferred column types!")

        # Convert DataFrame columns to native types for SQL
        df_sql = schema_helper.convert_df_for_sql(df, schema_info)

        # Set up blob data source (one-time setup) - ENABLED with SAS token
        print(f"    🔧 Setting up Azure Blob data source for BULK INSERT...")
        blob_setup_success = setup_blob_data_source_with_sas(cursor, conn, account_name, target_container)

        if blob_setup_success:
            # Use BULK INSERT method
            print(f"    🚀 Using BLOB BULK INSERT method...")
            csv_buffer = io.StringIO()
            df_sql.to_csv(csv_buffer, index=False, quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n', encoding='utf-8')
            csv_data = csv_buffer.getvalue().encode('utf-8-sig')
            blob_name = f"csv_temp/{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            blob_container_client = blob_svc.get_container_client(target_container)
            blob_client = blob_container_client.get_blob_client(blob_name)
            blob_client.upload_blob(csv_data, overwrite=True)
            if not blob_client.exists():
                raise RuntimeError("blob upload failed – nothing to load!")
            try:
                # Execute BULK INSERT
                bulk_insert_sql = f"""
                BULK INSERT dbo.{table_name}
                FROM '{blob_name}'
                WITH (
                    DATA_SOURCE = 'CsvBlobSrc',
                    FORMAT = 'CSV',
                    FIRSTROW = 2,
                    FIELDTERMINATOR = ',',
                    ROWTERMINATOR = '0x0a',
                    TABLOCK
                )
                """
                cursor.execute(bulk_insert_sql)
                conn.commit()
                # Get final row count
                cursor.execute(f"SELECT COUNT(*) FROM dbo.{table_name}")
                row_count = cursor.fetchone()[0]
                print(f"    ✅ BLOB BULK INSERT SUCCESS! Loaded {row_count:,} rows")
                return {
                    'success': True,
                    'method': 'BLOB_BULK_INSERT',
                    'table_name': table_name,
                    'rows_loaded': row_count,
                    'columns_count': len(df.columns),
                    'column_names': list(df.columns),
                    'schema_info': schema_info
                }
            except Exception as e:
                print(f"    ❌ BULK INSERT failed: {e}")
                print(f"    ⚠️ Falling back to row-by-row insert with error logging...")
                # Fallback: row-by-row insert with error logging
                error_rows = []
                success_count = 0
                col_names = list(df_sql.columns)
                placeholders = ', '.join(['?' for _ in col_names])
                col_names_sql = ', '.join([f'[{col}]' for col in col_names])
                insert_sql = f"INSERT INTO dbo.{table_name} ({col_names_sql}) VALUES ({placeholders})"
                for idx, row in df_sql.iterrows():
                    try:
                        cursor.execute(insert_sql, tuple(row))
                        success_count += 1
                    except Exception as row_e:
                        error_rows.append({
                            'row_index': idx,
                            'row_data': row.to_dict(),
                            'error': str(row_e)
                        })
                conn.commit()
                print(f"    ✅ Row-by-row insert complete. {success_count} rows loaded, {len(error_rows)} failed.")
                # Write error log if any
                error_log_path = None
                if error_rows:
                    import json
                    os.makedirs('notebooks/csv_temp', exist_ok=True)
                    error_log_path = f"notebooks/csv_temp/{table_name}_row_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(error_log_path, 'w', encoding='utf-8') as f:
                        json.dump(error_rows, f, indent=2, ensure_ascii=False)
                    print(f"    ⚠️ Row errors logged to: {error_log_path}")
                return {
                    'success': len(error_rows) == 0,
                    'method': 'ROW_BY_ROW_INSERT',
                    'table_name': table_name,
                    'rows_loaded': success_count,
                    'rows_failed': len(error_rows),
                    'error_log': error_log_path,
                    'columns_count': len(df.columns),
                    'column_names': list(df.columns),
                    'schema_info': schema_info
                }
    except Exception as e:
        print(f"    ❌ Error in optimized load: {e}")
        return {
            'success': False,
            'method': 'ERROR',
            'table_name': table_name,
            'error': str(e),
            'rows_attempted': len(df) if 'df' in locals() else 0,
            'columns_count': len(df.columns) if 'df' in locals() else 0
        }
    finally:
        # Clean up blob file
        if blob_name:
            try:
                blob_client = blob_svc.get_blob_client(target_container, blob_name)
                blob_client.delete_blob()
                print(f"    🧹 Cleaned up blob file: {blob_name}")
            except:
                pass
        # Ensure connections are closed
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

def fallback_insert_method(df: pd.DataFrame, table_name: str, cursor, conn, column_mapping: dict, schema_analysis: dict) -> dict:
    """Fallback insert method using traditional executemany but with optimized schema"""
    try:
        start_time = time.time()
        print(f"    📊 Converting {len(df)} rows for optimized insert...")
        
        # Convert DataFrame to optimized Python data structure
        df_filled = df.fillna('')
        # Drop blank rows again for safety
        df_filled = df_filled[~(df_filled.apply(lambda row: row.astype(str).str.strip().eq('').all(), axis=1))]
        python_data = []
        for _, row in df_filled.iterrows():
            processed_row = []
            for val in row:
                if val == '' or pd.isna(val):
                    processed_row.append(None)
                else:
                    processed_row.append(str(val))
            python_data.append(tuple(processed_row))
        
        # Insert data
        clean_column_names = [column_mapping[col] for col in df.columns]
        placeholders = ', '.join(['?' for _ in range(len(clean_column_names))])
        col_names = ', '.join([f'[{col}]' for col in clean_column_names])
        insert_sql = f"INSERT INTO dbo.{table_name} ({col_names}) VALUES ({placeholders})"
        
        cursor.executemany(insert_sql, python_data)
        conn.commit()
        
        total_time = time.time() - start_time
        print(f"    ✅ Optimized insert completed in {total_time:.2f}s!")
        
        return {
            'success': True,
            'method': 'OPTIMIZED_INSERT',
            'table_name': table_name,
            'rows_loaded': len(python_data),
            'columns_count': len(clean_column_names),
            'column_names': clean_column_names,
            'schema_analysis': schema_analysis
        }
        
    except Exception as e:
        print(f"    ❌ Optimized insert failed: {e}")
        return {
            'success': False,
            'method': 'OPTIMIZED_ERROR',
            'table_name': table_name,
            'error': str(e),
            'rows_attempted': len(df),
            'columns_count': len(df.columns)
        }

# ─── MAIN EXECUTION ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Start global timing
    global_start_time = time.time()
    
    print("=" * 80)
    print("🚀 COMPLETE XLSX TO SQL ORCHESTRATOR WITH COLUMN COMPARISON")
    print("=" * 80)
    print(f"📂 Source container: {source_container} (XLSX files)")
    print(f"📂 Target container: {target_container} (CSV files)")
    print(f"🗄️  Database: {db_key}")
    print(f"🔄 Overwrite CSV: {OVERWRITE_CSV}")
    print(f"🔄 Overwrite DB tables: {OVERWRITE_DB_TABLES}")
    print(f"📊 Compare with incumbent: {COMPARE_WITH_INCUMBENT}")
    
    # Initialize tracking lists
    processing_results = []
    
    try:
        # Test database connection
        print("\n📋 Testing database connection...")
        test_conn = db_helper.get_connection(db_key)
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT 1 AS connection_test")
        test_result = test_cursor.fetchone()
        test_cursor.close()
        test_conn.close()
        print("✅ Database connection test successful!")
        
        # Get blob client
        print("☁️ Connecting to Azure Blob Storage...")
        source_client = blob_svc.get_container_client(source_container)
        
        # Get list of XLSX files to process
        if PROCESS_ALL_XLSX:
            print(f"📁 Listing all XLSX files in container...")
            xlsx_blobs = [blob for blob in source_client.list_blobs() 
                         if blob.name.lower().endswith(('.xlsx', '.xls'))]
        else:
            print(f"🎯 Processing single file: {SINGLE_XLSX_FILE}")
            xlsx_blobs = [blob for blob in source_client.list_blobs() 
                         if blob.name == SINGLE_XLSX_FILE]
        
        if not xlsx_blobs:
            print(f"❌ No XLSX files found to process!")
            sys.exit(1)
        
        print(f"📊 Found {len(xlsx_blobs)} XLSX file(s) to process")
        
        # Process each XLSX file
        for i, blob in enumerate(xlsx_blobs, 1):
            print(f"\n[{i}/{len(xlsx_blobs)}] 🚀 PROCESSING: {blob.name}")
            print("=" * 80)
            
            # Add pause for manual control if processing multiple files and AUTO_CONFIRM is False
            if len(xlsx_blobs) > 1 and not AUTO_CONFIRM:
                response = input("  ⏸️ Press 'y' + Enter to process this file (or Ctrl+C to stop): ").strip().lower()
                if response != 'y':
                    print("  ⏭️ Skipping this file...")
                    continue
            
            # Process the file
            result = process_single_xlsx_file(blob.name)
            processing_results.append(result)
        
        # Generate final summary
        global_total_time = time.time() - global_start_time
        
        print(f"\n" + "=" * 80)
        print(f"📊 FINAL ORCHESTRATION SUMMARY")
        print("=" * 80)
        print(f"⏱️ Total processing time: {global_total_time:.2f}s ({global_total_time/60:.1f} minutes)")
        
        # Enhanced summary: classify partial/incomplete loads
        successful = []
        partial = []
        failed = []
        for r in processing_results:
            # If status is FAILED or db_load_success is False, it's failed
            if r['status'] == 'FAILED' or not r.get('db_load_success', True):
                failed.append(r)
            # If status is SUCCESS but 0 rows loaded or integrity < 100%, it's partial
            elif r['status'] == 'SUCCESS' and (
                r.get('rows_processed', 0) == 0 or r.get('integrity_accuracy', 100) < 100
            ):
                partial.append(r)
            else:
                successful.append(r)

        print(f"📁 Total files processed: {len(processing_results)}")
        print(f"✅ Successful: {len(successful)}")
        print(f"⚠️ Completed with issues: {len(partial)}")
        print(f"❌ Failed: {len(failed)}")

        # Alert on any partial or failed loads
        if partial:
            print(f"\n⚠️  PARTIAL/INCOMPLETE LOADS:")
            for r in partial:
                reason = []
                if r.get('rows_processed', 0) == 0:
                    reason.append("0 rows loaded")
                if r.get('integrity_accuracy', 100) < 100:
                    reason.append(f"integrity {r.get('integrity_accuracy', 0):.1f}%")
                print(f"  ⚠️ {r['xlsx_file']}: {', '.join(reason)}")

        if failed:
            print(f"\n❌ FAILED FILES:")
            for r in failed:
                print(f"  ❌ {r['xlsx_file']}: {r.get('error', 'Unknown error')}")

        # Print metrics for successful and partial loads
        metric_set = successful + partial
        if metric_set:
            total_rows = sum(r.get('rows_processed', 0) for r in metric_set)
            avg_accuracy = sum(r.get('integrity_accuracy', 0) for r in metric_set) / len(metric_set)

            print(f"📊 Tables created: {len(metric_set)}")
            print(f"📈 Total rows processed: {total_rows:,}")
            print(f"🎯 Average accuracy: {avg_accuracy:.1f}%")

            # Performance metrics
            total_processing_time = sum(r['timing']['total_time'] for r in metric_set)
            avg_file_time = total_processing_time / len(metric_set)
            overall_rate = total_rows / global_total_time if global_total_time > 0 else 0

            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"  • Average file processing time: {avg_file_time:.2f}s")
            print(f"  • Overall processing rate: {overall_rate:.0f} records/second")
            print(f"  • Overall processing rate: {overall_rate * 60:.0f} records/minute")

            # Method breakdown
            method_counts = {}
            for result in metric_set:
                method = result.get('db_load_method', 'UNKNOWN')
                method_counts[method] = method_counts.get(method, 0) + 1

            print(f"\n🔧 DATABASE LOADING METHODS:")
            for method, count in method_counts.items():
                print(f"  • {method}: {count} file(s)")

            # Column comparison summary
            if COMPARE_WITH_INCUMBENT:
                comparison_results = [r for r in metric_set if r.get('comparison_result') and r['comparison_result']['comparison_possible']]
                if comparison_results:
                    avg_column_accuracy = sum(r['comparison_result']['accuracy_score'] for r in comparison_results) / len(comparison_results)
                    total_new_columns = sum(len(r['comparison_result']['new_columns']) for r in comparison_results)
                    total_missing_columns = sum(len(r['comparison_result']['missing_columns']) for r in comparison_results)
                    total_modified_columns = sum(len(r['comparison_result']['modified_columns']) for r in comparison_results)
                    tables_100_match = sum(1 for r in comparison_results if abs(r['comparison_result']['accuracy_score'] - 100.0) < 1e-6)
                    print(f"\n📊 COLUMN COMPARISON SUMMARY:")
                    print(f"  • Tables compared with incumbent: {len(comparison_results)}")
                    print(f"  • Tables with 100% column match: {tables_100_match}")
                    print(f"  • Average column match accuracy: {avg_column_accuracy:.1f}%")
                    print(f"  • Total new columns: {total_new_columns}")
                    print(f"  • Total missing columns: {total_missing_columns}")
                    print(f"  • Total modified columns: {total_modified_columns}")
                else:
                    print(f"\n📊 COLUMN COMPARISON SUMMARY:")
                    print(f"  • No incumbent tables found for comparison")

            # ORDERS_UNIFIED comparison summary
            orders_unified_results = [r for r in metric_set if r.get('orders_unified_comparison')]
            if orders_unified_results:
                avg_orders_unified_match = sum(r['orders_unified_comparison']['match_percent'] for r in orders_unified_results) / len(orders_unified_results)
                total_missing_in_orders_unified = sum(len(r['orders_unified_comparison']['missing_columns']) for r in orders_unified_results)
                tables_100_orders_unified_match = sum(1 for r in orders_unified_results if abs(r['orders_unified_comparison']['match_percent'] - 100.0) < 1e-6)
                print(f"\n📊 ORDERS_UNIFIED COMPARISON SUMMARY:")
                print(f"  • Tables compared with ORDERS_UNIFIED: {len(orders_unified_results)}")
                print(f"  • Tables with 100% ORDERS_UNIFIED match: {tables_100_orders_unified_match}")
                print(f"  • Average ORDERS_UNIFIED match accuracy: {avg_orders_unified_match:.1f}%")
                print(f"  • Total columns missing in ORDERS_UNIFIED: {total_missing_in_orders_unified}")

            # --- Summary by File Table ---
            print(f"\n📋 Summary by File")
            print("-" * 110)
            header = [
                "File",
                "Match Accuracy (%)",
                "ORDERS_UNIFIED (%)",
                "Processing Rate (rows/s)",
                "New Columns",
                "Missing Columns",
                "Rows (Source)",
                "Rows (Target)",
                "Status"
            ]
            print("| " + " | ".join(header) + " |")
            print("|" + "---|" * len(header))
            for r in metric_set:
                comp = r.get('comparison_result')
                ou_comp = r.get('orders_unified_comparison')
                match_acc = f"{comp['accuracy_score']:.1f}" if comp and comp.get('comparison_possible') else "-"
                ou_match_acc = f"{ou_comp['match_percent']:.1f}" if ou_comp else "-"
                proc_rate = r.get('rows_processed', 0) / r['timing']['total_time'] if r['timing']['total_time'] > 0 else 0
                new_cols = len(comp['new_columns']) if comp and comp.get('comparison_possible') else "-"
                missing_cols = len(comp['missing_columns']) if comp and comp.get('comparison_possible') else "-"
                rows_source = r.get('rows_processed', '-')
                rows_target = r.get('db_rows', '-') if 'db_rows' in r else rows_source
                status = r['status']
                if r in partial:
                    status = 'PARTIAL'
                print(f"| {r['xlsx_file']} | {match_acc} | {ou_match_acc} | {proc_rate:.1f} | {new_cols} | {missing_cols} | {rows_source} | {rows_target} | {status} |")
        
        # Save detailed results
        if processing_results:
            # Flatten results for CSV export
            export_results = []
            for result in processing_results:
                export_row = {
                    'xlsx_file': result['xlsx_file'],
                    'csv_file': result['csv_file'],
                    'table_name': result['table_name'],
                    'incumbent_table': result.get('incumbent_table', ''),
                    'status': result['status'],
                    'rows_processed': result.get('rows_processed', 0),
                    'columns_processed': result.get('columns_processed', 0),
                    'db_load_method': result.get('db_load_method', ''),
                    'integrity_accuracy': result.get('integrity_accuracy', 0),
                    'total_time': result['timing']['total_time']
                }
                
                # Add comparison data if available
                if result.get('comparison_result') and result['comparison_result']['comparison_possible']:
                    comp = result['comparison_result']
                    export_row.update({
                        'column_match_accuracy': comp['accuracy_score'],
                        'new_columns_count': len(comp['new_columns']),
                        'missing_columns_count': len(comp['missing_columns']),
                        'modified_columns_count': len(comp['modified_columns']),
                        'new_columns': ', '.join(comp['new_columns'][:5]),  # First 5 only
                        'missing_columns': ', '.join(comp['missing_columns'][:5]),  # First 5 only
                    })
                else:
                    export_row.update({
                        'column_match_accuracy': 0,
                        'new_columns_count': 0,
                        'missing_columns_count': 0,
                        'modified_columns_count': 0,
                        'new_columns': '',
                        'missing_columns': ''
                    })
                
                # Add ORDERS_UNIFIED comparison data if available
                if result.get('orders_unified_comparison'):
                    ou_comp = result['orders_unified_comparison']
                    export_row.update({
                        'orders_unified_match_percent': ou_comp['match_percent'],
                        'orders_unified_missing_columns_count': len(ou_comp['missing_columns']),
                        'orders_unified_missing_columns': ', '.join(ou_comp['missing_columns'][:5]),  # First 5 only
                        'orders_unified_total_columns': ou_comp['orders_unified_total_columns']
                    })
                else:
                    export_row.update({
                        'orders_unified_match_percent': 0,
                        'orders_unified_missing_columns_count': 0,
                        'orders_unified_missing_columns': '',
                        'orders_unified_total_columns': 0
                    })
                
                export_results.append(export_row)
            
            # Export to CSV
            import os
            os.makedirs('notebooks/csv_temp', exist_ok=True)
            results_df = pd.DataFrame(export_results)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = os.path.join('notebooks/csv_temp', f"orchestration_results_{timestamp}.csv")
            results_df.to_csv(results_file, index=False)
            print(f"\n💾 Detailed results saved to: {results_file}")
            
            # Create summary
            summary_data = {
                'total_files': len(processing_results),
                'successful_files': len(successful),
                'failed_files': len(failed),
                'total_rows': sum(r.get('rows_processed', 0) for r in successful),
                'total_processing_time': global_total_time,
                'average_accuracy': avg_accuracy if successful else 0,
                'comparison_enabled': COMPARE_WITH_INCUMBENT
            }
            
            summary_df = pd.DataFrame([summary_data])
            summary_file = os.path.join('notebooks/csv_temp', f"orchestration_summary_{timestamp}.csv")
            summary_df.to_csv(summary_file, index=False)
            print(f"📋 Summary saved to: {summary_file}")
        
        # Final status
        success_rate = (len(successful) / len(processing_results)) * 100 if processing_results else 0
        print(f"\n🎉 ORCHESTRATION COMPLETE!")
        print(f"✅ Success rate: {success_rate:.1f}%")
        
        if failed:
            print(f"\n⚠️  FAILED FILES:")
            for result in failed:
                print(f"  ❌ {result['xlsx_file']}: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
