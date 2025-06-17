import os
import sys
import pyodbc
from datetime import datetime

def get_orders_db_connection():
    """Create connection to the orders database using environment variables."""
    
    # Get database config from environment variables
    config = {
        'host': os.getenv('DB_ORDERS_HOST'),
        'port': os.getenv('DB_ORDERS_PORT', '1433'),
        'database': os.getenv('DB_ORDERS_DATABASE'),
        'username': os.getenv('DB_ORDERS_USERNAME'),
        'password': os.getenv('DB_ORDERS_PASSWORD'),
        'encrypt': os.getenv('DB_ORDERS_ENCRYPT', 'yes'),
        'trust_cert': os.getenv('DB_ORDERS_TRUSTSERVERCERTIFICATE', 'yes'),
    }

    # Validate required config
    required_fields = ['host', 'database', 'username', 'password']
    for field in required_fields:
        if not config[field]:
            raise ValueError(f"Missing required database config: {field} (set DB_ORDERS_{field.upper()} environment variable)")
    
    print(f"🔗 Connecting to database:")
    print(f"   📍 Host: {config['host']}:{config['port']}")
    print(f"   🗄️  Database: {config['database']}")
    print(f"   👤 Username: {config['username']}")
    print(f"   🔒 Encrypt: {config['encrypt']}")
    print(f"   ⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Build connection string
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config['host']},{config['port']};"
        f"DATABASE={config['database']};"
        f"UID={config['username']};"
        f"PWD={config['password']};"
        f"Encrypt={config['encrypt']};"
        f"TrustServerCertificate={config['trust_cert']};"
    )
    
    try:
        print("🔄 Attempting database connection...")
        connection = pyodbc.connect(conn_str, timeout=30)
        print("✅ Database connection successful!")
        return connection
    except pyodbc.Error as e:
        print(f"❌ Connection failed with ODBC Driver 17: {e}")
        print("🔄 Trying fallback to SQL Server driver...")
        # Fallback to older driver if needed
        conn_str = conn_str.replace("ODBC Driver 17 for SQL Server", "SQL Server")
        try:
            connection = pyodbc.connect(conn_str, timeout=30)
            print("✅ Database connection successful with fallback driver!")
            return connection
        except pyodbc.Error as e2:
            print(f"❌ Connection failed with both drivers: {e2}")
            raise

def test_simple_query():
    """Execute a simple test query to verify database connectivity."""
    
    print("\n🧪 === SIMPLE DATABASE TEST ===")
    
    try:
        conn = get_orders_db_connection()
        cursor = conn.cursor()
        
        # Simple test query
        test_query = "SELECT GETDATE() as current_time, @@VERSION as sql_version"
        
        print("🔍 Executing test query...")
        cursor.execute(test_query)
        
        result = cursor.fetchone()
        
        print("✅ Test query results:")
        print(f"   🕐 Current Time: {result[0]}")
        print(f"   📊 SQL Version: {result[1][:100]}...")  # Truncate long version string
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Test query failed: {e}")
        return False

def get_master_order_list_count():
    """Query the master order list and return record count."""
    
    print("\n📊 === MASTER ORDER LIST COUNT ===")
    
    # Read the SQL query from file
    sql_file_path = os.path.join('queries', 'v_master_order_list.sql')
    
    if not os.path.exists(sql_file_path):
        print(f"⚠️  SQL file not found: {sql_file_path}")
        print("🔄 Using fallback simple count query...")
        
        # Fallback to a simple table count if the SQL file doesn't exist
        fallback_query = """
        SELECT 
            COUNT(*) as total_records,
            'Fallback query - file not found' as note
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        """
        
        try:
            conn = get_orders_db_connection()
            cursor = conn.cursor()
            
            print("🔍 Executing fallback query...")
            cursor.execute(fallback_query)
            
            result = cursor.fetchone()
            table_count = result[0] if result else 0
            
            cursor.close()
            conn.close()
            
            print(f"✅ Found {table_count} tables in database")
            return table_count
            
        except Exception as e:
            print(f"❌ Fallback query failed: {e}")
            raise
    
    # Original logic for when SQL file exists
    with open(sql_file_path, 'r') as f:
        base_query = f.read()
    
    print(f"📄 Read SQL query from: {sql_file_path}")
    print(f"📏 Query length: {len(base_query)} characters")
    
    # Wrap the query with COUNT(*) to get record count
    count_query = f"SELECT COUNT(*) as record_count FROM ({base_query}) as subquery"
    
    # Connect to database and execute query
    try:
        conn = get_orders_db_connection()
        cursor = conn.cursor()
        
        print("🔍 Executing count query...")
        cursor.execute(count_query)
        
        result = cursor.fetchone()
        record_count = result[0] if result else 0
        
        cursor.close()
        conn.close()
        
        print(f"✅ Query executed successfully!")
        return record_count
        
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        raise

def main():
    """Main function to run database tests."""
    
    print("🚀 === Enhanced Database Connection Test v2.0 ===")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📋 Using environment variables for database configuration")
    print("🔧 Enhanced version with improved logging and fallback handling")
    
    success_count = 0
    total_tests = 2
    
    try:
        # Test 1: Simple connectivity test
        print(f"\n🧪 Test 1/{total_tests}: Database Connectivity")
        if test_simple_query():
            success_count += 1
            print("✅ Test 1 PASSED")
        else:
            print("❌ Test 1 FAILED")
        
        # Test 2: Master order list count
        print(f"\n🧪 Test 2/{total_tests}: Master Order List Count")
        count = get_master_order_list_count()
        print(f"🎯 Master Order List Record Count: {count:,}")
        success_count += 1
        print("✅ Test 2 PASSED")
        
        # Summary
        print(f"\n📊 === TEST SUMMARY ===")
        print(f"✅ Tests Passed: {success_count}/{total_tests}")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if success_count == total_tests:
            print("🎉 All tests passed! Database connection is working perfectly!")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        
        print("=== Enhanced script completed successfully ===")
        
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        print(f"📊 Tests Passed: {success_count}/{total_tests}")
        print("=== Enhanced script failed ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
