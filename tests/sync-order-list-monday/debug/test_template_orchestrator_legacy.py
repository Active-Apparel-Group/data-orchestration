"""
Template-Driven Merge Orchestrator Test Suite (Legacy - moved from debug/)
⚠️ THIS FILE CONTAINS MOCK CONFIGURATIONS - DO NOT USE IN PRODUCTION

REPLACED BY: Integration tests in /tests/sync-order-list-monday/integration/
This file is kept for reference but should not be used for real testing.

Use the new structure:
- tests/sync-order-list-monday/integration/test_merge_headers.py
- tests/sync-order-list-monday/integration/test_config_parser_real.py
- tests/sync-order-list-monday/e2e/test_complete_pipeline.py
"""

import sys
from pathlib import Path
import logging
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import project modules
from src.pipelines.sync_order_list.merge_orchestrator import create_merge_orchestrator
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine
from src.pipelines.sync_order_list.config_parser import load_delta_sync_config

class TemplateOrchestrorTestFramework:
    """⚠️ LEGACY - Modern test framework for template-driven ORDER_LIST V2 pipeline"""
    
    def __init__(self):
        print("⚠️ WARNING: This is a legacy test file with mock configurations!")
        print("Use the new integration tests in /tests/sync-order-list-monday/integration/ instead")
        self.test_results = {}
        # Setup logging for test visibility
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def test_phase_1_template_engine_validation(self) -> Dict[str, Any]:
        """⚠️ LEGACY - Phase 1: Validate SQLTemplateEngine (uses mock config)"""
        self.logger.warning("⚠️ LEGACY TEST - Use integration tests instead!")
        
        # Legacy test implementation (kept for reference)
        return {
            'success': False,
            'error': 'Legacy test - use integration tests in /tests/sync-order-list-monday/integration/',
            'phase': 'template_engine_validation_legacy'
        }


def main():
    """⚠️ LEGACY - Run template-driven merge orchestrator test suite"""
    print("\n" + "="*80)
    print("⚠️  LEGACY TEST FILE - DO NOT USE FOR PRODUCTION TESTING")
    print("="*80)
    print("This file has been replaced by:")
    print("  • tests/sync-order-list-monday/integration/test_merge_headers.py")
    print("  • tests/sync-order-list-monday/integration/test_config_parser_real.py")  
    print("  • tests/sync-order-list-monday/e2e/test_complete_pipeline.py")
    print("="*80)
    
    # Don't run the legacy test
    sys.exit(1)


if __name__ == "__main__":
    main()
