#!/usr/bin/env python3
"""
SQL Query Extractor & Debugger for Test Framework
Purpose: Extract all SQL queries from test files and add comprehensive debugging
Location: tests/debug/sql_query_debugger.py
"""
import sys
from pathlib import Path
import re
import pandas as pd
from datetime import datetime

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

# Import utilities
import db_helper as db
import logger_helper

logger = logger_helper.get_logger(__name__)

class SQLQueryDebugger:
    """Extract and debug all SQL queries from test framework"""
    
    def __init__(self):
        self.logger = logger
        self.queries = []
        self.test_files = []
        
    def extract_all_queries(self):
        """Extract all SQL queries from test files"""
        
        test_dirs = [
            repo_root / "tests" / "end_to_end",
            repo_root / "tests" / "debug",
            repo_root / "tests" / "sql_queries"
        ]
        
        for test_dir in test_dirs:
            if test_dir.exists():
                for test_file in test_dir.glob("*.py"):
                    self._extract_queries_from_file(test_file)
        
        return self.queries
    
    def _extract_queries_from_file(self, file_path: Path):
        """Extract SQL queries from a specific file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.test_files.append(str(file_path))
            
            # Pattern 1: Multi-line SQL in triple quotes
            sql_pattern1 = r'(?:sql\s*=\s*)?"""([^"]*SELECT[^"]*?)"""'
            matches1 = re.findall(sql_pattern1, content, re.DOTALL | re.IGNORECASE)
            
            # Pattern 2: Single line SQL strings
            sql_pattern2 = r'(?:sql\s*=\s*)?["\']([^"\']*SELECT[^"\']*?)["\']'
            matches2 = re.findall(sql_pattern2, content, re.IGNORECASE)
            
            # Pattern 3: SQL in f-strings
            sql_pattern3 = r'f["\']([^"\']*SELECT[^"\']*?)["\']'
            matches3 = re.findall(sql_pattern3, content, re.IGNORECASE)
            
            # Combine all matches
            all_matches = matches1 + matches2 + matches3
            
            for i, sql in enumerate(all_matches):
                if sql.strip() and 'SELECT' in sql.upper():
                    query_info = {
                        'file': file_path.name,
                        'full_path': str(file_path),
                        'query_index': i + 1,
                        'sql': sql.strip(),
                        'type': self._classify_query(sql),
                        'tables': self._extract_tables(sql),
                        'columns': self._extract_columns(sql)
                    }
                    self.queries.append(query_info)
                    
        except Exception as e:
            self.logger.error(f"Error extracting from {file_path}: {e}")
    
    def _classify_query(self, sql: str) -> str:
        """Classify the type of SQL query"""
        sql_upper = sql.upper()
        
        if 'COUNT(' in sql_upper and 'GROUP BY' not in sql_upper:
            return 'COUNT_VALIDATION'
        elif 'INFORMATION_SCHEMA' in sql_upper:
            return 'SCHEMA_CHECK'
        elif 'EXISTS' in sql_upper:
            return 'EXISTENCE_CHECK'
        elif 'WHERE' in sql_upper and ('GREYSON' in sql_upper or '4755' in sql_upper):
            return 'GREYSON_FILTER'
        elif 'STG_' in sql_upper:
            return 'STAGING_TABLE'
        elif 'MON_' in sql_upper:
            return 'PRODUCTION_TABLE'
        elif 'JOIN' in sql_upper:
            return 'JOIN_QUERY'
        else:
            return 'GENERAL_SELECT'
    
    def _extract_tables(self, sql: str) -> list:
        """Extract table names from SQL"""
        # Simple pattern to find table names after FROM and JOIN
        table_pattern = r'(?:FROM|JOIN)\s+(?:\[dbo\]\.)?\[?(\w+)\]?'
        tables = re.findall(table_pattern, sql, re.IGNORECASE)
        return list(set(tables))  # Remove duplicates
    
    def _extract_columns(self, sql: str) -> list:
        """Extract column names from SQL SELECT clause"""
        # Extract SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.DOTALL | re.IGNORECASE)
        if not select_match:
            return []
        
        select_clause = select_match.group(1)
        
        # Handle common patterns
        if '*' in select_clause:
            return ['*']
        
        # Split by comma and clean up
        columns = []
        for col in select_clause.split(','):
            col = col.strip()
            # Remove aliases (AS keyword)
            col = re.sub(r'\s+AS\s+\w+', '', col, flags=re.IGNORECASE)
            # Remove brackets and schema prefixes
            col = re.sub(r'^\[?.*?\]?\.', '', col)
            col = re.sub(r'[\[\]]', '', col)
            if col and not col.startswith('('):  # Skip functions for now
                columns.append(col.strip())
        
        return columns[:10]  # Limit to first 10 for readability
    
    def test_all_queries(self):
        """Test all extracted queries against the database"""
        
        results = []
        
        for query_info in self.queries:
            result = self._test_single_query(query_info)
            results.append(result)
            
        return results
    
    def _test_single_query(self, query_info: dict) -> dict:
        """Test a single query and return results"""
        
        try:
            # Try to execute the query
            with db.get_connection('orders') as conn:
                start_time = datetime.now()
                df = pd.read_sql(query_info['sql'], conn)
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
            
            return {
                'file': query_info['file'],
                'query_index': query_info['query_index'],
                'type': query_info['type'],
                'tables': query_info['tables'],
                'status': 'SUCCESS',
                'execution_time': execution_time,
                'row_count': len(df),
                'column_count': len(df.columns) if not df.empty else 0,
                'sample_data': df.head(2).to_dict('records') if not df.empty else [],
                'sql': query_info['sql'][:200] + '...' if len(query_info['sql']) > 200 else query_info['sql']
            }
            
        except Exception as e:
            return {
                'file': query_info['file'],
                'query_index': query_info['query_index'],
                'type': query_info['type'],
                'tables': query_info['tables'],
                'status': 'ERROR',
                'error': str(e),
                'sql': query_info['sql'][:200] + '...' if len(query_info['sql']) > 200 else query_info['sql']
            }
    
    def print_query_summary(self):
        """Print a comprehensive summary of all queries"""
        
        print("=" * 80)
        print("🔍 SQL QUERY EXTRACTOR & DEBUGGER - COMPREHENSIVE REPORT")
        print("=" * 80)
        
        # Extract queries
        queries = self.extract_all_queries()
        
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"   Files scanned: {len(self.test_files)}")
        print(f"   Queries found: {len(queries)}")
        
        # Group by file
        queries_by_file = {}
        for query in queries:
            file_name = query['file']
            if file_name not in queries_by_file:
                queries_by_file[file_name] = []
            queries_by_file[file_name].append(query)
        
        print(f"\n📁 QUERIES BY FILE:")
        for file_name, file_queries in queries_by_file.items():
            print(f"   {file_name}: {len(file_queries)} queries")
        
        # Group by type
        queries_by_type = {}
        for query in queries:
            query_type = query['type']
            if query_type not in queries_by_type:
                queries_by_type[query_type] = []
            queries_by_type[query_type].append(query)
        
        print(f"\n🏷️ QUERIES BY TYPE:")
        for query_type, type_queries in queries_by_type.items():
            print(f"   {query_type}: {len(type_queries)} queries")
        
        print(f"\n🔍 ALL QUERIES (DETAILED):")
        print("-" * 80)
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i:02d}] {query['file']} - Query #{query['query_index']}")
            print(f"     Type: {query['type']}")
            print(f"     Tables: {', '.join(query['tables']) if query['tables'] else 'None detected'}")
            print(f"     SQL:")
            
            # Format SQL for better readability
            sql_lines = query['sql'].split('\n')
            for line in sql_lines:
                print(f"         {line.strip()}")
        
        # Test all queries
        print(f"\n🧪 TESTING ALL QUERIES:")
        print("-" * 80)
        
        test_results = self.test_all_queries()
        
        success_count = sum(1 for r in test_results if r['status'] == 'SUCCESS')
        error_count = len(test_results) - success_count
        
        print(f"\n📊 TEST RESULTS SUMMARY:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📈 Success Rate: {success_count/len(test_results)*100:.1f}%")
        
        print(f"\n🔍 DETAILED TEST RESULTS:")
        
        for result in test_results:
            status_emoji = "✅" if result['status'] == 'SUCCESS' else "❌"
            print(f"\n{status_emoji} {result['file']} - Query #{result['query_index']}")
            print(f"     Type: {result['type']}")
            print(f"     Tables: {', '.join(result['tables']) if result['tables'] else 'None'}")
            print(f"     Status: {result['status']}")
            
            if result['status'] == 'SUCCESS':
                print(f"     Execution Time: {result['execution_time']:.3f}s")
                print(f"     Rows: {result['row_count']}")
                print(f"     Columns: {result['column_count']}")
                if result['sample_data']:
                    print(f"     Sample Data: {result['sample_data'][0] if result['sample_data'] else 'No data'}")
            else:
                print(f"     Error: {result['error']}")
            
            print(f"     SQL: {result['sql']}")
        
        return {
            'queries_extracted': len(queries),
            'test_results': test_results,
            'success_rate': success_count/len(test_results)*100 if test_results else 0
        }

def main():
    """Main execution function"""
    
    logger.info("Starting SQL Query Extractor & Debugger...")
    
    debugger = SQLQueryDebugger()
    summary = debugger.print_query_summary()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = repo_root / f"sql_query_debug_results_{timestamp}.json"
    
    import json
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"Results saved to: {results_file}")
    
    return summary

if __name__ == "__main__":
    main()
