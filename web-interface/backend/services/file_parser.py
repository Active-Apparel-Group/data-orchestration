"""
File Parser Service
Purpose: Parse CSV and Excel files with column detection and validation
Author: Data Engineering Team
Date: August 8, 2025

This service handles file upload parsing, column detection, and data preview
generation for the React frontend.
"""

import io
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

class FileParserService:
    """
    Service for parsing uploaded CSV and Excel files with intelligent
    column detection and data type inference.
    """
    
    def __init__(self):
        self.supported_extensions = {'.csv', '.xlsx', '.xls'}
        self.max_preview_rows = 10
        self.max_file_size_mb = 50
        
    def is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        return Path(filename).suffix.lower() in self.supported_extensions
    
    def validate_file_size(self, file_content: bytes) -> bool:
        """Validate file size is within limits"""
        size_mb = len(file_content) / (1024 * 1024)
        return size_mb <= self.max_file_size_mb
    
    async def parse_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse uploaded file and return analysis
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            File analysis with columns, data types, and sample data
        """
        try:
            if not self.is_supported_file(filename):
                raise ValueError(f"Unsupported file type. Supported: {self.supported_extensions}")
            
            if not self.validate_file_size(file_content):
                raise ValueError(f"File too large. Maximum size: {self.max_file_size_mb}MB")
            
            # Parse based on file type
            if filename.lower().endswith('.csv'):
                df = self._parse_csv(file_content, filename)
            else:
                df = self._parse_excel(file_content, filename)
            
            # Analyze the DataFrame
            analysis = self._analyze_dataframe(df, filename)
            
            return analysis
            
        except Exception as e:
            raise ValueError(f"Failed to parse file '{filename}': {str(e)}")
    
    def _parse_csv(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Parse CSV file with multiple encoding attempts"""
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
        
        for encoding in encodings:
            try:
                # Try different separators
                for sep in [',', ';', '\t']:
                    try:
                        df = pd.read_csv(
                            io.BytesIO(file_content),
                            encoding=encoding,
                            sep=sep,
                            dtype=str,  # Read everything as strings initially
                            na_filter=False  # Don't convert to NaN
                        )
                        
                        # Check if we got meaningful columns (more than 1 column usually)
                        if len(df.columns) > 1 and len(df) > 0:
                            return df
                    except Exception:
                        continue
                        
            except Exception:
                continue
        
        raise ValueError("Could not parse CSV file with any supported encoding or separator")
    
    def _parse_excel(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Parse Excel file with sheet detection"""
        try:
            # Read Excel file
            excel_file = pd.ExcelFile(io.BytesIO(file_content), engine='openpyxl')
            
            # Try to find the best sheet
            sheet_name = self._find_best_sheet(excel_file)
            
            # Read the selected sheet
            df = pd.read_excel(
                io.BytesIO(file_content),
                sheet_name=sheet_name,
                dtype=str,  # Read everything as strings initially
                na_filter=False,  # Don't convert to NaN
                engine='openpyxl'
            )
            
            return df
            
        except Exception as e:
            raise ValueError(f"Could not parse Excel file: {str(e)}")
    
    def _find_best_sheet(self, excel_file) -> str:
        """Find the best sheet to use from Excel file"""
        sheet_names = excel_file.sheet_names
        
        # Prefer sheets with common names
        preferred_names = ['data', 'main', 'sheet1', 'orders', 'master']
        
        for preferred in preferred_names:
            for sheet_name in sheet_names:
                if preferred.lower() in sheet_name.lower():
                    return sheet_name
        
        # Default to first sheet
        return sheet_names[0]
    
    def _analyze_dataframe(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Analyze DataFrame and generate column information"""
        try:
            # Clean up the DataFrame
            df = self._clean_dataframe(df)
            
            # Detect column information
            columns_info = []
            for col in df.columns:
                col_info = self._analyze_column(df[col], col)
                columns_info.append(col_info)
            
            # Generate sample data
            sample_data = self._generate_sample_data(df)
            
            # Calculate file statistics
            total_rows = len(df)
            total_columns = len(df.columns)
            
            return {
                "filename": filename,
                "file_type": "csv" if filename.lower().endswith('.csv') else "excel",
                "total_rows": total_rows,
                "total_columns": total_columns,
                "detected_columns": columns_info,
                "sample_data": sample_data,
                "data_quality": self._assess_data_quality(df)
            }
            
        except Exception as e:
            raise ValueError(f"Failed to analyze DataFrame: {str(e)}")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame by removing empty rows/columns"""
        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Remove completely empty rows
        df = df.dropna(axis=0, how='all')
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Remove columns with unnamed/empty names
        df = df.loc[:, df.columns != '']
        df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
        
        return df
    
    def _analyze_column(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """Analyze a single column to detect data type and characteristics"""
        # Basic stats
        total_values = len(series)
        non_empty_values = series.astype(str).str.strip().replace('', np.nan).dropna()
        null_count = total_values - len(non_empty_values)
        
        # Get sample values (non-empty)
        sample_values = non_empty_values.head(5).tolist() if len(non_empty_values) > 0 else []
        
        # Detect data type
        data_type = self._detect_data_type(non_empty_values)
        
        # Additional analysis based on type
        type_specific_info = self._get_type_specific_info(non_empty_values, data_type)
        
        return {
            "name": column_name,
            "data_type": data_type,
            "sample_values": sample_values,
            "null_count": null_count,
            "fill_rate": ((total_values - null_count) / total_values * 100) if total_values > 0 else 0,
            "unique_values": len(non_empty_values.unique()) if len(non_empty_values) > 0 else 0,
            **type_specific_info
        }
    
    def _detect_data_type(self, series: pd.Series) -> str:
        """Detect the most likely data type for a column"""
        if len(series) == 0:
            return "text"
        
        # Convert to string for analysis
        str_series = series.astype(str).str.strip()
        
        # Check for numeric (integers and floats)
        numeric_pattern = str_series.str.match(r'^-?\d+\.?\d*$', na=False)
        if numeric_pattern.sum() / len(str_series) > 0.8:  # 80% are numeric
            return "numbers"
        
        # Check for dates (various formats)
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # MM-DD-YYYY
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # M/D/YYYY
        ]
        
        for pattern in date_patterns:
            date_matches = str_series.str.match(pattern, na=False)
            if date_matches.sum() / len(str_series) > 0.7:  # 70% match date pattern
                return "date"
        
        # Check for boolean-like values
        boolean_values = {'true', 'false', 'yes', 'no', '1', '0', 'y', 'n'}
        unique_lower = set(str_series.str.lower().unique())
        if unique_lower.issubset(boolean_values) and len(unique_lower) <= 4:
            return "checkbox"
        
        # Check if looks like a dropdown (limited unique values)
        unique_count = len(str_series.unique())
        if unique_count <= 20 and unique_count / len(str_series) < 0.5:  # Low cardinality
            return "dropdown"
        
        # Check for email pattern
        email_pattern = str_series.str.contains(r'^[^@]+@[^@]+\.[^@]+$', na=False, regex=True)
        if email_pattern.sum() / len(str_series) > 0.8:
            return "email"
        
        # Default to text
        return "text"
    
    def _get_type_specific_info(self, series: pd.Series, data_type: str) -> Dict[str, Any]:
        """Get additional information based on detected data type"""
        info = {}
        
        if data_type == "numbers":
            try:
                numeric_series = pd.to_numeric(series, errors='coerce').dropna()
                if len(numeric_series) > 0:
                    info["min_value"] = float(numeric_series.min())
                    info["max_value"] = float(numeric_series.max())
                    info["has_decimals"] = any(numeric_series % 1 != 0)
            except Exception:
                pass
        
        elif data_type == "dropdown":
            unique_values = series.unique()[:10]  # Limit to 10 values for display
            info["possible_values"] = unique_values.tolist()
        
        elif data_type == "text":
            str_series = series.astype(str)
            if len(str_series) > 0:
                info["avg_length"] = int(str_series.str.len().mean())
                info["max_length"] = int(str_series.str.len().max())
        
        return info
    
    def _generate_sample_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate sample data for preview"""
        sample_df = df.head(self.max_preview_rows)
        return sample_df.to_dict('records')
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess overall data quality"""
        total_cells = df.shape[0] * df.shape[1]
        empty_cells = df.astype(str).eq('').sum().sum()
        
        return {
            "total_cells": total_cells,
            "empty_cells": empty_cells,
            "fill_rate": ((total_cells - empty_cells) / total_cells * 100) if total_cells > 0 else 0,
            "duplicate_rows": df.duplicated().sum(),
            "quality_score": self._calculate_quality_score(df)
        }
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> int:
        """Calculate overall quality score (0-100)"""
        try:
            # Factors for quality score
            fill_rate = (df.astype(str) != '').all(axis=1).mean() * 100
            uniqueness = (1 - df.duplicated().sum() / len(df)) * 100 if len(df) > 0 else 100
            column_completeness = (df.columns != '').mean() * 100
            
            # Weighted average
            quality_score = (fill_rate * 0.5 + uniqueness * 0.3 + column_completeness * 0.2)
            
            return int(quality_score)
            
        except Exception:
            return 50  # Default moderate score if calculation fails
