#!/usr/bin/env python3
"""
Setup Validation - Check if environment is ready for Delta Sync V3

This script validates that all dependencies and connections are working
before starting the main implementation.
"""

import sys
from pathlib import Path

def validate_setup():
    """Validate the development environment setup"""
    
    print("🔍 Validating Delta Sync V3 Setup")
    print("=" * 50)
    
    issues = []
    warnings = []    # 1. Check utils imports
    try:
        # Add utils to path using absolute path
        current_file = Path(__file__).resolve()
        repo_root = current_file.parent.parent.parent.parent  # Go up to repo root
        utils_path = repo_root / "utils"
        
        print(f"🔍 Looking for utils at: {utils_path}")
        
        if utils_path.exists():
            sys.path.insert(0, str(utils_path))
            import db_helper
            import logger_helper
            print("✅ Utils imports: db_helper and logger_helper found")
        else:
            issues.append(f"Utils directory not found at {utils_path}")
            print(f"❌ Utils directory not found at {utils_path}")
        
    except ImportError as e:
        issues.append(f"Utils import failed: {str(e)}")
        print(f"❌ Utils imports: {str(e)}")
    
    # 2. Check config files
    try:
        config_path = repo_root / "utils" / "config.yaml"
        if config_path.exists():
            print("✅ Config file: config.yaml found")
        else:
            warnings.append("config.yaml not found - may need database setup")
            print("⚠️  Config file: config.yaml not found")
            
    except Exception as e:
        issues.append(f"Config check failed: {str(e)}")
    
    # 3. Check Python packages
    required_packages = ['pandas', 'pyodbc', 'yaml']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ Package: {package} installed")
        except ImportError:
            issues.append(f"Missing package: {package}")
            print(f"❌ Package: {package} not installed")
    
    # 4. Check project structure
    project_root = Path(__file__).parent.parent
    required_files = [
        'delta_sync_main.py',
        'uuid_manager.py', 
        'change_detector.py',
        'customer_batcher.py',
        'staging_processor.py'
    ]
    
    for file in required_files:
        file_path = project_root / file
        if file_path.exists():
            print(f"✅ Module: {file} exists")
        else:
            issues.append(f"Missing module: {file}")
            print(f"❌ Module: {file} missing")
      # 5. Database connection test (if utils work)
    if not issues:
        try:
            # Test basic database connection
            conn = db_helper.get_connection('orders')
            conn.close()
            print("✅ Database: ORDERS connection test passed")
        except Exception as e:
            warnings.append(f"Database connection error: {str(e)}")
            print(f"⚠️  Database: {str(e)}")
    
    # 6. Summary
    print("\n" + "=" * 50)
    print("🎯 Setup Validation Summary")
    print("=" * 50)
    
    if not issues:
        print("🎉 READY TO START! All critical requirements met")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} warnings to address:")
            for warning in warnings:
                print(f"   - {warning}")
        
        print("\n🚀 Next Steps:")
        print("   1. cd dev/orders_unified_delta_sync_v3")
        print("   2. python delta_sync_main.py --mode TEST --customer GREYSON --limit 5")
        print("   3. Start Phase 1: UUID implementation")
        
        return True
        
    else:
        print(f"❌ {len(issues)} critical issues to fix:")
        for issue in issues:
            print(f"   - {issue}")
        
        print("\n🔧 Setup Actions Required:")
        if 'pandas' in str(issues):
            print("   pip install pandas pyodbc pyyaml")
        
        if 'config.yaml' in str(issues):
            print("   Set up utils/config.yaml with database connections")
        
        if 'Module' in str(issues):
            print("   Re-run the project creation scripts")
        
        return False

if __name__ == "__main__":
    success = validate_setup()
    
    if success:
        print("\n✅ Environment validation PASSED!")
        exit(0)
    else:
        print("\n❌ Environment validation FAILED!")
        print("   Fix the issues above and try again")
        exit(1)
