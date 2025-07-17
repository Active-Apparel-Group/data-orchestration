"""
Country Mapping Utility for Monday.com API
Purpose: Centralized country code mapping for Monday.com country column formatting
Location: pipelines/utils/country_mapper.py
Author: CTO / Head Data Engineer
Date: 2025-07-15

Features:
- ISO country code mapping for Monday.com API
- Consistent country formatting across all scripts
- Cambodia support and 60+ countries
- Fallback handling for unknown countries
"""

import pandas as pd
from typing import Dict, Optional, Union
import logging

# ISO Country Code Mapping for Monday.com country columns
COUNTRY_CODES = {
    'Afghanistan': 'AF', 'Albania': 'AL', 'Algeria': 'DZ', 'Argentina': 'AR', 'Australia': 'AU',
    'Austria': 'AT', 'Bangladesh': 'BD', 'Belgium': 'BE', 'Brazil': 'BR', 'Bulgaria': 'BG',
    'Cambodia': 'KH', 'Canada': 'CA', 'Chile': 'CL', 'China': 'CN', 'Colombia': 'CO',
    'Czech Republic': 'CZ', 'Denmark': 'DK', 'Egypt': 'EG', 'Estonia': 'EE', 'Finland': 'FI',
    'France': 'FR', 'Germany': 'DE', 'Greece': 'GR', 'Hong Kong': 'HK', 'Hungary': 'HU',
    'India': 'IN', 'Indonesia': 'ID', 'Ireland': 'IE', 'Israel': 'IL', 'Italy': 'IT',
    'Japan': 'JP', 'Jordan': 'JO', 'Kazakhstan': 'KZ', 'Kenya': 'KE', 'Kuwait': 'KW',
    'Latvia': 'LV', 'Lebanon': 'LB', 'Lithuania': 'LT', 'Luxembourg': 'LU', 'Malaysia': 'MY',
    'Mexico': 'MX', 'Morocco': 'MA', 'Netherlands': 'NL', 'New Zealand': 'NZ', 'Norway': 'NO',
    'Pakistan': 'PK', 'Peru': 'PE', 'Philippines': 'PH', 'Poland': 'PL', 'Portugal': 'PT',
    'Romania': 'RO', 'Russia': 'RU', 'Saudi Arabia': 'SA', 'Singapore': 'SG', 'Slovakia': 'SK',
    'Slovenia': 'SI', 'South Africa': 'ZA', 'South Korea': 'KR', 'Spain': 'ES', 'Sri Lanka': 'LK',
    'Sweden': 'SE', 'Switzerland': 'CH', 'Taiwan': 'TW', 'Thailand': 'TH', 'Turkey': 'TR',
    'Ukraine': 'UA', 'United Arab Emirates': 'AE', 'United Kingdom': 'GB', 'United States': 'US',
    'Uruguay': 'UY', 'Venezuela': 'VE', 'Vietnam': 'VN'
}

class CountryMapper:
    """
    Monday.com country column formatting utility.
    
    Provides methods to format country names into Monday.com API-compatible
    JSON structure with countryCode and countryName fields.
    """
    
    def __init__(self, logger=None):
        """Initialize country mapper with optional logger"""
        self.logger = logger or logging.getLogger(__name__)
        self.country_codes = COUNTRY_CODES.copy()
    
    def format_country_value(self, country_name: Union[str, None]) -> Optional[Dict[str, str]]:
        """
        Format country value for Monday.com country column type.
        
        Args:
            country_name: Country name (e.g., "Cambodia", "Vietnam")
            
        Returns:
            Dict with countryCode and countryName for Monday.com API
            None if country_name is null/empty
            
        Example:
            format_country_value("Cambodia") -> {"countryCode": "KH", "countryName": "Cambodia"}
        """
        if not country_name or pd.isna(country_name):
            return None
            
        # Clean the country name
        clean_name = str(country_name).strip()
        
        if not clean_name:
            return None
        
        # Get country code from mapping
        country_code = self.country_codes.get(clean_name, 'US')  # Default to US if not found
        
        # Log warning if country not found in mapping
        if clean_name not in self.country_codes and self.logger:
            self.logger.warning(f"Country '{clean_name}' not found in COUNTRY_CODES mapping, defaulting to US")
        
        return {
            "countryCode": country_code,
            "countryName": clean_name
        }
    
    def get_country_code(self, country_name: str) -> str:
        """
        Get ISO country code for a country name.
        
        Args:
            country_name: Country name
            
        Returns:
            Two-letter ISO country code (defaults to 'US' if not found)
        """
        if not country_name or pd.isna(country_name):
            return 'US'
            
        clean_name = str(country_name).strip()
        return self.country_codes.get(clean_name, 'US')
    
    def is_valid_country(self, country_name: str) -> bool:
        """
        Check if country name exists in mapping.
        
        Args:
            country_name: Country name to check
            
        Returns:
            True if country exists in mapping, False otherwise
        """
        if not country_name or pd.isna(country_name):
            return False
            
        clean_name = str(country_name).strip()
        return clean_name in self.country_codes
    
    def get_supported_countries(self) -> Dict[str, str]:
        """
        Get all supported countries and their codes.
        
        Returns:
            Dictionary of country names to country codes
        """
        return self.country_codes.copy()

# Factory function for easy usage
def create_country_mapper(logger=None) -> CountryMapper:
    """
    Factory function to create CountryMapper instance.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        CountryMapper instance
    """
    return CountryMapper(logger)

# Convenience function for direct formatting
def format_country_for_monday(country_name: Union[str, None], logger=None) -> Optional[Dict[str, str]]:
    """
    Convenience function to format country for Monday.com API.
    
    Args:
        country_name: Country name to format
        logger: Optional logger for warnings
        
    Returns:
        Formatted country dict or None
        
    Example:
        format_country_for_monday("Cambodia") -> {"countryCode": "KH", "countryName": "Cambodia"}
    """
    mapper = CountryMapper(logger)
    return mapper.format_country_value(country_name)
