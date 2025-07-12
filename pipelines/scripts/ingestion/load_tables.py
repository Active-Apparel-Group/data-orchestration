#!/usr/bin/env python3
"""
Generic DB-to-DB Extract and Load (ETL) - Atomic Swap Version
------------------------------------------------------------
* Loads job config from config/db_jobs/job_<JOB_NAME>.toml
* Extracts from source DB/table/query, loads to target DB/table
* Uses atomic swap pattern for zero-downtime deployment
* Supports optional column mapping and transforms
"""

import os, sys, tomli, pandas as pd
from pathlib import Path
import logging, time
from typing import Optional, Dict, Any

# Find repo root and add to path
def find_repo_root() -> Path:
    cur = Path(__file__).resolve()
    while cur.parent != cur:
        if (cur / "pipelines/utils" / "db_helper.py").exists():
            return cur
        cur = cur.parent
    raise RuntimeError("repo root with ./utils/db_helper.py not found")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines/utils"))

# Import helpers
import db_helper
import logger_helper
import staging_helper

# Set staging mode for general DB-to-DB transfers (robust handling for safety)
staging_helper.set_staging_mode('robust')

logger = logger_helper.get_logger("db_to_db_refresh")

def load_job_config(job_name: str) -> Dict[str, Any]:
    """Load job configuration from TOML file"""
    config_path = repo_root / f"configs/db_jobs/job_{job_name}.toml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    with open(config_path, "rb") as f:
        cfg = tomli.load(f)
    
    # Add computed fields
    cfg['config_path'] = config_path
    if cfg.get('target', {}).get('table'):
        cfg['stage_table'] = f"swp_{cfg['target']['table']}"
    
    return cfg

def extract_data(cfg: Dict[str, Any]) -> pd.DataFrame:
    """Extract data from source database"""
    src = cfg["source"]
    
    # Check if using stored procedure configuration
    if "stored_procedure" in src:
        sp_config = src["stored_procedure"]
        query = build_stored_procedure_query(sp_config)
        logger.info(f"Using stored procedure: {sp_config.get('procedure_name', 'unknown')}")
    # Build query from direct query or table
    elif src.get("query"):
        query = src["query"]
        logger.info(f"Using custom query from config")
    else:
        query = f"SELECT * FROM {src['table']}"
        logger.info(f"Using default table query: {src['table']}")
    
    logger.info(f"Extracting from {src['db_name']}: {query[:100]}...")
    
    # Use db_helper to run query
    df = db_helper.run_query(query, src['db_name'])
    
    logger.info(f"Extracted {len(df)} rows, {len(df.columns)} columns")
    return df

def build_stored_procedure_query(sp_config: Dict[str, Any]) -> str:
    """Build EXEC query from stored procedure configuration"""
    proc_name = sp_config.get("procedure_name", "")
    
    # Build parameter list
    params = []
    for key, value in sp_config.items():
        if key in ["db_name", "procedure_name"]:
            continue  # Skip non-parameter keys
            
        # Handle different value types
        if value is None or str(value).lower() == "null" or value == "":
            params.append(f"@{key} = NULL")
        elif isinstance(value, str) and value.startswith(("DATEADD", "GETDATE", "DATEFROMPARTS", "EOMONTH")):
            # Dynamic SQL expressions - don't quote
            params.append(f"@{key} = {value}")
        else:
            # String literals - quote them
            params.append(f"@{key} = '{value}'")
    
    # Build final query
    if params:
        params_str = ",\n    ".join(params)
        query = f"EXEC [dbo].[{proc_name}]\n    {params_str}"
    else:
        query = f"EXEC [dbo].[{proc_name}]"
    
    return query

def apply_mapping_and_transform(df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Apply optional column mapping and transforms"""
    mapping = cfg.get("mapping", {})
    transforms = cfg.get("transform", {})
    
    # Apply column mapping if specified
    if mapping:
        logger.info(f"Applying column mapping: {len(mapping)} columns")
        df = df.rename(columns=mapping)
    
    # Apply transforms if specified
    if transforms:
        logger.info(f"Applying transforms: {len(transforms)} columns")
        for col, func_str in transforms.items():
            if col in df.columns:
                try:
                    transform_func = eval(func_str)
                    df[col] = df[col].apply(transform_func)
                    logger.info(f"Applied transform to column: {col}")
                except Exception as e:
                    logger.error(f"Transform failed for column {col}: {e}")
                    raise
    
    # Apply column exclusions if specified
    exclude_cols = cfg.get("exclude", {}).get("columns", [])
    if exclude_cols:
        existing_exclude_cols = [col for col in exclude_cols if col in df.columns]
        if existing_exclude_cols:
            df = df.drop(columns=existing_exclude_cols)
            logger.info(f"Excluded columns: {existing_exclude_cols}")
    
    return df

def load_data_atomic_swap(df: pd.DataFrame, cfg: Dict[str, Any]) -> None:
    """Load data using atomic swap pattern"""
    tgt = cfg["target"]
    options = cfg.get("options", {})
    
    # Configuration
    target_table = tgt["table"]
    stage_table = cfg.get("stage_table", f"swp_{target_table}")
    db_name = tgt["db_name"]
    chunk_size = options.get("chunk_size", 1000)
    
    logger.info(f"Loading to {db_name}.{target_table} via staging table {stage_table}")
    logger.info(f"Using chunk size: {chunk_size} for {len(df)} rows")
    
    try:
        # Step 1: Create/prepare staging table
        logger.info("Step 1: Preparing staging table...")
        options = cfg.get("options", {})
        staging_helper.prepare_staging_table(df, stage_table, target_table, db_name, options=options)
        
        # Step 2: Load data to staging table
        logger.info("Step 2: Loading data to staging table...")
        start_time = time.time()
        staging_helper.load_to_staging_table(df, stage_table, db_name, batch_size=chunk_size)
        load_time = time.time() - start_time
        
        logger.info(f"Staging load completed in {load_time:.2f}s ({len(df)/load_time:.0f} rows/sec)")
        
        # Step 3: Atomic swap
        logger.info("Step 3: Performing atomic table swap...")
        staging_helper.atomic_swap_tables(stage_table, target_table, db_name)
        
        # Replace Unicode/emoji log messages with ASCII
        logger.info("SUCCESS: Atomic swap completed successfully")
    except Exception as e:
        logger.error(f"LOAD FAILED: {e}")
        raise

def validate_results(cfg: Dict[str, Any], source_row_count: int) -> None:
    """Validate the ETL results"""
    tgt = cfg["target"]
    
    # Count rows in target table
    count_query = f"SELECT COUNT(*) as row_count FROM {tgt['table']}"
    result_df = db_helper.run_query(count_query, tgt['db_name'])
    target_row_count = result_df.iloc[0]['row_count']
    
    logger.info(f"Validation: Source={source_row_count}, Target={target_row_count}")
    
    if source_row_count == target_row_count:
        logger.info("✅ Row count validation passed")
    else:
        logger.warning(f"⚠️ Row count mismatch: expected {source_row_count}, got {target_row_count}")
    
    # Sample data logging if enabled
    options = cfg.get("options", {})
    if options.get("log_sample_data", False):
        sample_query = f"SELECT TOP 3 * FROM {tgt['table']}"
        sample_df = db_helper.run_query(sample_query, tgt['db_name'])
        logger.info(f"Sample data (first 3 rows):\n{sample_df.to_string()}")

def main():
    """Main ETL orchestration function"""
    import argparse
    parser = argparse.ArgumentParser(description="DB-to-DB Extract and Load with Atomic Swap")
    parser.add_argument("-j", "--job", required=True, help="Job name (matches TOML config)")
    parser.add_argument("-v", "--validate", action="store_true", help="Run validation after load")
    args = parser.parse_args()

    # Load configuration
    logger.info(f"Starting DB-to-DB ETL job: {args.job}")
    cfg = load_job_config(args.job)
    logger.info(f"Loaded config: {cfg['meta']['description']}")
    
    total_start = time.time()
    
    try:
        # Extract
        logger.info("=== EXTRACT PHASE ===")
        df = extract_data(cfg)
        source_row_count = len(df)
        
        # Transform  
        logger.info("=== TRANSFORM PHASE ===")
        df = apply_mapping_and_transform(df, cfg)
        
        # Load
        logger.info("=== LOAD PHASE ===")
        load_data_atomic_swap(df, cfg)
        
        # Validate
        if args.validate:
            logger.info("=== VALIDATION PHASE ===")
            validate_results(cfg, source_row_count)
        
        # Performance summary
        total_time = time.time() - total_start
        rows_per_sec = source_row_count / total_time if total_time > 0 else 0
        
        logger.info("=== ETL COMPLETE ===")
        logger.info(f"SUCCESS: Successfully processed {source_row_count} rows")
        logger.info(f"TIME: Total time: {total_time:.2f}s ({rows_per_sec:.0f} rows/sec)")
        logger.info(f"TARGET: {cfg['target']['db_name']}.{cfg['target']['table']}")
        
    except Exception as e:
        logger.error(f"ETL job failed: {e}")
        raise

if __name__ == "__main__":
    main()
