#!/usr/bin/env python3
"""
Debug version - step by step execution
"""

print("DEBUG: Starting script...")

try:
    print("DEBUG: Importing modules...")
    import os, re, requests, pandas as pd, pyodbc
    from datetime import datetime
    print("DEBUG: Imports successful")

    # Configuration
    print("DEBUG: Setting up configuration...")
    BOARD_ID = 8709134353
    API_VER = "2025-04"
    MONDAY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM"

    HEADERS = {
        "Authorization": f"Bearer {MONDAY_TOKEN}",
        "API-Version": API_VER,
        "Content-Type": "application/json"
    }

    # Database connection parameters
    DB_CONFIG = {
        'host': 'ross-db-srv-test.database.windows.net',
        'port': '1433',
        'database': 'ORDERS',
        'username': 'admin_ross',
        'password': 'Active@IT2023'
    }
    print("DEBUG: Configuration complete")

    def main():
        print("DEBUG: Entering main function...")
        print("🚀 === Monday.com to Database End-to-End Test ===")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            print("DEBUG: About to test database connection...")
            # Step 1: Test database connection
            print("\n=== STEP 1: Testing Database Connection ===")
            
            conn_str = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={DB_CONFIG['host']},{DB_CONFIG['port']};"
                f"DATABASE={DB_CONFIG['database']};"
                f"UID={DB_CONFIG['username']};"
                f"PWD={DB_CONFIG['password']};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=yes;"
            )
            print("DEBUG: About to connect...")
            conn = pyodbc.connect(conn_str, timeout=30)
            print("✅ Database connection successful!")
            
            cursor = conn.cursor()
            print("DEBUG: Testing simple query...")
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"DEBUG: Simple query result: {result[0]}")
            
            cursor.close()
            conn.close()
            print("DEBUG: Database connection closed")
            
        except Exception as e:
            print(f"❌ Error in main: {e}")
            import traceback
            traceback.print_exc()

    print("DEBUG: About to call main...")
    if __name__ == "__main__":
        main()
        print("DEBUG: Main function completed")

except Exception as e:
    print(f"❌ Error during script execution: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Script finished")
