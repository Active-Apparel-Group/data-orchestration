"""
Deploy Staging Infrastructure to SQL Server
This script deploys all staging tables needed for the new Monday.com workflow
"""

import os
import sys
import pyodbc
import base64
from pathlib import Path

def get_db_connection_string():
    """Get database connection string"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
    
    # Get password - try encoded first, then plain text
    password = os.getenv('SECRET_ORDERS_PWD')
    if password:
        try:
            password = base64.b64decode(password).decode()
        except:
            pass
    else:
        password = os.getenv('DB_ORDERS_PASSWORD')
    
    host = os.getenv('DB_ORDERS_HOST')
    port = int(os.getenv('DB_ORDERS_PORT', 1433))
    database = os.getenv('DB_ORDERS_DATABASE')
    username = os.getenv('DB_ORDERS_USERNAME')
    
    if not all([host, database, username, password]):
        raise ValueError("Missing required database connection environment variables")
    
    # Use working driver detection
    driver = "{ODBC Driver 17 for SQL Server}"
    try:
        test_conn_str = f"DRIVER={driver};SERVER=test;DATABASE=test;"
        pyodbc.connect(test_conn_str, timeout=1)
    except:
        driver = "{SQL Server}"
    
    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={username};PWD={password};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )
    
    return conn_str

def execute_sql_file(cursor, sql_file_path, description):
    """Execute SQL from file with error handling"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Split by GO statements and execute each batch
        batches = [batch.strip() for batch in sql_content.split('GO') if batch.strip()]
        
        for i, batch in enumerate(batches):
            if batch.strip():
                try:
                    cursor.execute(batch)
                    print(f"   ✓ Executed batch {i+1}/{len(batches)}")
                except Exception as e:
                    if "already exists" in str(e) or "name is already used" in str(e):
                        print(f"   → Already exists (batch {i+1}/{len(batches)})")
                    else:
                        print(f"   ✗ Error in batch {i+1}: {e}")
                        raise
        
        print(f"✅ {description}")
        return True
        
    except Exception as e:
        print(f"❌ Failed {description}: {e}")
        return False

def deploy_staging_schema():
    """Deploy complete staging schema"""
    
    print("🚀 Deploying Monday.com Staging Infrastructure")
    print("=" * 60)
    
    try:
        # Connect to database
        conn_str = get_db_connection_string()
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
              # Get script directory - go up to workspace root then to sql/ddl
            script_dir = Path(__file__).parent.parent / 'sql' / 'ddl'
            
            # Deployment order (respecting dependencies)
            deployment_files = [
                # 1. Batch tracking first (no dependencies)
                (script_dir / 'tables' / 'orders' / 'tracking' / 'mon_batchprocessing.sql', 
                 "Batch Processing Table"),
                
                # 2. Main staging table
                (script_dir / 'tables' / 'orders' / 'staging' / 'stg_mon_custmasterschedule.sql', 
                 "Main Staging Table"),
                
                # 3. Subitems staging table (depends on main staging)
                (script_dir / 'tables' / 'orders' / 'staging' / 'stg_mon_custmasterschedule_subitems.sql', 
                 "Subitems Staging Table"),
                
                # 4. Error tables
                (script_dir / 'tables' / 'orders' / 'error' / 'err_mon_custmasterschedule.sql', 
                 "Main Error Table"),
                
                (script_dir / 'tables' / 'orders' / 'error' / 'err_mon_custmasterschedule_subitems.sql', 
                 "Subitems Error Table"),
                
                # 5. Monitoring view
                (script_dir / 'views' / 'orders' / 'vw_mon_activebatches.sql', 
                 "Active Batches View")
            ]
            
            # Deploy each component
            success_count = 0
            for sql_file, description in deployment_files:
                if sql_file.exists():
                    print(f"\n📋 Deploying {description}...")
                    if execute_sql_file(cursor, sql_file, description):
                        success_count += 1
                        conn.commit()
                    else:
                        conn.rollback()
                else:
                    print(f"❌ File not found: {sql_file}")
            
            print(f"\n{'='*60}")
            print(f"✅ Deployment Complete: {success_count}/{len(deployment_files)} components deployed")
            
            # Test basic functionality
            print(f"\n🧪 Testing basic functionality...")
            
            # Test batch creation
            cursor.execute("""
                INSERT INTO [dbo].[MON_BatchProcessing] 
                ([batch_id], [customer_name], [batch_type], [status])
                VALUES (NEWID(), 'TEST_CUSTOMER', 'TEST', 'STARTED')
            """)
            
            cursor.execute("SELECT @@ROWCOUNT as rows_inserted")
            rows = cursor.fetchone()[0]
            
            if rows > 0:
                print("✅ Batch tracking table working")
                
                # Clean up test data
                cursor.execute("DELETE FROM [dbo].[MON_BatchProcessing] WHERE [customer_name] = 'TEST_CUSTOMER'")
                conn.commit()
                print("✅ Test data cleaned up")
            else:
                print("❌ Batch tracking test failed")
            
            print(f"\n🎉 Staging infrastructure is ready for testing!")
            return True
            
    except Exception as e:
        print(f"\n💥 Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = deploy_staging_schema()
    exit(0 if success else 1)
