#!/usr/bin/env python3
"""
SQL Validation Results Analyzer
Purpose: Analyze JSON output from targeted SQL query validation to identify real issues
Location: tests/debug/analyze_sql_validation_results.py
"""
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re

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

import logger_helper

class SQLValidationAnalyzer:
    """Analyze SQL validation results to identify actionable issues"""
    
    def __init__(self, json_file_path: str):
        """Initialize analyzer with JSON results file"""
        self.logger = logger_helper.get_logger(__name__)
        self.json_file_path = json_file_path
        self.results = None
        self.analysis = {}
        
    def load_results(self) -> Dict[str, Any]:
        """Load JSON results from file"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.results = json.load(f)
            self.logger.info(f"Loaded {self.results.get('total_queries', 0)} query results")
            return self.results
        except Exception as e:
            self.logger.error(f"Failed to load JSON file: {e}")
            raise
    
    def categorize_errors(self) -> Dict[str, List[Dict]]:
        """Categorize SQL errors by type for better understanding"""
        if not self.results:
            self.load_results()
        
        error_categories = {
            'syntax_errors': [],
            'missing_tables': [],
            'missing_columns': [],
            'permission_errors': [],
            'sql_server_specific': [],
            'parameterization_issues': [],
            'mysql_syntax_in_sqlserver': [],
            'documentation_parsed_as_sql': [],
            'other_errors': []
        }
        
        failed_queries = [q for q in self.results['query_analyses'] if 'ERROR' in str(q['test_result'])]
        
        for query in failed_queries:
            error_msg = str(query['test_result']).upper()
            query_text = query['query'].upper()
            
            # Categorize by error patterns
            if 'INVALID OBJECT NAME' in error_msg or 'OBJECT NOT FOUND' in error_msg:
                error_categories['missing_tables'].append(query)
            elif 'INVALID COLUMN NAME' in error_msg or 'COLUMN NOT FOUND' in error_msg:
                error_categories['missing_columns'].append(query)
            elif 'PERMISSION' in error_msg or 'ACCESS DENIED' in error_msg:
                error_categories['permission_errors'].append(query)
            elif 'LIMIT' in query_text and 'TOP' not in query_text:
                error_categories['mysql_syntax_in_sqlserver'].append(query)
            elif any(doc_word in query_text for doc_word in ['PURPOSE:', 'ARGS:', 'RETURNS:', 'EXAMPLE:']):
                error_categories['documentation_parsed_as_sql'].append(query)
            elif 'INCORRECT SYNTAX' in error_msg or 'SYNTAX ERROR' in error_msg:
                error_categories['syntax_errors'].append(query)
            elif query['has_parameters']:
                error_categories['parameterization_issues'].append(query)
            else:
                error_categories['other_errors'].append(query)
        
        return error_categories
    
    def analyze_critical_workflow_issues(self) -> Dict[str, Any]:
        """Focus on errors that affect our core customer-orders workflow"""
        if not self.results:
            self.load_results()
        
        # Critical categories for our workflow
        critical_categories = ['STAGING_OPERATIONS', 'PRODUCTION_OPERATIONS', 'GREYSON_PO_4755_TEST']
        
        critical_issues = []
        for query in self.results['query_analyses']:
            if (query['query_category'] in critical_categories and 
                'ERROR' in str(query['test_result'])):
                critical_issues.append(query)
        
        # Analyze patterns in critical issues
        table_issues = {}
        column_issues = {}
        syntax_issues = []
        
        for issue in critical_issues:
            error_msg = str(issue['test_result'])
            
            # Extract table names from errors
            table_pattern = r"Invalid object name '([^']+)'"
            table_matches = re.findall(table_pattern, error_msg)
            for table in table_matches:
                if table not in table_issues:
                    table_issues[table] = []
                table_issues[table].append({
                    'file': issue['file'],
                    'line': issue['line'],
                    'error': error_msg[:100]
                })
            
            # Extract column names from errors
            column_pattern = r"Invalid column name '([^']+)'"
            column_matches = re.findall(column_pattern, error_msg)
            for column in column_matches:
                if column not in column_issues:
                    column_issues[column] = []
                column_issues[column].append({
                    'file': issue['file'],
                    'line': issue['line'],
                    'error': error_msg[:100]
                })
            
            # Track syntax issues
            if 'syntax' in error_msg.lower():
                syntax_issues.append({
                    'file': issue['file'],
                    'line': issue['line'],
                    'query_preview': issue['query'][:150],
                    'error': error_msg[:100]
                })
        
        return {
            'total_critical_issues': len(critical_issues),
            'missing_tables': table_issues,
            'missing_columns': column_issues,
            'syntax_issues': syntax_issues,
            'critical_queries': critical_issues
        }
    
    def identify_mapping_gaps(self) -> Dict[str, Any]:
        """Identify gaps between SQL queries and our mapping files"""
        if not self.results:
            self.load_results()
        
        # Extract all table and column references from successful queries
        successful_queries = [q for q in self.results['query_analyses'] if q['test_result'] == 'SUCCESS']
        
        tables_in_use = set()
        columns_in_use = set()
        
        for query in successful_queries:
            tables_in_use.update(query['table_references'])
            columns_in_use.update(query['column_references'])
        
        # Compare with failed queries to see what's missing
        failed_queries = [q for q in self.results['query_analyses'] if 'ERROR' in str(q['test_result'])]
        
        missing_tables = set()
        missing_columns = set()
        
        for query in failed_queries:
            if 'Invalid object name' in str(query['test_result']):
                # Extract table name from error
                match = re.search(r"Invalid object name '([^']+)'", str(query['test_result']))
                if match:
                    missing_tables.add(match.group(1))
            
            if 'Invalid column name' in str(query['test_result']):
                # Extract column name from error
                match = re.search(r"Invalid column name '([^']+)'", str(query['test_result']))
                if match:
                    missing_columns.add(match.group(1))
        
        return {
            'working_tables': list(tables_in_use),
            'working_columns': list(columns_in_use),
            'missing_tables': list(missing_tables),
            'missing_columns': list(missing_columns),
            'mapping_coverage': {
                'tables_covered': len(tables_in_use),
                'tables_missing': len(missing_tables),
                'columns_covered': len(columns_in_use),
                'columns_missing': len(missing_columns)
            }
        }
    
    def generate_actionable_recommendations(self) -> List[Dict[str, Any]]:
        """Generate specific, actionable recommendations to fix issues"""
        error_categories = self.categorize_errors()
        critical_analysis = self.analyze_critical_workflow_issues()
        mapping_gaps = self.identify_mapping_gaps()
        
        recommendations = []
        
        # 1. MySQL syntax issues (easy fixes)
        if error_categories['mysql_syntax_in_sqlserver']:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'SQL Syntax',
                'issue': f"{len(error_categories['mysql_syntax_in_sqlserver'])} queries use MySQL LIMIT syntax",
                'action': 'Replace LIMIT with TOP clause for SQL Server compatibility',
                'files_affected': [q['file'] for q in error_categories['mysql_syntax_in_sqlserver']],
                'effort': 'LOW'
            })
        
        # 2. Documentation parsed as SQL (false positives)
        if error_categories['documentation_parsed_as_sql']:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Code Quality',
                'issue': f"{len(error_categories['documentation_parsed_as_sql'])} documentation blocks parsed as SQL",
                'action': 'Improve SQL extraction regex to exclude documentation',
                'files_affected': [q['file'] for q in error_categories['documentation_parsed_as_sql']],
                'effort': 'LOW'
            })
        
        # 3. Missing tables (schema issues)
        if critical_analysis['missing_tables']:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Database Schema',
                'issue': f"Missing tables: {', '.join(critical_analysis['missing_tables'].keys())}",
                'action': 'Create missing tables or update table names in queries',
                'files_affected': list(set([issue['file'] for issues in critical_analysis['missing_tables'].values() for issue in issues])),
                'effort': 'HIGH'
            })
        
        # 4. Missing columns (mapping issues)
        if critical_analysis['missing_columns']:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Column Mapping',
                'issue': f"Missing columns: {', '.join(critical_analysis['missing_columns'].keys())}",
                'action': 'Update column names in queries or add columns to schema',
                'files_affected': list(set([issue['file'] for issues in critical_analysis['missing_columns'].values() for issue in issues])),
                'effort': 'MEDIUM'
            })
        
        # 5. Parameterized queries (validation limitation)
        if error_categories['parameterization_issues']:
            recommendations.append({
                'priority': 'LOW',
                'category': 'Test Coverage',
                'issue': f"{len(error_categories['parameterization_issues'])} parameterized queries cannot be validated",
                'action': 'Create test cases with sample parameters for validation',
                'files_affected': [q['file'] for q in error_categories['parameterization_issues']],
                'effort': 'MEDIUM'
            })
        
        return recommendations
    
    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive analysis report"""
        if not self.results:
            self.load_results()
        
        error_categories = self.categorize_errors()
        critical_analysis = self.analyze_critical_workflow_issues()
        mapping_gaps = self.identify_mapping_gaps()
        recommendations = self.generate_actionable_recommendations()
        
        report = []
        report.append("=" * 80)
        report.append("SQL VALIDATION ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Source File: {Path(self.json_file_path).name}")
        report.append("")
        
        # Executive Summary
        report.append("📊 EXECUTIVE SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Queries Analyzed: {self.results['total_queries']}")
        report.append(f"✅ Successful: {self.results['successful_queries']} ({self.results['successful_queries']/self.results['total_queries']*100:.1f}%)")
        report.append(f"❌ Failed: {self.results['failed_queries']} ({self.results['failed_queries']/self.results['total_queries']*100:.1f}%)")
        report.append(f"⏭️  Skipped: {self.results['skipped_queries']} ({self.results['skipped_queries']/self.results['total_queries']*100:.1f}%)")
        report.append(f"🚨 Critical Issues: {critical_analysis['total_critical_issues']}")
        report.append("")
        
        # Error Categories
        report.append("🔍 ERROR CATEGORIZATION")
        report.append("-" * 40)
        for category, errors in error_categories.items():
            if errors:
                category_name = category.replace('_', ' ').title()
                report.append(f"  {category_name}: {len(errors)} queries")
        report.append("")
        
        # Critical Workflow Issues
        if critical_analysis['total_critical_issues'] > 0:
            report.append("🚨 CRITICAL WORKFLOW ISSUES")
            report.append("-" * 40)
            
            if critical_analysis['missing_tables']:
                report.append("Missing Tables:")
                for table, issues in critical_analysis['missing_tables'].items():
                    report.append(f"  ❌ {table} (used in {len(issues)} queries)")
                    for issue in issues[:2]:  # Show first 2 examples
                        report.append(f"     📁 {issue['file']} (line {issue.get('line', 'unknown')})")
                report.append("")
            
            if critical_analysis['missing_columns']:
                report.append("Missing Columns:")
                for column, issues in critical_analysis['missing_columns'].items():
                    report.append(f"  ❌ {column} (used in {len(issues)} queries)")
                    for issue in issues[:2]:  # Show first 2 examples
                        report.append(f"     📁 {issue['file']} (line {issue.get('line', 'unknown')})")
                report.append("")
        
        # Mapping Coverage Analysis
        report.append("📋 MAPPING COVERAGE ANALYSIS")
        report.append("-" * 40)
        coverage = mapping_gaps['mapping_coverage']
        report.append(f"Working Tables: {coverage['tables_covered']}")
        report.append(f"Missing Tables: {coverage['tables_missing']}")
        report.append(f"Working Columns: {coverage['columns_covered']}")
        report.append(f"Missing Columns: {coverage['columns_missing']}")
        
        if mapping_gaps['missing_tables']:
            report.append("\nMissing Tables:")
            for table in mapping_gaps['missing_tables'][:10]:  # Show first 10
                report.append(f"  ❌ {table}")
        
        if mapping_gaps['missing_columns']:
            report.append("\nMissing Columns:")
            for column in mapping_gaps['missing_columns'][:10]:  # Show first 10
                report.append(f"  ❌ {column}")
        report.append("")
        
        # Actionable Recommendations
        report.append("🎯 ACTIONABLE RECOMMENDATIONS")
        report.append("-" * 40)
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📋", "LOW": "💡"}
            report.append(f"{i}. {priority_emoji.get(rec['priority'], '📋')} {rec['priority']} - {rec['category']}")
            report.append(f"   Issue: {rec['issue']}")
            report.append(f"   Action: {rec['action']}")
            report.append(f"   Effort: {rec['effort']}")
            report.append(f"   Files: {len(rec['files_affected'])} affected")
            report.append("")
        
        # Quick Wins
        quick_wins = [r for r in recommendations if r['effort'] == 'LOW']
        if quick_wins:
            report.append("⚡ QUICK WINS (Low Effort, High Impact)")
            report.append("-" * 40)
            for win in quick_wins:
                report.append(f"  • {win['issue']}")
                report.append(f"    Action: {win['action']}")
            report.append("")
        
        return "\n".join(report)
    
    def export_to_excel(self, output_file: str = None):
        """Export detailed analysis to Excel for further investigation"""
        if not self.results:
            self.load_results()
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"sql_validation_analysis_{timestamp}.xlsx"
        
        # Prepare data for Excel export
        queries_df = pd.DataFrame(self.results['query_analyses'])
        
        error_categories = self.categorize_errors()
        critical_analysis = self.analyze_critical_workflow_issues()
        mapping_gaps = self.identify_mapping_gaps()
        
        # Create separate sheets for different analyses
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            # Main queries data
            queries_df.to_excel(writer, sheet_name='All_Queries', index=False)
            
            # Failed queries only
            failed_df = queries_df[queries_df['test_result'].str.contains('ERROR', na=False)]
            failed_df.to_excel(writer, sheet_name='Failed_Queries', index=False)
            
            # Critical issues
            if critical_analysis['critical_queries']:
                critical_df = pd.DataFrame(critical_analysis['critical_queries'])
                critical_df.to_excel(writer, sheet_name='Critical_Issues', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': ['Total Queries', 'Successful', 'Failed', 'Skipped', 'Critical Issues'],
                'Count': [
                    self.results['total_queries'],
                    self.results['successful_queries'],
                    self.results['failed_queries'],
                    self.results['skipped_queries'],
                    critical_analysis['total_critical_issues']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        self.logger.info(f"Detailed analysis exported to: {output_file}")
        return output_file

def main():
    """Main execution function"""
    print("🔍 SQL Validation Results Analyzer")
    print("=" * 50)
    
    # Find the most recent JSON results file
    json_files = list(Path().glob("targeted_sql_analysis_results_*.json"))
    if not json_files:
        print("❌ No SQL analysis results files found!")
        print("   Run targeted_sql_query_analyzer.py first to generate results.")
        return
    
    # Use the most recent file
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Analyzing: {latest_file}")
    
    # Initialize analyzer
    analyzer = SQLValidationAnalyzer(str(latest_file))
    
    # Generate and display report
    print("\n📊 GENERATING COMPREHENSIVE ANALYSIS...")
    report = analyzer.generate_comprehensive_report()
    print(report)
    
    # Export detailed results to Excel
    excel_file = analyzer.export_to_excel()
    print(f"\n💾 Detailed analysis exported to: {excel_file}")
    
    return analyzer

if __name__ == "__main__":
    analyzer = main()
