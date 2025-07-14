"""
Enhanced auth_helper.py with database-backed MSAL token cache
Stores token cache in SQL Server instead of local file for production use
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from msal import PublicClientApplication, SerializableTokenCache
import requests

# Add project utils to path
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with pipelines/utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))  # Only use pipelines/utils for Kestra compatibility

import db_helper  # noqa: E402

class InsecureSession(requests.Session):
    def request(self, *args, **kwargs):
        kwargs['verify'] = True
        logging.debug("Using insecure session: SSL verification is disabled.")
        return super().request(*args, **kwargs)

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID", "70c40022-9957-4db8-b402-f7d6d32beefb")
TENANT_ID = os.getenv("TENANT_ID", "95d7583a-1925-44b1-b78b-3483e00c5b46")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Files.Read.All", "Sites.Read.All", "User.Read"]


class DatabaseTokenCache(SerializableTokenCache):
    """
    Custom MSAL token cache that stores tokens in SQL Server database
    instead of local file system
    """
    
    def __init__(self, cache_key: str = "msal_default", db_key: str = "dms"):
        super().__init__()
        self.cache_key = cache_key
        self.db_key = db_key
        self._ensure_cache_table()
        self._load_from_db()
    
    def _ensure_cache_table(self):
        """Create the token cache table if it doesn't exist"""
        create_table_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='msal_token_cache' AND xtype='U')
        CREATE TABLE msal_token_cache (
            cache_key NVARCHAR(100) PRIMARY KEY,
            cache_data NVARCHAR(MAX),
            created_at DATETIME2 DEFAULT GETDATE(),
            updated_at DATETIME2 DEFAULT GETDATE(),
            expires_at DATETIME2 NULL,
            user_info NVARCHAR(500) NULL
        )
        """
        
        try:
            with db_helper.get_connection(self.db_key) as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                logging.info("✅ MSAL token cache table ready")
        except Exception as e:
            logging.error(f"❌ Failed to create token cache table: {e}")
            raise
    
    def _load_from_db(self):
        """Load token cache from database"""
        try:
            with db_helper.get_connection(self.db_key) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT cache_data FROM msal_token_cache WHERE cache_key = ?",
                    (self.cache_key,)
                )
                row = cursor.fetchone()
                
                if row and row[0]:
                    cache_data = row[0]
                    self.deserialize(cache_data)
                    logging.info("✅ Token cache loaded from database")
                else:
                    logging.info("📝 No existing token cache found in database")
                    
        except Exception as e:
            logging.warning(f"⚠️ Could not load token cache from database: {e}")
            # Continue without cached tokens (will require fresh authentication)
    
    def _save_to_db(self, cache_data: str):
        """Save token cache to database"""
        try:
            # Extract some metadata from cache for tracking
            try:
                cache_json = json.loads(cache_data) if cache_data else {}
                accounts = cache_json.get("Account", {})
                user_info = list(accounts.keys())[0] if accounts else "unknown"
                
                # Try to find expiration time from access tokens
                access_tokens = cache_json.get("AccessToken", {})
                expires_at = None
                if access_tokens:
                    token_data = list(access_tokens.values())[0]
                    if isinstance(token_data, dict) and "expires_on" in token_data:
                        try:
                            from datetime import datetime
                            expires_at = datetime.fromtimestamp(int(token_data["expires_on"]))
                        except:
                            pass
                            
            except:
                user_info = "unknown"
                expires_at = None
            
            with db_helper.get_connection(self.db_key) as conn:
                cursor = conn.cursor()
                
                # Use MERGE for upsert functionality
                merge_sql = """
                MERGE msal_token_cache AS target
                USING (SELECT ? AS cache_key, ? AS cache_data, ? AS user_info, ? AS expires_at) AS source
                ON target.cache_key = source.cache_key
                WHEN MATCHED THEN
                    UPDATE SET 
                        cache_data = source.cache_data,
                        updated_at = GETDATE(),
                        user_info = source.user_info,
                        expires_at = source.expires_at
                WHEN NOT MATCHED THEN
                    INSERT (cache_key, cache_data, user_info, expires_at)
                    VALUES (source.cache_key, source.cache_data, source.user_info, source.expires_at);
                """
                
                cursor.execute(merge_sql, (self.cache_key, cache_data, user_info, expires_at))
                conn.commit()
                logging.info("✅ Token cache saved to database")
                
        except Exception as e:
            logging.error(f"❌ Failed to save token cache to database: {e}")
            # Don't raise - continue execution even if cache save fails
    
    def serialize(self) -> str:
        """Override serialize to save to database"""
        cache_data = super().serialize()
        self._save_to_db(cache_data)
        return cache_data
    
    def deserialize(self, state: str):
        """Override deserialize and save to database"""
        super().deserialize(state)
        self._save_to_db(state)


def get_token(cache_key: str = "msal_default", db_key: str = "dms") -> str:
    """
    Get Microsoft Graph access token using database-backed token cache
    
    Args:
        cache_key: Unique identifier for this token cache (useful for multiple users/apps)
        db_key: Database connection key from config.yaml
        
    Returns:
        Access token string or raises exception
    """
    
    # Use database-backed token cache
    token_cache = DatabaseTokenCache(cache_key=cache_key, db_key=db_key)
    
    session = InsecureSession()
    app = PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=token_cache,
        http_client=session
    )

    accounts = app.get_accounts()
    result = None

    if accounts:
        logging.info("🔄 Attempting silent token acquisition...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        logging.info("🔐 Interactive authentication required...")
        flow = app.initiate_device_flow(scopes=SCOPES)
        self.logger.info(flow["message"])
        input("Press Enter once you have completed login in the browser...")
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        logging.info("✅ Successfully acquired access token")
        return result["access_token"]
    else:
        error_msg = f"Failed to acquire token: {result.get('error_description', 'Unknown error')}"
        logging.error(f"❌ {error_msg}")
        raise Exception(error_msg)


def clear_token_cache(cache_key: str = "msal_default", db_key: str = "dms"):
    """
    Clear stored token cache for fresh authentication
    Useful for troubleshooting or switching users
    """
    try:
        with db_helper.get_connection(db_key) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM msal_token_cache WHERE cache_key = ?",
                (cache_key,)
            )
            conn.commit()
            logging.info(f"✅ Cleared token cache for key: {cache_key}")
    except Exception as e:
        logging.error(f"❌ Failed to clear token cache: {e}")
        raise


def list_token_caches(db_key: str = "dms"):
    """
    List all stored token caches for debugging/management
    """
    try:
        with db_helper.get_connection(db_key) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    cache_key,
                    user_info,
                    created_at,
                    updated_at,
                    expires_at,
                    CASE 
                        WHEN expires_at IS NULL THEN 'Unknown'
                        WHEN expires_at > GETDATE() THEN 'Valid'
                        ELSE 'Expired'
                    END as status
                FROM msal_token_cache
                ORDER BY updated_at DESC
            """)
            
            rows = cursor.fetchall()
            if rows:
                self.logger.info("\n📋 MSAL Token Cache Status:")
                self.logger.info("-" * 80)
                for row in rows:
                    cache_key, user_info, created, updated, expires, status = row
                    self.logger.info(f"Key: {cache_key}")
                    self.logger.info(f"User: {user_info}")
                    self.logger.info(f"Status: {status}")
                    self.logger.info(f"Updated: {updated}")
                    self.logger.info("-" * 40)
            else:
                self.logger.info("📭 No token caches found in database")
                
    except Exception as e:
        logging.error(f"❌ Failed to list token caches: {e}")
        raise


# Backward compatibility - keep the original interface
if __name__ == "__main__":
    token = get_token()
    self.logger.info(f"Token acquired successfully: {token[:50]}...")
    
