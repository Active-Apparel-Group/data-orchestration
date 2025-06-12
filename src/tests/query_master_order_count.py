import os
import sys
import pyodbc

def get_orders_db_connection():
    """Create connection to the orders database using hardcoded config from config.yaml."""
    
    # Direct credentials from config.yaml - ORDERS database
    config = {
        'host': 'ross-db-srv-test.database.windows.net',
        'port': 1433,
        'database': 'ORDERS',
        'username': 'admin_ross',
        'password': 'Active@IT2023',
    }
    
    # Validate required config
    for key, value in config.items():
        if not value:
            raise ValueError(f"Missing required database config: {key}")
    
    # Build connection string
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config['host']},{config['port']};"
        f"DATABASE={config['database']};"
        f"UID={config['username']};"
        f"PWD={config['password']};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"    )
    
    try:
        return pyodbc.connect(conn_str, timeout=30)
    except pyodbc.Error as e:
        # Fallback to older driver if needed
        conn_str = conn_str.replace("ODBC Driver 17 for SQL Server", "SQL Server")
        return pyodbc.connect(conn_str, timeout=30)

def get_master_order_list_count():
    """Query the master order list and return record count."""
    
    # Read the SQL query from file
    sql_file_path = os.path.join('sql', 'staging', 'v_master_order_list.sql')

    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")
    
    with open(sql_file_path, 'r') as f:
        base_query = f.read()
    
    # Wrap the query with COUNT(*) to get record count
    count_query = f"SELECT COUNT(*) as record_count FROM ({base_query}) as subquery"
      # Connect to database and execute query
    try:
        conn = get_orders_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(count_query)
        
        result = cursor.fetchone()
        record_count = result[0] if result else 0
        
        cursor.close()
        conn.close()
        
        return record_count
        
    except Exception as e:
        raise

def main():
    """Main function to run the count query."""
    
    try:
        count = get_master_order_list_count()
        print(f"Master Order List Record Count: {count:,}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
