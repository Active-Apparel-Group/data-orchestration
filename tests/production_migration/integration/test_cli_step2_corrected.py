#!/usr/bin/env python3
"""
CLI Step 2 CORRECTED: Proper Environment Swap
=============================================
Purpose: Execute CORRECT environment swap to use production board as development target
Location: tests/production_migration/integration/test_cli_step2_corrected.py
Created: 2025-07-29

This fixes the swap logic to actually swap the board IDs properly.
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

def execute_correct_environment_swap():
    """Execute the CORRECT environment swap - swap board IDs between development and production"""
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    
    print("🔄 Executing CORRECTED Environment Swap...")
    print("=" * 50)
    
    try:
        # Read current configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 Current Configuration:")
        print("   Development board_id: 9609317401")
        print("   Production board_id: 9200517329")
        
        print("\n🎯 TARGET Configuration:")
        print("   Development board_id: 9200517329 (clean production board)")
        print("   Production board_id: 9609317401 (tested development board)")
        
        # Method: Direct replacement of specific board IDs
        print("\n🔄 Step 1: Swap development board_id (9609317401 → 9200517329)")
        
        # Replace development board_id
        content = content.replace(
            'board_id = 9609317401                   # Dev items board',
            'board_id = 9200517329                   # Dev items board (was prod)'
        )
        
        print("🔄 Step 2: Swap production board_id (9200517329 → 9609317401)")
        
        # Replace production board_id  
        content = content.replace(
            'board_id = 9200517329                   # Prod items board',
            'board_id = 9609317401                   # Prod items board (was dev)'
        )
        
        # Write back the swapped configuration
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Board IDs swapped successfully!")
        
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
    print("\n🧪 Validating CLI status with swapped configuration...")
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
            print("✅ CLI status command successful with swapped configuration!")
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
    print("🚀 CLI Step 2 CORRECTED: Proper Environment Swap")
    print("=" * 60)
    
    # Execute corrected environment swap
    swap_success = execute_correct_environment_swap()
    
    if not swap_success:
        print("❌ Environment swap failed")
        return {'success': False, 'error': 'Environment swap failed'}
    
    print("\n🎉 Environment Swap CORRECTED and Complete!")
    print("✅ Development now targets clean production board (9200517329)")
    print("✅ Production now targets tested development board (9609317401)")
    print("\n📋 Ready for CLI execution with swapped boards!")
    
    return {'success': True, 'environment_swapped': True, 'cli_ready': True}

if __name__ == "__main__":
    result = main()
    if result['success']:
        print("\n🎯 Ready to run CLI with swapped configuration!")
        print("🚀 Next: python tests/production_migration/integration/test_cli_live_execution.py")
    else:
        print(f"\n🔧 Environment swap needs attention")
