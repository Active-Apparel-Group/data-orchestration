#!/usr/bin/env python3
"""
Data Type Validator & Auto-Corrector for Monday.com Board ETL

This module provides systematic detection and correction of data type mismatches
between Monday.com API data and SQL Server schema expectations.

Key Features:
- Pre-deployment data sampling and type validation
- Automatic type mapping corrections based on actual data
- Integration with board schema generator for better DDL generation
- Detailed reporting of type mismatches and corrections
"""

import os
import sys
import json
import requests
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import logging

# Repository root discovery
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

try:
    import db_helper as db
    import logger_helper
except ImportError as e:
    print(f"Warning: Could not import utilities: {e}")

logger = logging.getLogger(__name__)

class DataTypeAnalyzer:
    """Analyzes actual Monday.com data to determine optimal SQL data types"""
    
    def __init__(self, monday_token: str):
        self.monday_token = monday_token
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": f"Bearer {monday_token}",
            "API-Version": "2025-04",
            "Content-Type": "application/json"
        }
    
    def sample_board_data(self, board_id: int, sample_size: int = 50) -> Dict[str, List[Any]]:
        """Sample actual data from Monday.com board to analyze data types"""
        logger.info(f"Sampling {sample_size} records from board {board_id} for type analysis...")
        
        query = f'''
        query SampleBoardData {{
          boards(ids: {board_id}) {{
            name
            items_page(limit: {sample_size}) {{
              items {{
                id
                name
                column_values {{
                  column {{
                    id
                    title
                    type
                  }}
                  value
                  text
                  ... on ItemIdValue {{ item_id }}
                  ... on NumbersValue {{ number }}
                  ... on StatusValue {{ label }}
                  ... on PeopleValue {{ text }}
                  ... on DropdownValue {{ text }}
                  ... on MirrorValue {{ display_value }}
                  ... on BoardRelationValue {{ display_value }}
                  ... on FormulaValue {{ display_value }}
                }}
              }}
            }}
          }}
        }}
        '''
        
        try:
            response = requests.post(self.api_url, json={"query": query}, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'errors' in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            board = data['data']['boards'][0]
            items = board['items_page']['items']
            
            # Organize sample data by column
            column_samples = {}
            
            for item in items:
                for cv in item['column_values']:
                    col_title = cv['column']['title']
                    col_type = cv['column']['type']
                    
                    if col_title not in column_samples:
                        column_samples[col_title] = {
                            'monday_type': col_type,
                            'monday_id': cv['column']['id'],
                            'sample_values': [],
                            'sample_raw_values': []
                        }
                    
                    # Extract actual value using multiple strategies
                    actual_value = self._extract_sample_value(cv)
                    raw_value = cv.get('value')
                    
                    if actual_value is not None:
                        column_samples[col_title]['sample_values'].append(actual_value)
                        column_samples[col_title]['sample_raw_values'].append(raw_value)
            
            logger.info(f"Sampled data from {len(items)} items, found {len(column_samples)} columns")
            return column_samples
            
        except Exception as e:
            logger.error(f"Failed to sample board data: {e}")
            raise
    
    def _extract_sample_value(self, column_value: Dict) -> Any:
        """Extract the actual value from a Monday.com column_value object"""
        cv = column_value
        col_type = cv['column']['type']
        
        # Try different extraction strategies based on type
        if col_type == 'item_id' and cv.get('item_id'):
            return cv['item_id']
        elif col_type == 'numbers' and cv.get('number') is not None:
            return cv['number']
        elif col_type == 'status' and cv.get('label'):
            return cv['label']
        elif cv.get('display_value'):
            return cv['display_value']
        elif cv.get('text'):
            return cv['text']
        elif cv.get('value'):
            return cv['value']
        
        return None
    
    def analyze_column_types(self, column_samples: Dict[str, Dict]) -> Dict[str, Dict]:
        """Analyze sampled data to determine optimal SQL data types"""
        logger.info("Analyzing column data types based on actual samples...")
        
        type_analysis = {}
        
        for col_name, col_data in column_samples.items():
            monday_type = col_data['monday_type']
            sample_values = col_data['sample_values']
            
            analysis = {
                'monday_type': monday_type,
                'monday_id': col_data['monday_id'],
                'sample_count': len(sample_values),
                'null_count': sample_values.count(None),
                'non_null_values': [v for v in sample_values if v is not None],
                'recommended_sql_type': None,
                'type_issues': [],
                'sample_preview': sample_values[:5]  # First 5 samples for preview
            }
            
            # Analyze non-null values
            non_null_values = analysis['non_null_values']
            
            if not non_null_values:
                analysis['recommended_sql_type'] = 'NVARCHAR(255)'
                analysis['type_issues'].append('All values are null')
            else:
                analysis['recommended_sql_type'] = self._infer_sql_type(monday_type, non_null_values)
                analysis['type_issues'] = self._detect_type_issues(monday_type, non_null_values)
            
            type_analysis[col_name] = analysis
            
            # Log significant findings
            if analysis['type_issues']:
                logger.warning(f"Column '{col_name}' has type issues: {analysis['type_issues']}")
            
        return type_analysis
    
    def _infer_sql_type(self, monday_type: str, values: List[Any]) -> str:
        """Infer the best SQL data type based on actual values"""
        
        if not values:
            return 'NVARCHAR(255)'
        
        # Convert all values to strings for analysis
        str_values = [str(v) for v in values if v is not None]
        
        if monday_type == 'item_id':
            # Check if all values are pure integers
            if all(self._is_integer(v) for v in str_values):
                return 'BIGINT'
            else:
                # Mixed or non-integer item IDs - use string
                max_len = max(len(s) for s in str_values) if str_values else 50
                return f'NVARCHAR({min(max_len + 50, 255)})'
        
        elif monday_type == 'numbers':
            # Check numeric precision needs
            if all(self._is_integer(v) for v in str_values):
                return 'BIGINT'
            else:
                return 'DECIMAL(18,4)'  # More precision for financial data
        
        elif monday_type in ['text', 'long_text']:
            max_len = max(len(s) for s in str_values) if str_values else 255
            if max_len > 4000:
                return 'NVARCHAR(MAX)'
            else:
                return f'NVARCHAR({min(max_len * 2, 4000)})'  # 2x buffer
        
        elif monday_type == 'date':
            return 'DATE'
        
        elif monday_type in ['dropdown', 'status']:
            max_len = max(len(s) for s in str_values) if str_values else 100
            return f'NVARCHAR({min(max_len + 50, 255)})'
        
        else:
            # Default for unknown types
            max_len = max(len(s) for s in str_values) if str_values else 255
            if max_len > 1000:
                return 'NVARCHAR(MAX)'
            else:
                return f'NVARCHAR({min(max_len + 100, 1000)})'
    
    def _detect_type_issues(self, monday_type: str, values: List[Any]) -> List[str]:
        """Detect potential type conversion issues"""
        issues = []
        str_values = [str(v) for v in values if v is not None]
        
        if monday_type == 'item_id':
            non_integer_count = sum(1 for v in str_values if not self._is_integer(v))
            if non_integer_count > 0:
                issues.append(f'{non_integer_count}/{len(str_values)} values are not pure integers')
        
        elif monday_type == 'numbers':
            non_numeric_count = sum(1 for v in str_values if not self._is_numeric(v))
            if non_numeric_count > 0:
                issues.append(f'{non_numeric_count}/{len(str_values)} values are not numeric')
        
        elif monday_type == 'date':
            non_date_count = sum(1 for v in str_values if not self._is_date_like(v))
            if non_date_count > 0:
                issues.append(f'{non_date_count}/{len(str_values)} values are not date-like')
        
        # Check for extremely long values
        max_len = max(len(s) for s in str_values) if str_values else 0
        if max_len > 4000:
            issues.append(f'Maximum value length: {max_len} characters')
        
        return issues
    
    def _is_integer(self, value: Any) -> bool:
        """Check if value can be converted to integer"""
        try:
            int(str(value))
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if value can be converted to float"""
        try:
            float(str(value))
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_date_like(self, value: Any) -> bool:
        """Check if value looks like a date"""
        str_val = str(value).strip()
        
        # Common date patterns
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO datetime
            r'^{"date":"[\d-]+"}$'  # Monday.com date JSON
        ]
        
        return any(re.match(pattern, str_val) for pattern in date_patterns)
    
    def generate_corrected_ddl_suggestions(self, type_analysis: Dict[str, Dict]) -> Dict[str, str]:
        """Generate corrected DDL type mappings based on analysis"""
        suggestions = {}
        
        for col_name, analysis in type_analysis.items():
            if analysis['type_issues']:
                suggestions[col_name] = analysis['recommended_sql_type']
        
        return suggestions

def validate_and_fix_board_types(board_id: int, monday_token: str) -> Dict[str, Any]:
    """
    Main function to validate and fix data types for a Monday.com board
    
    Returns:
        Dictionary with analysis results and correction suggestions
    """
    logger.info(f"Starting data type validation for board {board_id}")
    
    # Initialize analyzer
    analyzer = DataTypeAnalyzer(monday_token)
    
    # Sample board data
    column_samples = analyzer.sample_board_data(board_id, sample_size=100)
    
    # Analyze types
    type_analysis = analyzer.analyze_column_types(column_samples)
    
    # Generate corrections
    corrections = analyzer.generate_corrected_ddl_suggestions(type_analysis)
    
    # Summary report
    total_columns = len(type_analysis)
    problematic_columns = len(corrections)
    
    report = {
        'board_id': board_id,
        'total_columns': total_columns,
        'problematic_columns': problematic_columns,
        'success_rate': (total_columns - problematic_columns) / total_columns if total_columns > 0 else 0,
        'type_analysis': type_analysis,
        'recommended_corrections': corrections,
        'validation_timestamp': datetime.now().isoformat()
    }
    
    logger.info(f"Data type validation completed: {problematic_columns}/{total_columns} columns need corrections")
    
    return report

if __name__ == "__main__":
    # Test with Customer Master Schedule board
    import os
    import sys
    
    # Add utils for config loading
    sys.path.insert(0, str(find_repo_root() / "utils"))
    import db_helper as db
    
    config = db.load_config()
    monday_token = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
    
    if not monday_token:
        print("❌ Monday.com API token not found")
        sys.exit(1)
    
    # Test validation
    report = validate_and_fix_board_types(9200517329, monday_token)
    
    print("\n🔍 DATA TYPE VALIDATION REPORT")
    print("=" * 50)
    print(f"Board ID: {report['board_id']}")
    print(f"Total Columns: {report['total_columns']}")
    print(f"Problematic Columns: {report['problematic_columns']}")
    print(f"Success Rate: {report['success_rate']:.1%}")
    
    if report['recommended_corrections']:
        print(f"\n⚠️ RECOMMENDED TYPE CORRECTIONS:")
        for col_name, sql_type in report['recommended_corrections'].items():
            issues = report['type_analysis'][col_name]['type_issues']
            print(f"  • {col_name}: {sql_type}")
            print(f"    Issues: {', '.join(issues)}")
    else:
        print("\n✅ No type corrections needed!")
