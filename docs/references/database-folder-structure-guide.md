# 📊 Database Folder Structure Guide

> **Purpose**: Clear understanding of database-related folders and their distinct purposes

## 🎯 **Key Distinction: `db/` vs `sql/`**

### **`db/` Folder - Database Schema Management**
**Purpose**: Managing how your database schema **changes over time** (schema evolution)

```text
db/
├── ddl/                    # Current table definitions (documentation)
│   ├── tables/
│   ├── views/
│   ├── indexes/
│   └── procedures/
├── migrations/             # Versioned schema changes
│   ├── 001_initial_schema.sql
│   ├── 002_add_priority_column.sql
│   └── 003_create_audit_table.sql
├── utility/                # Migration helper scripts
└── tests/                  # Schema validation tests
```

**Key Characteristics**:
- ✅ **Versioned changes** (001, 002, 003...)
- ✅ **Run once per environment** (production, staging, dev)
- ✅ **Schema evolution tracking** (database version control)
- ✅ **Rollback capabilities** (undo changes if needed)

---

### **`sql/` Folder - Operational Database Files**
**Purpose**: Day-to-day database operations and application queries

```text
sql/
├── graphql/                # Monday.com API operations
├── mappings/               # Field transformation configs
├── staging/                # Data staging queries
├── transformations/        # ETL transformation scripts
├── warehouse/              # Data warehouse queries
├── payload-templates/      # API payload examples
└── utility/                # Helper queries
```

**Key Characteristics**:
- ✅ **Current working files** (no versioning needed)
- ✅ **Run repeatedly** (daily operations)
- ✅ **Application queries** (SELECT, INSERT, ETL)
- ✅ **Integration files** (GraphQL, mappings)

---

## 🔄 **What is a Database Migration?**

A **migration** is a script that makes **specific, versioned changes** to your database schema.

### **Migration Examples**:

#### **Adding a Column**:
```sql
-- db/migrations/023_add_order_priority.sql
-- Description: Add priority column to orders table
-- Date: 2025-07-18

ALTER TABLE orders 
ADD COLUMN priority VARCHAR(10) DEFAULT 'NORMAL';

-- Update existing records
UPDATE orders 
SET priority = 'HIGH' 
WHERE order_value > 10000;
```

#### **Creating a Table**:
```sql
-- db/migrations/024_create_audit_log.sql
-- Description: Create audit log table for tracking changes
-- Date: 2025-07-18

CREATE TABLE audit_log (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    changed_at DATETIME2 DEFAULT GETDATE(),
    old_values NVARCHAR(MAX),
    new_values NVARCHAR(MAX)
);
```

#### **Adding Indexes**:
```sql
-- db/migrations/025_add_performance_indexes.sql
-- Description: Add indexes for query performance
-- Date: 2025-07-18

CREATE INDEX idx_orders_customer_date ON orders(customer, order_date);
CREATE INDEX idx_orders_priority ON orders(priority);
```

---

## 📋 **Migration Workflow**

### **Development Process**:
1. **Identify need** for schema change
2. **Create migration file** with next version number
3. **Write forward changes** (what to add/modify)
4. **Write rollback script** (how to undo)
5. **Test on development database**
6. **Apply to staging environment**
7. **Deploy to production**

### **Version Tracking**:
```text
Database Version 001: Initial schema
Database Version 002: Add customer_priority column  
Database Version 003: Create audit_log table
Database Version 004: Add performance indexes
```

### **Migration States**:
- **Pending**: Migration exists but not applied
- **Applied**: Migration successfully executed
- **Failed**: Migration encountered errors
- **Rolled Back**: Migration was undone

---

## 🎯 **Real-World Scenario**

### **Business Need**: Track order priority for customer service

#### **Step 1**: Create Migration
```sql
-- db/migrations/026_add_order_priority_tracking.sql
-- Add priority tracking to orders

-- Forward migration
ALTER TABLE orders ADD COLUMN priority VARCHAR(10) DEFAULT 'NORMAL';
ALTER TABLE orders ADD COLUMN priority_set_by VARCHAR(100);
ALTER TABLE orders ADD COLUMN priority_set_at DATETIME2;

CREATE INDEX idx_orders_priority_tracking ON orders(priority, priority_set_at);

-- Rollback instructions (commented)
-- DROP INDEX idx_orders_priority_tracking;
-- ALTER TABLE orders DROP COLUMN priority_set_at;
-- ALTER TABLE orders DROP COLUMN priority_set_by;
-- ALTER TABLE orders DROP COLUMN priority;
```

#### **Step 2**: Update Documentation
```sql
-- db/ddl/tables/orders.sql (current schema documentation)
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer VARCHAR(100),
    order_date DATE,
    order_value DECIMAL(10,2),
    priority VARCHAR(10) DEFAULT 'NORMAL',        -- NEW
    priority_set_by VARCHAR(100),                 -- NEW
    priority_set_at DATETIME2,                    -- NEW
    -- ... other columns
);
```

#### **Step 3**: Use in Operations
```sql
-- sql/transformations/high_priority_orders.sql (daily operations)
SELECT 
    order_id,
    customer,
    priority,
    priority_set_by,
    order_date
FROM orders 
WHERE priority = 'HIGH'
  AND priority_set_at >= DATEADD(day, -7, GETDATE())
ORDER BY priority_set_at DESC;
```

---

## 🚨 **Common Anti-Patterns to Avoid**

### **❌ Don't Do This**:
1. **Mix schema changes with operations** - Keep them separate
2. **Modify production directly** - Always use migrations
3. **Skip version numbers** - Maintain sequential numbering
4. **No rollback plan** - Always include undo instructions
5. **DDL in sql/ folder** - Schema changes belong in db/

### **✅ Do This Instead**:
1. **Separate concerns** - Schema evolution vs daily operations
2. **Version everything** - Track all schema changes
3. **Test migrations** - Validate on dev/staging first
4. **Document changes** - Clear descriptions and dates
5. **Plan rollbacks** - Know how to undo changes

---

## 🔧 **Tools Integration**

### **Migration Tools**:
- **Alembic** (Python): Database migration tool
- **Flyway** (Java): Database migration framework
- **Custom Scripts**: PowerShell/Python deployment tools

### **AAG Project Integration**:
```powershell
# Apply pending migrations
.\tools\deploy-migrations.ps1 -environment production

# Rollback last migration
.\tools\rollback-migration.ps1 -version 025

# Check migration status
.\tools\check-migration-status.ps1
```

---

## 📊 **Summary**

| Purpose | `db/` (Schema Management) | `sql/` (Operations) |
|---------|-------------------------|-------------------|
| **Goal** | Change database structure | Use database |
| **When** | Schema needs evolution | Daily operations |
| **Versioning** | Strict (001, 002...) | Current working files |
| **Frequency** | Once per environment | Repeatedly |
| **Examples** | `ALTER TABLE`, `CREATE TABLE` | `SELECT`, `INSERT`, ETL |
| **Rollback** | Required | Not applicable |

**Key Takeaway**: Think of `db/` as "database evolution" and `sql/` as "database operations". This separation enables safe, trackable schema changes while keeping operational queries organized.
