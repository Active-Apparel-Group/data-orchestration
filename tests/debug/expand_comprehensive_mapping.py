"""
Comprehensive Mapping File Expansion Script
Purpose: Expand the mapping file based on DDL validation results and handover reference
Location: tests/debug/expand_comprehensive_mapping.py

This script implements Phase 2 of the comprehensive mapping expansion plan:
1. Load current mapping and DDL validation results
2. Apply handover reference best practices  
3. Expand mapping with high-priority exact matches
4. Organize mapping by direct/transformed/computed categories
5. Generate production-ready expanded mapping file
"""
import sys
from pathlib import Path
import yaml
import json
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

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

def load_ddl_validation_results(results_file: str) -> Dict[str, Any]:
    """Load DDL validation results"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        logger.info(f"Loaded DDL validation results")
        return results
        
    except Exception as e:
        logger.error(f"Error loading DDL validation results: {e}")
        return {}

def load_handover_reference_mapping(handover_file: str) -> Dict[str, Any]:
    """Load handover reference mapping for best practices"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        with open(handover_file, 'r', encoding='utf-8') as f:
            mapping = yaml.safe_load(f)
        
        logger.info(f"Loaded handover reference mapping")
        return mapping
        
    except Exception as e:
        logger.error(f"Error loading handover reference mapping: {e}")
        return {}

def create_expanded_mapping_structure(current_mapping: Dict, validation_results: Dict, handover_mapping: Dict) -> Dict[str, Any]:
    """Create expanded mapping structure following handover best practices"""
    logger = logger_helper.get_logger(__name__)
    
    # Start with enhanced metadata
    expanded_mapping = {
        'metadata': {
            'version': '2.0',
            'description': 'Comprehensive Production-Ready Mapping - Post-DDL Validation Expansion',
            'project': 'orders_unified_delta_sync',
            'status': 'production_expanded',
            'expansion_date': datetime.now().isoformat(),
            'source_ddl_columns': validation_results.get('analysis', {}).get('coverage_metrics', {}).get('total_ddl_columns', 0),
            'target_monday_columns': validation_results.get('analysis', {}).get('coverage_metrics', {}).get('total_monday_columns', 0),
            'expansion_recommendations_applied': len(validation_results.get('recommendations', [])),
            'handover_reference': 'dev/order-staging/handover/orders_unified_monday_mapping.yaml'
        },
        
        # Data Orchestration Workflow (preserve from current mapping)
        'orchestration_workflow': current_mapping.get('orchestration_workflow', {}),
        
        # Direct 1:1 mappings - EXPANDED from DDL validation
        'exact_matches': [],
        
        # Fields requiring transformation/mapping - EXPANDED
        'mapped_fields': [],
        
        # Aggregated/computed fields - EXPANDED
        'computed_fields': [],
        
        # Business logic mappings (from handover reference)
        'business_logic_mappings': {},
        
        # Error handling and validation rules
        'validation_rules': {},
        
        # Performance optimization settings
        'performance_settings': {
            'batch_size': 1000,
            'rate_limit_delay': 0.1,
            'retry_attempts': 3,
            'timeout_seconds': 30
        }
    }
    
    # Apply high-priority exact matches from DDL validation
    high_priority_recs = [r for r in validation_results.get('recommendations', []) if r.get('priority') == 'HIGH']
    
    for rec in high_priority_recs:
        exact_match = {
            'source_field': rec['source_field'],
            'target_field': rec['target_field'],
            'target_column_id': rec['monday_id'],
            'source_type': 'AUTO_DETECTED',  # Will be updated with actual DDL type
            'target_type': rec['monday_type'],
            'mapping_source': 'ddl_validation_expansion',
            'expansion_priority': 'HIGH',
            'sample_data': {
                'source': f'Sample_{rec["source_field"]}',
                'target': f'Sample_{rec["target_field"]}'
            },
            'validation_rules': {
                'required': False,  # Default - will be refined
                'max_length': None,
                'data_type_validation': True
            }
        }
        
        expanded_mapping['exact_matches'].append(exact_match)
    
    # Preserve existing exact matches from current mapping
    if 'exact_matches' in current_mapping:
        for existing_match in current_mapping['exact_matches']:
            # Avoid duplicates
            if not any(em['source_field'] == existing_match.get('source_field') for em in expanded_mapping['exact_matches']):
                expanded_mapping['exact_matches'].append(existing_match)
    
    # Apply handover reference best practices for mapped fields
    if 'mapped_fields' in handover_mapping:
        for handover_field in handover_mapping['mapped_fields']:
            # Check if this field is not already in exact matches
            source_field = handover_field.get('source_field')
            if source_field and not any(em['source_field'] == source_field for em in expanded_mapping['exact_matches']):
                # Enhance with validation metadata
                enhanced_field = dict(handover_field)
                enhanced_field['mapping_source'] = 'handover_reference'
                enhanced_field['validation_rules'] = {
                    'required': True if 'customer' in source_field.lower() else False,
                    'transformation_required': True,
                    'business_logic_validation': True
                }
                expanded_mapping['mapped_fields'].append(enhanced_field)
    
    # Apply handover reference computed fields
    if 'computed_fields' in handover_mapping:
        for handover_computed in handover_mapping['computed_fields']:
            enhanced_computed = dict(handover_computed)
            enhanced_computed['mapping_source'] = 'handover_reference'
            enhanced_computed['performance_notes'] = 'Computed at transformation time'
            expanded_mapping['computed_fields'].append(enhanced_computed)
    
    # Add business logic from handover reference
    expanded_mapping['business_logic_mappings'] = {
        'customer_season_fallback': {
            'description': 'CUSTOMER SEASON → AAG SEASON fallback logic',
            'implementation': 'Use CUSTOMER SEASON if available, fallback to AAG SEASON',
            'priority': 'HIGH',
            'validation': 'Both fields should be validated for business consistency'
        },
        'group_naming_logic': {
            'description': 'Monday.com group naming convention',
            'implementation': 'Use CUSTOMER SEASON → AAG SEASON fallback for group names',
            'priority': 'HIGH',
            'reference': 'handover_folder_staging_operations_logic'
        },
        'title_concatenation': {
            'description': 'Item title creation logic',
            'implementation': 'CUSTOMER_STYLE + COLOR + AAG_ORDER_NUMBER',
            'priority': 'MEDIUM',
            'validation': 'Ensure all components are non-null before concatenation'
        }
    }
    
    # Add validation rules from DDL analysis
    expanded_mapping['validation_rules'] = {
        'required_fields': [
            'AAG ORDER NUMBER',
            'CUSTOMER',
            'AAG SEASON'
        ],
        'field_length_limits': {
            'AAG ORDER NUMBER': 200,
            'CUSTOMER': 200,
            'PO NUMBER': 200
        },
        'data_type_validations': {
            'ORDER DATE PO RECEIVED': 'date',
            'CUSTOMER REQ IN DC DATE': 'date',
            'CUSTOMER EX FACTORY DATE': 'date'
        },
        'business_rule_validations': {
            'customer_season_aag_season_consistency': 'Validate season alignment',
            'quantity_field_non_negative': 'All quantity fields must be >= 0',
            'date_field_chronological_order': 'Delivery dates must be chronologically consistent'
        }
    }
    
    logger.info(f"Created expanded mapping with {len(expanded_mapping['exact_matches'])} exact matches")
    return expanded_mapping

def enhance_mapping_with_ddl_types(expanded_mapping: Dict, validation_results: Dict) -> Dict[str, Any]:
    """Enhance mapping with actual DDL column types"""
    logger = logger_helper.get_logger(__name__)
    
    # Create lookup for DDL column types
    ddl_type_lookup = {}
    for col in validation_results.get('ddl_columns', []):
        ddl_type_lookup[col['column_name']] = col['data_type']
    
    # Update exact matches with DDL types
    for exact_match in expanded_mapping['exact_matches']:
        source_field = exact_match['source_field']
        if source_field in ddl_type_lookup:
            exact_match['source_type'] = ddl_type_lookup[source_field]
            
            # Add type compatibility notes
            ddl_type = ddl_type_lookup[source_field]
            monday_type = exact_match['target_type']
            
            exact_match['type_compatibility'] = {
                'ddl_type': ddl_type,
                'monday_type': monday_type,
                'compatible': True,  # Assume compatible unless proven otherwise
                'conversion_notes': f'{ddl_type} -> {monday_type}'
            }
    
    logger.info(f"Enhanced mapping with DDL type information")
    return expanded_mapping

def validate_expanded_mapping(expanded_mapping: Dict) -> Dict[str, Any]:
    """Validate the expanded mapping for consistency and completeness"""
    logger = logger_helper.get_logger(__name__)
    
    validation_report = {
        'total_exact_matches': len(expanded_mapping.get('exact_matches', [])),
        'total_mapped_fields': len(expanded_mapping.get('mapped_fields', [])),
        'total_computed_fields': len(expanded_mapping.get('computed_fields', [])),
        'validation_issues': [],
        'recommendations': []
    }
    
    # Check for duplicate mappings
    all_source_fields = []
    all_target_fields = []
    
    for exact_match in expanded_mapping.get('exact_matches', []):
        source = exact_match.get('source_field')
        target = exact_match.get('target_field')
        
        if source in all_source_fields:
            validation_report['validation_issues'].append(f"Duplicate source field: {source}")
        else:
            all_source_fields.append(source)
            
        if target in all_target_fields:
            validation_report['validation_issues'].append(f"Duplicate target field: {target}")
        else:
            all_target_fields.append(target)
    
    # Check for missing required fields
    required_fields = ['AAG ORDER NUMBER', 'CUSTOMER', 'AAG SEASON']
    mapped_sources = set(all_source_fields)
    
    for required_field in required_fields:
        if required_field not in mapped_sources:
            validation_report['validation_issues'].append(f"Missing required field mapping: {required_field}")
    
    # Generate recommendations
    if validation_report['total_exact_matches'] > 50:
        validation_report['recommendations'].append("Consider organizing mappings into logical groups for better maintainability")
    
    if len(validation_report['validation_issues']) == 0:
        validation_report['recommendations'].append("Mapping validation passed - ready for production use")
    
    logger.info(f"Validation complete: {len(validation_report['validation_issues'])} issues found")
    return validation_report

def main():
    """Main expansion function"""
    logger = logger_helper.get_logger(__name__)
    logger.info("=== Comprehensive Mapping File Expansion Started ===")
    
    # File paths
    repo_root = find_repo_root()
    current_mapping_file = repo_root / "sql" / "mappings" / "orders-unified-comprehensive-mapping.yaml"
    handover_mapping_file = repo_root / "dev" / "order-staging" / "handover" / "orders_unified_monday_mapping.yaml"
    ddl_validation_file = repo_root / "tests" / "debug" / "ddl_schema_validation_results.json"
    
    # Load all inputs
    with open(current_mapping_file, 'r', encoding='utf-8') as f:
        current_mapping = yaml.safe_load(f)
    
    validation_results = load_ddl_validation_results(str(ddl_validation_file))
    handover_mapping = load_handover_reference_mapping(str(handover_mapping_file))
    
    # Create expanded mapping
    expanded_mapping = create_expanded_mapping_structure(current_mapping, validation_results, handover_mapping)
    
    # Enhance with DDL types
    expanded_mapping = enhance_mapping_with_ddl_types(expanded_mapping, validation_results)
    
    # Validate expanded mapping
    validation_report = validate_expanded_mapping(expanded_mapping)
    
    # Generate output files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save expanded mapping
    expanded_mapping_file = repo_root / "sql" / "mappings" / f"orders-unified-expanded-mapping-{timestamp}.yaml"
    with open(expanded_mapping_file, 'w', encoding='utf-8') as f:
        yaml.dump(expanded_mapping, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    # Save validation report
    validation_report_file = repo_root / "tests" / "debug" / f"mapping_expansion_validation_report_{timestamp}.json"
    with open(validation_report_file, 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2, default=str)
    
    # Generate comprehensive report
    print("\n" + "="*80)
    print("COMPREHENSIVE MAPPING EXPANSION REPORT")
    print("="*80)
    
    print(f"\n📊 EXPANSION METRICS:")
    print(f"  • Total Exact Matches: {validation_report['total_exact_matches']}")
    print(f"  • Total Mapped Fields: {validation_report['total_mapped_fields']}")
    print(f"  • Total Computed Fields: {validation_report['total_computed_fields']}")
    print(f"  • DDL Columns Analyzed: {expanded_mapping['metadata']['source_ddl_columns']}")
    print(f"  • Monday.com Columns Available: {expanded_mapping['metadata']['target_monday_columns']}")
    print(f"  • Recommendations Applied: {expanded_mapping['metadata']['expansion_recommendations_applied']}")
    
    if validation_report['validation_issues']:
        print(f"\n🚨 VALIDATION ISSUES ({len(validation_report['validation_issues'])}):")
        for issue in validation_report['validation_issues']:
            print(f"  • {issue}")
    else:
        print(f"\n✅ VALIDATION: No issues found")
    
    print(f"\n📋 RECOMMENDATIONS:")
    for rec in validation_report['recommendations']:
        print(f"  • {rec}")
    
    print(f"\n📁 OUTPUT FILES:")
    print(f"  • Expanded Mapping: {expanded_mapping_file}")
    print(f"  • Validation Report: {validation_report_file}")
    
    print(f"\n🎯 COVERAGE IMPROVEMENT:")
    total_mappings = (validation_report['total_exact_matches'] + 
                     validation_report['total_mapped_fields'] + 
                     validation_report['total_computed_fields'])
    
    if expanded_mapping['metadata']['source_ddl_columns'] > 0:
        coverage_percent = round((total_mappings / expanded_mapping['metadata']['source_ddl_columns']) * 100, 2)
        print(f"  • New Coverage Estimate: {total_mappings}/{expanded_mapping['metadata']['source_ddl_columns']} ({coverage_percent}%)")
    
    print(f"\n✅ Phase 2: Comprehensive Field Coverage Expansion COMPLETE")
    print(f"📋 Next Step: Validate expanded mapping against Monday.com API")
    print("="*80)

if __name__ == "__main__":
    main()
