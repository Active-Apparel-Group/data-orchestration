
import sys
import requests
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

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

# Import helpers
import db_helper as db
import logger_helper
import staging_helper

# Set staging mode for API token storage (robust handling for safety)
staging_helper.set_staging_mode('robust')

# Load configuration from centralized config
config = db.load_config()

# Create logger instance for consistent usage
logger = logger_helper.get_logger("load_boards")

client_id       = os.getenv('PA_CLIENT_ID') or "{{ secret('PA_CLIENT_ID') }}"
client_secret   = os.getenv('PA_CLIENT_SECRET') or "{{ secret('PA_CLIENT_SECRET') }}"

def get_oauth_config() -> Dict[str, str]:
    """Get OAuth configuration"""
    return {
        "url": "https://login.microsoftonline.com/95d7583a-1925-44b1-b78b-3483e00c5b46/oauth2/v2.0/token",
        "grant_type": "client_credentials",
        # PA_CLIENT_ID
        "client_id": client_id,
        # PA_CLIENT_SECRET
        "client_secret": client_secret,
        "scope": "https://management.azure.com/.default"  # Azure Resource Manager for Logic Apps
    }

def get_bearer_token():
    """Retrieve bearer token from Microsoft OAuth endpoint"""
    try:
        print("🔐 Retrieving bearer token from Microsoft OAuth...")
        
        oauth_config = get_oauth_config()
        url = oauth_config.pop("url")
        
        # Make OAuth request
        response = requests.post(url, data=oauth_config, timeout=30)
        response.raise_for_status()
        
        # Parse JSON response
        payload = response.json()
        token = payload.get("access_token")
        expires = payload.get("expires_in")
        
        if not token:
            raise RuntimeError("Failed to get access_token from Azure AD response")
        
        print("Successfully retrieved bearer token!")
        print(f"Token preview: {token[:50]}...")
        print(f"Expires in: {expires} seconds ({expires/3600:.1f} hours)")
        
        return token, expires
        
    except Exception as e:
        print(f"Failed to retrieve token: {e}")
        raise

def store_token_in_database(token, expires):
    """Store bearer token in database using db_helper"""
    try:
        print("Storing bearer token in database...")
        
        # Use stored procedure with db_helper
        store_sql = """
        EXEC log.InsertBearerToken 
            @bearerToken = ?, 
            @expires_in = ?
        """
        
        # Execute using db_helper
        rows_affected = db.execute(
            store_sql, 
            "orders", 
            params=(token, expires)
        )
        
        print("Bearer token stored successfully!")
        print(f"Database rows affected: {rows_affected}")
        
        # Verify storage
        verify_sql = "SELECT COUNT(*) as token_count FROM log.BearerTokens"
        result = db.run_query(verify_sql, "orders")
        token_count = result.iloc[0]['token_count']
        print(f"Total tokens in database: {token_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to store token in database: {e}")
        raise

def main():
    """Main execution flow for Power Automate token retrieval"""
    print("=" * 60)
    print("POWER AUTOMATE BEARER TOKEN RETRIEVAL")
    print("=" * 60)
    
    try:
        # Step 1: Setup db_helper
        find_repo_root()
        
        # Step 2: Verify database connection
        db_config = db.get_database_config()
        print("Available database configurations:")
        for db_key, db_info in db_config.items():
            host = db_info.get("host", "N/A")
            database = db_info.get("database", "N/A")
            print(f"  • {db_key.upper()}: {host} → {database}")

        if "orders" in db_config:
            test_query = "SELECT 1 AS connection_test"
            test_result = db.run_query(test_query, "orders")
            print("Database connection test successful!")
        else:
            print("'orders' database configuration not found")
            return
        
        # Step 3: Get token
        token, expires = get_bearer_token()
        print("Access Token Retrieved:")
        print(token)
        
        # Step 4: Store in database
        store_token_in_database(token, expires)
        
        print("\nSUCCESS! Token retrieved and stored using db_helper")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
