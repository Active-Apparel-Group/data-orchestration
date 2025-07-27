#!/usr/bin/envimport sys
from pathlib import Path
import tomli as toml
from typing import Dict, List, Any
"""
TOML Configuration Validation and Logic Review
=============================================

PURPOSE: Review TOML configuration for logic issues and validate migration strategy alignment
- Environment configuration validation
- Database table mapping verification  
- Migration strategy alignment check
- Logic consistency validation

Based on user request to "review and update any logic issues with TOML file"
"""

import sys
from pathlib import Path
import tomli
from typing import Dict, List, Any

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

class TOMLConfigurationValidator:
    """
    Comprehensive TOML configuration validation for production migration
    
    VALIDATION AREAS:
    1. Environment configuration (dev/production alignment)
    2. Database table mapping (source/target consistency)
    3. Migration strategy compatibility
    4. Logic consistency across sections
    """
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.logger = logger  # Use logger directly
        
        # Load TOML configuration
        with open(self.config_path, 'rb') as f:
            self.toml_config = toml.load(f)
        
        # Load parsed configuration
        self.config = DeltaSyncConfig.from_toml(str(self.config_path))
        
        self.validation_issues = []
        self.validation_warnings = []
        self.validation_recommendations = []
    
    def validate_complete_configuration(self) -> Dict[str, Any]:
        """
        Execute comprehensive TOML configuration validation
        
        Returns:
            Dictionary with validation results and recommendations
        """
        self.logger.info("🔍 Starting TOML Configuration Validation")
        
        # Validation categories
        validations = [
            ('Environment Configuration', self._validate_environment_configuration),
            ('Database Table Mapping', self._validate_database_table_mapping),
            ('Migration Strategy Alignment', self._validate_migration_strategy_alignment),
            ('Monday.com Configuration', self._validate_monday_configuration),
            ('Transformation Logic', self._validate_transformation_logic),
            ('Column Mapping Consistency', self._validate_column_mapping_consistency)
        ]
        
        validation_results = {}
        
        for category, validation_func in validations:
            self.logger.info(f"   🔧 Validating: {category}")
            try:
                result = validation_func()
                validation_results[category] = result
                
                if result.get('issues'):
                    self.validation_issues.extend(result['issues'])
                if result.get('warnings'):
                    self.validation_warnings.extend(result['warnings'])
                if result.get('recommendations'):
                    self.validation_recommendations.extend(result['recommendations'])
                    
            except Exception as e:
                self.logger.error(f"   ❌ Validation failed for {category}: {e}")
                validation_results[category] = {
                    'success': False,
                    'error': str(e),
                    'issues': [f"Validation failed: {e}"]
                }
        
        # Compile overall results
        total_issues = len(self.validation_issues)
        total_warnings = len(self.validation_warnings)
        total_recommendations = len(self.validation_recommendations)
        
        overall_success = (total_issues == 0)
        
        result = {
            'success': overall_success,
            'total_issues': total_issues,
            'total_warnings': total_warnings,
            'total_recommendations': total_recommendations,
            'validation_results': validation_results,
            'issues': self.validation_issues,
            'warnings': self.validation_warnings,
            'recommendations': self.validation_recommendations,
            'migration_readiness': self._assess_migration_readiness()
        }
        
        self._log_validation_summary(result)
        return result
    
    def _validate_environment_configuration(self) -> Dict[str, Any]:
        """Validate environment configuration (dev/production)."""
        issues = []
        warnings = []
        recommendations = []
        
        # Check environment sections exist
        env_dev = self.toml_config.get('environment', {}).get('development', {})
        env_prod = self.toml_config.get('environment', {}).get('production', {})
        
        if not env_dev:
            issues.append("Missing [environment.development] section")
        if not env_prod:
            issues.append("Missing [environment.production] section")
        
        # Validate table mappings are consistent
        dev_tables = {
            'source': env_dev.get('source_table'),
            'target': env_dev.get('target_table'),
            'lines': env_dev.get('lines_table'),
            'database': env_dev.get('database')
        }
        
        prod_tables = {
            'source': env_prod.get('source_table'),
            'target': env_prod.get('target_table'),
            'lines': env_prod.get('lines_table'),
            'database': env_prod.get('database')
        }
        
        # Check for migration strategy alignment
        if dev_tables['source'] != prod_tables['source']:
            warnings.append(f"Source table differs: dev={dev_tables['source']}, prod={prod_tables['source']}")
        
        if dev_tables['target'] != prod_tables['target']:
            recommendations.append(f"Target table alignment: dev={dev_tables['target']}, prod={prod_tables['target']} - This is expected for migration")
        
        if dev_tables['database'] != prod_tables['database']:
            issues.append(f"Database differs: dev={dev_tables['database']}, prod={prod_tables['database']}")
        
        # Validate migration strategy compatibility
        expected_source = "swp_ORDER_LIST_SYNC"  # User's migration strategy
        expected_target_prod = "FACT_ORDER_LIST"  # Production target
        
        if prod_tables['source'] != expected_source:
            issues.append(f"Production source table should be '{expected_source}' for migration strategy, got '{prod_tables['source']}'")
        
        if prod_tables['target'] != expected_target_prod:
            issues.append(f"Production target table should be '{expected_target_prod}' for migration strategy, got '{prod_tables['target']}'")
        
        return {
            'success': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendations': recommendations,
            'dev_tables': dev_tables,
            'prod_tables': prod_tables
        }
    
    def _validate_database_table_mapping(self) -> Dict[str, Any]:
        """Validate database table mapping consistency."""
        issues = []
        warnings = []
        recommendations = []
        
        # Check essential columns configuration
        essential_cols = self.toml_config.get('database', {}).get('essential_columns', [])
        
        required_essential = [
            "AAG ORDER NUMBER",
            "CUSTOMER NAME", 
            "PO NUMBER",
            "CUSTOMER STYLE"
        ]
        
        for col in required_essential:
            if col not in essential_cols:
                issues.append(f"Missing essential column: '{col}'")
        
        # Check sync columns configuration
        sync_headers = self.toml_config.get('database', {}).get('sync_columns_headers', [])
        sync_lines = self.toml_config.get('database', {}).get('sync_columns_lines', [])
        
        required_sync_headers = [
            "action_type",
            "sync_state", 
            "monday_item_id",
            "sync_attempted_at",
            "sync_completed_at"
        ]
        
        for col in required_sync_headers:
            if col not in sync_headers:
                warnings.append(f"Missing sync header column: '{col}'")
        
        # Validate size detection configuration
        size_config = self.toml_config.get('size_detection', {})
        if not size_config.get('start_after'):
            issues.append("Missing size_detection.start_after configuration")
        if not size_config.get('end_before'):
            issues.append("Missing size_detection.end_before configuration")
        
        # Check transformation configuration
        group_transform = self.toml_config.get('database', {}).get('group_name_transformation', {})
        item_transform = self.toml_config.get('database', {}).get('item_name_transformation', {})
        
        if group_transform.get('enabled') and not group_transform.get('primary_columns'):
            issues.append("Group transformation enabled but missing primary_columns")
        
        if item_transform.get('enabled') and not item_transform.get('columns'):
            issues.append("Item transformation enabled but missing columns")
        
        return {
            'success': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendations': recommendations,
            'essential_columns_count': len(essential_cols),
            'sync_headers_count': len(sync_headers),
            'sync_lines_count': len(sync_lines)
        }
    
    def _validate_migration_strategy_alignment(self) -> Dict[str, Any]:
        """Validate configuration aligns with user's migration strategy."""
        issues = []
        warnings = []
        recommendations = []
        
        # User's strategy: Load ALL FACT_ORDER_LIST → Delete NEW orders → Insert to swp_ORDER_LIST_SYNC → Run pipeline
        
        # Check if configuration supports this strategy
        prod_config = self.toml_config.get('environment', {}).get('production', {})
        
        # Target should be FACT_ORDER_LIST (where we load ALL orders)
        target_table = prod_config.get('target_table')
        if target_table != 'FACT_ORDER_LIST':
            issues.append(f"Target table should be 'FACT_ORDER_LIST' for migration strategy, got '{target_table}'")
        
        # Source should be swp_ORDER_LIST_SYNC (where we insert NEW orders)
        source_table = prod_config.get('source_table')
        if source_table != 'swp_ORDER_LIST_SYNC':
            issues.append(f"Source table should be 'swp_ORDER_LIST_SYNC' for migration strategy, got '{source_table}'")
        
        # Check if transformation logic is non-destructive
        # (merge_orchestrator.py should only transform, not truncate)
        phase_config = self.toml_config.get('phase', {})
        current_phase = phase_config.get('current', '')
        
        if 'truncate' in current_phase.lower() or 'delete' in current_phase.lower():
            warnings.append(f"Current phase '{current_phase}' may include destructive operations")
        
        # Validate Monday.com configuration supports NEW orders only
        monday_prod = self.toml_config.get('monday', {}).get('production', {})
        if not monday_prod:
            warnings.append("Missing Monday.com production configuration")
        
        # Check if auto-create groups is enabled (needed for NEW orders)
        group_creation = self.toml_config.get('monday', {}).get('groups', {})
        if not group_creation.get('auto_create'):
            recommendations.append("Consider enabling monday.groups.auto_create for NEW order processing")
        
        return {
            'success': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendations': recommendations,
            'strategy_alignment': {
                'target_table_correct': target_table == 'FACT_ORDER_LIST',
                'source_table_correct': source_table == 'swp_ORDER_LIST_SYNC',
                'non_destructive_approach': 'truncate' not in current_phase.lower()
            }
        }
    
    def _validate_monday_configuration(self) -> Dict[str, Any]:
        """Validate Monday.com configuration."""
        issues = []
        warnings = []
        recommendations = []
        
        # Check development vs production board configuration
        monday_dev = self.toml_config.get('monday', {}).get('development', {})
        monday_prod = self.toml_config.get('monday', {}).get('production', {})
        
        if not monday_dev.get('board_id'):
            issues.append("Missing development board_id")
        if not monday_prod.get('board_id'):
            issues.append("Missing production board_id")
        
        # Validate column mappings exist
        dev_headers = self.toml_config.get('monday', {}).get('column_mapping', {}).get('development', {}).get('headers', {})
        prod_headers = self.toml_config.get('monday', {}).get('column_mapping', {}).get('production', {}).get('headers', {})
        
        if not dev_headers:
            issues.append("Missing development header column mappings")
        if not prod_headers:
            issues.append("Missing production header column mappings")
        
        # Check for essential column mappings
        essential_mappings = [
            "AAG ORDER NUMBER",
            "CUSTOMER NAME",
            "PO NUMBER",
            "CUSTOMER STYLE"
        ]
        
        for essential in essential_mappings:
            if essential not in prod_headers:
                issues.append(f"Missing production mapping for essential column: '{essential}'")
        
        # Validate rate limiting configuration
        rate_limits = self.toml_config.get('monday', {}).get('rate_limits', {})
        if not rate_limits.get('group_batch_size'):
            warnings.append("Missing rate_limits.group_batch_size - using default")
        
        return {
            'success': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendations': recommendations,
            'dev_mappings_count': len(dev_headers),
            'prod_mappings_count': len(prod_headers)
        }
    
    def _validate_transformation_logic(self) -> Dict[str, Any]:
        """Validate transformation logic configuration."""
        issues = []
        warnings = []
        recommendations = []
        
        # Check group name transformation
        group_config = self.toml_config.get('database', {}).get('group_name_transformation', {})
        
        if group_config.get('enabled'):
            primary_cols = group_config.get('primary_columns', [])
            fallback_cols = group_config.get('fallback_columns', [])
            
            if len(primary_cols) != 2:
                issues.append(f"Group transformation primary_columns should have 2 elements, got {len(primary_cols)}")
            
            if len(fallback_cols) != 2:
                issues.append(f"Group transformation fallback_columns should have 2 elements, got {len(fallback_cols)}")
            
            # Validate columns exist in schema
            expected_cols = ["CUSTOMER NAME", "CUSTOMER SEASON", "AAG SEASON"]
            all_cols = primary_cols + fallback_cols
            
            for col in all_cols:
                if col not in expected_cols:
                    warnings.append(f"Unexpected column in group transformation: '{col}'")
        
        # Check item name transformation
        item_config = self.toml_config.get('database', {}).get('item_name_transformation', {})
        
        if item_config.get('enabled'):
            columns = item_config.get('columns', [])
            
            if len(columns) != 3:
                issues.append(f"Item transformation columns should have 3 elements, got {len(columns)}")
            
            expected_item_cols = ["CUSTOMER STYLE", "CUSTOMER COLOUR DESCRIPTION", "AAG ORDER NUMBER"]
            for col in columns:
                if col not in expected_item_cols:
                    warnings.append(f"Unexpected column in item transformation: '{col}'")
        
        return {
            'success': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendations': recommendations,
            'group_transformation_enabled': group_config.get('enabled', False),
            'item_transformation_enabled': item_config.get('enabled', False)
        }
    
    def _validate_column_mapping_consistency(self) -> Dict[str, Any]:
        """Validate column mapping consistency across environments."""
        issues = []
        warnings = []
        recommendations = []
        
        # Compare development vs production mappings
        dev_headers = self.toml_config.get('monday', {}).get('column_mapping', {}).get('development', {}).get('headers', {})
        prod_headers = self.toml_config.get('monday', {}).get('column_mapping', {}).get('production', {}).get('headers', {})
        
        # Check if essential columns have consistent mappings
        essential_columns = [
            "AAG ORDER NUMBER",
            "CUSTOMER NAME",
            "PO NUMBER",
            "CUSTOMER STYLE",
            "CUSTOMER COLOUR DESCRIPTION"
        ]
        
        for col in essential_columns:
            dev_mapping = dev_headers.get(col)
            prod_mapping = prod_headers.get(col)
            
            if dev_mapping != prod_mapping:
                warnings.append(f"Column '{col}' has different mappings: dev='{dev_mapping}', prod='{prod_mapping}'")
        
        # Check for missing mappings in either environment
        dev_only = set(dev_headers.keys()) - set(prod_headers.keys())
        prod_only = set(prod_headers.keys()) - set(dev_headers.keys())
        
        if dev_only:
            recommendations.append(f"Development-only columns: {list(dev_only)}")
        if prod_only:
            recommendations.append(f"Production-only columns: {list(prod_only)}")
        
        return {
            'success': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendations': recommendations,
            'dev_mappings': len(dev_headers),
            'prod_mappings': len(prod_headers),
            'common_mappings': len(set(dev_headers.keys()) & set(prod_headers.keys()))
        }
    
    def _assess_migration_readiness(self) -> Dict[str, Any]:
        """Assess overall migration readiness."""
        readiness_score = 100
        blocking_issues = []
        
        # Deduct points for issues
        readiness_score -= len(self.validation_issues) * 20
        readiness_score -= len(self.validation_warnings) * 5
        
        # Check for blocking issues
        for issue in self.validation_issues:
            if any(keyword in issue.lower() for keyword in ['missing', 'should be', 'target table']):
                blocking_issues.append(issue)
        
        # Determine readiness level
        if readiness_score >= 90 and len(blocking_issues) == 0:
            readiness_level = "READY"
        elif readiness_score >= 70 and len(blocking_issues) <= 1:
            readiness_level = "MOSTLY_READY"
        elif readiness_score >= 50:
            readiness_level = "NEEDS_FIXES"
        else:
            readiness_level = "NOT_READY"
        
        return {
            'readiness_score': max(0, readiness_score),
            'readiness_level': readiness_level,
            'blocking_issues': blocking_issues,
            'ready_for_migration': (readiness_level in ["READY", "MOSTLY_READY"])
        }
    
    def _log_validation_summary(self, result: Dict[str, Any]):
        """Log comprehensive validation summary."""
        self.logger.info("📋 TOML Configuration Validation Summary")
        self.logger.info(f"   ✅ Overall Success: {result['success']}")
        self.logger.info(f"   🚨 Issues: {result['total_issues']}")
        self.logger.info(f"   ⚠️  Warnings: {result['total_warnings']}")
        self.logger.info(f"   💡 Recommendations: {result['total_recommendations']}")
        
        migration_readiness = result['migration_readiness']
        self.logger.info(f"   🎯 Migration Readiness: {migration_readiness['readiness_level']} ({migration_readiness['readiness_score']}/100)")
        
        if result['issues']:
            self.logger.info("   🚨 CRITICAL ISSUES:")
            for issue in result['issues'][:5]:  # Show first 5
                self.logger.info(f"     • {issue}")
        
        if result['warnings']:
            self.logger.info("   ⚠️  WARNINGS:")
            for warning in result['warnings'][:3]:  # Show first 3
                self.logger.info(f"     • {warning}")
        
        if result['recommendations']:
            self.logger.info("   💡 RECOMMENDATIONS:")
            for rec in result['recommendations'][:3]:  # Show first 3
                self.logger.info(f"     • {rec}")

def main():
    """Execute TOML configuration validation."""
    print("🔍 Validating TOML Configuration...")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    
    # Initialize validator
    validator = TOMLConfigurationValidator(config_path)
    
    # Execute comprehensive validation
    result = validator.validate_complete_configuration()
    
    # Display results
    print(f"\n📊 Validation Results:")
    print(f"   Success: {result['success']}")
    print(f"   Issues: {result['total_issues']}")
    print(f"   Warnings: {result['total_warnings']}")
    print(f"   Recommendations: {result['total_recommendations']}")
    
    migration_readiness = result['migration_readiness']
    print(f"\n🎯 Migration Readiness: {migration_readiness['readiness_level']}")
    print(f"   Score: {migration_readiness['readiness_score']}/100")
    print(f"   Ready: {migration_readiness['ready_for_migration']}")
    
    # Show critical issues
    if result['issues']:
        print(f"\n🚨 Critical Issues to Fix:")
        for i, issue in enumerate(result['issues'], 1):
            print(f"   {i}. {issue}")
    
    # Migration strategy recommendation
    if migration_readiness['ready_for_migration']:
        print(f"\n✅ RECOMMENDATION: Configuration is ready for production migration strategy")
    else:
        print(f"\n⚠️  RECOMMENDATION: Fix critical issues before proceeding with migration")

if __name__ == "__main__":
    main()
