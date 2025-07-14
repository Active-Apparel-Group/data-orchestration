import os
import sys
import pyodbc

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
    
    print(f"Connecting to database:")
    print(f"  Host: {config['host']}:{config['port']}")
    print(f"  Database: {config['database']}")
    print(f"  Username: {config['username']}")
    print(f"  Encrypt: {config['encrypt']}")
    
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
        print("Attempting database connection...")
        connection = pyodbc.connect(conn_str, timeout=30)
        print("✅ Database connection successful!")
        return connection
    except pyodbc.Error as e:
        print(f"❌ Connection failed with ODBC Driver 17: {e}")
        print("Trying fallback to SQL Server driver...")
        # Fallback to older driver if needed
        conn_str = conn_str.replace("ODBC Driver 17 for SQL Server", "SQL Server")
        try:
            connection = pyodbc.connect(conn_str, timeout=30)
            print("✅ Database connection successful with fallback driver!")
            return connection
        except pyodbc.Error as e2:
            print(f"❌ Connection failed with both drivers: {e2}")
            raise

def get_master_order_list_count():
    """Query the master order list and return record count."""
    
    # Read the SQL query from file
    sql_file_path = os.path.join('queries', 'v_master_order_list.sql')
    
    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")
    
    with open(sql_file_path, 'r') as f:
        base_query = f.read()
    
    print(f"Read SQL query from: {sql_file_path}")
    print(f"Query length: {len(base_query)} characters")
    
    # Wrap the query with COUNT(*) to get record count
    count_query = f"SELECT COUNT(*) as record_count FROM ({base_query}) as subquery"
    
    # Connect to database and execute query
    try:
        conn = get_orders_db_connection()
        cursor = conn.cursor()
        
        print("Executing count query...")
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
    """Main function to run the count query."""
    
    print("=== Master Order List Count Script ===")
    print("Using environment variables for database configuration")
    
    try:
        count = get_master_order_list_count()
        print(f"🎯 Master Order List Record Count: {count:,}")
        print("=== Script completed successfully ===")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("=== Script failed ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
