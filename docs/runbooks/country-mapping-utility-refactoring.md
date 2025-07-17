# Country Mapping Utility Refactoring - Runbook

## 📋 Overview

**Date**: 2025-07-15  
**Purpose**: Consolidate duplicate country mapping code into shared utility  
**Files Affected**: 3 files  
**Impact**: Single source of truth for Monday.com country formatting  

## 🎯 Problem Solved

### Before Refactoring:
- ❌ Duplicate COUNTRY_CODES dictionary in both update scripts
- ❌ Duplicate format_country_value() methods
- ❌ Inconsistent country formatting logic
- ❌ Hard to maintain and update country mappings

### After Refactoring:
- ✅ Single shared utility in `pipelines/utils/country_mapper.py`
- ✅ Both scripts import from shared source
- ✅ Consistent country formatting across all scripts
- ✅ Easy to add new countries or update mappings

## 📁 Files Created/Modified

### 1. New Shared Utility
**File**: `pipelines/utils/country_mapper.py`
**Purpose**: Centralized country mapping for Monday.com API

```python
# Key components:
- COUNTRY_CODES: 72 countries with ISO codes
- CountryMapper class: Full-featured mapper
- format_country_for_monday(): Convenience function
- Comprehensive error handling and logging
```

### 2. Updated Scripts
**Files**:
- `pipelines/scripts/update/update_boards.py`  
- `pipelines/scripts/update/update_boards_batch.py`

**Changes**:
- Removed duplicate COUNTRY_CODES dictionary
- Updated imports to use shared utility
- Simplified format_country_value() to delegate to utility
- Maintained exact same API interface

### 3. Updated Test
**File**: `tests/debug/test_country_column_enhancement.py`
**Changes**: Updated imports to use shared utility

## 🔧 Technical Implementation

### Import Pattern (Both Scripts):
```python
# Before:
COUNTRY_CODES = {'Cambodia': 'KH', ...}  # 72 countries duplicated

# After:
from country_mapper import format_country_for_monday
```

### Method Updates:
```python
# Before (duplicated in both scripts):
def format_country_value(self, country_name: str) -> dict:
    clean_name = str(country_name).strip()
    country_code = COUNTRY_CODES.get(clean_name, 'US')
    # ... 15+ lines of duplicate logic

# After (both scripts):
def format_country_value(self, country_name: str) -> dict:
    return format_country_for_monday(country_name, self.logger)
```

## 📊 Country Mapping Features

### Supported Countries: 72
- **Key Countries**: Cambodia (KH), Vietnam (VN), China (CN), USA (US)
- **Coverage**: Asia-Pacific, Europe, Americas, Middle East, Africa
- **Format**: ISO 2-letter country codes

### API Format for Monday.com:
```json
{
  "countryCode": "KH",
  "countryName": "Cambodia"
}
```

### Error Handling:
- **Unknown countries**: Default to US with warning
- **Null/empty values**: Return None
- **Invalid input**: Graceful fallback with logging

## 🧪 Validation Results

### Test Coverage:
✅ **Country Mapping**: All test countries format correctly  
✅ **Column Type Detection**: Metadata-driven formatting works  
✅ **Batch Updater**: Batch processing maintains formatting  
✅ **Direct Utility**: Standalone utility functions properly  

### Test Files:
- `tests/debug/test_country_column_enhancement.py` - Complete integration test
- `tests/debug/test_country_mapper_utility.py` - Direct utility test

### Key Validations:
- Cambodia → `{"countryCode": "KH", "countryName": "Cambodia"}` ✅
- Vietnam → `{"countryCode": "VN", "countryName": "Vietnam"}` ✅
- Unknown → `{"countryCode": "US", "countryName": "Unknown"}` ✅
- Null/Empty → `None` ✅

## 🚀 Benefits Achieved

### 1. **Single Source of Truth**
- One place to update country mappings
- Consistent formatting across all scripts
- Reduced maintenance overhead

### 2. **Better Code Organization**
- Follows project structure rules (`utils/` for shared modules)
- Clean separation of concerns
- Improved readability

### 3. **Enhanced Functionality**
- Class-based approach with multiple utility methods
- Better error handling and logging
- Factory functions for easy usage

### 4. **Future-Proof Design**
- Easy to add new countries
- Support for different country formats
- Extensible for other Monday.com column types

## 🔄 Usage Examples

### For Update Scripts:
```python
# Both scripts now use identical pattern:
from country_mapper import format_country_for_monday

class MondayUpdater:
    def format_country_value(self, country_name: str) -> dict:
        return format_country_for_monday(country_name, self.logger)
```

### Direct Usage:
```python
from country_mapper import CountryMapper, format_country_for_monday

# Quick function
result = format_country_for_monday("Cambodia")

# Full class
mapper = CountryMapper()
result = mapper.format_country_value("Cambodia")
valid = mapper.is_valid_country("Cambodia")
code = mapper.get_country_code("Cambodia")
```

## 📈 Impact Metrics

### Code Reduction:
- **Lines Removed**: ~50 lines of duplicate code
- **Maintainability**: Single update point for 72 countries
- **Consistency**: 100% identical formatting logic

### Test Coverage:
- **Integration Tests**: 3/3 passed ✅
- **Unit Tests**: All functions validated ✅
- **Error Cases**: Handled gracefully ✅

## 🎯 Next Steps

### Immediate:
- ✅ Refactoring complete and tested
- ✅ All scripts using shared utility
- ✅ Cambodia GraphQL error resolved

### Future Enhancements:
- 🔄 Add more countries as needed
- 🔄 Extend to other Monday.com column types (date, status, etc.)
- 🔄 Create similar utilities for other shared logic

## 🚨 Breaking Changes: None

The refactoring maintains **100% backward compatibility**:
- Same method signatures
- Same return values  
- Same error handling
- Same logging behavior

Both update scripts work exactly as before, just with cleaner, shared code.

## 📝 Maintenance Notes

### Adding New Countries:
1. Edit `pipelines/utils/country_mapper.py`
2. Add to COUNTRY_CODES dictionary
3. Run test suite to validate
4. No changes needed in update scripts

### Updating Country Logic:
1. Modify CountryMapper class methods
2. Test with `test_country_mapper_utility.py`
3. Validate integration with `test_country_column_enhancement.py`

---

**✅ Refactoring Status**: **COMPLETE**  
**🎉 Result**: Single source of truth for Monday.com country formatting established!
