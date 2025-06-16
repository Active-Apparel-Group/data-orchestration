"""
Quick database connection test
"""
import os
import pyodbc

def test_db():
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        load_dotenv(dotenv_path=env_path)
    except:
        pass
    
    import base64
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
    
    print(f"Host: {host}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else 'None'}")
    
    # Try available drivers
    available_drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
    print(f"Available SQL Server drivers: {available_drivers}")
    
    if not available_drivers:
        print("No SQL Server drivers found!")
        return
    
    driver = available_drivers[0]
    print(f"Using driver: {driver}")
    
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={username};PWD={password};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )
    
    try:
        conn = pyodbc.connect(conn_str)
        print("Connection successful!")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_db()
