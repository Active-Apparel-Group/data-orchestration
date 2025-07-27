"""
DDL Schema Foundation Validation Script
Purpose: Validate all DDL table definitions against current mapping and Monday.com board metadata
Location: tests/debug/validate_ddl_schema_foundation.py

This script implements Phase 1 of the comprehensive mapping expansion plan:
1. Extract all column definitions from DDL files
2. Cross-reference with current mapping file
3. Identify Monday.com board columns available for mapping
4. Document schema alignment issues
"""
import sys
from pathlib import Path
import yaml
import json
import pandas as pd
import re
from typing import Dict, List, Any

# Standard import pattern - use this in ALL scripts
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import from utils/ - PRODUCTION PATTERN
import logger_helper

def extract_ddl_columns(ddl_file_path: str) -> List[Dict[str, Any]]:
    """Extract column definitions from DDL SQL file"""
    logger = logger_helper.get_logger(__name__)
    columns = []
    
    try:
        with open(ddl_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract CREATE TABLE section
        create_table_match = re.search(r'CREATE TABLE.*?\((.*?)\);', content, re.DOTALL | re.IGNORECASE)
        if not create_table_match:
            logger.warning(f"No CREATE TABLE found in {ddl_file_path}")
            return columns
        
        table_content = create_table_match.group(1)
        
        # Extract column definitions - handle brackets in column names
        column_pattern = r'\[([^\]]+)\]\s+([^\s,]+)(?:\s+([^,\n]+))?'
        matches = re.findall(column_pattern, table_content)
        
        for match in matches:
            column_name = match[0]
            data_type = match[1]
            constraints = match[2] if len(match) > 2 else ""
            
            # Skip constraint lines
            if column_name.upper() in ['PRIMARY', 'FOREIGN', 'CONSTRAINT', 'INDEX']:
                continue
                
            columns.append({
                'column_name': column_name,
                'data_type': data_type,
                'constraints': constraints.strip(),
                'source_file': Path(ddl_file_path).name
            })
        
        logger.info(f"Extracted {len(columns)} columns from {Path(ddl_file_path).name}")
        return columns
        
    except Exception as e:
        logger.error(f"Error extracting columns from {ddl_file_path}: {e}")
        return []

def load_monday_board_metadata(metadata_file: str) -> List[Dict[str, Any]]:
    """Load Monday.com board column metadata"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        columns = []
        for col in metadata.get('columns', []):
            columns.append({
                'monday_id': col.get('monday_id'),
                'monday_title': col.get('monday_title'),
                'monday_type': col.get('monday_type'),
                'sql_column': col.get('sql_column'),
                'sql_type': col.get('sql_type'),
                'extraction_field': col.get('extraction_field'),
                'is_system_field': col.get('is_system_field', False)
            })
        
        logger.info(f"Loaded {len(columns)} Monday.com columns from metadata")
        return columns
        
    except Exception as e:
        logger.error(f"Error loading Monday.com metadata: {e}")
        return []

def load_current_mapping(mapping_file: str) -> Dict[str, Any]:
    """Load current mapping configuration"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = yaml.safe_load(f)
        
        logger.info(f"Loaded current mapping configuration")
        return mapping
        
    except Exception as e:
        logger.error(f"Error loading mapping file: {e}")
        return {}

def analyze_schema_coverage(ddl_columns: List[Dict], monday_columns: List[Dict], mapping: Dict) -> Dict[str, Any]:
    """Analyze mapping coverage and schema alignment"""
    logger = logger_helper.get_logger(__name__)
    
    # Extract mapped fields from current mapping
    mapped_fields = set()
    
    # Get direct mappings
    if 'direct_mappings' in mapping:
        for field_map in mapping['direct_mappings']:
            if 'source_field' in field_map:
                mapped_fields.add(field_map['source_field'])
    
    # Get exact matches
    if 'exact_matches' in mapping:
        for field_map in mapping['exact_matches']:
            if 'source_field' in field_map:
                mapped_fields.add(field_map['source_field'])
    
    # Get computed fields source fields
    if 'computed_fields' in mapping:
        for field_map in mapping['computed_fields']:
            if 'source_fields' in field_map:
                for source_field in field_map['source_fields']:
                    mapped_fields.add(source_field)
    
    # Analyze coverage
    ddl_column_names = {col['column_name'] for col in ddl_columns}
    monday_column_names = {col['monday_title'] for col in monday_columns if col['monday_title']}
    
    # Calculate coverage metrics
    total_ddl_columns = len(ddl_column_names)
    mapped_ddl_columns = len(mapped_fields.intersection(ddl_column_names))
    unmapped_ddl_columns = ddl_column_names - mapped_fields
    
    total_monday_columns = len(monday_column_names)
    available_monday_columns = monday_column_names - mapped_fields
    
    analysis = {
        'coverage_metrics': {
            'total_ddl_columns': total_ddl_columns,
            'mapped_ddl_columns': mapped_ddl_columns,
            'mapping_coverage_percent': round((mapped_ddl_columns / total_ddl_columns) * 100, 2) if total_ddl_columns > 0 else 0,
            'unmapped_ddl_columns_count': len(unmapped_ddl_columns),
            'total_monday_columns': total_monday_columns,
            'available_monday_columns_count': len(available_monday_columns)
        },
        'unmapped_ddl_columns': sorted(list(unmapped_ddl_columns)),
        'available_monday_columns': sorted(list(available_monday_columns)),
        'mapped_fields': sorted(list(mapped_fields)),
        'schema_alignment_issues': []
    }
    
    # Check for schema alignment issues
    for mapped_field in mapped_fields:
        if mapped_field not in ddl_column_names:
            analysis['schema_alignment_issues'].append({
                'issue': 'mapped_field_not_in_ddl',
                'field': mapped_field,
                'description': f"Field '{mapped_field}' is mapped but not found in DDL schema"
            })
    
    logger.info(f"Schema analysis complete: {analysis['coverage_metrics']['mapping_coverage_percent']}% coverage")
    return analysis

def generate_expansion_recommendations(analysis: Dict, ddl_columns: List[Dict], monday_columns: List[Dict]) -> List[Dict]:
    """Generate recommendations for mapping expansion"""
    logger = logger_helper.get_logger(__name__)
    
    recommendations = []
    
    # High-priority direct mappings (exact name matches)
    ddl_names = {col['column_name'] for col in ddl_columns}
    monday_names = {col['monday_title'] for col in monday_columns if col['monday_title']}
    
    exact_matches = ddl_names.intersection(monday_names)
    for field_name in exact_matches:
        if field_name not in analysis['mapped_fields']:
            # Find the Monday.com column details
            monday_col = next((col for col in monday_columns if col['monday_title'] == field_name), None)
            if monday_col:
                recommendations.append({
                    'priority': 'HIGH',
                    'type': 'exact_match',
                    'source_field': field_name,
                    'target_field': field_name,
                    'monday_id': monday_col['monday_id'],
                    'monday_type': monday_col['monday_type'],
                    'justification': 'Exact field name match between DDL and Monday.com'
                })
    
    # Medium-priority similar name mappings (fuzzy matching)
    for ddl_col in ddl_columns:
        ddl_name = ddl_col['column_name']
        if ddl_name not in analysis['mapped_fields']:
            # Look for similar Monday.com columns
            for monday_col in monday_columns:
                monday_name = monday_col['monday_title'] or ''
                if monday_name and monday_name not in analysis['mapped_fields']:
                    # Simple similarity check (contains/partial match)
                    if (ddl_name.lower() in monday_name.lower() or 
                        monday_name.lower() in ddl_name.lower() or
                        ddl_name.replace(' ', '').lower() == monday_name.replace(' ', '').lower()):
                        
                        recommendations.append({
                            'priority': 'MEDIUM',
                            'type': 'similar_match',
                            'source_field': ddl_name,
                            'target_field': monday_name,
                            'monday_id': monday_col['monday_id'],
                            'monday_type': monday_col['monday_type'],
                            'justification': f'Similar field names: "{ddl_name}" -> "{monday_name}"'
                        })
                        break  # Only suggest first match
    
    logger.info(f"Generated {len(recommendations)} expansion recommendations")
    return recommendations

def main():
    """Main validation function"""
    logger = logger_helper.get_logger(__name__)
    logger.info("=== DDL Schema Foundation Validation Started ===")
    
    # File paths
    repo_root = find_repo_root()
    ddl_folder = repo_root / "sql" / "ddl" / "tables" / "orders"
    mapping_file = repo_root / "sql" / "mappings" / "orders-unified-comprehensive-mapping.yaml"
    monday_metadata_file = repo_root / "dev" / "monday-boards-dynamic" / "metadata" / "boards" / "board_9200517329_metadata.json"
    
    # Extract DDL columns from all relevant files
    ddl_files = [
        ddl_folder / "dbo_ORDERS_UNIFIED_ddl.sql",
        ddl_folder / "staging" / "stg_mon_custmasterschedule.sql",
        ddl_folder / "dbo_mon_custmasterschedule.sql"
    ]
    
    all_ddl_columns = []
    for ddl_file in ddl_files:
        if ddl_file.exists():
            columns = extract_ddl_columns(str(ddl_file))
            all_ddl_columns.extend(columns)
        else:
            logger.warning(f"DDL file not found: {ddl_file}")
    
    # Load Monday.com metadata
    monday_columns = load_monday_board_metadata(str(monday_metadata_file))
    
    # Load current mapping
    current_mapping = load_current_mapping(str(mapping_file))
    
    # Perform analysis
    analysis = analyze_schema_coverage(all_ddl_columns, monday_columns, current_mapping)
    
    # Generate expansion recommendations
    recommendations = generate_expansion_recommendations(analysis, all_ddl_columns, monday_columns)
    
    # Generate comprehensive report
    print("\n" + "="*80)
    print("DDL SCHEMA FOUNDATION VALIDATION REPORT")
    print("="*80)
    
    print(f"\n📊 COVERAGE METRICS:")
    metrics = analysis['coverage_metrics']
    print(f"  • Total DDL Columns: {metrics['total_ddl_columns']}")
    print(f"  • Currently Mapped: {metrics['mapped_ddl_columns']} ({metrics['mapping_coverage_percent']}%)")
    print(f"  • Unmapped DDL Columns: {metrics['unmapped_ddl_columns_count']}")
    print(f"  • Available Monday.com Columns: {metrics['available_monday_columns_count']}")
    
    if analysis['schema_alignment_issues']:
        print(f"\n🚨 SCHEMA ALIGNMENT ISSUES ({len(analysis['schema_alignment_issues'])}):")
        for issue in analysis['schema_alignment_issues']:
            print(f"  • {issue['description']}")
    
    print(f"\n📋 HIGH-PRIORITY EXPANSION RECOMMENDATIONS ({len([r for r in recommendations if r['priority'] == 'HIGH'])}):")
    for rec in recommendations:
        if rec['priority'] == 'HIGH':
            print(f"  • {rec['source_field']} -> {rec['target_field']} ({rec['monday_id']})")
    
    print(f"\n📋 MEDIUM-PRIORITY EXPANSION RECOMMENDATIONS ({len([r for r in recommendations if r['priority'] == 'MEDIUM'])}):")
    for rec in recommendations[:10]:  # Show first 10 only
        if rec['priority'] == 'MEDIUM':
            print(f"  • {rec['source_field']} -> {rec['target_field']} ({rec['monday_id']})")
    
    print(f"\n📝 UNMAPPED DDL COLUMNS (First 20):")
    for col in sorted(analysis['unmapped_ddl_columns'])[:20]:
        print(f"  • {col}")
    
    print(f"\n📝 AVAILABLE MONDAY.COM COLUMNS (First 20):")
    for col in sorted(analysis['available_monday_columns'])[:20]:
        print(f"  • {col}")
    
    # Save detailed results
    output_file = repo_root / "tests" / "debug" / "ddl_schema_validation_results.json"
    results = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'analysis': analysis,
        'recommendations': recommendations,
        'ddl_columns': all_ddl_columns,
        'monday_columns': monday_columns
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    print(f"\n✅ Phase 1: DDL Schema Foundation Validation COMPLETE")
    print("📋 Next Step: Review recommendations and begin mapping file expansion")
    print("="*80)

if __name__ == "__main__":
    main()
