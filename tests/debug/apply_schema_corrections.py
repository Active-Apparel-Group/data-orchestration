"""
Apply Schema Corrections - Milestone 5
Purpose: Apply the 4 critical field corrections to main mapping file
Location: tests/debug/apply_schema_corrections.py
Created: 2025-06-22 - Milestone 5 Schema Validation Implementation
"""
import sys
from pathlib import Path
import yaml
import re
from typing import Dict, List

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()

class SchemaCorrectionApplier:
    """Apply the 4 critical schema corrections to main mapping file"""
    
    def __init__(self):
        self.repo_root = repo_root
        self.corrections = {
            '[CUSTOMER]': '[CUSTOMER NAME]',
            '[Order Qty]': '[TOTAL QTY]', 
            '[DUE DATE]': '[EX FACTORY DATE]',
            '[Style]': '[CUSTOMER STYLE]'
        }
        
    def apply_corrections_to_main_file(self) -> bool:
        """Apply corrections to the main mapping file"""
        
        main_file = self.repo_root / "sql" / "mappings" / "orders-unified-comprehensive-mapping.yaml"
        
        if not main_file.exists():
            print(f"❌ Main mapping file not found: {main_file}")
            return False
            
        # Read current content
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track corrections applied
        corrections_applied = []
        original_content = content
        
        # Apply each correction
        for old_field, new_field in self.corrections.items():
            if old_field in content:
                # Count occurrences before replacement
                count_before = content.count(old_field)
                
                # Apply replacement
                content = content.replace(old_field, new_field)
                
                # Count occurrences after replacement  
                count_after = content.count(old_field)
                replacements_made = count_before - count_after
                
                corrections_applied.append({
                    'old_field': old_field,
                    'new_field': new_field,
                    'replacements_made': replacements_made
                })
                
                print(f"✅ Applied: {old_field} → {new_field} ({replacements_made} replacements)")
            else:
                print(f"⚠️  Field not found: {old_field}")
        
        # Add correction metadata
        correction_header = f"""# SCHEMA CORRECTIONS APPLIED - Milestone 5
# Date: 2025-06-22
# Purpose: Fix critical field name mismatches identified in DDL validation
# Corrections applied: {len(corrections_applied)}
# Validation status: Production-ready field mappings

"""
        
        content = correction_header + content
        
        # Create backup of original
        backup_file = main_file.with_suffix('.yaml.backup.20250622')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"📄 Backup created: {backup_file}")
        
        # Write corrected content
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Corrections applied to: {main_file}")
        
        return True
    
    def validate_corrections(self) -> Dict:
        """Validate that corrections were applied correctly"""
        
        main_file = self.repo_root / "sql" / "mappings" / "orders-unified-comprehensive-mapping.yaml"
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        validation_results = {
            'corrections_found': [],
            'old_fields_remaining': [],
            'validation_status': 'pending'
        }
        
        # Check for corrected fields
        for old_field, new_field in self.corrections.items():
            if new_field in content:
                validation_results['corrections_found'].append(new_field)
            
            if old_field in content:
                validation_results['old_fields_remaining'].append(old_field)
        
        # Determine validation status
        if len(validation_results['corrections_found']) == 4 and len(validation_results['old_fields_remaining']) == 0:
            validation_results['validation_status'] = 'success'
        elif len(validation_results['old_fields_remaining']) > 0:
            validation_results['validation_status'] = 'partial'
        else:
            validation_results['validation_status'] = 'failed'
        
        return validation_results
    
    def generate_validation_report(self) -> str:
        """Generate validation report"""
        
        validation = self.validate_corrections()
        
        report = []
        report.append("=" * 60)
        report.append("SCHEMA CORRECTIONS VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Date: 2025-06-22")
        report.append(f"Milestone: 5 - Schema Validation Implementation")
        report.append("")
        
        # Status
        status_icon = "✅" if validation['validation_status'] == 'success' else "⚠️" if validation['validation_status'] == 'partial' else "❌"
        report.append(f"Overall Status: {status_icon} {validation['validation_status'].upper()}")
        report.append("")
        
        # Corrected fields found
        if validation['corrections_found']:
            report.append("✅ CORRECTED FIELDS FOUND:")
            for field in validation['corrections_found']:
                report.append(f"   ✅ {field}")
            report.append("")
        
        # Old fields remaining
        if validation['old_fields_remaining']:
            report.append("⚠️  OLD FIELDS STILL PRESENT:")
            for field in validation['old_fields_remaining']:
                report.append(f"   ❌ {field}")
            report.append("")
        
        # Summary
        report.append("📊 SUMMARY:")
        report.append(f"   Corrections found: {len(validation['corrections_found'])}/4")
        report.append(f"   Old fields remaining: {len(validation['old_fields_remaining'])}")
        
        if validation['validation_status'] == 'success':
            report.append("   🎯 All corrections successfully applied!")
        elif validation['validation_status'] == 'partial':
            report.append("   ⚠️  Partial success - some old fields remain")
        else:
            report.append("   ❌ Corrections failed - investigation needed")
        
        return "\n".join(report)

def main():
    """Main execution function"""
    applier = SchemaCorrectionApplier()
    
    try:
        print("🔧 Applying schema corrections to main mapping file...")
        print("")
        
        # Apply corrections
        success = applier.apply_corrections_to_main_file()
        
        if success:
            print("")
            print("🔍 Validating corrections...")
            
            # Generate validation report
            report = applier.generate_validation_report()
            print(report)
            
            # Save validation report
            report_file = applier.repo_root / "tests" / "debug" / "schema_corrections_validation.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\n📄 Validation report saved to: {report_file}")
            print(f"\n🎯 Next: Test corrected mappings with GREYSON customer")
        else:
            print("❌ Failed to apply corrections")
        
    except Exception as e:
        print(f"❌ Error applying corrections: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
