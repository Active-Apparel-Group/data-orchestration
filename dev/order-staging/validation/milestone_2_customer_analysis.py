"""
MILESTONE 2: Customer Analysis for Staging Workflow
=====================================================

This script analyzes customers with new orders ready for staging.
Provides detailed review before proceeding with actual staging.

Usage:
    python scripts/milestone_2_customer_analysis.py
"""

import pandas as pd
import pyodbc
import os
import base64
from datetime import datetime

def get_db_connection_string():
    """Get database connection string"""
    password = base64.b64decode(os.getenv('SECRET_ORDERS_PWD')).decode()
    host = os.getenv('DB_ORDERS_HOST')
    port = int(os.getenv('DB_ORDERS_PORT', 1433))
    database = os.getenv('DB_ORDERS_DATABASE')
    username = os.getenv('DB_ORDERS_USERNAME')
    
    return f"DRIVER={{SQL Server}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password};"

def analyze_customers_with_new_orders():
    """Analyze customers that have new orders ready for staging"""
    print("📊 MILESTONE 2: Customer Analysis for Staging")
    print("=" * 60)
    
    conn_str = get_db_connection_string()
    
    # Query to find customers with new orders (not yet in Monday.com)
    # Using correct column names from ORDERS_UNIFIED table structure
    analysis_query = """
    WITH customer_summary AS (
        SELECT 
            ou.[CUSTOMER NAME],
            COUNT(*) as total_orders,
            MIN(ou.[ORDER DATE PO RECEIVED]) as earliest_order_date,
            MAX(ou.[ORDER DATE PO RECEIVED]) as latest_order_date,
            SUM(CASE WHEN ou.[TOTAL QTY] IS NOT NULL THEN ou.[TOTAL QTY] ELSE 0 END) as total_qty,
            COUNT(DISTINCT ou.[CUSTOMER STYLE]) as unique_styles,
            COUNT(DISTINCT ou.[CUSTOMER COLOUR DESCRIPTION]) as unique_colors,
            COUNT(DISTINCT ou.[AAG ORDER NUMBER]) as unique_order_numbers
        FROM [dbo].[ORDERS_UNIFIED] ou
        LEFT JOIN [dbo].[MON_CustMasterSchedule] mcs 
            ON ou.[AAG ORDER NUMBER] = mcs.[AAG ORDER NUMBER]
            AND ou.[CUSTOMER NAME] = mcs.[CUSTOMER]
            AND ou.[CUSTOMER STYLE] = mcs.[STYLE] 
            AND ou.[CUSTOMER COLOUR DESCRIPTION] = mcs.[COLOR]
        WHERE mcs.[Item ID] IS NULL  -- Not yet in Monday.com
            AND ou.[CUSTOMER NAME] IS NOT NULL
            AND ou.[AAG ORDER NUMBER] IS NOT NULL
        GROUP BY ou.[CUSTOMER NAME]
    )
    SELECT 
        [CUSTOMER NAME] as CUSTOMER,
        total_orders,
        earliest_order_date,
        latest_order_date,
        total_qty,
        unique_styles,
        unique_colors,
        unique_order_numbers
    FROM customer_summary
    ORDER BY total_orders DESC;
    """
    
    with pyodbc.connect(conn_str) as conn:
        df = pd.read_sql(analysis_query, conn)
    
    if df.empty:
        print("ℹ️  No customers with new orders found.")
        return df
    
    print(f"📈 Found {len(df)} customers with new orders")
    print(f"📦 Total new orders across all customers: {df['total_orders'].sum():,}")
    print(f"📋 Total quantity: {df['total_qty'].sum():,}")
    print("")
    
    # Display summary table
    print("📊 CUSTOMER SUMMARY (Top 15)")
    print("-" * 100)
    
    # Format the display
    display_df = df.head(15).copy()
    display_df['earliest_order_date'] = pd.to_datetime(display_df['earliest_order_date']).dt.strftime('%Y-%m-%d')
    display_df['latest_order_date'] = pd.to_datetime(display_df['latest_order_date']).dt.strftime('%Y-%m-%d')
    
    # Pretty print the table
    for idx, row in display_df.iterrows():
        print(f"{row['CUSTOMER']:<35} | {row['total_orders']:>5} orders | {row['total_qty']:>7,} qty | "
              f"{row['unique_styles']:>3} styles | {row['unique_colors']:>3} colors | "
              f"{row['earliest_order_date']} to {row['latest_order_date']}")
    
    if len(df) > 15:
        remaining = len(df) - 15
        remaining_orders = df.iloc[15:]['total_orders'].sum()
        print(f"... and {remaining} more customers with {remaining_orders:,} additional orders")
    
    print("")
    print("🎯 MILESTONE 2 ANALYSIS COMPLETE")
    print("=" * 60)
    print("✅ Customer analysis completed")
    print("✅ Data volumes identified")
    print("✅ Ready for milestone 3: Single customer test")
    print("")
    print("💡 NEXT STEPS:")
    print("   1. Review the customer list above")
    print("   2. Choose a customer with moderate volume for testing (10-50 orders)")
    print("   3. Proceed to milestone 3: Test single customer staging")
    
    return df

def get_customer_detail(customer_name=None, po_number=None, customer_season=None, aag_season=None):
    """Get detailed breakdown with optional filtering
    
    Args:
        customer_name (str, optional): Filter by customer name
        po_number (str, optional): Filter by PO number
        customer_season (str, optional): Filter by customer season
        aag_season (str, optional): Filter by AAG season
    """
    
    # Build filter description
    filters = []
    if customer_name:
        filters.append(f"Customer: {customer_name}")
    if po_number:
        filters.append(f"PO: {po_number}")
    if customer_season:
        filters.append(f"Customer Season: {customer_season}")
    if aag_season:
        filters.append(f"AAG Season: {aag_season}")
    
    filter_desc = " | ".join(filters) if filters else "All customers"
    print(f"🔍 Detailed Analysis - Filters: {filter_desc}")
    print("=" * 80)
    
    conn_str = get_db_connection_string()
      # Query to get detailed orders with optional filters
    # Using correct column names from ORDERS_UNIFIED table structure
    # Fixed: Added table aliases to resolve ambiguous column names
    base_query = """
    SELECT 
        ou.[CUSTOMER NAME] as CUSTOMER,
        ou.[AAG ORDER NUMBER],
        ou.[CUSTOMER STYLE] as STYLE,
        ou.[CUSTOMER COLOUR DESCRIPTION] as COLOR,
        ou.[TOTAL QTY] as ORDER_QTY,
        ou.[ORDER DATE PO RECEIVED],
        ou.[CUSTOMER SEASON],
        ou.[AAG SEASON],
        ou.[DROP],
        ou.[PO NUMBER]
    FROM [dbo].[ORDERS_UNIFIED] ou
    LEFT JOIN [dbo].[MON_CustMasterSchedule] mcs 
        ON ou.[AAG ORDER NUMBER] = mcs.[AAG ORDER NUMBER]
        AND ou.[CUSTOMER NAME] = mcs.[CUSTOMER]
        AND ou.[CUSTOMER STYLE] = mcs.[STYLE] 
        AND ou.[CUSTOMER COLOUR DESCRIPTION] = mcs.[COLOR]
    WHERE mcs.[Item ID] IS NULL  -- Not yet in Monday.com
    """
    
    # Build WHERE conditions dynamically
    where_conditions = []
    params = []
    
    if customer_name:
        where_conditions.append("AND ou.[CUSTOMER NAME] = ?")
        params.append(customer_name)
    
    if po_number:
        where_conditions.append("AND ou.[PO NUMBER] = ?")
        params.append(po_number)
        
    if customer_season:
        where_conditions.append("AND ou.[CUSTOMER SEASON] = ?")
        params.append(customer_season)
        
    if aag_season:
        where_conditions.append("AND ou.[AAG SEASON] = ?")
        params.append(aag_season)
    
    # If no filters provided, limit results to prevent overwhelming output
    if not any([customer_name, po_number, customer_season, aag_season]):
        where_conditions.append("AND ou.[CUSTOMER NAME] IS NOT NULL")
      # Combine query with table aliases in ORDER BY clause
    where_clause = " ".join(where_conditions)
    detail_query = f"{base_query} {where_clause} ORDER BY ou.[ORDER DATE PO RECEIVED] DESC, ou.[AAG ORDER NUMBER];"
    
    with pyodbc.connect(conn_str) as conn:
        df = pd.read_sql(detail_query, conn, params=params)
    
    if df.empty:
        print(f"❌ No new orders found with the specified filters")
        return df
    
    print(f"📦 {len(df)} new orders found")
    
    # Show summary by customer if multiple customers
    if not customer_name and len(df['CUSTOMER'].unique()) > 1:
        customer_summary = df.groupby('CUSTOMER').agg({
            'ORDER_QTY': 'sum',
            'AAG ORDER NUMBER': 'count'
        }).rename(columns={'AAG ORDER NUMBER': 'order_count'}).sort_values('order_count', ascending=False)
        
        print("")
        print("� CUSTOMER BREAKDOWN")
        print("-" * 50)
        for customer, row in customer_summary.head(10).iterrows():
            print(f"{customer:<35} | {row['order_count']:>5} orders | {row['ORDER_QTY']:>7,} qty")
        if len(customer_summary) > 10:
            print(f"... and {len(customer_summary) - 10} more customers")
    
    print("")
    print("🗂️  ORDER DETAILS (First 15)")
    print("-" * 140)    # Display first 15 orders with proper null handling
    display_df = df.head(15).copy()
    for idx, row in display_df.iterrows():
        order_date = pd.to_datetime(row['ORDER DATE PO RECEIVED']).strftime('%Y-%m-%d') if pd.notna(row['ORDER DATE PO RECEIVED']) else 'N/A'
        order_qty = row['ORDER_QTY'] if pd.notna(row['ORDER_QTY']) else 0
        customer_season = row.get('CUSTOMER SEASON', 'N/A') if pd.notna(row.get('CUSTOMER SEASON', None)) else 'N/A'
        aag_season = row.get('AAG SEASON', 'N/A') if pd.notna(row.get('AAG SEASON', None)) else 'N/A'
        
        print(f"{row['AAG ORDER NUMBER']:<15} | {row['CUSTOMER']:<20} | {row['STYLE']:<20} | {row['COLOR']:<15} | "
              f"{order_qty:>5} | {order_date} | {customer_season:<15} | {aag_season:<15}")
    
    if len(df) > 15:
        print(f"... and {len(df) - 15} more orders")
    
    return df

if __name__ == "__main__":
    # Run customer analysis
    customers_df = analyze_customers_with_new_orders()    # Optionally analyze a specific customer
    if not customers_df.empty:
        print("")
        print("💡 To analyze specific orders, run:")
        print("   from milestone_2_customer_analysis import get_customer_detail")
        print("   ")
        print("   # Examples:")
        print("   get_customer_detail('BC BRANDS')  # Single customer")
        print("   get_customer_detail(po_number='8148-00')  # Single PO")
        print("   get_customer_detail('BC BRANDS', customer_season='SPRING SUMMER 2026')  # Customer + Season")
        print("   get_customer_detail(aag_season='2026 SPRING')  # All customers for AAG season")
        print("   get_customer_detail()  # All customers (limited output)")
