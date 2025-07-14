# DDL Management Guide

## 📁 Directory Structure

```
sql/ddl/
├── tables/          # CREATE TABLE statements
│   ├── orders/      # Tables from ORDERS database
│   ├── dms/         # Tables from DMS database
│   └── distribution/ # Tables from DISTRIBUTION database
├── indexes/         # Index creation scripts
├── views/           # View definitions
└── procedures/      # Stored procedures
```

## 🎯 Purpose

This directory contains **source-controlled DDL scripts** for:
- **Documentation**: Understanding table structures
- **Deployment**: Creating tables in new environments
- **Version Control**: Tracking schema changes over time
- **Code Review**: Reviewing schema modifications

## 📜 File Naming Conventions

### Tables
- `{database}_{schema}_{table_name}.sql`
- Example: `orders_dbo_orders_unified.sql`

### Indexes
- `{database}_{schema}_{table_name}_indexes.sql`
- Example: `orders_dbo_orders_unified_indexes.sql`

### Views
- `{database}_{schema}_{view_name}.sql` 
- Example: `staging_dbo_v_packed_products.sql`

## 🔧 Generating DDL Files

### Method 1: Python Script (Recommended)
```bash
# From project root
python scripts/extract_ddl.py
```

### Method 2: Manual T-SQL
```sql
-- Use the utility script
-- sql/utility/extract_table_ddl.sql
```

### Method 3: PowerShell
```powershell
# For batch extraction
.\scripts\extract_ddl.ps1 -ServerName "server" -DatabaseName "db" -Username "user" -Password "pass"
```

## 📋 File Template

Each DDL file should follow this structure:

```sql
-- Table: {schema}.{table_name}
-- Database: {database_name}
-- Purpose: [Brief description of table purpose]
-- Dependencies: [List any dependent tables/views]
-- Last Updated: YYYY-MM-DD
-- Author: [Your name]

-- Table Creation
CREATE TABLE [schema].[table_name] (
    -- Column definitions
);

-- Indexes
CREATE INDEX [IX_...] ON [schema].[table_name] (...);

-- Foreign Keys (if any)
ALTER TABLE [schema].[table_name] 
ADD CONSTRAINT [FK_...] FOREIGN KEY (...) REFERENCES [...];

-- Comments/Documentation
EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Table description',
    @level0type = N'SCHEMA', @level0name = N'schema',
    @level1type = N'TABLE', @level1name = N'table_name';
```

## 🔄 Best Practices

### 1. **Separation of Concerns**
- **`outputs/ddl/`**: Generated artifacts (can be deleted/regenerated)
- **`sql/ddl/`**: Source-controlled schema definitions
- **`sql/staging/`**: Data extraction views
- **`sql/migrations/`**: Schema change scripts

### 2. **Version Control**
- Commit DDL files to git
- Use meaningful commit messages for schema changes
- Review DDL changes in pull requests

### 3. **Documentation**
- Add table/column descriptions
- Document business rules and constraints
- List dependencies and relationships

### 4. **Environment Management**
- Use DDL files to create consistent schemas across environments
- Test DDL scripts in development before production
- Include rollback scripts for migrations

## 🚀 Deployment Workflow

1. **Extract DDL** from production/staging
2. **Save to** `sql/ddl/` directory
3. **Add documentation** and descriptions
4. **Commit to git** with descriptive message
5. **Use for deployment** to new environments

## 📊 Related Files

- **`scripts/extract_ddl.py`**: Main DDL extraction tool
- **`scripts/extract_ddl.ps1`**: PowerShell DDL extraction
- **`sql/utility/extract_table_ddl.sql`**: Manual T-SQL queries
- **`sql/migrations/`**: Schema change scripts

## 🔍 Examples

### Extract single table
```bash
python scripts/extract_ddl.py
# Select: 2 (ORDERS)
# Table: ORDERS_UNIFIED
# Save to source: y
```

### Extract all tables from database
```bash
python scripts/extract_ddl.py
# Select: 2 (ORDERS)  
# Table: [press Enter for all]
# Save to source: y
```

---

**Last Updated**: June 15, 2025  
**Maintainer**: Data Engineering Team
