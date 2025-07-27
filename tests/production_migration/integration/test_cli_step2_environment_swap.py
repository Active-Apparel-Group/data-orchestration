#!/usr/bin/env python3
"""
CLI Step 2: Environment Swap + Status Validation
===============================================
Purpose: Execute 3-step environment swap and validate CLI status
Location: tests/production_migration/integration/test_cli_step2_environment_swap.py
Created: 2025-07-28

This script executes the 3-step environment swap then validates CLI status.
Run this AFTER user completes data preparation phase.
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
import tomli
import subprocess

logger = logger.get_logger(__name__)

def execute_3_step_environment_swap():
    """Execute the 3-step environment swap strategy"""
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    
    print("🔄 Executing 3-Step Environment Swap...")
    print("=" * 50)
    
    try:
        # Step 1: development -> devtoprod (temporary)
        print("\n🔄 Step 1: development -> devtoprod (temporary)")
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('[monday.development]', '[monday.devtoprod]')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Step 1 complete: development -> devtoprod")
        
        # Step 2: production -> development
        print("\n🔄 Step 2: production -> development")
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('[monday.production]', '[monday.development]')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Step 2 complete: production -> development")
        
        # Step 3: devtoprod -> production
        print("\n🔄 Step 3: devtoprod -> production")
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('[monday.devtoprod]', '[monday.production]')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Step 3 complete: devtoprod -> production")
        
        # Validate final configuration
        print("\n📋 Validating final configuration...")
        with open(config_path, 'rb') as f:
            final_config = tomli.load(f)
        
        final_dev_board = final_config.get('monday', {}).get('development', {}).get('board_id', 'NOT FOUND')
        final_prod_board = final_config.get('monday', {}).get('production', {}).get('board_id', 'NOT FOUND')
        
        print(f"   Final development board_id: {final_dev_board}")
        print(f"   Final production board_id: {final_prod_board}")
        
        # Verify the swap worked correctly
        expected_final_dev = "9200517329"    # Should now be the clean production board
        expected_final_prod = "9609317401"   # Should now be the tested development board
        
        if final_dev_board == expected_final_dev and final_prod_board == expected_final_prod:
            print("✅ Environment swap completed successfully!")
            return True
        else:
            print(f"❌ Environment swap validation failed:")
            print(f"   Expected dev: {expected_final_dev}, Got: {final_dev_board}")
            print(f"   Expected prod: {expected_final_prod}, Got: {final_prod_board}")
            return False
            
    except Exception as e:
        logger.exception(f"Environment swap failed: {e}")
        return False

def validate_cli_status():
    """Validate CLI status command works with new configuration"""
    print("\n🧪 Validating CLI status with new configuration...")
    print("=" * 50)
    
    try:
        # Test CLI status command
        result = subprocess.run([
            sys.executable, '-m', 'src.pipelines.sync_order_list.cli', 'status'
        ], 
        cwd=str(repo_root),
        capture_output=True, 
        text=True,
        timeout=30
        )
        
        if result.returncode == 0:
            print("✅ CLI status command successful!")
            print("📋 CLI Output:")
            print(result.stdout)
            return True
        else:
            print("❌ CLI status command failed!")
            print("📋 CLI Error:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ CLI status command timed out")
        return False
    except Exception as e:
        logger.exception(f"CLI status validation failed: {e}")
        return False

def main():
    print("🚀 CLI Step 2: Environment Swap + Status Validation")
    print("=" * 60)
    
    # Execute 3-step environment swap
    swap_success = execute_3_step_environment_swap()
    
    if not swap_success:
        print("❌ Environment swap failed - aborting CLI validation")
        return {'success': False, 'error': 'Environment swap failed'}
    
    # Validate CLI status
    cli_success = validate_cli_status()
    
    if cli_success:
        print("\n🎉 CLI Step 2 Complete!")
        print("✅ Environment swap successful")
        print("✅ CLI status validation successful")
        print("\n📋 Ready for CLI Step 3: Dry Run + Live Execution")
        return {'success': True, 'environment_swapped': True, 'cli_ready': True}
    else:
        print("\n⚠️ CLI Step 2 Partial Success")
        print("✅ Environment swap successful")
        print("❌ CLI status validation failed")
        return {'success': False, 'environment_swapped': True, 'cli_ready': False}

if __name__ == "__main__":
    result = main()
    if result['success']:
        print("\n🎯 Ready to proceed to CLI Step 3!")
    else:
        print(f"\n🔧 CLI Step 2 needs attention before proceeding")
