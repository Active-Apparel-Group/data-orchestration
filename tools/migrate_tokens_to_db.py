"""
MSAL Token Migration Tool
Purpose: Migrate existing local .msal_cache.bin tokens to database storage
This enables seamless authentication without interactive prompts
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project utils to path
def find_repo_root() -> Path:
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent / "utils").exists():
            return current.parent
        current = current.parent
    raise RuntimeError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper
import auth_helper

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def migrate_local_tokens_to_database():
    """
    Migrate tokens from .msal_cache.bin to database storage
    This enables database-only authentication for all pipelines
    """
    
    print("🔄 MSAL Token Migration Tool")
    print("=" * 50)
    
    # Check for local token cache file
    local_cache_file = repo_root / ".msal_cache.bin"
    
    if not local_cache_file.exists():
        print("❌ No .msal_cache.bin file found")
        print("   Please run authentication manually first to generate tokens")
        return False
    
    try:
        # Load local token cache
        print("📂 Loading local token cache...")
        with open(local_cache_file, 'r') as f:
            local_cache_data = f.read()
        
        if not local_cache_data.strip():
            print("❌ Local token cache file is empty")
            return False
        
        # Parse and validate token data
        try:
            token_json = json.loads(local_cache_data)
            print("✅ Local token cache loaded successfully")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in token cache: {e}")
            return False
        
        # Extract token information for display
        access_tokens = token_json.get("AccessToken", {})
        refresh_tokens = token_json.get("RefreshToken", {})
        accounts = token_json.get("Account", {})
        
        print(f"📊 Token Inventory:")
        print(f"   Access Tokens: {len(access_tokens)}")
        print(f"   Refresh Tokens: {len(refresh_tokens)}")
        print(f"   Accounts: {len(accounts)}")
        
        if accounts:
            account_info = list(accounts.values())[0]
            username = account_info.get("username", "unknown")
            print(f"   Primary Account: {username}")
        
        # Check token expiration
        if access_tokens:
            token_data = list(access_tokens.values())[0]
            if "expires_on" in token_data:
                try:
                    expires_timestamp = int(token_data["expires_on"])
                    expires_dt = datetime.fromtimestamp(expires_timestamp)
                    now = datetime.now()
                    
                    if expires_dt > now:
                        time_left = expires_dt - now
                        print(f"   ✅ Access token valid for: {time_left}")
                    else:
                        print(f"   ⚠️ Access token expired: {expires_dt}")
                        print("   Refresh token will be used to get new access token")
                except:
                    print("   ⚠️ Could not parse token expiration")
        
        # Migrate to database for multiple cache keys
        cache_keys_to_migrate = [
            "order_list_pipeline",  # For ORDER_LIST pipeline
            "msal_default",         # For general use
            "sharepoint_access",    # Alternative key
        ]
        
        print("\n🏪 Migrating to database storage...")
        
        migration_results = []
        
        for cache_key in cache_keys_to_migrate:
            try:
                print(f"   Migrating cache key: {cache_key}")
                
                # Create database token cache and load the data
                db_cache = auth_helper.DatabaseTokenCache(
                    cache_key=cache_key,
                    db_key="dms"
                )
                
                # Deserialize the local cache data into the database cache
                db_cache.deserialize(local_cache_data)
                
                # Verify it was saved
                with db_helper.get_connection("dms") as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT cache_key, user_info, expires_at FROM msal_token_cache WHERE cache_key = ?",
                        (cache_key,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        print(f"   ✅ Successfully migrated: {cache_key}")
                        migration_results.append({
                            'cache_key': cache_key,
                            'success': True,
                            'user_info': row[1],
                            'expires_at': row[2]
                        })
                    else:
                        print(f"   ❌ Migration failed: {cache_key}")
                        migration_results.append({
                            'cache_key': cache_key,
                            'success': False
                        })
                        
            except Exception as e:
                print(f"   ❌ Error migrating {cache_key}: {e}")
                migration_results.append({
                    'cache_key': cache_key,
                    'success': False,
                    'error': str(e)
                })
        
        # Summary
        successful_migrations = [r for r in migration_results if r['success']]
        failed_migrations = [r for r in migration_results if not r['success']]
        
        print(f"\n📈 Migration Summary:")
        print(f"   Successful: {len(successful_migrations)}")
        print(f"   Failed: {len(failed_migrations)}")
        
        if successful_migrations:
            print(f"\n✅ Database Token Caches Created:")
            for result in successful_migrations:
                print(f"   - {result['cache_key']}: {result.get('user_info', 'unknown user')}")
        
        if failed_migrations:
            print(f"\n❌ Failed Migrations:")
            for result in failed_migrations:
                error = result.get('error', 'Unknown error')
                print(f"   - {result['cache_key']}: {error}")
        
        # Test database authentication
        print(f"\n🧪 Testing Database Authentication...")
        try:
            test_token = auth_helper.get_token(
                cache_key="order_list_pipeline",
                db_key="dms"
            )
            
            if test_token:
                print("✅ Database authentication test PASSED")
                print("   Pipelines can now use database-stored tokens")
                
                # Optional: Backup and remove local cache file
                print(f"\n🗂️ Local Cache File Management:")
                backup_file = repo_root / f".msal_cache.bin.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Create backup
                import shutil
                shutil.copy2(local_cache_file, backup_file)
                print(f"   ✅ Backup created: {backup_file.name}")
                
                # Ask user if they want to remove original
                print(f"\n❓ Remove original .msal_cache.bin file? (y/n): ", end="")
                response = input().strip().lower()
                
                if response in ['y', 'yes']:
                    local_cache_file.unlink()
                    print("   ✅ Original .msal_cache.bin removed")
                    print("   🎯 All authentication now uses database storage")
                else:
                    print("   ℹ️ Original .msal_cache.bin kept")
                    print("   ⚠️ Note: Local file takes precedence over database")
                
                return True
                
            else:
                print("❌ Database authentication test FAILED")
                print("   Please check database connection and token data")
                return False
                
        except Exception as e:
            print(f"❌ Database authentication test error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def verify_database_tokens():
    """Verify what token caches are stored in database"""
    print("\n📊 Database Token Cache Inventory:")
    print("-" * 40)
    
    try:
        with db_helper.get_connection("dms") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    cache_key,
                    user_info,
                    expires_at,
                    updated_at,
                    LEN(cache_data) as cache_size
                FROM msal_token_cache
                ORDER BY updated_at DESC
            """)
            
            rows = cursor.fetchall()
            
            if rows:
                print(f"Found {len(rows)} token cache entries:")
                for row in rows:
                    cache_key, user_info, expires_at, updated_at, cache_size = row
                    print(f"\n🔑 Cache Key: {cache_key}")
                    print(f"   User: {user_info}")
                    print(f"   Expires: {expires_at}")
                    print(f"   Last Updated: {updated_at}")
                    print(f"   Cache Size: {cache_size:,} characters")
            else:
                print("❌ No token caches found in database")
                
    except Exception as e:
        print(f"❌ Database query error: {e}")


def main():
    """Main migration workflow"""
    print("🚀 Starting MSAL Token Migration")
    print("Purpose: Move from local file to database authentication")
    print("=" * 60)
    
    # First, show current database state
    verify_database_tokens()
    
    # Perform migration
    success = migrate_local_tokens_to_database()
    
    if success:
        print("\n🎉 Migration Complete!")
        print("✅ Database authentication is now active")
        print("✅ No more interactive authentication prompts")
        print("✅ Tokens automatically refresh using database storage")
        
        # Show final database state
        verify_database_tokens()
        
    else:
        print("\n❌ Migration failed - please check errors above")
        
    print("\n" + "=" * 60)
    return success


if __name__ == "__main__":
    main()
