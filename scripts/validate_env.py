#!/usr/bin/env python3
"""
Final environment validation script
Tests configuration loading and Azure SQL connectivity
"""

from src.audit_pipeline.config import get_connection, get_db_config
import sys
import os

def test_azure_databases():
    """Test Azure SQL database connections"""
    print("🔧 Testing Azure SQL databases...")
    print("-" * 40)
    
    azure_dbs = ['dms', 'orders']
    results = {}
    
    for db in azure_dbs:
        try:
            config = get_db_config(db)
            print(f"✅ {db.upper():8} | Config loaded: {config['host']}")
            
            # Test connection (with timeout)
            conn = get_connection(db)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0] == 1:
                print(f"✅ {db.upper():8} | Connection successful")
                results[db] = True
            else:
                results[db] = False
                
        except Exception as e:
            print(f"❌ {db.upper():8} | Error: {str(e)}")
            results[db] = False
    
    return results

def test_environment_loading():
    """Test environment variable loading"""
    print("🌍 Testing environment configuration...")
    print("-" * 40)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test key variables
    test_vars = [
        'DB_DMS_HOST',
        'DB_ORDERS_HOST', 
        'SECRET_DMS_PWD',
        'SECRET_ORDERS_PWD'
    ]
    
    all_good = True
    for var in test_vars:
        value = os.getenv(var)
        if value:
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var:20} | {masked_value}")
        else:
            print(f"❌ {var:20} | Missing")
            all_good = False
    
    return all_good

def main():
    """Main validation function"""
    print("🚀 Data Orchestration Environment Validation")
    print("=" * 50)
    
    # Test environment loading
    env_ok = test_environment_loading()
    print()
    
    # Test Azure databases
    azure_results = test_azure_databases()
    print()
    
    # Summary
    print("=" * 50)
    print("📊 Validation Summary:")
    
    azure_success = sum(azure_results.values())
    azure_total = len(azure_results)
    
    print(f"  Environment Variables | {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"  Azure SQL Connections | {azure_success}/{azure_total} successful")
    
    if env_ok and azure_success == azure_total:
        print("\n🎉 Environment is ready for development!")
        print("💡 Note: On-premise databases (Distribution, WAH) require VPN access")
        return True
    else:
        print("\n⚠️  Environment validation failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
