#!/usr/bin/env python3
"""
Quick SQL Issues Summary
Purpose: Extract key issues from SQL validation results
Location: tests/debug/quick_sql_summary.py
"""
import json
from pathlib import Path

def main():
    # Find latest results file
    json_files = list(Path().glob("targeted_sql_analysis_results_*.json"))
    if not json_files:
        print("No results files found!")
        return
    
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    print("=== KEY FINDINGS FROM SQL VALIDATION ===")
    print()
    
    # Summary stats
    print(f"📊 SUMMARY:")
    print(f"  Total Queries: {data['total_queries']}")
    print(f"  ✅ Successful: {data['successful_queries']} ({data['successful_queries']/data['total_queries']*100:.1f}%)")
    print(f"  ❌ Failed: {data['failed_queries']} ({data['failed_queries']/data['total_queries']*100:.1f}%)")
    print(f"  ⏭️  Skipped: {data['skipped_queries']} (parameterized)")
    print()
    
    # Critical workflow issues
    critical_categories = ['STAGING_OPERATIONS', 'PRODUCTION_OPERATIONS', 'GREYSON_PO_4755_TEST']
    critical_failures = [q for q in data['query_analyses'] 
                        if q['query_category'] in critical_categories and 'ERROR' in str(q['test_result'])]
    
    print(f"🚨 CRITICAL WORKFLOW ISSUES: {len(critical_failures)}")
    for i, failure in enumerate(critical_failures, 1):
        print(f"  {i}. {failure['file']} ({failure['query_category']})")
        # Extract short error reason
        error = str(failure['test_result'])
        if "Invalid object name" in error:
            print(f"     ❌ Missing table/object")
        elif "Invalid column name" in error:
            print(f"     ❌ Missing column")
        elif "Incorrect syntax" in error:
            print(f"     ❌ SQL syntax error")
        else:
            print(f"     ❌ {error[:50]}...")
    print()
    
    # Success by category
    print("✅ SUCCESSFUL QUERIES BY CATEGORY:")
    successful = [q for q in data['query_analyses'] if q['test_result'] == 'SUCCESS']
    by_category = {}
    for q in successful:
        cat = q['query_category']
        by_category[cat] = by_category.get(cat, 0) + 1
    
    for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} queries")
    print()
    
    # Failed categories
    print("❌ FAILED QUERIES BY CATEGORY:")
    failed = [q for q in data['query_analyses'] if 'ERROR' in str(q['test_result'])]
    failed_by_category = {}
    for q in failed:
        cat = q['query_category']
        failed_by_category[cat] = failed_by_category.get(cat, 0) + 1
    
    for cat, count in sorted(failed_by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} queries")
    print()
    
    # Key recommendations
    print("🎯 KEY RECOMMENDATIONS:")
    syntax_errors = len([q for q in failed if 'syntax' in str(q['test_result']).lower()])
    mysql_limit_errors = len([q for q in failed if 'LIMIT' in q['query'] and 'TOP' not in q['query']])
    
    if syntax_errors > 0:
        print(f"  1. Fix {syntax_errors} SQL syntax errors")
    if mysql_limit_errors > 0:
        print(f"  2. Convert {mysql_limit_errors} LIMIT clauses to SQL Server TOP")
    if critical_failures:
        print(f"  3. Address {len(critical_failures)} critical workflow issues first")
    
    print()
    print("📁 FILES WITH MOST ISSUES:")
    file_issues = {}
    for q in failed:
        file = q['file']
        file_issues[file] = file_issues.get(file, 0) + 1
    
    for file, count in sorted(file_issues.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {file}: {count} failed queries")

if __name__ == "__main__":
    main()
