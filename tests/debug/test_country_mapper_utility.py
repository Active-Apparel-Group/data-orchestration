"""
Quick Test: Country Mapper Utility
Purpose: Test the shared country mapping utility independently
Date: 2025-07-15
"""
import sys
from pathlib import Path

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines" / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

from country_mapper import format_country_for_monday, COUNTRY_CODES, CountryMapper

def test_direct_utility():
    """Test the country utility directly"""
    print("Testing Country Mapper Utility")
    print("=" * 40)
    
    # Test direct function
    cambodia = format_country_for_monday("Cambodia")
    print(f"Direct function: Cambodia -> {cambodia}")
    
    # Test with CountryMapper class
    mapper = CountryMapper()
    vietnam = mapper.format_country_value("Vietnam")
    print(f"Mapper class: Vietnam -> {vietnam}")
    
    # Test unknown country
    unknown = mapper.format_country_value("Unknown Country")
    print(f"Unknown country: -> {unknown}")
    
    # Test null values
    null_test = mapper.format_country_value(None)
    print(f"Null value: -> {null_test}")
    
    # Test supported countries count
    countries = mapper.get_supported_countries()
    print(f"Supported countries: {len(countries)}")
    
    # Test if Cambodia is supported
    is_valid = mapper.is_valid_country("Cambodia")
    print(f"Cambodia is valid: {is_valid}")
    
    # Test country code lookup
    code = mapper.get_country_code("Cambodia")
    print(f"Cambodia country code: {code}")
    
    print("\n✅ All country mapper tests completed!")

if __name__ == "__main__":
    test_direct_utility()
