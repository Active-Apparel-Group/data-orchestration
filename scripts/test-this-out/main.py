import os
import sys
import pyodbc
from datetime import datetime

def main():
    """
    Main workflow function for test-this-out.
    
    Description: testing
    Database Connections: orders
    """
    
    print(f"🚀 === testing ===")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Workflow: test-this-out")
    print(f"🏷️  Namespace: company.team")
    print(f"🗄️  Database Connections: orders")
    print()
    
    try:
        # Test database connections
        # Test orders database connection
        print("🧪 Testing orders database connection...")
        conn = get_database_connection('orders')
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE() as current_datetime")
        result = cursor.fetchone()
        print(f"✅ orders database test successful! Current time: {result[0]}")
        cursor.close()
        conn.close()
        
        # TODO: Add your workflow logic here
        print("🔧 Implementing workflow logic...")
        print("📊 Processing data...")
        
        print("⚠️  This is a template - implement your specific logic here!")
        
        print()
        print("✅ Workflow completed successfully!")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        print(f"⏰ Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(1)

def get_database_connection(db_name):
    """
    Create database connection using environment variables from Kestra workflow.
    
    Args:
        db_name (str): Database name (e.g., 'orders', 'dms', 'infor_132')
    """
    
    # Get connection details from environment variables (set by Kestra workflow)
    env_prefix = f"DB_{db_name.upper()}_"
    config = {
        'host': os.getenv(f'{env_prefix}HOST'),
        'port': os.getenv(f'{env_prefix}PORT', '1433'),
        'database': os.getenv(f'{env_prefix}DATABASE'),
        'username': os.getenv(f'{env_prefix}USERNAME'),
        'password': os.getenv(f'{env_prefix}PASSWORD'),
        'encrypt': os.getenv(f'{env_prefix}ENCRYPT', 'yes'),
        'trust_cert': os.getenv(f'{env_prefix}TRUSTSERVERCERTIFICATE', 'yes'),
    }
    
    # Validate required config
    required_fields = ['host', 'database', 'username', 'password']
    for field in required_fields:
        if not config[field]:
            raise ValueError(f"Missing required database config for {db_name}: {field}")
    
    print(f"🔗 Connecting to {db_name} database:")
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
        print(f"🔄 Attempting {db_name} database connection...")
        connection = pyodbc.connect(conn_str, timeout=30)
        print(f"✅ {db_name} database connection successful!")
        return connection
    except pyodbc.Error as e:
        print(f"❌ Connection failed with ODBC Driver 17: {e}")
        print("🔄 Trying fallback to SQL Server driver...")
        # Fallback to older driver if needed
        conn_str = conn_str.replace("ODBC Driver 17 for SQL Server", "SQL Server")
        try:
            connection = pyodbc.connect(conn_str, timeout=30)
            print(f"✅ {db_name} database connection successful with fallback driver!")
            return connection
        except pyodbc.Error as e2:
            print(f"❌ Connection failed with both drivers: {e2}")
            raise

if __name__ == "__main__":
    main()
