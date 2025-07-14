"""
Deploy DDL Helper - Python component
Deploys DDL scripts to specified SQL Server database
"""
import sys
from pathlib import Path

# Add utils to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "utils"))

from db_helper import get_connection
from logger_helper import get_logger

def deploy_sql_server_ddl(ddl_file_path: str, database_name: str = 'ORDERS', dry_run: bool = False) -> bool:
    """Deploy DDL to SQL Server"""
    logger = get_logger(__name__)
    
    if dry_run:
        print("🔍 DRY RUN - Would deploy SQL Server DDL")
        print(f"   File: {ddl_file_path}")
        print(f"   Database: {database_name}")
        return True
    
    try:
        with open(ddl_file_path, 'r') as f:
            ddl_content = f.read()
        
        # Split by GO statements and execute each batch
        batches = [batch.strip() for batch in ddl_content.split('GO') if batch.strip()]
        
        print(f"Deploying to database: {database_name}")
        print(f"Found {len(batches)} SQL batches to execute")
        
        with get_connection(database_name) as conn:
            cursor = conn.cursor()
            for i, batch in enumerate(batches):
                print(f'Executing batch {i+1}/{len(batches)}...')
                try:
                    cursor.execute(batch)
                    print(f'   ✓ Batch {i+1} completed successfully')
                except Exception as batch_error:
                    print(f'   ❌ Batch {i+1} failed: {batch_error}')
                    raise
            
            conn.commit()
            print('✅ SQL Server deployment successful!')
            return True
            
    except Exception as e:
        print(f'❌ SQL Server deployment failed: {e}')
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deploy_ddl.py <ddl_file_path> [--database <db_name>] [--dry-run]")
        print("Available databases: dms, dms_item, orders, infor_132, gfs, gws")
        sys.exit(1)
    
    ddl_file = sys.argv[1]
    database_name = 'ORDERS'  # Default database
    dry_run = "--dry-run" in sys.argv
    
    # Parse database parameter
    if "--database" in sys.argv:
        try:
            db_index = sys.argv.index("--database")
            if db_index + 1 < len(sys.argv):
                database_name = sys.argv[db_index + 1]
            else:
                print("❌ --database flag requires a database name")
                sys.exit(1)
        except ValueError:
            pass
    
    print(f"Deploying DDL script: {ddl_file}")
    print(f"Target database: {database_name}")
    if dry_run:
        print("Mode: DRY RUN")
    
    success = deploy_sql_server_ddl(ddl_file, database_name, dry_run)
    sys.exit(0 if success else 1)
