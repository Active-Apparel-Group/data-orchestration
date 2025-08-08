"""
Column Mapper Service
Purpose: Intelligent mapping between file columns and Monday.com board columns
Author: Data Engineering Team
Date: August 8, 2025

This service provides intelligent column mapping suggestions based on name similarity,
data type compatibility, and historical mappings.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import json

class ColumnMapperService:
    """
    Service for intelligent mapping between file columns and Monday.com board columns.
    Uses name similarity, data type compatibility, and learning from previous mappings.
    """
    
    def __init__(self):
        # Common column name mappings
        self.common_mappings = {
            # Customer/Company information
            'customer': ['customer', 'client', 'company', 'account', 'customer_name', 'client_name'],
            'company': ['company', 'organization', 'org', 'business', 'customer', 'client'],
            
            # Order information
            'order_number': ['order', 'order_number', 'order_id', 'po', 'po_number', 'purchase_order'],
            'item_name': ['item', 'product', 'item_name', 'product_name', 'description', 'title'],
            'quantity': ['quantity', 'qty', 'amount', 'count', 'units'],
            'price': ['price', 'cost', 'amount', 'value', 'unit_price'],
            
            # Status fields
            'status': ['status', 'state', 'condition', 'stage'],
            'priority': ['priority', 'importance', 'urgency'],
            
            # Dates
            'due_date': ['due_date', 'deadline', 'target_date', 'delivery_date', 'ship_date'],
            'start_date': ['start_date', 'begin_date', 'commence_date'],
            'created_date': ['created', 'created_date', 'date_created', 'timestamp'],
            
            # People
            'assignee': ['assignee', 'assigned_to', 'owner', 'responsible', 'person'],
            'contact': ['contact', 'contact_person', 'representative'],
            
            # Location
            'location': ['location', 'site', 'warehouse', 'facility'],
            'address': ['address', 'street', 'location'],
            
            # Production specific
            'style': ['style', 'style_number', 'sku', 'model'],
            'color': ['color', 'colour', 'shade'],
            'size': ['size', 'dimension', 'measurements'],
            'fabric': ['fabric', 'material', 'composition'],
            'season': ['season', 'collection', 'line'],
            
            # Financial
            'budget': ['budget', 'allocated', 'planned_cost'],
            'actual_cost': ['actual', 'spent', 'actual_cost', 'real_cost'],
            
            # Generic
            'notes': ['notes', 'comments', 'remarks', 'description', 'details'],
            'tags': ['tags', 'labels', 'categories', 'keywords']
        }
        
        # Monday.com column type mappings
        self.monday_type_mappings = {
            'text': ['text', 'long-text'],
            'numbers': ['numbers', 'rating'],
            'date': ['date'],
            'dropdown': ['dropdown', 'status'],
            'checkbox': ['checkbox'],
            'email': ['email'],
            'people': ['people'],
            'timeline': ['timeline'],
            'tags': ['tags'],
            'link': ['link'],
            'file': ['file']
        }
        
        # Data type compatibility matrix
        self.type_compatibility = {
            'text': ['text', 'long-text', 'dropdown', 'status', 'tags', 'email', 'link'],
            'numbers': ['numbers', 'rating', 'text'],
            'date': ['date', 'timeline', 'text'],
            'dropdown': ['dropdown', 'status', 'text'],
            'checkbox': ['checkbox', 'text'],
            'email': ['email', 'text'],
        }
    
    async def suggest_mappings(self, 
                             file_columns: List[Dict[str, Any]], 
                             monday_columns: List[Dict[str, Any]],
                             previous_mappings: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Suggest intelligent mappings between file and Monday.com columns
        
        Args:
            file_columns: List of file column information
            monday_columns: List of Monday.com column information
            previous_mappings: Optional previous mapping history
            
        Returns:
            Mapping suggestions with confidence scores
        """
        try:
            suggestions = {}
            used_monday_columns = set()
            
            # Sort file columns by importance/quality
            sorted_file_columns = self._prioritize_file_columns(file_columns)
            
            for file_col in sorted_file_columns:
                file_name = file_col['name']
                file_type = file_col['data_type']
                
                # Find best Monday.com column match
                best_match = self._find_best_match(
                    file_col, 
                    monday_columns, 
                    used_monday_columns,
                    previous_mappings
                )
                
                if best_match:
                    suggestions[file_name] = {
                        'monday_column': best_match['monday_column'],
                        'confidence': best_match['confidence'],
                        'reasons': best_match['reasons'],
                        'type_compatible': best_match['type_compatible'],
                        'alternative_matches': best_match.get('alternatives', [])
                    }
                    
                    used_monday_columns.add(best_match['monday_column']['id'])
                else:
                    suggestions[file_name] = {
                        'monday_column': None,
                        'confidence': 0,
                        'reasons': ['No suitable Monday.com column found'],
                        'type_compatible': False,
                        'alternative_matches': []
                    }
            
            # Generate mapping summary
            mapping_summary = self._generate_mapping_summary(suggestions, file_columns, monday_columns)
            
            return {
                'suggestions': suggestions,
                'summary': mapping_summary,
                'unmapped_monday_columns': self._get_unmapped_monday_columns(monday_columns, used_monday_columns)
            }
            
        except Exception as e:
            raise ValueError(f"Failed to generate mapping suggestions: {str(e)}")
    
    def _prioritize_file_columns(self, file_columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize file columns by importance and quality"""
        def priority_score(col):
            score = 0
            
            # Higher score for higher fill rate
            score += col.get('fill_rate', 0)
            
            # Higher score for columns that match common important fields
            col_name_lower = col['name'].lower()
            for key_field in ['order', 'customer', 'item', 'status', 'date']:
                if key_field in col_name_lower:
                    score += 50
                    break
            
            # Higher score for unique columns
            if col.get('unique_values', 0) > 1:
                score += 20
            
            return score
        
        return sorted(file_columns, key=priority_score, reverse=True)
    
    def _find_best_match(self, 
                        file_col: Dict[str, Any], 
                        monday_columns: List[Dict[str, Any]], 
                        used_columns: set,
                        previous_mappings: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Find the best Monday.com column match for a file column"""
        
        file_name = file_col['name']
        file_type = file_col['data_type']
        
        best_match = None
        best_score = 0
        alternatives = []
        
        for monday_col in monday_columns:
            if monday_col['id'] in used_columns:
                continue
            
            # Calculate match score
            match_info = self._calculate_match_score(file_col, monday_col, previous_mappings)
            
            if match_info['score'] > best_score:
                if best_match:
                    alternatives.append({
                        'monday_column': best_match['monday_column'],
                        'confidence': best_match['confidence'],
                        'reasons': best_match['reasons']
                    })
                
                best_match = match_info
                best_score = match_info['score']
            elif match_info['score'] > 0.3:  # Include as alternative if decent score
                alternatives.append({
                    'monday_column': monday_col,
                    'confidence': int(match_info['score'] * 100),
                    'reasons': match_info['reasons']
                })
        
        if best_match:
            best_match['alternatives'] = alternatives[:3]  # Limit to top 3 alternatives
            
        return best_match
    
    def _calculate_match_score(self, 
                              file_col: Dict[str, Any], 
                              monday_col: Dict[str, Any],
                              previous_mappings: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Calculate match score between file column and Monday.com column"""
        
        file_name = file_col['name'].lower().strip()
        monday_name = monday_col['title'].lower().strip()
        file_type = file_col['data_type']
        monday_type = monday_col['type']
        
        score = 0
        reasons = []
        
        # 1. Check previous mappings (highest priority)
        if previous_mappings and file_col['name'] in previous_mappings:
            if previous_mappings[file_col['name']] == monday_col['id']:
                score += 0.8
                reasons.append("Previously mapped")
        
        # 2. Exact name match
        if file_name == monday_name:
            score += 0.7
            reasons.append("Exact name match")
        elif self._normalize_name(file_name) == self._normalize_name(monday_name):
            score += 0.6
            reasons.append("Normalized name match")
        
        # 3. Semantic similarity using common mappings
        semantic_score = self._calculate_semantic_similarity(file_name, monday_name)
        if semantic_score > 0:
            score += semantic_score * 0.5
            reasons.append(f"Semantic similarity ({int(semantic_score * 100)}%)")
        
        # 4. String similarity
        string_similarity = SequenceMatcher(None, file_name, monday_name).ratio()
        if string_similarity > 0.6:
            score += string_similarity * 0.3
            reasons.append(f"String similarity ({int(string_similarity * 100)}%)")
        
        # 5. Data type compatibility
        type_compatible = self._is_type_compatible(file_type, monday_type)
        if type_compatible:
            score += 0.2
            reasons.append("Compatible data types")
        else:
            score *= 0.5  # Penalize incompatible types
            reasons.append("Incompatible data types")
        
        # 6. Column quality bonus
        fill_rate = file_col.get('fill_rate', 0)
        if fill_rate > 80:
            score += 0.1
            reasons.append("High data quality")
        
        return {
            'score': min(score, 1.0),  # Cap at 1.0
            'monday_column': monday_col,
            'confidence': int(min(score, 1.0) * 100),
            'reasons': reasons,
            'type_compatible': type_compatible
        }
    
    def _normalize_name(self, name: str) -> str:
        """Normalize column name for comparison"""
        # Remove common prefixes/suffixes
        normalized = name.lower().strip()
        
        # Remove common word variations
        replacements = {
            '_': ' ',
            '-': ' ',
            'num': 'number',
            'qty': 'quantity',
            'desc': 'description',
            'addr': 'address',
            'po': 'purchase_order'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _calculate_semantic_similarity(self, file_name: str, monday_name: str) -> float:
        """Calculate semantic similarity using common mapping patterns"""
        
        # Find which semantic group the file column belongs to
        file_groups = []
        for semantic_key, patterns in self.common_mappings.items():
            for pattern in patterns:
                if pattern in file_name or file_name in pattern:
                    file_groups.append(semantic_key)
                    break
        
        # Find which semantic group the Monday column belongs to
        monday_groups = []
        for semantic_key, patterns in self.common_mappings.items():
            for pattern in patterns:
                if pattern in monday_name or monday_name in pattern:
                    monday_groups.append(semantic_key)
                    break
        
        # Check for overlap
        overlap = set(file_groups) & set(monday_groups)
        if overlap:
            return 1.0  # Perfect semantic match
        
        # Check for partial matches
        for file_group in file_groups:
            for monday_group in monday_groups:
                if file_group in monday_group or monday_group in file_group:
                    return 0.7
        
        return 0.0
    
    def _is_type_compatible(self, file_type: str, monday_type: str) -> bool:
        """Check if file data type is compatible with Monday.com column type"""
        
        compatible_types = self.type_compatibility.get(file_type, [])
        return monday_type in compatible_types
    
    def _generate_mapping_summary(self, 
                                 suggestions: Dict[str, Any], 
                                 file_columns: List[Dict[str, Any]], 
                                 monday_columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for the mapping"""
        
        total_file_columns = len(file_columns)
        mapped_columns = sum(1 for s in suggestions.values() if s['monday_column'] is not None)
        high_confidence = sum(1 for s in suggestions.values() if s['confidence'] >= 80)
        medium_confidence = sum(1 for s in suggestions.values() if 50 <= s['confidence'] < 80)
        low_confidence = sum(1 for s in suggestions.values() if 0 < s['confidence'] < 50)
        
        return {
            'total_file_columns': total_file_columns,
            'mapped_columns': mapped_columns,
            'unmapped_columns': total_file_columns - mapped_columns,
            'mapping_rate': (mapped_columns / total_file_columns * 100) if total_file_columns > 0 else 0,
            'confidence_distribution': {
                'high': high_confidence,
                'medium': medium_confidence,
                'low': low_confidence
            },
            'quality_score': self._calculate_mapping_quality_score(suggestions)
        }
    
    def _calculate_mapping_quality_score(self, suggestions: Dict[str, Any]) -> int:
        """Calculate overall mapping quality score (0-100)"""
        if not suggestions:
            return 0
        
        total_confidence = sum(s['confidence'] for s in suggestions.values())
        mapped_count = sum(1 for s in suggestions.values() if s['monday_column'] is not None)
        
        # Average confidence of mapped columns
        avg_confidence = total_confidence / len(suggestions) if len(suggestions) > 0 else 0
        
        # Mapping completeness
        mapping_completeness = (mapped_count / len(suggestions) * 100) if len(suggestions) > 0 else 0
        
        # Weighted score
        quality_score = (avg_confidence * 0.7 + mapping_completeness * 0.3)
        
        return int(quality_score)
    
    def _get_unmapped_monday_columns(self, 
                                   monday_columns: List[Dict[str, Any]], 
                                   used_columns: set) -> List[Dict[str, Any]]:
        """Get list of Monday.com columns that weren't mapped"""
        return [col for col in monday_columns if col['id'] not in used_columns]
    
    async def validate_mapping(self, 
                             mapping: Dict[str, str], 
                             file_columns: List[Dict[str, Any]], 
                             monday_columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a user-defined mapping"""
        
        validation_results = {}
        issues = []
        
        monday_column_dict = {col['id']: col for col in monday_columns}
        file_column_dict = {col['name']: col for col in file_columns}
        
        for file_col_name, monday_col_id in mapping.items():
            if file_col_name not in file_column_dict:
                issues.append(f"File column '{file_col_name}' not found")
                continue
            
            if monday_col_id not in monday_column_dict:
                issues.append(f"Monday.com column '{monday_col_id}' not found")
                continue
            
            file_col = file_column_dict[file_col_name]
            monday_col = monday_column_dict[monday_col_id]
            
            # Check type compatibility
            is_compatible = self._is_type_compatible(file_col['data_type'], monday_col['type'])
            
            validation_results[file_col_name] = {
                'monday_column': monday_col,
                'type_compatible': is_compatible,
                'file_data_type': file_col['data_type'],
                'monday_data_type': monday_col['type'],
                'warning': None if is_compatible else f"Data type mismatch: {file_col['data_type']} -> {monday_col['type']}"
            }
        
        return {
            'validation_results': validation_results,
            'issues': issues,
            'is_valid': len(issues) == 0
        }
