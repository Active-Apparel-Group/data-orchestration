"""
Schema Validation Audit - Milestone 5
Purpose: Identify field name mismatches between YAML mapping and actual DDL
Location: tests/debug/schema_validation_audit.py
Created: 2025-06-22 - Milestone 5 Schema Validation Focus
"""
import sys
from pathlib import Path
import yaml
import re
from typing import Dict, List, Set, Tuple

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

# Import from utils/
try:
    import logger_helper
except ImportError:
    # Fallback if logger_helper not available
    import logging
    
    class FallbackLogger:
        def __init__(self, name):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(levelname)s: %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
        
        def info(self, msg): self.logger.info(msg)
        def error(self, msg): self.logger.error(msg)
        def warning(self, msg): self.logger.warning(msg)
        
        @staticmethod
        def get_logger(name):
            return FallbackLogger(name)
    
    logger_helper = FallbackLogger

class SchemaValidationAuditor:
    """Audit schema mismatches between YAML mappings and actual DDL"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.repo_root = repo_root
        self.ddl_fields = set()
        self.yaml_fields = set()
        self.mismatches = []
        
    def extract_ddl_fields(self) -> Set[str]:
        """Extract field names from actual DDL file"""
        ddl_file = self.repo_root / "sql" / "ddl" / "tables" / "orders" / "dbo_ORDERS_UNIFIED_ddl.sql"
        
        if not ddl_file.exists():
            self.logger.error(f"DDL file not found: {ddl_file}")
            return set()
            
        with open(ddl_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract field names from DDL - pattern: [FIELD NAME] TYPE
        # Looking for patterns like: [AAG ORDER NUMBER] NVARCHAR(MAX) NULL,
        field_pattern = r'\[([^\]]+)\]\s+\w+'
        matches = re.findall(field_pattern, content)
        
        # Also look for fields without brackets
        simple_pattern = r'^\s*(\w+)\s+\w+.*$'
        for line in content.split('\n'):
            if 'CREATE TABLE' in line or 'record_uuid' in line:
                continue
            simple_match = re.match(simple_pattern, line.strip())
            if simple_match and simple_match.group(1).upper() not in ['CONSTRAINT', 'PRIMARY', 'FOREIGN']:
                matches.append(simple_match.group(1))
        
        self.ddl_fields = set(matches)
        self.logger.info(f"Extracted {len(self.ddl_fields)} fields from DDL")
        return self.ddl_fields
    
    def extract_yaml_fields(self) -> Set[str]:
        """Extract field names referenced in YAML mapping file"""
        yaml_file = self.repo_root / "sql" / "mappings" / "orders-unified-comprehensive-mapping.yaml"
        
        if not yaml_file.exists():
            self.logger.error(f"YAML mapping file not found: {yaml_file}")
            return set()
            
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        yaml_fields = set()
        
        # Extract from various sections
        if 'source_schema' in content:
            if 'key_fields' in content['source_schema']:
                for field in content['source_schema']['key_fields']:
                    if 'field' in field:
                        # Remove brackets if present
                        field_name = field['field'].strip('[]')
                        yaml_fields.add(field_name)
                        
            if 'working_fields' in content['source_schema']:
                for field in content['source_schema']['working_fields']:
                    if 'field' in field:
                        field_name = field['field'].strip('[]')
                        yaml_fields.add(field_name)
        
        # Extract from field_mappings
        if 'field_mappings' in content:
            for section in ['exact_matches', 'numeric_fields', 'date_fields', 'text_fields']:
                if section in content['field_mappings']:
                    for mapping_key, mapping_data in content['field_mappings'][section].items():
                        if 'source' in mapping_data:
                            field_name = mapping_data['source'].strip('[]')
                            yaml_fields.add(field_name)
        
        self.yaml_fields = yaml_fields
        self.logger.info(f"Extracted {len(self.yaml_fields)} fields from YAML mapping")
        return yaml_fields
    
    def compare_schemas(self) -> Dict[str, List[str]]:
        """Compare DDL fields with YAML fields and identify mismatches"""
        
        # Fields in YAML but not in DDL (mapping errors)
        yaml_only = self.yaml_fields - self.ddl_fields
        
        # Fields in DDL but not referenced in YAML (potential missing mappings)
        ddl_only = self.ddl_fields - self.yaml_fields
        
        # Exact matches
        matches = self.yaml_fields & self.ddl_fields
        
        results = {
            'yaml_only': list(yaml_only),
            'ddl_only': list(ddl_only), 
            'matches': list(matches),
            'total_ddl_fields': len(self.ddl_fields),
            'total_yaml_fields': len(self.yaml_fields),
            'match_percentage': len(matches) / len(self.yaml_fields) * 100 if self.yaml_fields else 0
        }
        
        return results
    
    def find_potential_matches(self, yaml_field: str, ddl_fields: Set[str]) -> List[str]:
        """Find potential DDL matches for a YAML field using fuzzy matching"""
        potential_matches = []
        
        yaml_lower = yaml_field.lower()
        
        for ddl_field in ddl_fields:
            ddl_lower = ddl_field.lower()
            
            # Check for exact match (case insensitive)
            if yaml_lower == ddl_lower:
                potential_matches.append(f"EXACT: {ddl_field}")
                continue
                
            # Check for partial matches
            if yaml_lower in ddl_lower or ddl_lower in yaml_lower:
                potential_matches.append(f"PARTIAL: {ddl_field}")
                continue
                
            # Check for similar words (split by space/underscore)
            yaml_words = set(re.split(r'[\s_]+', yaml_lower))
            ddl_words = set(re.split(r'[\s_]+', ddl_lower))
            
            overlap = yaml_words & ddl_words
            if len(overlap) > 0:
                potential_matches.append(f"SIMILAR: {ddl_field} (overlap: {overlap})")
        
        return potential_matches[:5]  # Limit to top 5 matches
    
    def generate_report(self) -> str:
        """Generate comprehensive schema validation report"""
        
        self.logger.info("Starting schema validation audit...")
        
        # Extract fields from both sources
        ddl_fields = self.extract_ddl_fields()
        yaml_fields = self.extract_yaml_fields()
        
        # Compare schemas
        comparison = self.compare_schemas()
        
        # Generate detailed report
        report = []
        report.append("=" * 80)
        report.append("SCHEMA VALIDATION AUDIT REPORT - MILESTONE 5")
        report.append("=" * 80)
        report.append(f"Generated: 2025-06-22")
        report.append(f"Purpose: Identify YAML mapping vs DDL mismatches")
        report.append("")
        
        # Summary statistics
        report.append("📊 SUMMARY STATISTICS")
        report.append("-" * 40)
        report.append(f"Total DDL Fields: {comparison['total_ddl_fields']}")
        report.append(f"Total YAML Fields: {comparison['total_yaml_fields']}")
        report.append(f"Exact Matches: {len(comparison['matches'])}")
        report.append(f"Match Percentage: {comparison['match_percentage']:.1f}%")
        report.append("")
        
        # Critical mismatches (YAML fields not in DDL)
        if comparison['yaml_only']:
            report.append("🚨 CRITICAL: YAML Fields NOT Found in DDL")
            report.append("-" * 40)
            report.append("These fields are referenced in mapping but don't exist in actual schema:")
            for field in sorted(comparison['yaml_only']):
                report.append(f"  ❌ '{field}'")
                # Try to find potential matches
                matches = self.find_potential_matches(field, ddl_fields)
                if matches:
                    report.append(f"     Potential matches: {matches[0]}")
            report.append("")
        
        # Fields in DDL but not mapped
        if comparison['ddl_only']:
            report.append("⚠️  DDL Fields Not Referenced in YAML")
            report.append("-" * 40)
            report.append("These fields exist in DDL but aren't mapped (may be intentional):")
            for field in sorted(comparison['ddl_only'])[:20]:  # Show first 20
                report.append(f"  📋 '{field}'")
            if len(comparison['ddl_only']) > 20:
                report.append(f"  ... and {len(comparison['ddl_only']) - 20} more")
            report.append("")
        
        # Successful matches
        if comparison['matches']:
            report.append("✅ SUCCESSFUL MATCHES")
            report.append("-" * 40)
            for field in sorted(comparison['matches'])[:10]:  # Show first 10
                report.append(f"  ✅ '{field}'")
            if len(comparison['matches']) > 10:
                report.append(f"  ... and {len(comparison['matches']) - 10} more matches")
            report.append("")
        
        # Sample DDL fields for reference
        report.append("📋 SAMPLE ACTUAL DDL FIELDS")
        report.append("-" * 40)
        sample_ddl = sorted(list(ddl_fields))[:15]
        for field in sample_ddl:
            report.append(f"  📋 '{field}'")
        report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 40)
        if comparison['yaml_only']:
            report.append("1. 🚨 HIGH PRIORITY: Fix YAML field name mismatches")
            report.append("   - Update mapping file with correct DDL field names")
            report.append("   - These will cause runtime mapping errors")
        
        if comparison['match_percentage'] < 90:
            report.append("2. ⚠️  Schema alignment needed")
            report.append("   - Review field mappings for completeness")
            report.append("   - Consider if unmapped DDL fields are needed")
        
        report.append("3. ✅ Create automated validation")
        report.append("   - Run this audit as part of CI/CD pipeline")
        report.append("   - Prevent future schema drift")
        report.append("")
        
        return "\n".join(report)

def main():
    """Main execution function"""
    auditor = SchemaValidationAuditor()
    
    try:
        report = auditor.generate_report()
        print(report)
        
        # Also save to file
        report_file = auditor.repo_root / "tests" / "debug" / "schema_validation_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error during schema validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
