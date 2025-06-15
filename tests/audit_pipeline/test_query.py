#!/usr/bin/env python3
"""
Test config.py with v_master_order_list.sql
Execute the query and return top 100 records
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.audit_pipeline.config import get_connection
import pandas as pd
import sys
import os

def test_master_order_query():
    """Test the master order list query"""
    print("🔍 Testing v_master_order_list.sql query...")
    print("=" * 60)
    
    # Read the SQL file
    sql_file = 'sql/staging/v_master_order_list.sql'
    try:
        with open(sql_file, 'r') as f:
            query = f.read()
        print(f"✅ SQL file loaded: {sql_file}")
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        return False
    
    # Modify query to get top 100 records
    # Remove any existing ORDER BY and add TOP 100
    query_lines = query.split('\n')
    
    # Find the SELECT line and add TOP 100
    modified_query = []
    for line in query_lines:
        if line.strip().upper().startswith('SELECT'):
            # Add TOP 100 after SELECT
            if 'TOP ' not in line.upper():
                line = line.replace('SELECT', 'SELECT TOP 100', 1)
        modified_query.append(line)
    
    final_query = '\n'.join(modified_query)
    
    print(f"📊 Query modified to return TOP 100 records")
    
    # Execute query
    try:
        print("🔗 Connecting to ORDERS database...")
        conn = get_connection('orders')
        
        print("⚡ Executing query...")
        df = pd.read_sql(final_query, conn)
        conn.close()
        
        print(f"✅ Query executed successfully!")
        print(f"📈 Records returned: {len(df)}")
        print(f"📋 Columns: {len(df.columns)}")
        
        # Display basic info
        print("\n" + "=" * 60)
        print("📊 DATASET SUMMARY")
        print("=" * 60)
        print(f"Shape: {df.shape}")
        print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Show column names
        print(f"\n📋 Columns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        #!/usr/bin/env python3
        """
        Test config.py with SQL views
        Execute queries and return top 100 records for each view
        """

        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


        def modify_query_for_testing(query):
            """Modify query to get top 100 records"""
            query_lines = query.split('\n')
            modified_query = []
            
            for line in query_lines:
                if line.strip().upper().startswith('SELECT'):
                    if 'TOP ' not in line.upper():
                        line = line.replace('SELECT', 'SELECT TOP 100', 1)
                modified_query.append(line)
            
            return '\n'.join(modified_query)

        def display_query_results(df, query_name):
            """Display standardized results for a query"""
            print(f"✅ {query_name} executed successfully!")
            print(f"📈 Records returned: {len(df)}")
            print(f"📋 Columns: {len(df.columns)}")
            
            # Display basic info
            print("\n" + "=" * 60)
            print(f"📊 {query_name.upper()} SUMMARY")
            print("=" * 60)
            print(f"Shape: {df.shape}")
            print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            # Show column names
            print(f"\n📋 Columns ({len(df.columns)}):")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i:2d}. {col}")
            
            # Display first 5 rows
            print(f"\n🔍 FIRST 5 RECORDS:")
            print("=" * 60)
            
            # Show key columns only for readability
            key_columns = ['Customer', 'Customer_PO', 'Season', 'Style', 'Color', 'Qty', 'CartonID']
            display_cols = [col for col in key_columns if col in df.columns]
            
            if display_cols:
                print(df[display_cols].head().to_string(index=False))
            else:
                # Fallback to first few columns
                print(df.iloc[:5, :8].to_string(index=False))
            
            # Show some statistics
            print(f"\n📈 KEY STATISTICS:")
            print("=" * 60)
            
            if 'Customer' in df.columns:
                print(f"Unique Customers: {df['Customer'].nunique()}")
            if 'Customer_PO' in df.columns:
                print(f"Unique POs: {df['Customer_PO'].nunique()}")
            if 'Qty' in df.columns:
                print(f"Total Quantity: {df['Qty'].sum():,}")
                print(f"Avg Quantity: {df['Qty'].mean():.2f}")
            if 'CartonID' in df.columns:
                print(f"Unique Cartons: {df['CartonID'].nunique()}")
            
            # Show data types
            print(f"\n🏷️  DATA TYPES:")
            print("=" * 60)
            for col, dtype in df.dtypes.head(10).items():
                print(f"  {col[:30]:30} | {str(dtype)}")
            if len(df.dtypes) > 10:
                print(f"  ... and {len(df.dtypes) - 10} more columns")

        def test_master_order_query():
            """Test the master order list query"""
            print("🔍 Testing v_master_order_list.sql query...")
            print("=" * 60)
            
            sql_file = 'sql/staging/v_master_order_list.sql'
            try:
                with open(sql_file, 'r') as f:
                    query = f.read()
                print(f"✅ SQL file loaded: {sql_file}")
            except Exception as e:
                print(f"❌ Error reading SQL file: {e}")
                return False
            
            final_query = modify_query_for_testing(query)
            print(f"📊 Query modified to return TOP 100 records")
            
            try:
                print("🔗 Connecting to ORDERS database...")
                conn = get_connection('orders')
                
                print("⚡ Executing query...")
                df = pd.read_sql(final_query, conn)
                conn.close()
                
                display_query_results(df, "v_master_order_list")
                return True
                
            except Exception as e:
                print(f"❌ Error executing query: {e}")
                return False

        def test_packed_products_query():
            """Test the packed products view query"""
            print("\n🔍 Testing v_packed_products.sql query...")
            print("=" * 60)
            
            sql_file = 'sql/staging/v_packed_products.sql'
            try:
                with open(sql_file, 'r') as f:
                    query = f.read()
                print(f"✅ SQL file loaded: {sql_file}")
            except Exception as e:
                print(f"❌ Error reading SQL file: {e}")
                return False
            
            final_query = modify_query_for_testing(query)
            print(f"📊 Query modified to return TOP 100 records")
            
            try:
                print("🔗 Connecting to DISTRIBUTION database...")
                conn = get_connection('distribution')
                
                print("⚡ Executing query...")
                df = pd.read_sql(final_query, conn)
                conn.close()
                
                display_query_results(df, "v_packed_products")
                
                # Additional statistics for packed products
                if 'Stock_Age' in df.columns:
                    print(f"\n📦 STOCK AGE BREAKDOWN:")
                    print("=" * 60)
                    stock_age_counts = df['Stock_Age'].value_counts()
                    for age, count in stock_age_counts.items():
                        print(f"  {age}: {count} items")
                
                if 'Pack_Date' in df.columns:
                    print(f"\n📅 PACK DATE RANGE:")
                    print("=" * 60)
                    print(f"  Earliest: {df['Pack_Date'].min()}")
                    print(f"  Latest: {df['Pack_Date'].max()}")
                
                return True
                
            except Exception as e:
                print(f"❌ Error executing query: {e}")
                return False

        def test_shipped_query():
            """Test the shipped view query"""
            print("\n🔍 Testing v_shipped.sql query...")
            print("=" * 60)
            
            sql_file = 'sql/staging/v_shipped.sql'
            try:
                with open(sql_file, 'r') as f:
                    query = f.read()
                print(f"✅ SQL file loaded: {sql_file}")
            except Exception as e:
                print(f"❌ Error reading SQL file: {e}")
                return False
            
            final_query = modify_query_for_testing(query)
            print(f"📊 Query modified to return TOP 100 records")
            
            try:
                print("🔗 Connecting to WAH database...")
                conn = get_connection('wah')
                
                print("⚡ Executing query...")
                df = pd.read_sql(final_query, conn)
                conn.close()
                
                display_query_results(df, "v_shipped")
                
                # Additional statistics for shipped data
                if 'Shipped_Date' in df.columns:
                    print(f"\n📅 SHIPPING DATE RANGE:")
                    print("=" * 60)
                    print(f"  Earliest: {df['Shipped_Date'].min()}")
                    print(f"  Latest: {df['Shipped_Date'].max()}")
                
                if 'Shipping_Method' in df.columns:
                    print(f"\n🚢 SHIPPING METHODS:")
                    print("=" * 60)
                    shipping_methods = df['Shipping_Method'].value_counts()
                    for method, count in shipping_methods.items():
                        print(f"  {method}: {count} shipments")
                
                if 'shippingCountry' in df.columns:
                    print(f"\n🌍 TOP SHIPPING COUNTRIES:")
                    print("=" * 60)
                    top_countries = df['shippingCountry'].value_counts().head(10)
                    for country, count in top_countries.items():
                        print(f"  {country}: {count} shipments")
                
                return True
                
            except Exception as e:
                print(f"❌ Error executing query: {e}")
                return False

        def test_all_queries():
            """Test all SQL queries"""
            results = {}
            
            print("🚀 Testing All SQL Views")
            print("=" * 60)
            
            # Test master order list
            results['master_order_list'] = test_master_order_query()
            
            # Test packed products
            results['packed_products'] = test_packed_products_query()
            
            # Test shipped
            results['shipped'] = test_shipped_query()
            
            return results

        def main():
            """Main test function"""
            print("🚀 Testing Configuration with All SQL Views")
            print("=" * 80)
            
            results = test_all_queries()
            
            # Summary
            print("\n" + "=" * 80)
            print("📋 TEST SUMMARY")
            print("=" * 80)
            
            total_tests = len(results)
            passed_tests = sum(results.values())
            
            for test_name, passed in results.items():
                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"  {test_name.replace('_', ' ').title()}: {status}")
            
            print(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                print("🎉 All tests completed successfully!")
                print("💡 All configurations and queries are working properly.")
                return True
            else:
                print("⚠️  Some tests failed!")
                print("🔧 Check database connections and SQL syntax for failed queries.")
                return False

        if __name__ == "__main__":
            success = main()
            sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error executing query: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Configuration with Master Order List Query")
    print("=" * 60)
    
    success = test_master_order_query()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print("💡 The configuration and query are working properly.")
        return True
    else:
        print(f"\n⚠️  Test failed!")
        print("🔧 Check database connection and SQL syntax.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
