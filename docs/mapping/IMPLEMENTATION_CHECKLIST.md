# ORDERS_UNIFIED → Monday.com Mapping Implementation Checklist

## ✅ Completed Tasks

### 1. Field Analysis & Mapping
- [x] Analyzed 194 ORDERS_UNIFIED fields vs 80 Monday.com fields
- [x] Identified 37 exact field matches
- [x] Documented 7 fields requiring transformation/value mapping
- [x] Catalogued 28 Monday.com fields excluded from mapping (mirror/formula/board_relation types)
- [x] Identified 143 ORDERS_UNIFIED fields not present in Monday.com

### 2. Monday.com Column IDs & API Preparation
- [x] Extracted all Monday.com column IDs from source JSON
- [x] Added column IDs to both markdown documentation and YAML mapping
- [x] Created dedicated JSON file for quick column ID reference
- [x] Documented API implementation patterns and examples

### 3. Value Mappings & Transformations
- [x] ORDER TYPE (ACTIVE/CANCELLED) → ORDER STATUS (RECEIVED/CANCELLED) mapping
- [x] Customer name standardization rules (RHYTHM (AU) → RHYTHM, etc.)
- [x] Data type conversion requirements documented
- [x] Data cleaning rules for US TARIFF RATE field (TRUE → 0)

### 4. Power Query Analysis
- [x] Analyzed existing Power Query transformation logic
- [x] Extracted size aggregation rules (individual size columns → TOTAL QTY)
- [x] Documented customer filtering and date filtering requirements
- [x] Identified current production mapping patterns

### 5. Documentation & Files
- [x] **orders_unified_monday_comparison.md** - Comprehensive mapping documentation
- [x] **orders_unified_monday_mapping.yaml** - Structured YAML mapping configuration
- [x] **monday_column_ids.json** - Quick reference for column IDs
- [x] **IMPLEMENTATION_CHECKLIST.md** - This implementation checklist

### 6. Data Quality & Validation
- [x] YAML syntax validation (no errors)
- [x] Structural consistency checks
- [x] Sample data inclusion in mapping documentation
- [x] API mutation template and Python code examples

## 📋 Ready for Implementation

### ETL Pipeline Requirements
1. **Source Connection**: SQL Server (ORDERS_UNIFIED table)
2. **Target Connection**: Monday.com GraphQL API
3. **Required Transformations**:
   - Customer name standardization lookup
   - ORDER TYPE → ORDER STATUS value mapping
   - Size column aggregation into TOTAL QTY
   - Data type conversions (string → numeric for pricing fields)
   - Data cleaning (US TARIFF RATE: TRUE → 0)

### API Implementation
- Board ID: [TO BE CONFIGURED]
- GraphQL endpoint: https://api.monday.com/v2
- Authentication: API token required
- Mutation template provided in documentation
- Column value formatting examples included

### Data Filtering
- **Date Filter**: Current year orders only (ORDER DATE PO RECEIVED)
- **Customer Filter**: Only orders with valid customer mapping
- **Status Filter**: Active and cancelled orders

## 🎯 Next Steps for Implementation

1. **Environment Setup**
   - Configure Monday.com API credentials
   - Set up SQL Server connection
   - Install required Python packages (requests, pyodbc, etc.)

2. **ETL Development**
   - Create extraction module for ORDERS_UNIFIED
   - Implement transformation logic using YAML mapping
   - Build Monday.com API insertion module
   - Add error handling and logging

3. **Testing & Validation**
   - Test with sample data set
   - Validate API responses
   - Verify data integrity in Monday.com
   - Performance testing for large datasets

4. **Production Deployment**
   - Schedule automated ETL runs
   - Set up monitoring and alerting
   - Create data quality checks
   - Document operational procedures

## 📁 File Locations

| File | Purpose | Status |
|------|---------|--------|
| `docs/mapping/orders_unified_monday_comparison.md` | Main mapping documentation | ✅ Complete |
| `docs/mapping/orders_unified_monday_mapping.yaml` | YAML configuration for ETL | ✅ Complete |
| `docs/mapping/monday_column_ids.json` | Column ID reference | ✅ Complete |
| `src/add_orders/monday.json` | Source Monday.com schema | ✅ Available |
| `src/add_orders/power_query.m` | Current transformation logic | ✅ Analyzed |

---

**Status**: Ready for ETL implementation  
**Last Updated**: December 19, 2024  
**Version**: 1.0
