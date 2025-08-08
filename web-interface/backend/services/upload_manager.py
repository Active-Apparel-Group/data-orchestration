"""
Upload Manager Service
Purpose: Manage file uploads to Monday.com boards with batch processing
Author: Data Engineering Team
Date: August 8, 2025

This service coordinates the upload process, manages progress tracking,
and integrates with existing AsyncBatchMondayUpdater infrastructure.
"""

import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import json

class UploadStatus(Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class UploadManagerService:
    """
    Service for managing file uploads to Monday.com boards with progress tracking
    and integration with existing async batch infrastructure.
    """
    
    def __init__(self):
        self.active_uploads = {}  # Store active upload sessions
        self.upload_history = {}  # Store completed uploads
        self.batch_size = 100  # Items per batch
        self.max_concurrent_batches = 3
        
    async def start_upload(self, 
                          upload_request: Dict[str, Any],
                          progress_callback: Optional[Callable] = None) -> str:
        """
        Start a new upload session
        
        Args:
            upload_request: Upload configuration with file data, mapping, board info
            progress_callback: Optional callback for progress updates
            
        Returns:
            Upload session ID
        """
        try:
            # Generate unique upload ID
            upload_id = str(uuid.uuid4())
            
            # Validate upload request
            self._validate_upload_request(upload_request)
            
            # Create upload session
            upload_session = {
                'id': upload_id,
                'status': UploadStatus.PENDING,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'board_id': upload_request['board_id'],
                'group_id': upload_request.get('group_id'),
                'file_data': upload_request['file_data'],
                'column_mapping': upload_request['column_mapping'],
                'total_rows': len(upload_request['file_data']),
                'processed_rows': 0,
                'successful_rows': 0,
                'failed_rows': 0,
                'batches': [],
                'errors': [],
                'progress_callback': progress_callback,
                'options': upload_request.get('options', {})
            }
            
            # Store session
            self.active_uploads[upload_id] = upload_session
            
            # Start upload process asynchronously
            asyncio.create_task(self._process_upload(upload_id))
            
            return upload_id
            
        except Exception as e:
            raise ValueError(f"Failed to start upload: {str(e)}")
    
    async def get_upload_status(self, upload_id: str) -> Dict[str, Any]:
        """Get current status of an upload session"""
        
        # Check active uploads
        if upload_id in self.active_uploads:
            session = self.active_uploads[upload_id]
            return self._format_upload_status(session)
        
        # Check upload history
        if upload_id in self.upload_history:
            session = self.upload_history[upload_id]
            return self._format_upload_status(session)
        
        raise ValueError(f"Upload session '{upload_id}' not found")
    
    async def cancel_upload(self, upload_id: str) -> bool:
        """Cancel an active upload session"""
        
        if upload_id not in self.active_uploads:
            return False
        
        session = self.active_uploads[upload_id]
        
        if session['status'] in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
            return False
        
        # Mark as cancelled
        session['status'] = UploadStatus.CANCELLED
        session['updated_at'] = datetime.now().isoformat()
        
        # Move to history
        self.upload_history[upload_id] = session
        del self.active_uploads[upload_id]
        
        await self._notify_progress(session, "Upload cancelled by user")
        
        return True
    
    async def _process_upload(self, upload_id: str):
        """Process the upload in the background"""
        
        session = self.active_uploads[upload_id]
        
        try:
            # Update status to preparing
            session['status'] = UploadStatus.PREPARING
            session['updated_at'] = datetime.now().isoformat()
            await self._notify_progress(session, "Preparing upload...")
            
            # Prepare data batches
            batches = self._create_batches(session['file_data'], session['column_mapping'])
            session['batches'] = batches
            
            # Update status to uploading
            session['status'] = UploadStatus.UPLOADING
            session['updated_at'] = datetime.now().isoformat()
            await self._notify_progress(session, f"Uploading {len(batches)} batches...")
            
            # Process batches
            await self._process_batches(session)
            
            # Mark as completed
            if session['status'] != UploadStatus.CANCELLED:
                session['status'] = UploadStatus.COMPLETED
                session['updated_at'] = datetime.now().isoformat()
                await self._notify_progress(session, "Upload completed successfully!")
            
        except Exception as e:
            # Mark as failed
            session['status'] = UploadStatus.FAILED
            session['updated_at'] = datetime.now().isoformat()
            session['errors'].append({
                'type': 'system_error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
            await self._notify_progress(session, f"Upload failed: {str(e)}")
        
        finally:
            # Move to history
            self.upload_history[upload_id] = session
            if upload_id in self.active_uploads:
                del self.active_uploads[upload_id]
    
    def _validate_upload_request(self, request: Dict[str, Any]):
        """Validate upload request has required fields"""
        
        required_fields = ['board_id', 'file_data', 'column_mapping']
        
        for field in required_fields:
            if field not in request:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(request['file_data'], list):
            raise ValueError("file_data must be a list of dictionaries")
        
        if not isinstance(request['column_mapping'], dict):
            raise ValueError("column_mapping must be a dictionary")
        
        if len(request['file_data']) == 0:
            raise ValueError("file_data cannot be empty")
    
    def _create_batches(self, file_data: List[Dict], column_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Create batches for upload processing"""
        
        batches = []
        total_rows = len(file_data)
        
        for i in range(0, total_rows, self.batch_size):
            batch_data = file_data[i:i + self.batch_size]
            
            # Transform data according to mapping
            monday_items = []
            for row_data in batch_data:
                monday_item = self._transform_row_to_monday_item(row_data, column_mapping)
                monday_items.append(monday_item)
            
            batch = {
                'id': len(batches) + 1,
                'start_index': i,
                'end_index': min(i + self.batch_size, total_rows),
                'size': len(batch_data),
                'data': monday_items,
                'status': 'pending',
                'created_items': [],
                'errors': []
            }
            
            batches.append(batch)
        
        return batches
    
    def _transform_row_to_monday_item(self, row_data: Dict, column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Transform a file row to Monday.com item format"""
        
        monday_item = {
            'name': '',  # Will be set from mapped column or default
            'column_values': {}
        }
        
        # Process each mapped column
        for file_column, monday_column_id in column_mapping.items():
            if file_column in row_data:
                value = row_data[file_column]
                
                # Handle special case for item name
                if monday_column_id == 'name':
                    monday_item['name'] = str(value) if value else ''
                else:
                    # Format value for Monday.com column
                    formatted_value = self._format_column_value(value, monday_column_id)
                    monday_item['column_values'][monday_column_id] = formatted_value
        
        # Ensure we have a name
        if not monday_item['name']:
            # Use first mapped column value or row index
            for file_column, monday_column_id in column_mapping.items():
                if file_column in row_data and row_data[file_column]:
                    monday_item['name'] = str(row_data[file_column])[:50]  # Limit length
                    break
            
            if not monday_item['name']:
                monday_item['name'] = f"Item {hash(str(row_data)) % 10000}"
        
        return monday_item
    
    def _format_column_value(self, value: Any, monday_column_id: str) -> str:
        """Format a value for Monday.com column"""
        
        if value is None or value == '':
            return ''
        
        # For now, convert everything to string
        # TODO: Implement type-specific formatting based on Monday column type
        return str(value)
    
    async def _process_batches(self, session: Dict[str, Any]):
        """Process all batches for the upload session"""
        
        batches = session['batches']
        
        # Process batches with limited concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        
        async def process_batch(batch):
            async with semaphore:
                await self._process_single_batch(session, batch)
        
        # Create tasks for all batches
        tasks = [process_batch(batch) for batch in batches]
        
        # Wait for all batches to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_batch(self, session: Dict[str, Any], batch: Dict[str, Any]):
        """Process a single batch of items"""
        
        try:
            if session['status'] == UploadStatus.CANCELLED:
                return
            
            batch['status'] = 'processing'
            
            # TODO: Replace with actual Monday.com API integration
            # For now, simulate the upload process
            await self._simulate_monday_upload(session, batch)
            
            batch['status'] = 'completed'
            
            # Update session progress
            session['processed_rows'] += batch['size']
            session['successful_rows'] += len(batch['created_items'])
            session['failed_rows'] += len(batch['errors'])
            session['updated_at'] = datetime.now().isoformat()
            
            # Notify progress
            progress_percentage = (session['processed_rows'] / session['total_rows']) * 100
            await self._notify_progress(
                session, 
                f"Processed batch {batch['id']}: {session['processed_rows']}/{session['total_rows']} rows ({progress_percentage:.1f}%)"
            )
            
        except Exception as e:
            batch['status'] = 'failed'
            batch['errors'].append({
                'type': 'batch_error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            session['failed_rows'] += batch['size']
            session['errors'].append({
                'type': 'batch_error',
                'batch_id': batch['id'],
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    async def _simulate_monday_upload(self, session: Dict[str, Any], batch: Dict[str, Any]):
        """Simulate Monday.com upload (replace with actual implementation)"""
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Simulate successful creation of items
        for i, item_data in enumerate(batch['data']):
            # Simulate some failures (10% failure rate)
            if i % 10 == 0:
                batch['errors'].append({
                    'row_index': batch['start_index'] + i,
                    'item_name': item_data['name'],
                    'error': 'Simulated API error',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                batch['created_items'].append({
                    'row_index': batch['start_index'] + i,
                    'item_name': item_data['name'],
                    'monday_item_id': f"mock_item_{uuid.uuid4().hex[:8]}",
                    'timestamp': datetime.now().isoformat()
                })
    
    async def _notify_progress(self, session: Dict[str, Any], message: str):
        """Notify progress callback if available"""
        
        if session.get('progress_callback'):
            try:
                progress_data = {
                    'upload_id': session['id'],
                    'status': session['status'].value,
                    'message': message,
                    'progress': {
                        'total_rows': session['total_rows'],
                        'processed_rows': session['processed_rows'],
                        'successful_rows': session['successful_rows'],
                        'failed_rows': session['failed_rows'],
                        'percentage': (session['processed_rows'] / session['total_rows'] * 100) if session['total_rows'] > 0 else 0
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                await session['progress_callback'](progress_data)
                
            except Exception as e:
                # Don't fail the upload if progress notification fails
                print(f"Progress notification failed: {e}")
    
    def _format_upload_status(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Format upload session for API response"""
        
        return {
            'upload_id': session['id'],
            'status': session['status'].value if isinstance(session['status'], UploadStatus) else session['status'],
            'created_at': session['created_at'],
            'updated_at': session['updated_at'],
            'board_id': session['board_id'],
            'group_id': session.get('group_id'),
            'progress': {
                'total_rows': session['total_rows'],
                'processed_rows': session['processed_rows'],
                'successful_rows': session['successful_rows'],
                'failed_rows': session['failed_rows'],
                'percentage': (session['processed_rows'] / session['total_rows'] * 100) if session['total_rows'] > 0 else 0
            },
            'batches': {
                'total': len(session.get('batches', [])),
                'completed': len([b for b in session.get('batches', []) if b.get('status') == 'completed']),
                'failed': len([b for b in session.get('batches', []) if b.get('status') == 'failed'])
            },
            'errors': session.get('errors', []),
            'has_errors': len(session.get('errors', [])) > 0
        }
    
    async def get_upload_results(self, upload_id: str) -> Dict[str, Any]:
        """Get detailed results for a completed upload"""
        
        session = None
        if upload_id in self.upload_history:
            session = self.upload_history[upload_id]
        elif upload_id in self.active_uploads:
            session = self.active_uploads[upload_id]
        
        if not session:
            raise ValueError(f"Upload session '{upload_id}' not found")
        
        created_items = []
        failed_items = []
        
        # Collect results from all batches
        for batch in session.get('batches', []):
            created_items.extend(batch.get('created_items', []))
            failed_items.extend(batch.get('errors', []))
        
        return {
            'upload_id': upload_id,
            'status': session['status'].value if isinstance(session['status'], UploadStatus) else session['status'],
            'summary': {
                'total_rows': session['total_rows'],
                'successful_rows': session['successful_rows'],
                'failed_rows': session['failed_rows'],
                'success_rate': (session['successful_rows'] / session['total_rows'] * 100) if session['total_rows'] > 0 else 0
            },
            'created_items': created_items,
            'failed_items': failed_items,
            'system_errors': session.get('errors', [])
        }
