#!/usr/bin/env python3
"""
Targeted SQL Query Analyzer - Focused Scope
Purpose: Analyze ONLY queries from customer-orders workflow and related tests
Location: tests/debug/targeted_sql_query_analyzer.py
"""
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import pandas as pd

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

class TargetedSQLAnalyzer:
    """Analyze SQL queries ONLY from customer-orders workflow scope"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.queries = []
        self.analysis_results = {}
        
        # Define our FOCUSED scope
        self.target_files = [
            # Customer-orders workflow files
            "dev/customer-orders/customer_batch_processor.py",
            "dev/customer-orders/integration_monday.py", 
            "dev/customer-orders/staging_processor.py",
            "dev/customer-orders/customer_mapper.py",
            "dev/customer-orders/main_customer_orders.py",
            "dev/customer-orders/change_detector.py",
            
            # Test files for our workflow
            "tests/end_to_end/test_greyson_po_4755_complete_workflow.py",
            "tests/debug/test_greyson_po_4755_limited.py",
            "tests/debug/test_subitem_milestone_isolated.py",
            "tests/debug/debug_customer_filtering.py",
            "tests/debug/debug_table_schemas.py",
            
            # Supporting test files
            "tests/sql_queries/test_customer_analysis_query.py",
            "tests/sql_queries/test_customer_detail_query.py",
        ]
        
    def extract_queries_from_target_files(self) -> List[Dict[str, Any]]:
        """Extract queries ONLY from our target scope"""
        all_queries = []
        
        for target_file in self.target_files:
            file_path = repo_root / target_file
            if file_path.exists():
                self.logger.info(f"Analyzing: {target_file}")
                queries = self.extract_queries_from_file(file_path)
                all_queries.extend(queries)
            else:
                self.logger.warning(f"File not found: {target_file}")
        
        self.queries = all_queries
        self.logger.info(f"Extracted {len(all_queries)} SQL queries from {len(self.target_files)} target files")
        return all_queries
    
    def extract_queries_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract SQL queries from a specific Python file"""
        queries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern 1: Multi-line SQL strings (triple quotes) - REAL SQL only
            sql_pattern = r'"""(.*?SELECT.*?)"""'
            matches = re.findall(sql_pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if self.is_real_sql(match):
                    queries.append({
                        'file': str(file_path),
                        'type': 'multiline_sql',
                        'query': match.strip(),
                        'line_estimate': content[:content.find(match)].count('\n') + 1
                    })
            
            # Pattern 2: f-strings with SQL
            f_sql_pattern = r'f"""(.*?SELECT.*?)"""'
            matches = re.findall(f_sql_pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if self.is_real_sql(match):
                    queries.append({
                        'file': str(file_path),
                        'type': 'f_string_sql',
                        'query': match.strip(),
                        'line_estimate': content[:content.find(match)].count('\n') + 1
                    })
            
            # Pattern 3: pd.read_sql queries (high confidence these are real SQL)
            read_sql_pattern = r'pd\.read_sql\s*\(\s*["\']([^"\']*SELECT[^"\']*)["\']'
            matches = re.findall(read_sql_pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                queries.append({
                    'file': str(file_path),
                    'type': 'pd_read_sql',
                    'query': match.strip(),
                    'line_estimate': content[:content.find(match)].count('\n') + 1
                })
            
            # Pattern 4: cursor.execute queries (high confidence)
            cursor_pattern = r'cursor\.execute\s*\(\s*["\']([^"\']*(?:SELECT|INSERT|UPDATE|DELETE)[^"\']*)["\']'
            matches = re.findall(cursor_pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                queries.append({
                    'file': str(file_path),
                    'type': 'cursor_execute',
                    'query': match.strip(),
                    'line_estimate': content[:content.find(match)].count('\n') + 1
                })
                
            # Pattern 5: query = "SELECT..." assignments
            query_assignment_pattern = r'query\s*=\s*["\']([^"\']*(?:SELECT|INSERT|UPDATE|DELETE)[^"\']*)["\']'
            matches = re.findall(query_assignment_pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                queries.append({
                    'file': str(file_path),
                    'type': 'query_assignment',
                    'query': match.strip(),
                    'line_estimate': content[:content.find(match)].count('\n') + 1
                })
                
        except Exception as e:
            self.logger.error(f"Error extracting from {file_path}: {e}")
            
        return queries
    
    def is_real_sql(self, text: str) -> bool:
        """Check if text is actually SQL and not documentation"""
        # Filter out documentation/comments
        if any(doc_word in text.lower() for doc_word in [
            'purpose:', 'args:', 'returns:', 'raises:', 'example:', 
            'note:', 'todo:', 'fixme:', 'description:', 'implementation:'
        ]):
            return False
        
        # Must have SQL keywords
        sql_keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER']
        has_sql = any(keyword in text.upper() for keyword in sql_keywords)
        
        # Should not be mostly comments
        comment_ratio = text.count('#') / len(text) if len(text) > 0 else 0
        
        return has_sql and comment_ratio < 0.1
    
    def analyze_query(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single query for issues"""
        query = query_info['query']
        analysis = {
            'file': Path(query_info['file']).name,
            'line': query_info['line_estimate'],
            'type': query_info['type'],
            'query': query,
            'issues': [],
            'table_references': [],
            'column_references': [],
            'has_parameters': False,
            'test_result': None,
            'query_category': self.categorize_query(query)
        }
        
        # Extract table references
        table_pattern = r'FROM\s+\[?([^\s\]]+)\]?|\bJOIN\s+\[?([^\s\]]+)\]?|\bINTO\s+\[?([^\s\]]+)\]?|\bUPDATE\s+\[?([^\s\]]+)\]?'
        table_matches = re.findall(table_pattern, query, re.IGNORECASE)
        for match in table_matches:
            for table in match:
                if table:
                    analysis['table_references'].append(table)
        
        # Extract column references (basic pattern)
        column_pattern = r'\[([^\]]+)\]'
        column_matches = re.findall(column_pattern, query)
        analysis['column_references'] = list(set(column_matches))
        
        # Check for parameter placeholders
        if '?' in query or '{' in query or '%s' in query:
            analysis['has_parameters'] = True
        
        # Test the query against database
        try:
            with db.get_connection('orders') as conn:
                cursor = conn.cursor()
                
                if analysis['has_parameters']:
                    analysis['test_result'] = 'SKIPPED_PARAMETERIZED'
                else:
                    # Add TOP 1 for SQL Server if it's a SELECT without TOP/LIMIT
                    test_query = query
                    if 'SELECT' in query.upper() and 'TOP' not in query.upper() and 'LIMIT' not in query.upper():
                        test_query = re.sub(r'SELECT\s+', 'SELECT TOP 1 ', query, flags=re.IGNORECASE)
                    
                    cursor.execute(test_query)
                    analysis['test_result'] = 'SUCCESS'
                    
        except Exception as e:
            analysis['test_result'] = f'ERROR: {str(e)[:100]}...'
            analysis['issues'].append(f"EXECUTION_ERROR")
        
        return analysis
    
    def categorize_query(self, query: str) -> str:
        """Categorize the query by purpose"""
        query_upper = query.upper()
        
        if 'STG_MON_CUSTMASTERSCHEDULE' in query_upper:
            return 'STAGING_OPERATIONS'
        elif 'MON_CUSTMASTERSCHEDULE' in query_upper:
            return 'PRODUCTION_OPERATIONS'  
        elif 'ORDERS_UNIFIED' in query_upper:
            return 'SOURCE_DATA_ACCESS'
        elif 'MON_BATCHPROCESSING' in query_upper:
            return 'BATCH_TRACKING'
        elif 'GREYSON' in query_upper and '4755' in query:
            return 'GREYSON_PO_4755_TEST'
        elif any(word in query_upper for word in ['COUNT', 'SUM', 'AVG']):
            return 'DATA_VALIDATION'
        else:
            return 'OTHER'
    
    def analyze_all_queries(self) -> Dict[str, Any]:
        """Analyze all extracted queries"""
        if not self.queries:
            self.extract_queries_from_target_files()
        
        results = {
            'total_queries': len(self.queries),
            'successful_queries': 0,
            'failed_queries': 0,
            'skipped_queries': 0,
            'query_analyses': [],
            'categories': {},
            'issue_summary': {},
            'table_usage': {},
            'critical_issues': []
        }
        
        for query_info in self.queries:
            analysis = self.analyze_query(query_info)
            results['query_analyses'].append(analysis)
            
            # Count results
            if analysis['test_result'] == 'SUCCESS':
                results['successful_queries'] += 1
            elif 'ERROR' in str(analysis['test_result']):
                results['failed_queries'] += 1
            else:
                results['skipped_queries'] += 1
            
            # Categorize
            category = analysis['query_category']
            results['categories'][category] = results['categories'].get(category, 0) + 1
            
            # Track issues
            for issue in analysis['issues']:
                results['issue_summary'][issue] = results['issue_summary'].get(issue, 0) + 1
            
            # Track table usage
            for table in analysis['table_references']:
                results['table_usage'][table] = results['table_usage'].get(table, 0) + 1
            
            # Identify critical issues (errors in core workflow)
            if 'ERROR' in str(analysis['test_result']) and category in ['STAGING_OPERATIONS', 'PRODUCTION_OPERATIONS', 'GREYSON_PO_4755_TEST']:
                results['critical_issues'].append({
                    'file': analysis['file'],
                    'category': category,
                    'error': analysis['test_result'],
                    'query_preview': analysis['query'][:100] + '...'
                })
        
        self.analysis_results = results
        return results
    
    def generate_focused_report(self) -> str:
        """Generate a focused report for our workflow scope"""
        if not self.analysis_results:
            self.analyze_all_queries()
        
        results = self.analysis_results
        
        report = []
        report.append("=" * 80)
        report.append("TARGETED SQL ANALYSIS - CUSTOMER-ORDERS WORKFLOW SCOPE")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Scope summary
        report.append("🎯 ANALYSIS SCOPE")
        report.append("-" * 40)
        report.append(f"Target Files Analyzed: {len(self.target_files)}")
        report.append(f"SQL Queries Found: {results['total_queries']}")
        report.append("")
        
        # Success summary
        report.append("📊 EXECUTION RESULTS")
        report.append("-" * 40)
        report.append(f"✅ Successful: {results['successful_queries']}")
        report.append(f"❌ Failed: {results['failed_queries']}")
        report.append(f"⏭️  Skipped (Parameterized): {results['skipped_queries']}")
        
        success_rate = (results['successful_queries'] / results['total_queries'] * 100) if results['total_queries'] > 0 else 0
        report.append(f"📈 Success Rate: {success_rate:.1f}%")
        report.append("")
        
        # Query categories
        report.append("📋 QUERY CATEGORIES")
        report.append("-" * 40)
        for category, count in sorted(results['categories'].items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {category}: {count} queries")
        report.append("")
        
        # Critical issues
        if results['critical_issues']:
            report.append("🚨 CRITICAL ISSUES (Core Workflow)")
            report.append("-" * 40)
            for issue in results['critical_issues']:
                report.append(f"  📁 {issue['file']} - {issue['category']}")
                report.append(f"     Error: {issue['error'][:60]}...")
                report.append(f"     Query: {issue['query_preview']}")
                report.append("")
        
        # Table usage in our scope
        report.append("📋 TABLE USAGE (Our Workflow)")
        report.append("-" * 40)
        for table, count in sorted(results['table_usage'].items(), key=lambda x: x[1], reverse=True):
            if any(workflow_table in table.upper() for workflow_table in ['ORDERS_UNIFIED', 'STG_MON', 'MON_CUSTMASTER', 'MON_BATCH']):
                report.append(f"  {table}: {count} queries")
        
        return "\n".join(report)

def main():
    """Main execution function"""
    print("🎯 Targeted SQL Query Analyzer - Customer-Orders Workflow")
    print("=" * 60)
    
    analyzer = TargetedSQLAnalyzer()
    
    # Extract and analyze from focused scope only
    print("📤 Extracting queries from customer-orders workflow files...")
    analyzer.extract_queries_from_target_files()
    
    print("🔬 Analyzing workflow-specific queries...")
    analyzer.analyze_all_queries()
    
    # Generate and display focused report
    print("\n📊 FOCUSED ANALYSIS REPORT")
    print("=" * 60)
    report = analyzer.generate_focused_report()
    print(report)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = repo_root / f"targeted_sql_analysis_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(analyzer.analysis_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    return analyzer.analysis_results

if __name__ == "__main__":
    results = main()
