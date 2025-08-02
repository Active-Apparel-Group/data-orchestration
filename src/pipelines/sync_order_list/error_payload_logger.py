"""
Error Payload Logger for Monday.com API
=======================================
Purpose: Save API request/response payloads to JSONB files for error analysis
Location: src/pipelines/sync_order_list/error_payload_logger.py
Created: 2025-08-02

Core Philosophy: Fast JSONB file logging for errors, database for success
- Saves to configs/sync/ folder for easy access
- One file per record_uuid or per batch
- Separate request/response files or combined
- Performance-optimized for error scenarios
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.pipelines.utils import logger


class ErrorPayloadLogger:
    """
    High-performance error payload logger for Monday.com API failures
    Saves API request/response data to JSONB files for analysis
    """
    
    def __init__(self, sync_folder_path: Optional[str] = None):
        """
        Initialize error payload logger
        
        Args:
            sync_folder_path: Optional path to sync folder, defaults to configs/sync/
        """
        self.logger = logger.get_logger(__name__)
        
        # Default to configs/sync/ folder
        if sync_folder_path is None:
            repo_root = Path(__file__).parent.parent.parent.parent
            self.sync_folder = repo_root / "configs" / "sync"
        else:
            self.sync_folder = Path(sync_folder_path)
        
        # Ensure sync folder exists
        self.sync_folder.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Error payload logger initialized: {self.sync_folder}")
    
    def log_error_payload(self, record_uuid: str, operation_type: str, 
                         request_data: Any, response_data: Any, 
                         error_message: str = None, 
                         separate_files: bool = False) -> Dict[str, str]:
        """
        Log API error payload to JSONB file(s)
        
        Args:
            record_uuid: Unique record identifier
            operation_type: Type of operation (create_items, update_items, etc.)
            request_data: API request payload
            response_data: API response payload
            error_message: Optional error description
            separate_files: If True, save request/response in separate files
            
        Returns:
            Dict with file paths created
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        try:
            if separate_files:
                # Save request and response in separate files
                request_file = self.sync_folder / f"error_request_{record_uuid}_{timestamp}.jsonb"
                response_file = self.sync_folder / f"error_response_{record_uuid}_{timestamp}.jsonb"
                
                # Request file
                request_payload = {
                    "record_uuid": record_uuid,
                    "operation_type": operation_type,
                    "timestamp": timestamp,
                    "error_message": error_message,
                    "request_data": request_data
                }
                
                with open(request_file, 'w', encoding='utf-8') as f:
                    json.dump(request_payload, f, indent=2, default=str, ensure_ascii=False)
                
                # Response file
                response_payload = {
                    "record_uuid": record_uuid,
                    "operation_type": operation_type,
                    "timestamp": timestamp,
                    "error_message": error_message,
                    "response_data": response_data
                }
                
                with open(response_file, 'w', encoding='utf-8') as f:
                    json.dump(response_payload, f, indent=2, default=str, ensure_ascii=False)
                
                self.logger.info(f"💾 Error payloads saved (separate files): {request_file.name}, {response_file.name}")
                
                return {
                    "request_file": str(request_file),
                    "response_file": str(response_file)
                }
            
            else:
                # Save request and response in combined file
                combined_file = self.sync_folder / f"error_combined_{record_uuid}_{timestamp}.jsonb"
                
                combined_payload = {
                    "record_uuid": record_uuid,
                    "operation_type": operation_type,
                    "timestamp": timestamp,
                    "error_message": error_message,
                    "request_data": request_data,
                    "response_data": response_data,
                    "api_analysis": self._analyze_monday_error(response_data)
                }
                
                with open(combined_file, 'w', encoding='utf-8') as f:
                    json.dump(combined_payload, f, indent=2, default=str, ensure_ascii=False)
                
                self.logger.info(f"💾 Error payload saved (combined): {combined_file.name}")
                
                return {
                    "combined_file": str(combined_file)
                }
        
        except Exception as e:
            self.logger.error(f"Failed to save error payload for {record_uuid}: {e}")
            return {"error": str(e)}
    
    def log_batch_error_payload(self, batch_id: str, operation_type: str,
                               batch_request_data: List[Any], batch_response_data: Any,
                               failed_records: List[str] = None,
                               error_message: str = None) -> str:
        """
        Log batch API error payload to JSONB file
        
        Args:
            batch_id: Unique batch identifier
            operation_type: Type of batch operation
            batch_request_data: Batch API request payload
            batch_response_data: Batch API response payload
            failed_records: List of record UUIDs that failed
            error_message: Optional batch error description
            
        Returns:
            Path to created file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        batch_file = self.sync_folder / f"error_batch_{batch_id}_{timestamp}.jsonb"
        
        try:
            batch_payload = {
                "batch_id": batch_id,
                "operation_type": operation_type,
                "timestamp": timestamp,
                "error_message": error_message,
                "failed_records": failed_records or [],
                "batch_request_data": batch_request_data,
                "batch_response_data": batch_response_data,
                "batch_analysis": {
                    "total_records": len(batch_request_data) if isinstance(batch_request_data, list) else 1,
                    "failed_count": len(failed_records) if failed_records else 0,
                    "monday_errors": self._analyze_monday_error(batch_response_data)
                }
            }
            
            with open(batch_file, 'w', encoding='utf-8') as f:
                json.dump(batch_payload, f, indent=2, default=str, ensure_ascii=False)
            
            self.logger.info(f"💾 Batch error payload saved: {batch_file.name}")
            return str(batch_file)
        
        except Exception as e:
            self.logger.error(f"Failed to save batch error payload for {batch_id}: {e}")
            return f"ERROR: {str(e)}"
    
    def _analyze_monday_error(self, response_data: Any) -> Dict[str, Any]:
        """
        Analyze Monday.com API error response for common patterns
        
        Args:
            response_data: API response containing errors
            
        Returns:
            Analysis of error patterns
        """
        analysis = {
            "has_errors": False,
            "error_types": [],
            "status_codes": [],
            "retryable": False,
            "error_summary": None
        }
        
        try:
            if isinstance(response_data, dict):
                # Check for GraphQL errors array
                if 'errors' in response_data and response_data['errors']:
                    analysis["has_errors"] = True
                    
                    for error in response_data['errors']:
                        if isinstance(error, dict):
                            # Extract error message
                            message = error.get('message', '')
                            analysis["error_types"].append(message)
                            
                            # Extract status code from extensions
                            extensions = error.get('extensions', {})
                            status_code = extensions.get('status_code')
                            if status_code:
                                analysis["status_codes"].append(status_code)
                            
                            # Check for specific Monday.com error patterns
                            if 'JsonParseException' in extensions.get('code', ''):
                                analysis["error_summary"] = "JSON Syntax Error - Invalid column value format"
                            elif status_code in [500, 502, 503, 504, 429]:
                                analysis["retryable"] = True
                            elif 'timeout' in message.lower():
                                analysis["retryable"] = True
                
                # Check for data field null (indicates error)
                if response_data.get('data') is None and analysis["has_errors"]:
                    analysis["error_summary"] = analysis["error_summary"] or "API returned null data with errors"
        
        except Exception as e:
            analysis["analysis_error"] = str(e)
        
        return analysis
    
    def cleanup_old_error_files(self, days_to_keep: int = 7) -> int:
        """
        Clean up error payload files older than specified days
        
        Args:
            days_to_keep: Number of days to retain files
            
        Returns:
            Number of files cleaned up
        """
        try:
            cutoff_date = datetime.utcnow().timestamp() - (days_to_keep * 24 * 3600)
            cleanup_count = 0
            
            for error_file in self.sync_folder.glob("error_*.jsonb"):
                if error_file.stat().st_mtime < cutoff_date:
                    error_file.unlink()
                    cleanup_count += 1
            
            if cleanup_count > 0:
                self.logger.info(f"🧹 Cleaned up {cleanup_count} old error payload files (older than {days_to_keep} days)")
            
            return cleanup_count
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup old error files: {e}")
            return 0
