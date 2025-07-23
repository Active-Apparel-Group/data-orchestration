#!/usr/bin/env python3
"""
Column Mapping Tool: ORDER_LIST ↔ Monday.com Boards
==================================================
Fuzzy matches ORDER_LIST table columns with Monday board metadata
to generate accurate TOML column mappings.

Usage:
    python tools/match_order_list_columns.py

Outputs:
    - Exact matches (100% confidence)
    - Fuzzy matches with confidence scores
    - TOML-ready column mapping sections
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set

# Try to use rapidfuzz for better fuzzy matching, fall back to difflib if not available
try:
    from rapidfuzz import fuzz
    USE_RAPIDFUZZ = True
    print("🚀 Using rapidfuzz for enhanced fuzzy matching")
except ImportError:
    from difflib import SequenceMatcher
    USE_RAPIDFUZZ = False
    print("⚠️  rapidfuzz not available, using difflib (consider: pip install rapidfuzz)")
    
print(f"Debug: USE_RAPIDFUZZ = {USE_RAPIDFUZZ}")  # Debug line

def extract_order_list_columns(sql_file_path: Path) -> Set[str]:
    """Extract column names from ORDER_LIST SQL DDL file."""
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Extract column names from CREATE TABLE statement
    # Pattern matches: [COLUMN NAME] followed by data type
    column_pattern = r'\[([^\]]+)\]\s+(?:UNIQUEIDENTIFIER|NVARCHAR|DATETIME2|INT|SMALLINT|DECIMAL|CHAR|VARCHAR|BIGINT)'
    columns = set(re.findall(column_pattern, sql_content, re.IGNORECASE))
    
    # Filter out system/tracking columns that shouldn't be synced
    exclude_columns = {
        'record_uuid', '_SOURCE_TABLE', 'row_hash', 'sync_state', 
        'last_synced_at', 'monday_item_id', 'created_at', 'updated_at'
    }
    
    return columns - exclude_columns

def load_board_metadata(metadata_file_path: Path) -> List[Dict]:
    """Load Monday board metadata JSON."""
    with open(metadata_file_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    return metadata.get('columns', [])

def normalize_string(s: str) -> str:
    """Normalize string for better matching - handle case, spaces, punctuation."""
    # Convert to lowercase
    s = s.lower()
    
    # Replace common separators with spaces
    s = re.sub(r'[_\-/\\()]', ' ', s)
    
    # Remove extra spaces and strip
    s = ' '.join(s.split())
    
    return s

def fuzzy_similarity(a: str, b: str) -> float:
    """Calculate fuzzy similarity between two strings using best available method with normalization."""
    # Normalize both strings for consistent comparison
    norm_a = normalize_string(a)
    norm_b = normalize_string(b)
    
    if USE_RAPIDFUZZ:
        # Use multiple rapidfuzz algorithms with normalized strings
        ratio = fuzz.ratio(norm_a, norm_b) / 100.0
        partial = fuzz.partial_ratio(norm_a, norm_b) / 100.0
        token_sort = fuzz.token_sort_ratio(norm_a, norm_b) / 100.0
        token_set = fuzz.token_set_ratio(norm_a, norm_b) / 100.0
        
        # Get the best score from all algorithms
        best_score = max(ratio, partial, token_sort, token_set)
        
        # Special handling for common patterns (using normalized strings)
        # Handle "customer" vs "customer name" pattern
        if 'customer' in norm_a and 'customer' in norm_b:
            # If both contain "customer", boost the score
            customer_boost = min(0.95, best_score + 0.3)
            best_score = max(best_score, customer_boost)
        
        # Handle "style" patterns  
        if 'style' in norm_a and 'style' in norm_b:
            # If both contain "style", boost the score
            style_boost = min(0.90, best_score + 0.25)
            best_score = max(best_score, style_boost)
            
        # Handle color variations
        if ('color' in norm_a or 'colour' in norm_a) and ('color' in norm_b or 'colour' in norm_b):
            color_boost = min(0.95, best_score + 0.3)
            best_score = max(best_score, color_boost)
            
        # Handle exact word matches with different contexts
        words_a = set(norm_a.split())
        words_b = set(norm_b.split())
        common_words = words_a.intersection(words_b)
        
        if common_words and len(common_words) >= min(len(words_a), len(words_b)) * 0.5:
            # If 50% or more words match, boost score
            word_boost = min(0.88, best_score + 0.2)
            best_score = max(best_score, word_boost)
            
        return best_score
    else:
        # Enhanced difflib fallback with normalization
        base_score = SequenceMatcher(None, norm_a, norm_b).ratio()
        
        # Apply same special handling for difflib
        if 'customer' in norm_a and 'customer' in norm_b:
            base_score = max(base_score, min(0.95, base_score + 0.3))
        if 'style' in norm_a and 'style' in norm_b:
            base_score = max(base_score, min(0.90, base_score + 0.25))
        if ('color' in norm_a or 'colour' in norm_a) and ('color' in norm_b or 'colour' in norm_b):
            base_score = max(base_score, min(0.95, base_score + 0.3))
            
        return base_score

def find_column_matches(order_list_columns: Set[str], board_columns: List[Dict], 
                       min_confidence: float = 0.75) -> Tuple[List[Dict], List[Dict]]:
    """Find exact and fuzzy matches between ORDER_LIST and Monday columns."""
    exact_matches = []
    fuzzy_matches = []
    
    # Manual mapping overrides for known difficult matches (case-insensitive)
    manual_mappings = {
        'CUSTOMER NAME': ['CUSTOMER'],
        'CUSTOMER STYLE': ['STYLE', 'CUSTOMER STYLE'],
        'STYLE CODE': ['STYLE', 'STYLE CODE'],  
        'CUSTOMER COLOUR DESCRIPTION': ['COLOR', 'COLOUR', 'CUSTOMER COLOR', 'CUSTOMER COLOUR'],
        'CUSTOMER\'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS': ['COLOR CODE', 'COLOUR CODE'],
        'MAKE OR BUY': ['MAKE BUY', 'MAKE/BUY'],
        'PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)': ['PROMO GROUP', 'CAMPAIGN'],
    }
    
    for ol_column in sorted(order_list_columns):
        best_match = None
        best_score = 0.0
        found_exact = False
        
        for board_column in board_columns:
            monday_title = board_column.get('monday_title', '')
            sql_column = board_column.get('sql_column', '')
            
            # Check for exact match first
            if ol_column == sql_column:
                exact_matches.append({
                    'order_list_column': ol_column,
                    'monday_id': board_column['monday_id'],
                    'monday_title': monday_title,
                    'monday_type': board_column['monday_type'],
                    'extraction_field': board_column['extraction_field'],
                    'confidence': 1.0,
                    'match_type': 'exact'
                })
                found_exact = True
                break
            
            # Check manual mappings (case-insensitive)
            manual_match_found = False
            ol_normalized = normalize_string(ol_column)
            for pattern, targets in manual_mappings.items():
                if normalize_string(pattern) == ol_normalized:
                    for target in targets:
                        if normalize_string(target) == normalize_string(monday_title):
                            exact_matches.append({
                                'order_list_column': ol_column,
                                'monday_id': board_column['monday_id'],
                                'monday_title': monday_title,
                                'monday_type': board_column['monday_type'],
                                'extraction_field': board_column['extraction_field'],
                                'confidence': 1.0,
                                'match_type': 'manual_override'
                            })
                            manual_match_found = True
                            break
                    if manual_match_found:
                        break
            
            if manual_match_found:
                found_exact = True
                break
            
            # Calculate fuzzy similarity
            title_similarity = fuzzy_similarity(ol_column, monday_title)
            sql_similarity = fuzzy_similarity(ol_column, sql_column)
            max_similarity = max(title_similarity, sql_similarity)
            
            if max_similarity > best_score and max_similarity >= min_confidence:
                best_score = max_similarity
                best_match = {
                    'order_list_column': ol_column,
                    'monday_id': board_column['monday_id'],
                    'monday_title': monday_title,
                    'monday_type': board_column['monday_type'],
                    'extraction_field': board_column['extraction_field'],
                    'confidence': max_similarity,
                    'match_type': 'fuzzy',
                    'matched_against': 'title' if title_similarity > sql_similarity else 'sql_column'
                }
        
        if not found_exact and best_match:
            fuzzy_matches.append(best_match)
    
    return exact_matches, fuzzy_matches

def generate_toml_mapping(matches: List[Dict], board_name: str) -> str:
    """Generate TOML column mapping section."""
    toml_lines = [
        f'# Column mapping - ORDER_LIST headers to Monday items ({board_name})',
        f'[monday.column_mapping.headers]'
    ]
    
    # Enhanced categorization with more specific groupings
    categories = {
        'Core Order Information': [],
        'Product Details': [],
        'Season and Planning': [],
        'Dates and Timelines': [],
        'Pricing and Financials': [],
        'Status and Validation': [],
        'Shipping and Logistics': [],
        'Other': []
    }
    
    for match in matches:
        column = match['order_list_column']
        monday_id = match['monday_id']
        monday_title = match['monday_title']
        monday_type = match['monday_type']
        confidence = match['confidence']
        
        comment = f"# {monday_type} - {monday_title}"
        if confidence < 1.0:
            comment += f" (fuzzy: {confidence:.2f})"
        
        line = f'"{column}" = "{monday_id}"  {comment}'
        
        # Enhanced categorization logic
        column_lower = column.lower()
        
        # Core order information
        if any(keyword in column_lower for keyword in ['order', 'po', 'customer alt', 'aag order', 'bulk po']):
            categories['Core Order Information'].append(line)
        # Product details - enhanced keywords
        elif any(keyword in column_lower for keyword in ['style', 'color', 'colour', 'description', 'fabric', 'pattern', 'sku']):
            categories['Product Details'].append(line)
        # Season and planning
        elif any(keyword in column_lower for keyword in ['season', 'drop', 'collection', 'range', 'planner', 'category']):
            categories['Season and Planning'].append(line)
        # Dates and timelines
        elif any(keyword in column_lower for keyword in ['date', 'factory', 'warehouse', 'eta', 'ex factory', 'delivery']):
            categories['Dates and Timelines'].append(line)
        # Pricing and financials
        elif any(keyword in column_lower for keyword in ['price', 'fob', 'duty', 'tariff', 'cost', 'fee', 'charge', 'discount', 'works', 'ddp']):
            categories['Pricing and Financials'].append(line)
        # Status and validation
        elif any(keyword in column_lower for keyword in ['status', 'validation', 'approval', 'final prices']):
            categories['Status and Validation'].append(line)
        # Shipping and logistics
        elif any(keyword in column_lower for keyword in ['destination', 'delivery', 'freight', 'handling', 'tracking', 'hs code', 'country']):
            categories['Shipping and Logistics'].append(line)
        else:
            categories['Other'].append(line)
    
    # Add categorized sections
    for category, lines in categories.items():
        if lines:
            toml_lines.append(f'# === {category} ===')
            toml_lines.extend(lines)
            toml_lines.append('')  # Empty line between categories
    
    return '\n'.join(toml_lines)

def review_fuzzy_matches(matches: List[Dict], board_name: str) -> None:
    """Review fuzzy matches that might need manual verification."""
    fuzzy_matches = [m for m in matches if m['confidence'] < 1.0]
    
    if not fuzzy_matches:
        print(f"✅ {board_name}: All matches are exact!")
        return
    
    print(f"\n🔍 {board_name} FUZZY MATCHES REQUIRING REVIEW:")
    print("=" * 60)
    
    for match in sorted(fuzzy_matches, key=lambda x: x['confidence']):
        confidence = match['confidence']
        ol_column = match['order_list_column']
        monday_title = match['monday_title']
        monday_id = match['monday_id']
        
        # Color code confidence levels
        if confidence >= 0.95:
            confidence_color = "🟢 EXCELLENT"
        elif confidence >= 0.90:
            confidence_color = "🟡 GOOD"
        elif confidence >= 0.85:
            confidence_color = "🟠 QUESTIONABLE"
        else:
            confidence_color = "🔴 POOR"
            
        print(f"{confidence_color} ({confidence:.2f}): {ol_column}")
        print(f"   └─ Mapped to: {monday_title} ({monday_id})")
        print()

def main():
    """Main execution function."""
    print("🔍 ORDER_LIST ↔ Monday.com Column Mapping Tool")
    print("=" * 50)
    
    # File paths
    order_list_sql = Path('db/ddl/tables/orders/dbo_order_list.sql')
    dev_board_metadata = Path('configs/boards/board_9609317401_metadata.json')
    prod_board_metadata = Path('configs/boards/board_9200517329_metadata.json')
    
    # Verify files exist
    for file_path in [order_list_sql, dev_board_metadata, prod_board_metadata]:
        if not file_path.exists():
            print(f"❌ Error: {file_path} not found")
            return
    
    # Extract ORDER_LIST columns
    print("📋 Extracting ORDER_LIST columns...")
    order_list_columns = extract_order_list_columns(order_list_sql)
    print(f"   Found {len(order_list_columns)} columns")
    
    # Process Development Board
    print("\n🔧 Processing Development Board (9609317401)...")
    dev_board_columns = load_board_metadata(dev_board_metadata)
    dev_exact, dev_fuzzy = find_column_matches(order_list_columns, dev_board_columns)
    
    print(f"   Exact matches: {len(dev_exact)}")
    print(f"   Fuzzy matches: {len(dev_fuzzy)}")
    
    # Process Production Board
    print("\n🏭 Processing Production Board (9200517329)...")
    prod_board_columns = load_board_metadata(prod_board_metadata)
    prod_exact, prod_fuzzy = find_column_matches(order_list_columns, prod_board_columns)
    
    print(f"   Exact matches: {len(prod_exact)}")
    print(f"   Fuzzy matches: {len(prod_fuzzy)}")
    
    # Display results
    print("\n📊 DEVELOPMENT BOARD MATCHES")
    print("-" * 40)
    
    all_dev_matches = dev_exact + dev_fuzzy
    for match in sorted(all_dev_matches, key=lambda x: x['order_list_column']):
        confidence_indicator = "✅" if match['confidence'] == 1.0 else f"🔍 {match['confidence']:.2f}"
        print(f"{confidence_indicator} {match['order_list_column']} → {match['monday_id']} ({match['monday_title']})")
    
    print(f"\n📊 PRODUCTION BOARD MATCHES")
    print("-" * 40)
    
    all_prod_matches = prod_exact + prod_fuzzy
    for match in sorted(all_prod_matches, key=lambda x: x['order_list_column']):
        confidence_indicator = "✅" if match['confidence'] == 1.0 else f"🔍 {match['confidence']:.2f}"
        print(f"{confidence_indicator} {match['order_list_column']} → {match['monday_id']} ({match['monday_title']})")
    
    # Generate TOML mappings
    print(f"\n📝 GENERATING TOML MAPPINGS")
    print("-" * 40)
    
    dev_toml = generate_toml_mapping(all_dev_matches, "DEVELOPMENT BOARD: 9609317401")
    prod_toml = generate_toml_mapping(all_prod_matches, "PRODUCTION BOARD: 9200517329")
    
    # Save to files
    output_dir = Path('configs/mapping')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'dev_column_mapping.toml', 'w') as f:
        f.write(dev_toml)
    
    with open(output_dir / 'prod_column_mapping.toml', 'w') as f:
        f.write(prod_toml)
    
    print(f"✅ Development mapping saved to: {output_dir / 'dev_column_mapping.toml'}")
    print(f"✅ Production mapping saved to: {output_dir / 'prod_column_mapping.toml'}")
    
    # Review fuzzy matches for manual verification
    review_fuzzy_matches(all_dev_matches, "DEVELOPMENT")
    review_fuzzy_matches(all_prod_matches, "PRODUCTION")
    
    # Summary statistics
    print(f"\n📈 SUMMARY")
    print("-" * 40)
    print(f"ORDER_LIST columns: {len(order_list_columns)}")
    print(f"Development matches: {len(all_dev_matches)} ({len(all_dev_matches)/len(order_list_columns)*100:.1f}%)")
    print(f"Production matches: {len(all_prod_matches)} ({len(all_prod_matches)/len(order_list_columns)*100:.1f}%)")
    
    # Show unmapped columns
    mapped_dev_columns = {match['order_list_column'] for match in all_dev_matches}
    mapped_prod_columns = {match['order_list_column'] for match in all_prod_matches}
    
    unmapped_dev = order_list_columns - mapped_dev_columns
    unmapped_prod = order_list_columns - mapped_prod_columns
    
    if unmapped_dev:
        print(f"\n⚠️  UNMAPPED DEV COLUMNS ({len(unmapped_dev)}):")
        for col in sorted(unmapped_dev):
            print(f"   - {col}")
    
    if unmapped_prod:
        print(f"\n⚠️  UNMAPPED PROD COLUMNS ({len(unmapped_prod)}):")
        for col in sorted(unmapped_prod):
            print(f"   - {col}")
    
    print(f"\n🎯 Ready to update sync_order_list.toml with accurate mappings!")

if __name__ == "__main__":
    main()
