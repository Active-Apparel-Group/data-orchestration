import pandas as pd
import os
import logging
import numpy as np

def create_optimized_summary(summary_stats):
    """
    Create optimized summary with reduced columns and meaningful names.
    """
    # Create a copy and rename columns for better readability
    optimized = summary_stats.copy()
    
    # Rename columns to be more compact and meaningful
    column_mapping = {
        'Total_Records': 'Records',
        'Exact_Matches': 'Exact_#',
        'Exact_Match_Rate': 'Exact_%',
        'Fuzzy_Matches': 'Fuzzy_#',
        'Fuzzy_Match_Pct': 'Fuzzy_%',
        'No_Matches': 'NoMatch_#',
        'No_Match_Pct': 'NoMatch_%',
        'Style_Match_Pct': 'Style_%',
        'Color_Match_Pct': 'Color_%',
        'Size_Match_Pct': 'Size_%',
        'PO_Match_Pct': 'PO_%',
        'Primary_PO_Match_Pct': 'PO_Primary_%',
        'Alt_PO_Match_Pct': 'PO_Alt_%',
        'Total_Packed_Qty': 'Packed_Qty',
        'Total_Shipped_Qty': 'Shipped_Qty',
        'Total_Ordered_Qty': 'Ordered_Qty',
        'Over_Shipped_Pct': 'Over_Ship_%',
        'Under_Shipped_Pct': 'Under_Ship_%',
        'Missing_Orders_Pct': 'Missing_Ord_%',
        'Good_Quality_Pct': 'Quality_Good_%',
        'Avg_Fuzzy_Match_Score': 'Fuzzy_Avg_Score'
    }
    
    # Rename columns that exist
    for old_col, new_col in column_mapping.items():
        if old_col in optimized.columns:
            optimized = optimized.rename(columns={old_col: new_col})
    
    # Select key columns in logical order
    key_columns = [
        'Canonical_Customer', 'Records', 'Exact_#', 'Exact_%', 'Fuzzy_#', 'Fuzzy_%', 
        'NoMatch_#', 'NoMatch_%', 'Style_%', 'Color_%', 'Size_%', 'PO_%',
        'PO_Primary_%', 'PO_Alt_%', 'Packed_Qty', 'Shipped_Qty', 'Ordered_Qty',
        'Over_Ship_%', 'Under_Ship_%', 'Missing_Ord_%', 'Quality_Good_%', 'Fuzzy_Avg_Score'
    ]
    
    # Keep only columns that exist
    available_columns = [col for col in key_columns if col in optimized.columns]
    return optimized[available_columns]

def create_customer_match_analysis(customer_df):
    """
    Create match analysis breakdown for a customer.
    """
    match_analysis = []
    for match_type in ['EXACT', 'FUZZY', 'NO_MATCH']:
        subset = customer_df[customer_df['Match_Type'] == match_type]
        if len(subset) > 0:
            match_analysis.append({
                'Match_Type': match_type,
                'Records': len(subset),
                'Percentage': round(len(subset) / len(customer_df) * 100, 2),
                'Avg_Score': round(subset['Match_Score'].mean(), 1) if 'Match_Score' in subset.columns else 0,
                'Packed_Qty': int(subset['Packed_Qty'].sum()),
                'Shipped_Qty': int(subset['Shipped_Qty'].sum()),
                'Ordered_Qty': int(subset['Ordered_Qty'].sum())
            })
    
    return pd.DataFrame(match_analysis)

def create_field_issues_analysis(customer_df):
    """
    Create field-level issues analysis for a customer.
    """
    field_issues = []
    total_records = len(customer_df)
    
    for field in ['Style', 'Color', 'Size', 'Customer_PO', 'Customer_Alt_PO']:
        if field in customer_df.columns:
            missing_count = customer_df[field].isna().sum()
            empty_count = (customer_df[field] == '').sum() if customer_df[field].dtype == 'object' else 0
            
            field_issues.append({
                'Field': field,
                'Missing_Data': missing_count,
                'Empty_Data': empty_count,
                'Missing_%': round(missing_count / total_records * 100, 2),
                'Populated_Records': total_records - missing_count - empty_count,
                'Data_Quality': 'GOOD' if missing_count < total_records * 0.05 else 'POOR'
            })
    
    return pd.DataFrame(field_issues)

def create_quantity_variance_analysis(customer_df):
    """
    Create quantity variance analysis for a customer.
    """
    # Group by PO for variance analysis
    po_groups = customer_df.groupby(['Customer_PO', 'Customer_Alt_PO']).agg({
        'Ordered_Qty': 'sum',
        'Packed_Qty': 'sum',
        'Shipped_Qty': 'sum',
        'Match_Type': 'first'
    }).reset_index()
    
    po_groups['Total_Fulfilled'] = po_groups['Packed_Qty'] + po_groups['Shipped_Qty']
    po_groups['Variance'] = po_groups['Total_Fulfilled'] - po_groups['Ordered_Qty']
    po_groups['Variance_%'] = np.where(
        po_groups['Ordered_Qty'] > 0,
        (po_groups['Variance'] / po_groups['Ordered_Qty']) * 100,
        0
    )
    
    po_groups['Issue_Type'] = po_groups.apply(lambda row:
        'OVER_FULFILL' if row['Variance'] > 0 
        else 'UNDER_FULFILL' if row['Variance'] < 0 
        else 'MATCHED', axis=1)
    
    return po_groups.sort_values('Variance_%', key=abs, ascending=False)

def create_overall_summary(optimized_summary):
    """
    Create overall summary with multiple analytical tabs.
    """
    summary_tabs = {}
    
    # Tab 1: Executive Dashboard
    total_customers = len(optimized_summary)
    total_records = optimized_summary['Records'].sum() if 'Records' in optimized_summary.columns else 0
    avg_exact_rate = optimized_summary['Exact_%'].mean() if 'Exact_%' in optimized_summary.columns else 0
    avg_quality_rate = optimized_summary['Quality_Good_%'].mean() if 'Quality_Good_%' in optimized_summary.columns else 0
    
    exec_dashboard = pd.DataFrame([{
        'Metric': 'Total Customers',
        'Value': total_customers,
        'Details': f'{total_customers} unique customers analyzed'
    }, {
        'Metric': 'Total Records',
        'Value': total_records,
        'Details': f'{total_records:,} total transaction records'
    }, {
        'Metric': 'Average Exact Match Rate',
        'Value': f'{avg_exact_rate:.1f}%',
        'Details': f'Average across all customers'
    }, {
        'Metric': 'Average Quality Rate',
        'Value': f'{avg_quality_rate:.1f}%',
        'Details': f'Good quality matches average'
    }])
    
    if 'Exact_%' in optimized_summary.columns:
        high_performers = len(optimized_summary[optimized_summary['Exact_%'] > 90])
        problem_customers = len(optimized_summary[optimized_summary['Exact_%'] < 70])
        
        exec_dashboard = pd.concat([exec_dashboard, pd.DataFrame([{
            'Metric': 'High Performers (>90% Exact)',
            'Value': high_performers,
            'Details': f'Customers with >90% exact match rate'
        }, {
            'Metric': 'Problem Customers (<70% Exact)',
            'Value': problem_customers,
            'Details': f'Customers needing attention'
        }])], ignore_index=True)
    
    summary_tabs['Executive_Dashboard'] = exec_dashboard
    
    # Tab 2: Customer Rankings
    customer_rankings = optimized_summary.copy()
    if 'Exact_%' in customer_rankings.columns and 'Quality_Good_%' in customer_rankings.columns:
        customer_rankings['Performance_Score'] = (
            customer_rankings['Exact_%'] * 0.5 +
            customer_rankings['Quality_Good_%'] * 0.5
        )
        customer_rankings = customer_rankings.sort_values('Performance_Score', ascending=False)
    
    summary_tabs['Customer_Rankings'] = customer_rankings
    
    # Tab 3: Field Analysis
    field_columns = ['Style_%', 'Color_%', 'Size_%', 'PO_%']
    field_analysis = []
    
    for field in field_columns:
        if field in optimized_summary.columns:
            field_data = optimized_summary[field].dropna()
            if len(field_data) > 0:
                field_analysis.append({
                    'Field': field.replace('_%', ''),
                    'Avg_Match_Rate': round(field_data.mean(), 1),
                    'Customers_Above_90%': len(field_data[field_data > 90]),
                    'Customers_Below_70%': len(field_data[field_data < 70]),
                    'Best_Customer': optimized_summary.loc[field_data.idxmax(), 'Canonical_Customer'] if len(field_data) > 0 else 'N/A',
                    'Worst_Customer': optimized_summary.loc[field_data.idxmin(), 'Canonical_Customer'] if len(field_data) > 0 else 'N/A'
                })
    
    if field_analysis:
        summary_tabs['Field_Analysis'] = pd.DataFrame(field_analysis)
    
    # Tab 4: Problem Customers (Bottom performers)
    if 'Exact_%' in optimized_summary.columns:
        problem_customers = optimized_summary[optimized_summary['Exact_%'] < 80].copy()
        problem_customers = problem_customers.sort_values('Exact_%')
        summary_tabs['Problem_Customers'] = problem_customers
    
    return summary_tabs

def write_enhanced_reports(results_df, summary_stats, outdir="../outputs"):
    """
    Create enhanced reporting with overall summary and detailed customer reports.
    """
    os.makedirs(outdir, exist_ok=True)
    
    # Create optimized summary
    optimized_summary = create_optimized_summary(summary_stats)
    
    # Create overall summary file
    overall_summary_path = os.path.join(outdir, 'OVERALL_SUMMARY.xlsx')
    summary_tabs = create_overall_summary(optimized_summary)
    
    with pd.ExcelWriter(overall_summary_path, engine='xlsxwriter') as writer:
        for tab_name, tab_data in summary_tabs.items():
            if isinstance(tab_data, pd.DataFrame) and not tab_data.empty:
                tab_data.to_excel(writer, sheet_name=tab_name, index=False)
    
    logging.info(f"Overall summary exported to {overall_summary_path}")
    print(f"✓ Overall summary exported to {overall_summary_path}")
    
    # Create individual customer files
    customers = results_df['Canonical_Customer'].dropna().unique()
    print(f"Creating detailed reports for {len(customers)} customers...")
    
    for customer in customers:
            
        customer_df = results_df[results_df['Canonical_Customer'] == customer].copy()
        
        # Safe filename
        safe_customer_name = "".join(c for c in str(customer) if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_customer_name = safe_customer_name.replace(' ', '_')[:50]
        customer_path = os.path.join(outdir, f'CUSTOMER_{safe_customer_name}.xlsx')
        
        try:
            with pd.ExcelWriter(customer_path, engine='xlsxwriter') as writer:
                # Tab 1: Customer Summary
                customer_summary = optimized_summary[optimized_summary['Canonical_Customer'] == customer]
                if not customer_summary.empty:
                    customer_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Tab 2: Match Analysis
                match_analysis = create_customer_match_analysis(customer_df)
                if not match_analysis.empty:
                    match_analysis.to_excel(writer, sheet_name='Match_Analysis', index=False)
                
                # Tab 3: Field Issues
                field_issues = create_field_issues_analysis(customer_df)
                if not field_issues.empty:
                    field_issues.to_excel(writer, sheet_name='Field_Issues', index=False)
                
                # Tab 4: Quantity Variance
                qty_variance = create_quantity_variance_analysis(customer_df)
                if not qty_variance.empty:
                    qty_variance.to_excel(writer, sheet_name='Quantity_Analysis', index=False)
                
                # Tab 5: Transaction Detail (Enhanced)
                transaction_detail = customer_df.copy()
                
                # Add issue flags
                if len(transaction_detail) > 0:
                    transaction_detail['Over_Ship_Flag'] = transaction_detail['Shipped_Qty'] > transaction_detail['Ordered_Qty']
                    transaction_detail['Under_Ship_Flag'] = (transaction_detail['Ordered_Qty'] > 0) & (transaction_detail['Shipped_Qty'] < transaction_detail['Ordered_Qty'])
                    transaction_detail['Missing_Order_Flag'] = transaction_detail['Ordered_Qty'] == 0
                    
                    # Sort by PO for easier analysis
                    transaction_detail = transaction_detail.sort_values(['Customer_PO', 'Style', 'Color', 'Size'])
                    transaction_detail.to_excel(writer, sheet_name='Transaction_Detail', index=False)
                
            print(f"✓ Customer report created: {customer}")
            
        except Exception as e:
            logging.warning(f"Failed to create report for customer {customer}: {str(e)}")
            print(f"✗ Failed to create report for {customer}: {str(e)}")
    
    # Also create the original combined report for backward compatibility
    original_path = os.path.join(outdir, 'global_customer_audit_fuzzy_match_by_customer.xlsx')
    with pd.ExcelWriter(original_path, engine='xlsxwriter') as writer:
        optimized_summary.to_excel(writer, sheet_name='OPTIMIZED_SUMMARY', index=False)
        summary_stats.to_excel(writer, sheet_name='ORIGINAL_SUMMARY', index=False)
        for cust in results_df['Canonical_Customer'].dropna().unique()[:255]:  # Guard
            cust_df = results_df[results_df['Canonical_Customer'] == cust].copy()
            sheet_name = str(cust)[:31]
            cust_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"✓ Original format exported to {original_path}")
    logging.info(f"Original format exported to {original_path}")

def write_excel(results_df, summary_stats, outdir="../outputs"):
    """
    Enhanced function that creates both original and new report formats.
    """
    # Create enhanced reports
    write_enhanced_reports(results_df, summary_stats, outdir)
    
    print(f"✓ All reports generated successfully in {outdir}")
