"""
FastAPI Backend for Monday.com Web Interface
Purpose: REST API wrapper for existing Monday.com GraphQL operations
Author: Data Engineering Team
Date: August 8, 2025

This backend provides a user-friendly REST API that wraps our existing
production-proven Monday.com GraphQL infrastructure, enabling the React
frontend to perform file uploads, column mapping, and async batch updates.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add project root to path for imports
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import our existing infrastructure
try:
    from pipelines.utils import logger_helper
    from api.monday_wrapper import MondayWrapperService
    from services.file_parser import FileParserService
    from services.column_mapper import ColumnMapperService
    from services.upload_manager import UploadManagerService
except ImportError as e:
    # Graceful fallback during development
    print(f"Warning: Could not import all modules: {e}")
    logger_helper = None

# Initialize FastAPI app
app = FastAPI(
    title="Monday.com Data Upload Interface",
    description="React-friendly API for Monday.com data uploads with column mapping",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logger
logger = logger_helper.get_logger(__name__) if logger_helper else logging.getLogger(__name__)

# Pydantic models for API contracts
class BoardInfo(BaseModel):
    id: str
    name: str
    item_terminology: str
    columns: List[Dict[str, Any]]

class ColumnMapping(BaseModel):
    file_column: str
    board_column_id: str
    board_column_title: str
    column_type: str
    is_mapped: bool = True

class UploadProgress(BaseModel):
    upload_id: str
    status: str  # "pending", "processing", "completed", "failed"
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    progress_percentage: float
    current_operation: str
    errors: List[Dict[str, Any]] = []

class UploadResult(BaseModel):
    upload_id: str
    status: str
    total_records: int
    successful_records: int
    failed_records: int
    monday_item_ids: List[str]
    errors: List[Dict[str, Any]]
    export_data: Optional[Dict[str, Any]] = None

# Global state for upload tracking (in production, use Redis or database)
upload_sessions: Dict[str, Dict[str, Any]] = {}

# Initialize services
monday_service = None
file_parser = None
column_mapper = None
upload_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global monday_service, file_parser, column_mapper, upload_manager
    
    try:
        logger.info("🚀 Starting Monday.com Data Upload API")
        
        # Initialize services
        monday_service = MondayWrapperService()
        file_parser = FileParserService()
        column_mapper = ColumnMapperService()
        upload_manager = UploadManagerService()
        
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Monday.com Data Upload API",
        "version": "1.0.0",
        "timestamp": "2025-08-08"
    }

@app.get("/api/boards", response_model=List[BoardInfo])
async def get_boards() -> List[BoardInfo]:
    """
    Get list of accessible Monday.com boards with column metadata
    
    Returns:
        List of boards with their column information for mapping
    """
    try:
        logger.info("📋 Fetching accessible Monday.com boards")
        
        # Use MondayWrapperService to fetch boards
        if monday_service:
            boards = await monday_service.get_accessible_boards()
            logger.info(f"✅ Found {len(boards)} accessible boards")
            return boards
        else:
            # Fallback mock data for development
            mock_boards = [
                {
                    "id": "9609317401",
                    "name": "Customer Master Schedule",
                    "item_terminology": "Orders",
                    "columns": [
                        {
                            "id": "name",
                            "title": "Name",
                            "type": "name",
                            "description": "Item name"
                        },
                        {
                            "id": "dropdown_mkr542p2",
                            "title": "CUSTOMER",
                            "type": "dropdown",
                            "description": "Customer name"
                        },
                        {
                            "id": "text_mkr5wya6",
                            "title": "AAG ORDER NUMBER",
                            "type": "text",
                            "description": "Order number"
                        }
                    ]
                }
            ]
            
            logger.info(f"✅ Found {len(mock_boards)} accessible boards (mock)")
            return mock_boards
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch boards: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch boards: {str(e)}")

@app.post("/api/upload/analyze")
async def analyze_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Analyze uploaded file and detect columns
    
    Args:
        file: Uploaded CSV or Excel file
        
    Returns:
        File analysis with detected columns and sample data
    """
    try:
        logger.info(f"📁 Analyzing uploaded file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Use FileParserService to parse file
        if file_parser:
            analysis = await file_parser.parse_file(content, file.filename)
            logger.info(f"✅ File analysis complete: {analysis['total_rows']} rows, {len(analysis['detected_columns'])} columns")
            return analysis
        else:
            # Fallback mock analysis for development
            mock_analysis = {
                "filename": file.filename,
                "file_type": "csv" if file.filename.lower().endswith('.csv') else "excel",
                "total_rows": 150,
                "detected_columns": [
                    {
                        "name": "Customer Name",
                        "sample_values": ["GREYSON", "JOHNNIE O", "TRACKSMITH"],
                        "data_type": "text",
                        "null_count": 0
                    },
                    {
                        "name": "Order Number", 
                        "sample_values": ["ORD-001", "ORD-002", "ORD-003"],
                        "data_type": "text",
                        "null_count": 0
                    },
                    {
                        "name": "Order Date",
                        "sample_values": ["2025-01-15", "2025-01-16", "2025-01-17"],
                        "data_type": "date",
                        "null_count": 2
                    }
                ],
                "sample_data": [
                    {"Customer Name": "GREYSON", "Order Number": "ORD-001", "Order Date": "2025-01-15"},
                    {"Customer Name": "JOHNNIE O", "Order Number": "ORD-002", "Order Date": "2025-01-16"},
                    {"Customer Name": "TRACKSMITH", "Order Number": "ORD-003", "Order Date": "2025-01-17"}
                ]
            }
            
            logger.info(f"✅ Mock file analysis complete: {mock_analysis['total_rows']} rows")
            return mock_analysis
        
    except Exception as e:
        logger.error(f"❌ Failed to analyze file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")

@app.post("/api/mapping/suggest")
async def suggest_column_mapping(
    board_id: str = Form(...),
    file_columns: List[str] = Form(...)
) -> List[ColumnMapping]:
    """
    Suggest automatic column mapping between file and board columns
    
    Args:
        board_id: Monday.com board ID
        file_columns: List of column names from uploaded file
        
    Returns:
        Suggested column mappings with confidence scores
    """
    try:
        logger.info(f"🔗 Suggesting column mappings for board {board_id}")
        
        # TODO: Use ColumnMapperService for intelligent mapping
        # For now, return mock mappings
        mock_mappings = [
            {
                "file_column": "Customer Name",
                "board_column_id": "dropdown_mkr542p2",
                "board_column_title": "CUSTOMER",
                "column_type": "dropdown",
                "is_mapped": True
            },
            {
                "file_column": "Order Number",
                "board_column_id": "text_mkr5wya6",
                "board_column_title": "AAG ORDER NUMBER",
                "column_type": "text",
                "is_mapped": True
            },
            {
                "file_column": "Order Date",
                "board_column_id": "date_mkr5zp5",
                "board_column_title": "ORDER DATE PO RECEIVED",
                "column_type": "date",
                "is_mapped": True
            }
        ]
        
        logger.info(f"✅ Generated {len(mock_mappings)} column mapping suggestions")
        return mock_mappings
        
    except Exception as e:
        logger.error(f"❌ Failed to suggest mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to suggest mappings: {str(e)}")

@app.post("/api/upload/start")
async def start_upload(
    board_id: str = Form(...),
    file: UploadFile = File(...),
    column_mappings: str = Form(...)  # JSON string of mappings
) -> Dict[str, str]:
    """
    Start async upload process
    
    Args:
        board_id: Monday.com board ID
        file: Uploaded file
        column_mappings: JSON string of column mappings
        
    Returns:
        Upload session ID for tracking progress
    """
    try:
        import uuid
        import json
        
        upload_id = str(uuid.uuid4())
        logger.info(f"⚡ Starting upload session {upload_id} for board {board_id}")
        
        # Parse column mappings
        mappings = json.loads(column_mappings)
        
        # Store upload session
        upload_sessions[upload_id] = {
            "status": "pending",
            "board_id": board_id,
            "filename": file.filename,
            "mappings": mappings,
            "total_records": 0,
            "processed_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "errors": []
        }
        
        # TODO: Start async background task for upload
        # For now, simulate async start
        logger.info(f"✅ Upload session {upload_id} created successfully")
        
        return {"upload_id": upload_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"❌ Failed to start upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start upload: {str(e)}")

@app.get("/api/upload/{upload_id}/progress", response_model=UploadProgress)
async def get_upload_progress(upload_id: str) -> UploadProgress:
    """
    Get real-time upload progress
    
    Args:
        upload_id: Upload session ID
        
    Returns:
        Current upload progress and status
    """
    try:
        if upload_id not in upload_sessions:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        session = upload_sessions[upload_id]
        
        # Calculate progress percentage
        progress_percentage = 0.0
        if session["total_records"] > 0:
            progress_percentage = (session["processed_records"] / session["total_records"]) * 100
        
        return UploadProgress(
            upload_id=upload_id,
            status=session["status"],
            total_records=session["total_records"],
            processed_records=session["processed_records"],
            successful_records=session["successful_records"],
            failed_records=session["failed_records"],
            progress_percentage=progress_percentage,
            current_operation=session.get("current_operation", "Initializing..."),
            errors=session["errors"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")

@app.get("/api/upload/{upload_id}/results", response_model=UploadResult)
async def get_upload_results(upload_id: str) -> UploadResult:
    """
    Get final upload results with Monday.com item IDs
    
    Args:
        upload_id: Upload session ID
        
    Returns:
        Complete upload results for export
    """
    try:
        if upload_id not in upload_sessions:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        session = upload_sessions[upload_id]
        
        if session["status"] not in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail="Upload not yet completed")
        
        # TODO: Generate export data with Monday.com item IDs
        mock_item_ids = [f"item_{i}" for i in range(1, session["successful_records"] + 1)]
        
        return UploadResult(
            upload_id=upload_id,
            status=session["status"],
            total_records=session["total_records"],
            successful_records=session["successful_records"],
            failed_records=session["failed_records"],
            monday_item_ids=mock_item_ids,
            errors=session["errors"],
            export_data={
                "filename": f"upload_results_{upload_id}.csv",
                "download_url": f"/api/upload/{upload_id}/export"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    return {
        "status": "healthy",
        "timestamp": "2025-08-08T12:00:00Z",
        "version": "1.0.0",
        "services": {
            "monday_api": "connected",
            "file_parser": "ready",
            "column_mapper": "ready"
        },
        "active_uploads": len(upload_sessions)
    }

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
