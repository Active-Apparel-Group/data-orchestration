"""
Simple FastAPI Test Server
Purpose: Test basic FastAPI functionality for React web interface
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Monday.com Upload Interface - Test Server",
    description="Simple test server for React frontend development",
    version="1.0.0-test"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Monday.com Data Upload API - Test Mode",
        "version": "1.0.0-test",
        "message": "React backend is running!"
    }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint for frontend connection"""
    return {
        "success": True,
        "message": "Backend connection successful!",
        "timestamp": "2025-08-08T12:00:00Z"
    }

@app.get("/api/boards")
async def get_boards():
    """Mock boards endpoint"""
    return [
        {
            "id": "9609317401",
            "name": "Customer Master Schedule",
            "item_terminology": "Orders",
            "columns": [
                {
                    "id": "name",
                    "title": "Name",
                    "type": "name"
                },
                {
                    "id": "dropdown_mkr542p2",
                    "title": "CUSTOMER",
                    "type": "dropdown"
                }
            ]
        }
    ]

if __name__ == "__main__":
    print("🚀 Starting Monday.com Upload Interface - Test Server")
    print("📱 React frontend can connect to: http://localhost:8000")
    print("📋 API documentation available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
