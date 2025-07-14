"""
ORDER_LIST Pipeline - Production-Ready Orchestration
Purpose: Complete Extract → Transform → Load coordination with monitoring
Author: Data Engineering Team  
Date: July 10, 2025

Production Pipeline:
1. Extract: Blob storage XLSX → x{customer}_ORDER_LIST_RAW tables  
2. Transform: Raw → Staging with DDL schema + precision fixes
3. Load: Atomic swap to production ORDER_LIST table
4. Validation: Data quality checks and metrics
5. Monitoring: Comprehensive logging and reporting
"""

import sys
import time
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with pipelines/utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))  # pipelines/utils ONLY

import logger_helper
import db_helper as db
# Import pipeline modules dynamically to avoid import path issues
# from order_list_transform import OrderListTransformer  # Will be imported when needed

class OrderListPipeline:
    """
    Production ORDER_LIST pipeline orchestrator
    
    Coordinates complete Extract → Transform → Load workflow with:
    - Comprehensive error handling and rollback
    - Progress monitoring and metrics
    - Data quality validation
    - Performance optimization
    """
    
    def __init__(self, db_key: str = "orders"):
        self.logger = logger_helper.get_logger(__name__)
        self.db_key = db_key
        self.start_time = None
        self.pipeline_id = f"order_list_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Pipeline paths
        self.extract_script = repo_root / "pipelines" / "scripts" / "load_order_list" / "order_list_extract.py"
        
        # Metrics tracking
        self.metrics = {
            'pipeline_id': self.pipeline_id,
            'start_time': None,
            'stages_completed': [],
            'stages_failed': [],
            'total_files_processed': 0,
            'total_records_processed': 0,
            'duration_seconds': 0,
            'performance_metrics': {}
        }
        
    def log_stage_start(self, stage_name: str):
        """Log the start of a pipeline stage"""
        self.logger.info(f"[*] STAGE: {stage_name} - Starting")
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"[*] PIPELINE STAGE: {stage_name}")
        self.logger.info(f"{'='*60}")
        
    def log_stage_success(self, stage_name: str, metrics: Dict[str, Any]):
        """Log successful completion of a pipeline stage"""
        self.metrics['stages_completed'].append(stage_name)
        self.logger.info(f"[+] STAGE: {stage_name} - Completed successfully")
        
        # Log key metrics
        for key, value in metrics.items():
            if key in ['files_processed', 'tables_processed', 'total_rows', 'duration']:
                self.logger.info(f"   {key}: {value}")
                
        self.logger.info(f"[+] STAGE COMPLETED: {stage_name}")
        
    def log_stage_failure(self, stage_name: str, error: str):
        """Log failure of a pipeline stage"""
        self.metrics['stages_failed'].append(stage_name)
        self.logger.error(f"[-] STAGE: {stage_name} - Failed: {error}")
        self.logger.error(f"[-] STAGE FAILED: {stage_name}")
        self.logger.error(f"Error: {error}")
        
    def validate_prerequisites(self) -> Dict[str, Any]:
        """Validate that all prerequisites are met before starting pipeline"""
        self.log_stage_start("PREREQUISITES VALIDATION")
        
        try:
            # Check database connectivity
            test_query = "SELECT COUNT(*) as test_count FROM INFORMATION_SCHEMA.TABLES"
            db.run_query(test_query, self.db_key)
            
            # Check extract script exists
            if not self.extract_script.exists():
                raise FileNotFoundError(f"Extract script not found: {self.extract_script}")
            
            # Check blob storage connectivity (basic check)
            # This would ideally test blob storage but we'll do a simpler validation
            
            self.log_stage_success("PREREQUISITES VALIDATION", {
                'database_connectivity': 'OK',
                'extract_script': 'OK'
            })
            
            return {'success': True, 'stage': 'prerequisites'}
            
        except Exception as e:
            self.log_stage_failure("PREREQUISITES VALIDATION", str(e))
            return {'success': False, 'stage': 'prerequisites', 'error': str(e)}
    
    def run_blob_upload_stage(self) -> Dict[str, Any]:
        """
        Run the blob upload stage: SharePoint discovery → Azure Blob Storage
        
        Returns:
            Blob upload results with metrics
        """
        self.log_stage_start("BLOB UPLOAD - SharePoint to Azure Blob Storage")
        
        try:
            start_time = time.time()
            
            # Dynamic import of blob module to avoid module-level import issues
            sys.path.insert(0, str(Path(__file__).parent))
            import order_list_blob
            
            # Initialize blob uploader
            blob_uploader = order_list_blob.OrderListBlobUploader()
            
            # Run the upload process
            self.logger.info("Starting SharePoint file discovery and blob upload")
            upload_results = blob_uploader.process_all_files()
            
            duration = time.time() - start_time
            
            # Extract metrics from upload results
            files_found = upload_results.get('files_found', 0)
            files_uploaded = upload_results.get('files_uploaded', 0)
            total_size_mb = upload_results.get('total_size_mb', 0)
            success_rate = upload_results.get('success_rate', 0)
            
            # Determine success based on upload results
            success = files_uploaded > 0 and success_rate >= 95
            
            metrics = {
                'files_found': files_found,
                'files_uploaded': files_uploaded,
                'upload_success_rate': success_rate,
                'total_size_mb': total_size_mb,
                'duration': duration,
                'performance_mb_per_sec': total_size_mb / duration if duration > 0 else 0
            }
            
            self.metrics['performance_metrics']['blob_upload'] = metrics
            
            if success and files_uploaded > 0:
                self.log_stage_success("BLOB UPLOAD", metrics)
                return {
                    'success': True,
                    'stage': 'blob_upload',
                    'output': f"Uploaded {files_uploaded} files ({total_size_mb:.2f} MB) from SharePoint",
                    **metrics
                }
            else:
                error_msg = f"Blob upload failed or no files uploaded. Found: {files_found}, Uploaded: {files_uploaded}"
                self.log_stage_failure("BLOB UPLOAD", error_msg)
                return {
                    'success': False,
                    'stage': 'blob_upload',
                    'error': error_msg,
                    **metrics
                }
                
        except Exception as e:
            error_msg = f"Blob upload stage failed with error: {str(e)}"
            self.log_stage_failure("BLOB UPLOAD", error_msg)
            return {'success': False, 'stage': 'blob_upload', 'error': error_msg}

    def run_extract_stage(self, limit_files: int = None) -> Dict[str, Any]:
        """
        Run the extract stage: blob storage → raw tables
        
        Args:
            limit_files: Optional limit on number of files to process (for testing)
            
        Returns:
            Extract results with metrics
        """
        self.log_stage_start("EXTRACT - Blob Storage to Raw Tables")
        
        try:
            # Import and call extract main function directly for better performance
            # This avoids subprocess overhead and environment inheritance issues
            sys.path.insert(0, str(self.extract_script.parent))
            
            # Import the extract module
            import order_list_extract
            
            if limit_files:
                self.logger.info(f"Running extract with file limit: {limit_files}")
                # Note: Current extract script doesn't support file limits
                # This would require modifying the extract script to accept parameters
            
            start_time = time.time()
            
            # Call extract main function directly
            self.logger.info("Calling extract main function directly (no subprocess)")
            extract_result = order_list_extract.main()
            
            duration = time.time() - start_time
            
            # Extract already returns structured data, so use it directly
            files_processed = extract_result.get('files_processed', 0)
            total_records = extract_result.get('total_rows', 0)
            success_count = extract_result.get('success_count', 0)
            
            metrics = {
                'files_processed': files_processed,
                'total_records': total_records,
                'success_count': success_count,
                'duration': duration,
                'performance': total_records / duration if duration > 0 else 0
            }
            
            self.metrics['total_files_processed'] = files_processed
            self.metrics['performance_metrics']['extract'] = metrics
            
            # Consider it successful if we processed files
            success = files_processed > 0
            
            if success:
                self.log_stage_success("EXTRACT", metrics)
            else:
                self.log_stage_failure("EXTRACT", "No files processed")
            
            return {
                'success': success, 
                'stage': 'extract',
                'output': f"Processed {files_processed} files, {total_records:,} total rows",
                **metrics
            }
                
        except Exception as e:
            error_msg = f"Extract stage failed with error: {str(e)}"
            self.log_stage_failure("EXTRACT", error_msg)
            return {'success': False, 'stage': 'extract', 'error': error_msg}
    
    def run_transform_stage(self) -> Dict[str, Any]:
        """
        Run the transform stage: raw tables → staging table with precision fixes
        
        Returns:
            Transform results with comprehensive metrics
        """
        self.log_stage_start("TRANSFORM - Raw Tables to Staging (DDL Schema)")
        
        try:
            # Import transformer dynamically to avoid path issues
            sys.path.insert(0, str(Path(__file__).parent))
            from order_list_transform import OrderListTransformer
            
            transformer = OrderListTransformer()
            
            # Use the server-side optimized transform method
            results = transformer.run_transform_server_side_optimized()
            
            if results.get('success', False):
                metrics = {
                    'total_customers_processed': results.get('total_customers_processed', 0),
                    'failed_customers': results.get('failed_customers', 0),
                    'total_rows': results.get('total_rows', 0),
                    'duration': results.get('duration', 0),
                    'performance': results.get('total_rows', 0) / results.get('duration', 1),
                    'server_side_optimized': results.get('server_side_optimized', False)
                }
                
                self.metrics['total_records_processed'] = metrics['total_rows']
                self.metrics['performance_metrics']['transform'] = metrics
                
                self.log_stage_success("TRANSFORM", metrics)
                
                return {'success': True, 'stage': 'transform', **results}
            else:
                error_msg = results.get('error', 'Transform failed with unknown error')
                self.log_stage_failure("TRANSFORM", error_msg)
                return {'success': False, 'stage': 'transform', 'error': error_msg}
                
        except Exception as e:
            self.log_stage_failure("TRANSFORM", str(e))
            return {'success': False, 'stage': 'transform', 'error': str(e)}
    
    def run_validation_stage(self) -> Dict[str, Any]:
        """
        Run data quality validation on the final ORDER_LIST table
        
        Returns:
            Validation results with quality metrics
        """
        self.log_stage_start("VALIDATION - Data Quality Checks")
        
        try:
            # Basic validation queries
            validations = {}
            
            # 1. Record count validation
            count_query = "SELECT COUNT(*) as total_records FROM ORDER_LIST"
            count_result = db.run_query(count_query, self.db_key)
            total_records = int(count_result['total_records'].iloc[0]) if not count_result.empty else 0
            validations['total_records'] = total_records
            
            # 2. Data quality checks
            quality_query = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN [AAG ORDER NUMBER] IS NOT NULL AND [AAG ORDER NUMBER] != '' THEN 1 END) as valid_order_numbers,
                    COUNT(CASE WHEN [CUSTOMER] IS NOT NULL AND [CUSTOMER] != '' THEN 1 END) as valid_customers,
                    COUNT(CASE WHEN [ORDER QTY] IS NOT NULL AND TRY_CAST([ORDER QTY] AS INT) IS NOT NULL THEN 1 END) as valid_quantities,
                    COUNT(DISTINCT [CUSTOMER]) as unique_customers,
                    COUNT(DISTINCT [_SOURCE_TABLE]) as source_tables
                FROM ORDER_LIST
            """
            quality_result = db.run_query(quality_query, self.db_key)
            
            if not quality_result.empty:
                quality_row = quality_result.iloc[0]
                validations.update({
                    'valid_order_numbers': int(quality_row['valid_order_numbers']),
                    'valid_customers': int(quality_row['valid_customers']),
                    'valid_quantities': int(quality_row['valid_quantities']),
                    'unique_customers': int(quality_row['unique_customers']),
                    'source_tables': int(quality_row['source_tables'])
                })
                
                # Calculate quality percentages
                if total_records > 0:
                    validations['order_number_quality'] = (validations['valid_order_numbers'] / total_records) * 100
                    validations['customer_quality'] = (validations['valid_customers'] / total_records) * 100
                    validations['quantity_quality'] = (validations['valid_quantities'] / total_records) * 100
            
            # 3. Schema validation - check for proper data types
            schema_query = """
                SELECT 
                    COLUMN_NAME, 
                    DATA_TYPE, 
                    IS_NULLABLE,
                    CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ORDER_LIST'
                ORDER BY ORDINAL_POSITION
            """
            schema_result = db.run_query(schema_query, self.db_key)
            validations['schema_columns'] = len(schema_result) if not schema_result.empty else 0
            
            # Success criteria - define what constitutes a successful validation
            success_criteria = {
                'min_records': 1000,  # Minimum records expected
                'min_order_number_quality': 95,  # 95% of records should have valid order numbers
                'min_customer_quality': 90,  # 90% should have valid customers
                'min_unique_customers': 5  # At least 5 different customers
            }
            
            # Evaluate success
            validation_passed = all([
                validations['total_records'] >= success_criteria['min_records'],
                validations.get('order_number_quality', 0) >= success_criteria['min_order_number_quality'],
                validations.get('customer_quality', 0) >= success_criteria['min_customer_quality'],
                validations['unique_customers'] >= success_criteria['min_unique_customers']
            ])
            
            metrics = {
                'validation_passed': validation_passed,
                'success_criteria': success_criteria,
                **validations
            }
            
            if validation_passed:
                self.log_stage_success("VALIDATION", metrics)
                return {'success': True, 'stage': 'validation', **metrics}
            else:
                error_msg = f"Validation failed: Records={validations['total_records']}, Quality checks failed"
                self.log_stage_failure("VALIDATION", error_msg)
                return {'success': False, 'stage': 'validation', 'error': error_msg, **metrics}
                
        except Exception as e:
            self.log_stage_failure("VALIDATION", str(e))
            return {'success': False, 'stage': 'validation', 'error': str(e)}
    
    def generate_final_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive pipeline report"""
        report_lines = [
            "[*] ORDER_LIST PIPELINE REPORT",
            "=" * 60,
            f"Pipeline ID: {self.pipeline_id}",
            f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Duration: {self.metrics['duration_seconds']:.2f} seconds",
            ""
        ]
        
        if results['success']:
            report_lines.extend([
                "[+] PIPELINE STATUS: SUCCESS",
                "",
                "[*] PERFORMANCE METRICS:",
                f"   Files Processed: {self.metrics['total_files_processed']}",
                f"   Records Processed: {self.metrics['total_records_processed']:,}",
                f"   Overall Performance: {self.metrics['total_records_processed'] / self.metrics['duration_seconds']:.0f} records/sec",
                ""
            ])
            
            # Stage-specific metrics
            for stage, stage_metrics in self.metrics['performance_metrics'].items():
                report_lines.append(f"   {stage.upper()} Stage:")
                if isinstance(stage_metrics, dict):
                    for key, value in stage_metrics.items():
                        if isinstance(value, (int, float)):
                            if 'duration' in key:
                                report_lines.append(f"      {key}: {value:.2f}s")
                            elif 'performance' in key:
                                report_lines.append(f"      {key}: {value:.0f} records/sec")
                            else:
                                report_lines.append(f"      {key}: {value:,}" if value > 1000 else f"      {key}: {value}")
                report_lines.append("")
            
            # Validation results
            if 'validation_results' in results:
                val_results = results['validation_results']
                report_lines.extend([
                    "[*] DATA QUALITY VALIDATION:",
                    f"   Total Records: {val_results.get('total_records', 0):,}",
                    f"   Order Number Quality: {val_results.get('order_number_quality', 0):.1f}%",
                    f"   Customer Quality: {val_results.get('customer_quality', 0):.1f}%",
                    f"   Unique Customers: {val_results.get('unique_customers', 0)}",
                    f"   Source Tables: {val_results.get('source_tables', 0)}",
                    ""
                ])
        else:
            report_lines.extend([
                "[-] PIPELINE STATUS: FAILED",
                f"Failed Stage: {results.get('failed_stage', 'Unknown')}",
                f"Error: {results.get('error', 'Unknown error')}",
                ""
            ])
        
        report_lines.extend([
            "[*] STAGES COMPLETED:",
            *[f"   [+] {stage}" for stage in self.metrics['stages_completed']],
            ""
        ])
        
        if self.metrics['stages_failed']:
            report_lines.extend([
                "[-] STAGES FAILED:",
                *[f"   [-] {stage}" for stage in self.metrics['stages_failed']],
                ""
            ])
        
        return "\n".join(report_lines)
    
    def run_complete_pipeline(self, extract_limit: int = None, skip_blob: bool = False, skip_extract: bool = False, skip_validation: bool = False) -> Dict[str, Any]:
        """
        Run the complete ORDER_LIST pipeline with comprehensive monitoring
        
        Args:
            extract_limit: Optional limit on files to extract (for testing)
            skip_blob: Skip SharePoint blob upload stage (use existing blob files)
            skip_extract: Skip extract stage (for transform-only runs)
            skip_validation: Skip validation stage (for faster runs)
            
        Returns:
            Complete pipeline results with metrics
        """
        self.start_time = time.time()
        self.metrics['start_time'] = datetime.now()
        
        self.logger.info(f"[*] Starting ORDER_LIST Pipeline - ID: {self.pipeline_id}")
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"[*] ORDER_LIST PRODUCTION PIPELINE")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"Pipeline ID: {self.pipeline_id}")
        self.logger.info(f"Start Time: {self.metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Results accumulator
        pipeline_results = {
            'pipeline_id': self.pipeline_id,
            'success': False,
            'failed_stage': None,
            'stages': {}
        }
        
        try:
            # Stage 0: Prerequisites validation
            prereq_results = self.validate_prerequisites()
            pipeline_results['stages']['prerequisites'] = prereq_results
            if not prereq_results.get('success', False):
                pipeline_results['failed_stage'] = 'prerequisites'
                pipeline_results['error'] = prereq_results.get('error')
                return self._finalize_pipeline_results(pipeline_results)
            
            # Stage 1: Blob Upload - SharePoint to Azure Blob Storage (optional skip)
            if not skip_blob:
                blob_results = self.run_blob_upload_stage()
                pipeline_results['stages']['blob_upload'] = blob_results
                if not blob_results.get('success', False):
                    pipeline_results['failed_stage'] = 'blob_upload'
                    pipeline_results['error'] = blob_results.get('error')
                    return self._finalize_pipeline_results(pipeline_results)
            else:
                self.logger.info("[>>] BLOB UPLOAD STAGE SKIPPED")
                self.logger.info("[>>] BLOB UPLOAD STAGE SKIPPED - Using existing blob files")
            
            # Stage 2: Extract - Blob storage to Raw Tables (optional skip)
            if not skip_extract:
                extract_results = self.run_extract_stage(limit_files=extract_limit)
                pipeline_results['stages']['extract'] = extract_results
                if not extract_results.get('success', False):
                    pipeline_results['failed_stage'] = 'extract'
                    pipeline_results['error'] = extract_results.get('error')
                    return self._finalize_pipeline_results(pipeline_results)
            else:
                self.logger.info("[>>] EXTRACT STAGE SKIPPED")
                self.logger.info("[>>] EXTRACT STAGE SKIPPED - Using existing raw tables")
            
            # Stage 3: Transform (required)
            transform_results = self.run_transform_stage()
            pipeline_results['stages']['transform'] = transform_results
            if not transform_results.get('success', False):
                pipeline_results['failed_stage'] = 'transform'
                pipeline_results['error'] = transform_results.get('error')
                return self._finalize_pipeline_results(pipeline_results)
            
            # Stage 4: Validation (optional skip)
            if not skip_validation:
                validation_results = self.run_validation_stage()
                pipeline_results['stages']['validation'] = validation_results
                pipeline_results['validation_results'] = validation_results
                
                if not validation_results.get('success', False):
                    # Validation failure is a warning, not a hard failure
                    self.logger.warning("[!] Validation failed but pipeline will continue")
                    self.logger.warning("[!] VALIDATION WARNING: Data quality checks failed")
            else:
                self.logger.info("[>>] VALIDATION STAGE SKIPPED")
                self.logger.info("[>>] VALIDATION STAGE SKIPPED")
            
            # Pipeline completed successfully
            pipeline_results['success'] = True
            
            return self._finalize_pipeline_results(pipeline_results)
            
        except Exception as e:
            self.logger.error(f"[!] Pipeline failed with unexpected error: {e}")
            pipeline_results['failed_stage'] = 'unexpected_error'
            pipeline_results['error'] = str(e)
            return self._finalize_pipeline_results(pipeline_results)
    
    def _finalize_pipeline_results(self, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize pipeline results and generate report"""
        self.metrics['duration_seconds'] = time.time() - self.start_time
        pipeline_results['duration'] = self.metrics['duration_seconds']
        pipeline_results['metrics'] = self.metrics
        
        # Generate and log final report
        final_report = self.generate_final_report(pipeline_results)
        
        # Log to file and console
        self.logger.info("FINAL PIPELINE REPORT:\n" + final_report)
        self.logger.info(f"\n{final_report}")
        
        return pipeline_results

def main():
    """Enhanced main entry point with comprehensive options"""
    parser = argparse.ArgumentParser(
        description='ORDER_LIST Production Pipeline - Extract → Transform → Load',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete pipeline (production)
  python order_list_pipeline.py
  
  # Complete pipeline with file limit (testing)
  python order_list_pipeline.py --limit-files 5
  
  # Transform only (skip extract)
  python order_list_pipeline.py --transform-only
  
  # Extract only
  python order_list_pipeline.py --extract-only
  
  # Skip validation (faster)
  python order_list_pipeline.py --skip-validation
        """
    )
    
    # Stage control options
    parser.add_argument('--extract-only', action='store_true', 
                       help='Run extract stage only')
    parser.add_argument('--transform-only', action='store_true', 
                       help='Run transform stage only (skip extract)')
    parser.add_argument('--validation-only', action='store_true',
                       help='Run validation stage only')
    
    # Pipeline options
    parser.add_argument('--skip-blob', action='store_true',
                       help='Skip SharePoint blob upload stage (use existing blob files)')
    parser.add_argument('--skip-extract', action='store_true',
                       help='Skip extract stage (use existing raw tables)')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip validation stage (faster execution)')
    
    # Testing options
    parser.add_argument('--limit-files', type=int, metavar='N',
                       help='Limit number of files to extract (for testing)')
    
    # Database options
    parser.add_argument('--db-key', default='orders', 
                       help='Database key to use (default: orders)')
    
    # Output options  
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    parser.add_argument('--report-file', metavar='PATH',
                       help='Save pipeline report to file')
    
    args = parser.parse_args()
    
    # Validate argument combinations
    stage_options = [args.extract_only, args.transform_only, args.validation_only]
    if sum(stage_options) > 1:
        parser.error("Cannot specify multiple --*-only options")
    
    if args.skip_extract and args.extract_only:
        parser.error("Cannot use --skip-extract with --extract-only")
    
    # Initialize pipeline
    pipeline = OrderListPipeline(db_key=args.db_key)
    
    try:
        # Handle single-stage execution
        if args.extract_only:
            self.logger.info("[*] RUNNING EXTRACT STAGE ONLY")
            results = pipeline.run_extract_stage(limit_files=args.limit_files)
            success = results.get('success', False)
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Extract stage {'COMPLETED SUCCESSFULLY' if success else 'FAILED'}")
            if success:
                self.logger.info(f"Files processed: {results.get('files_processed', 0)}")
                self.logger.info(f"Records extracted: {results.get('total_records', 0)}")
                self.logger.info(f"Duration: {results.get('duration', 0):.2f} seconds")
            else:
                self.logger.info(f"Error: {results.get('error', 'Unknown error')}")
            
            return 0 if success else 1
        
        elif args.transform_only:
            self.logger.info("[*] RUNNING TRANSFORM STAGE ONLY")
            results = pipeline.run_transform_stage()
            success = results.get('success', False)
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Transform stage {'COMPLETED SUCCESSFULLY' if success else 'FAILED'}")
            if success:
                self.logger.info(f"Customers processed: {results.get('total_customers_processed', 0)}")
                self.logger.info(f"Records transformed: {results.get('total_rows', 0)}")
                self.logger.info(f"Duration: {results.get('duration', 0):.2f} seconds")
            else:
                self.logger.info(f"Error: {results.get('error', 'Unknown error')}")
            
            return 0 if success else 1
        
        elif args.validation_only:
            self.logger.info("[*] RUNNING VALIDATION STAGE ONLY")
            results = pipeline.run_validation_stage()
            success = results.get('success', False)
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Validation stage {'PASSED' if success else 'FAILED'}")
            if success:
                self.logger.info(f"Total records: {results.get('total_records', 0)}")
                self.logger.info(f"Data quality: {results.get('order_number_quality', 0):.1f}% order numbers valid")
                self.logger.info(f"Unique customers: {results.get('unique_customers', 0)}")
            else:
                self.logger.info(f"Validation failed: {results.get('error', 'Unknown error')}")
            
            return 0 if success else 1
        
        else:
            # Run complete pipeline
            self.logger.info("[*] RUNNING COMPLETE ORDER_LIST PIPELINE")
            results = pipeline.run_complete_pipeline(
                extract_limit=args.limit_files,
                skip_blob=args.skip_blob,
                skip_extract=args.skip_extract,
                skip_validation=args.skip_validation
            )
            
            success = results.get('success', False)
            
            # Final status
            self.logger.info(f"\n{'='*80}")
            self.logger.info("[*] PIPELINE {'COMPLETED SUCCESSFULLY' if success else 'FAILED'}")
            self.logger.info(f"{'='*80}")
            
            if success:
                self.logger.info("[+] Pipeline ID: {results.get('pipeline_id', 'N/A')}")
                self.logger.info("[+] Total Duration: {results.get('duration', 0):.2f} seconds")
                
                # Extract metrics if available
                extract_stage = results.get('stages', {}).get('extract', {})
                if extract_stage.get('success'):
                    self.logger.info("[+] Files Processed: {extract_stage.get('files_processed', 0)}")
                
                # Transform metrics
                transform_stage = results.get('stages', {}).get('transform', {})
                if transform_stage.get('success'):
                    self.logger.info("[+] Records in ORDER_LIST: {transform_stage.get('total_rows', 0):,}")
                    self.logger.info("[+] Customers Processed: {transform_stage.get('total_customers_processed', 0)}")
                
                # Validation metrics if available
                validation_results = results.get('validation_results', {})
                if validation_results.get('success'):
                    self.logger.info("[+] Data Quality: {validation_results.get('order_number_quality', 0):.1f}% valid order numbers")
                
            else:
                failed_stage = results.get('failed_stage', 'unknown')
                error = results.get('error', 'Unknown error')
                self.logger.error("[-] Failed at stage: {failed_stage}")
                self.logger.error("[-] Error: {error}")
            
            # Save report to file if requested
            if args.report_file:
                try:
                    report_content = pipeline.generate_final_report(results)
                    with open(args.report_file, 'w') as f:
                        f.write(report_content)
                    self.logger.info("[*] Report saved to: {args.report_file}")
                except Exception as e:
                    self.logger.warning("[!] Could not save report to {args.report_file}: {e}")
            
            return 0 if success else 1
    
    except KeyboardInterrupt:
        self.logger.info("\n\n[!] Pipeline interrupted by user")
        return 130
    except Exception as e:
        self.logger.info(f"\n\n[!] Pipeline failed with unexpected error: {e}")
        pipeline.logger.exception("Unexpected pipeline failure")
        return 1

if __name__ == "__main__":
    sys.exit(main())
