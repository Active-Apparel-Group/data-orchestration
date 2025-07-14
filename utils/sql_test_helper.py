"""
SQL Testing Helper
==================

Utility for testing SQL queries against the database with standardized patterns.
Provides validation, performance testing, and result verification.

Location: utils/sql_test_helper.py
"""

import pandas as pd
import time
from typing import Dict, Any, Optional, List, Tuple
import db_helper as db
import logger_helper

class SQLTestHelper:
    """Helper class for testing SQL queries with standardized patterns"""
    
    def __init__(self, database_name: str = 'dms'):
        """Initialize with database connection"""
        self.database_name = database_name
        self.logger = logger_helper.get_logger(__name__)
    
    def test_query(self, 
                   query_name: str, 
                   sql_query: str, 
                   expected_columns: List[str] = None,
                   expected_min_rows: int = 0,
                   expected_max_rows: int = None,
                   params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Test a SQL query with validation and performance metrics
        
        Args:
            query_name: Descriptive name for the query test
            sql_query: The SQL query to test
            expected_columns: List of expected column names
            expected_min_rows: Minimum expected row count
            expected_max_rows: Maximum expected row count
            params: Query parameters for parameterized queries
            
        Returns:
            Dict with test results including success status, metrics, and data
        """
        
        result = {
            'query_name': query_name,
            'success': False,
            'execution_time': 0,
            'row_count': 0,
            'column_count': 0,
            'columns': [],
            'errors': [],
            'warnings': [],
            'data_sample': None
        }
        
        try:
            self.logger.info(f"Testing query: {query_name}")
            
            # Execute query with timing
            start_time = time.time()
            
            with db.get_connection(self.database_name) as conn:
                df = pd.read_sql(sql_query, conn, params=params)
            
            execution_time = time.time() - start_time
            
            # Collect metrics
            result['execution_time'] = round(execution_time, 3)
            result['row_count'] = len(df)
            result['column_count'] = len(df.columns)
            result['columns'] = list(df.columns)
            result['data_sample'] = df.head(3).to_dict('records') if not df.empty else []
            
            # Validate expected columns
            if expected_columns:
                missing_columns = [col for col in expected_columns if col not in df.columns]
                if missing_columns:
                    result['errors'].append(f"Missing expected columns: {missing_columns}")
                
                extra_columns = [col for col in df.columns if col not in expected_columns]
                if extra_columns:
                    result['warnings'].append(f"Extra columns found: {extra_columns}")
            
            # Validate row count
            if expected_min_rows and result['row_count'] < expected_min_rows:
                result['errors'].append(f"Row count {result['row_count']} below minimum {expected_min_rows}")
            
            if expected_max_rows and result['row_count'] > expected_max_rows:
                result['warnings'].append(f"Row count {result['row_count']} above maximum {expected_max_rows}")
            
            # Performance warnings
            if execution_time > 5.0:
                result['warnings'].append(f"Query took {execution_time:.1f}s - consider optimization")
            
            # Success if no errors
            result['success'] = len(result['errors']) == 0
            
            self.logger.info(f"Query test completed: {query_name} - {'PASSED' if result['success'] else 'FAILED'}")
            
        except Exception as e:
            result['errors'].append(f"Query execution failed: {str(e)}")
            self.logger.error(f"Query test failed: {query_name} - {str(e)}")
        
        return result
    
    def validate_data_quality(self, 
                            query_name: str,
                            sql_query: str,
                            validations: Dict[str, Any],
                            params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Test data quality aspects of a query result
        
        Args:
            query_name: Descriptive name for the validation
            sql_query: The SQL query to validate
            validations: Dict of validation rules
                - 'not_null_columns': List of columns that should not have nulls
                - 'unique_columns': List of columns that should be unique
                - 'positive_columns': List of numeric columns that should be positive
                - 'date_columns': List of date columns to validate
            params: Query parameters
            
        Returns:
            Dict with validation results
        """
        
        result = {
            'query_name': query_name,
            'success': False,
            'validations_passed': 0,
            'validations_failed': 0,
            'issues': [],
            'data_quality_score': 0
        }
        
        try:
            with db.get_connection(self.database_name) as conn:
                df = pd.read_sql(sql_query, conn, params=params)
            
            if df.empty:
                result['issues'].append("No data returned for validation")
                return result
            
            total_validations = 0
            passed_validations = 0
            
            # Check not null columns
            if 'not_null_columns' in validations:
                for col in validations['not_null_columns']:
                    total_validations += 1
                    if col in df.columns:
                        null_count = df[col].isnull().sum()
                        if null_count == 0:
                            passed_validations += 1
                        else:
                            result['issues'].append(f"Column '{col}' has {null_count} null values")
                    else:
                        result['issues'].append(f"Column '{col}' not found in results")
            
            # Check unique columns
            if 'unique_columns' in validations:
                for col in validations['unique_columns']:
                    total_validations += 1
                    if col in df.columns:
                        duplicate_count = len(df) - df[col].nunique()
                        if duplicate_count == 0:
                            passed_validations += 1
                        else:
                            result['issues'].append(f"Column '{col}' has {duplicate_count} duplicate values")
                    else:
                        result['issues'].append(f"Column '{col}' not found in results")
            
            # Check positive columns
            if 'positive_columns' in validations:
                for col in validations['positive_columns']:
                    total_validations += 1
                    if col in df.columns:
                        negative_count = (df[col] < 0).sum()
                        if negative_count == 0:
                            passed_validations += 1
                        else:
                            result['issues'].append(f"Column '{col}' has {negative_count} negative values")
                    else:
                        result['issues'].append(f"Column '{col}' not found in results")
            
            # Check date columns
            if 'date_columns' in validations:
                for col in validations['date_columns']:
                    total_validations += 1
                    if col in df.columns:
                        try:
                            pd.to_datetime(df[col])
                            passed_validations += 1
                        except:
                            result['issues'].append(f"Column '{col}' contains invalid date values")
                    else:
                        result['issues'].append(f"Column '{col}' not found in results")
            
            result['validations_passed'] = passed_validations
            result['validations_failed'] = total_validations - passed_validations
            result['data_quality_score'] = round((passed_validations / total_validations * 100), 1) if total_validations > 0 else 0
            result['success'] = result['validations_failed'] == 0
            
        except Exception as e:
            result['issues'].append(f"Validation failed: {str(e)}")
            self.logger.error(f"Data quality validation failed: {query_name} - {str(e)}")
        
        return result
    
    def compare_queries(self, 
                       query1_name: str, 
                       query1_sql: str,
                       query2_name: str, 
                       query2_sql: str,
                       params1: Dict[str, Any] = None,
                       params2: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Compare results of two queries for testing purposes
        
        Args:
            query1_name: Name of first query
            query1_sql: First SQL query
            query2_name: Name of second query  
            query2_sql: Second SQL query
            params1: Parameters for first query
            params2: Parameters for second query
            
        Returns:
            Dict with comparison results
        """
        
        result = {
            'query1_name': query1_name,
            'query2_name': query2_name,
            'identical': False,
            'row_count_match': False,
            'column_count_match': False,
            'differences': [],
            'query1_stats': {},
            'query2_stats': {}
        }
        
        try:
            with db.get_connection(self.database_name) as conn:
                df1 = pd.read_sql(query1_sql, conn, params=params1)
                df2 = pd.read_sql(query2_sql, conn, params=params2)
            
            result['query1_stats'] = {'rows': len(df1), 'columns': len(df1.columns)}
            result['query2_stats'] = {'rows': len(df2), 'columns': len(df2.columns)}
            
            result['row_count_match'] = len(df1) == len(df2)
            result['column_count_match'] = len(df1.columns) == len(df2.columns)
            
            if not result['row_count_match']:
                result['differences'].append(f"Row count differs: {len(df1)} vs {len(df2)}")
            
            if not result['column_count_match']:
                result['differences'].append(f"Column count differs: {len(df1.columns)} vs {len(df2.columns)}")
            
            # Check if dataframes are identical (if same structure)
            if result['row_count_match'] and result['column_count_match']:
                try:
                    if df1.equals(df2):
                        result['identical'] = True
                    else:
                        result['differences'].append("Data content differs between queries")
                except:
                    result['differences'].append("Cannot compare data content - different structure")
            
        except Exception as e:
            result['differences'].append(f"Comparison failed: {str(e)}")
            self.logger.error(f"Query comparison failed: {str(e)}")
        
        return result

def create_sql_tester(database_name: str = 'dms') -> SQLTestHelper:
    """Factory function to create SQL test helper instance"""
    return SQLTestHelper(database_name)
