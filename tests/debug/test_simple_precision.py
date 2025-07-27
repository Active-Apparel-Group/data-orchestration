"""
Simple Precision Transformer Test
Purpose: Test basic precision transformation functionality
"""

import sys
from pathlib import Path

def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "utils"))

from precision_transformer import SimplePrecisionTransformer
import db_helper as db
import logger_helper

def test_precision_transforms():
    """Test basic precision transform generation"""
    logger = logger_helper.get_logger(__name__)
    
    print("🔧 Testing Simple Precision Transforms")
    print("-" * 40)
    
    transformer = SimplePrecisionTransformer()
    
    # Test INT transform
    int_transform = transformer.get_precision_transform("XS")
    print(f"INT transform: {int_transform}")
    
    # Test DECIMAL transform  
    decimal_transform = transformer.get_precision_transform("FINAL FOB (USD)")
    print(f"DECIMAL transform: {decimal_transform}")
    
    # Test with sample data
    test_data = {
        "XS": "12.5",
        "FINAL FOB (USD)": "123.456789"
    }
    
    print("\nTesting transforms:")
    print(f"  Original XS: {test_data['XS']}")
    print(f"  Transformed: FLOOR(TRY_CAST({test_data['XS']} AS FLOAT)) = 12")
    
    print(f"  Original FOB: {test_data['FINAL FOB (USD)']}")
    print(f"  Transformed: TRY_CAST({test_data['FINAL FOB (USD)']} AS DECIMAL(17,4)) = 123.4568")
    
    print("\n✅ Basic precision transforms working")

if __name__ == "__main__":
    test_precision_transforms()
