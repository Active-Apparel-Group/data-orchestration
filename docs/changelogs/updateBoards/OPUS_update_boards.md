# OPUS Update Boards - Comprehensive Implementation Guide

## 🎯 **Project Overview**

**Initiative**: Extend Monday.com integration to support bidirectional data flow
**Current State**: Read-only Monday.com board extraction via `load_boards.py`
**Target State**: Full bidirectional sync with update capabilities using staging framework
**Timeline**: 3 phases over 2 weeks for production readiness

## 🔍 **Comprehensive Plan Review**

### **Context & Motivation**

Active Apparel Group has successfully implemented a robust Monday.com board extraction system using `load_boards.py` and the staging framework. The next logical evolution is to enable updates back to Monday.com, completing the bidirectional data flow needed for operational efficiency.

### **Key Insights from CTO Requirements**

1. **GraphQL Operation Types** (not field types):
   - `update_items` - Primary item updates
   - `update_subitems` - Subitem quantity/status updates  
   - `update_groups` - Group organization changes
   - `update_boards` - Board-level metadata updates

2. **Leverage Existing Infrastructure**:
   - Proven staging framework architecture
   - Existing `BatchProcessor`, `MondayApiClient`, `staging_operations`
   - Established metadata-driven patterns
   - Working conversion functions and error handling

3. **Rapid Time to Production**:
   - Extend existing code rather than rebuild
   - Iterate on proven patterns
   - Days not weeks to operational capability

## 🚀 **RECOMMENDED PATH: Extend Staging Framework for Updates**

### **Why This is the Optimal Strategy**

#### **1. Minimal New Development**
- **Reuse Infrastructure**: Leverage existing `MondayApiClient`, `staging_operations`, `BatchProcessor`
- **Proven Patterns**: Use established metadata-driven configuration approach
- **Existing Safety**: Built-in error handling, retry logic, audit trails already exist

#### **2. Architectural Advantages**
- **Staging-First**: Updates flow through staging tables for validation and rollback
- **Batch Processing**: Existing batch infrastructure handles rate limiting and performance
- **Error Resilience**: Comprehensive error handling with retry and recovery mechanisms
- **Monitoring**: Existing monitoring and alerting systems extend naturally

#### **3. Risk Mitigation**
- **Incremental Deployment**: Build on working foundation
- **Rollback Capability**: Staging approach enables safe rollbacks
- **Validation Framework**: Existing validation patterns ensure data integrity
- **Rate Limiting**: Production-tested API interaction patterns

## 📋 **Detailed Implementation Plan**

### **Phase 0: Foundation Extension** (1-2 days) 🚀

#### **Goal**: Extend existing staging framework for update operations

#### **Milestone 0.1: Update Staging Tables** (2 hours)

**Objective**: Add update tracking capabilities to existing staging tables

**Implementation**:
```sql
-- Extend STG_MON_CustMasterSchedule for updates
ALTER TABLE STG_MON_CustMasterSchedule ADD
    update_operation VARCHAR(50) DEFAULT 'CREATE',  -- CREATE/UPDATE/DELETE
    update_fields NVARCHAR(MAX),                    -- JSON of fields to update
    source_table VARCHAR(100),                      -- Source table/view name
    source_query NVARCHAR(MAX),                     -- Query that generated update
    update_batch_id VARCHAR(50),                    -- Batch tracking
    validation_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/VALID/INVALID
    validation_errors NVARCHAR(MAX);                -- Validation error details

-- Extend STG_MON_CustMasterSchedule_Subitems for updates  
ALTER TABLE STG_MON_CustMasterSchedule_Subitems ADD
    update_operation VARCHAR(50) DEFAULT 'CREATE',
    update_fields NVARCHAR(MAX),
    source_table VARCHAR(100),
    source_query NVARCHAR(MAX),
    update_batch_id VARCHAR(50),
    validation_status VARCHAR(20) DEFAULT 'PENDING',
    validation_errors NVARCHAR(MAX);

-- Create update audit table for rollback capability
CREATE TABLE MON_UpdateAudit (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    batch_id VARCHAR(50),
    update_operation VARCHAR(50),
    monday_item_id BIGINT,
    monday_board_id BIGINT,
    column_id VARCHAR(100),
    old_value NVARCHAR(MAX),
    new_value NVARCHAR(MAX),
    update_timestamp DATETIME2 DEFAULT GETUTCDATE(),
    rollback_timestamp DATETIME2,
    rollback_reason NVARCHAR(500)
);