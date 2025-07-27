#!/usr/bin/env python3
"""
SQL Query Extractor and Analyzer
Purpose: Extract ALL SQL queries from test files and analyze them for errors
Location: tests/debug/sql_query_extractor_and_analyzer.py
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

class SQLQueryExtractorAnalyzer:
    """Extract and analyze all SQL queries from test files"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.queries = []
        self.analysis_results = {}
        
    def extract_queries_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract SQL queries from a Python file"""
        queries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern 1: Multi-line SQL strings (triple quotes)
            triple_quote_pattern = r'"""(.*?)"""'
            matches = re.findall(triple_quote_pattern, content, re.DOTALL)
            for match in matches:
                if any(keyword in match.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER']):
                    queries.append({
                        'file': str(file_path),
                        'type': 'triple_quote',
                        'query': match.strip(),
                        'line_estimate': content[:content.find(match)].count('\n') + 1
                    })
            
            # Pattern 2: f-strings with SQL
            f_string_pattern = r'f"""(.*?)"""'
            matches = re.findall(f_string_pattern, content, re.DOTALL)
            for match in matches:
                if any(keyword in match.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER']):
                    queries.append({
                        'file': str(file_path),
                        'type': 'f_string',
                        'query': match.strip(),
                        'line_estimate': content[:content.find(match)].count('\n') + 1
                    })
            
            # Pattern 3: Single-line SQL assignments
            single_line_pattern = r'query\s*=\s*["\']([^"\']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)[^"\']*)["\']'
            matches = re.findall(single_line_pattern, content, re.IGNORECASE)
            for match in matches:
                queries.append({
                    'file': str(file_path),
                    'type': 'single_line',
                    'query': match.strip(),
                    'line_estimate': content[:content.find(match)].count('\n') + 1
                })
            
            # Pattern 4: pd.read_sql queries
            read_sql_pattern = r'pd\.read_sql\s*\(\s*["\']([^"\']*)["\']'
            matches = re.findall(read_sql_pattern, content, re.IGNORECASE)
            for match in matches:
                queries.append({
                    'file': str(file_path),
                    'type': 'pd_read_sql',
                    'query': match.strip(),
                    'line_estimate': content[:content.find(match)].count('\n') + 1
                })
            
            # Pattern 5: cursor.execute queries
            cursor_pattern = r'cursor\.execute\s*\(\s*["\']([^"\']*)["\']'
            matches = re.findall(cursor_pattern, content, re.IGNORECASE)
            for match in matches:
                queries.append({
                    'file': str(file_path),
                    'type': 'cursor_execute',
                    'query': match.strip(),
                    'line_estimate': content[:content.find(match)].count('\n') + 1
                })
                
        except Exception as e:
            self.logger.error(f"Error extracting from {file_path}: {e}")
            
        return queries
    
    def extract_all_queries(self) -> List[Dict[str, Any]]:
        """Extract queries from all test files"""
        test_directories = [
            repo_root / "tests",
            repo_root / "dev" / "customer-orders",
            repo_root / "scripts",
        ]
        
        all_queries = []
        
        for test_dir in test_directories:
            if test_dir.exists():
                for py_file in test_dir.rglob("*.py"):
                    queries = self.extract_queries_from_file(py_file)
                    all_queries.extend(queries)
        
        self.queries = all_queries
        self.logger.info(f"Extracted {len(all_queries)} SQL queries from test files")
        return all_queries
    
    def analyze_query(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single query for issues"""
        query = query_info['query']
        analysis = {
            'file': query_info['file'],
            'line': query_info['line_estimate'],
            'type': query_info['type'],
            'query': query,
            'issues': [],
            'table_references': [],
            'column_references': [],
            'has_parameters': False,
            'incomplete_where': False,
            'test_result': None
        }
        
        # Extract table references
        table_pattern = r'FROM\s+\[?(\w+)\]?|\bJOIN\s+\[?(\w+)\]?|\bINTO\s+\[?(\w+)\]?|\bUPDATE\s+\[?(\w+)\]?'
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
        
        # Check for incomplete WHERE clauses
        if re.search(r'WHERE.*[=<>]\s*$|WHERE.*LIKE\s*$', query, re.IGNORECASE):
            analysis['incomplete_where'] = True
            analysis['issues'].append("INCOMPLETE_WHERE_CLAUSE")
        
        # Check for common table name issues
        problematic_tables = ['STG_MON_CustMasterSchedule', 'STG_MON_CustMasterSchedule_Subitems', 
                            'MON_BatchProcessing', 'ERR_MON_CustMasterSchedule']
        for table in analysis['table_references']:
            if table in problematic_tables:
                analysis['issues'].append(f"STAGING_TABLE_REFERENCE: {table}")
        
        # Test the query against database
        try:
            with db.get_connection('orders') as conn:
                cursor = conn.cursor()
                
                # For parameterized queries, skip execution
                if analysis['has_parameters'] or analysis['incomplete_where']:
                    analysis['test_result'] = 'SKIPPED_PARAMETERIZED'
                else:
                    # Try to execute with LIMIT to avoid large results
                    test_query = query
                    if 'SELECT' in query.upper() and 'LIMIT' not in query.upper() and 'TOP' not in query.upper():
                        # Add TOP clause for SQL Server
                        test_query = re.sub(r'SELECT\s+', 'SELECT TOP 1 ', query, flags=re.IGNORECASE)
                    
                    cursor.execute(test_query)
                    analysis['test_result'] = 'SUCCESS'
                    
        except Exception as e:
            analysis['test_result'] = f'ERROR: {str(e)}'
            analysis['issues'].append(f"EXECUTION_ERROR: {str(e)}")
        
        return analysis
    
    def analyze_all_queries(self) -> Dict[str, Any]:
        """Analyze all extracted queries"""
        if not self.queries:
            self.extract_all_queries()
        
        results = {
            'total_queries': len(self.queries),
            'successful_queries': 0,
            'failed_queries': 0,
            'skipped_queries': 0,
            'query_analyses': [],
            'issue_summary': {},
            'table_usage': {},
            'column_usage': {},
            'files_with_issues': set()
        }
        
        for query_info in self.queries:
            analysis = self.analyze_query(query_info)
            results['query_analyses'].append(analysis)
            
            # Count results
            if analysis['test_result'] == 'SUCCESS':
                results['successful_queries'] += 1
            elif 'ERROR' in str(analysis['test_result']):
                results['failed_queries'] += 1
                results['files_with_issues'].add(analysis['file'])
            else:
                results['skipped_queries'] += 1
            
            # Aggregate issues
            for issue in analysis['issues']:
                results['issue_summary'][issue] = results['issue_summary'].get(issue, 0) + 1
            
            # Aggregate table usage
            for table in analysis['table_references']:
                results['table_usage'][table] = results['table_usage'].get(table, 0) + 1
            
            # Aggregate column usage
            for column in analysis['column_references']:
                results['column_usage'][column] = results['column_usage'].get(column, 0) + 1
        
        results['files_with_issues'] = list(results['files_with_issues'])
        self.analysis_results = results
        return results
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        if not self.analysis_results:
            self.analyze_all_queries()
        
        results = self.analysis_results
        
        report = []
        report.append("=" * 80)
        report.append("SQL QUERY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Queries Found: {results['total_queries']}")
        report.append(f"✅ Successful: {results['successful_queries']}")
        report.append(f"❌ Failed: {results['failed_queries']}")
        report.append(f"⏭️  Skipped (Parameterized): {results['skipped_queries']}")
        
        success_rate = (results['successful_queries'] / results['total_queries'] * 100) if results['total_queries'] > 0 else 0
        report.append(f"📈 Success Rate: {success_rate:.1f}%")
        report.append("")
        
        # Issue Summary
        if results['issue_summary']:
            report.append("🚨 ISSUES FOUND")
            report.append("-" * 40)
            for issue, count in sorted(results['issue_summary'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {issue}: {count} occurrences")
            report.append("")
        
        # Table Usage
        report.append("📋 TABLE USAGE")
        report.append("-" * 40)
        for table, count in sorted(results['table_usage'].items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {table}: {count} queries")
        report.append("")
        
        # Failed Queries Detail
        failed_queries = [q for q in results['query_analyses'] if 'ERROR' in str(q['test_result'])]
        if failed_queries:
            report.append("❌ FAILED QUERIES DETAIL")
            report.append("-" * 40)
            for i, query in enumerate(failed_queries[:10], 1):  # Show first 10
                report.append(f"\n{i}. File: {Path(query['file']).name}:{query['line']}")
                report.append(f"   Error: {query['test_result']}")
                report.append(f"   Query: {query['query'][:100]}...")
                if query['table_references']:
                    report.append(f"   Tables: {', '.join(query['table_references'])}")
        
        # Files with Issues
        if results['files_with_issues']:
            report.append("\n📁 FILES WITH ISSUES")
            report.append("-" * 40)
            for file_path in results['files_with_issues']:
                report.append(f"  {Path(file_path).name}")
        
        return "\n".join(report)
    
    def save_detailed_results(self, output_path: Path = None):
        """Save detailed results to JSON"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = repo_root / f"sql_query_analysis_results_{timestamp}.json"
        
        # Convert sets to lists for JSON serialization
        results = self.analysis_results.copy()
        results['files_with_issues'] = list(results['files_with_issues'])
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Detailed results saved to: {output_path}")
        return output_path

def main():
    """Main execution function"""
    print("🔍 SQL Query Extractor and Analyzer")
    print("=" * 50)
    
    analyzer = SQLQueryExtractorAnalyzer()
    
    # Extract and analyze
    print("📤 Extracting queries from test files...")
    analyzer.extract_all_queries()
    
    print("🔬 Analyzing queries...")
    analyzer.analyze_all_queries()
    
    # Generate and display report
    print("\n📊 ANALYSIS REPORT")
    print("=" * 50)
    report = analyzer.generate_report()
    print(report)
    
    # Save detailed results
    output_file = analyzer.save_detailed_results()
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    return analyzer.analysis_results

if __name__ == "__main__":
    results = main()
