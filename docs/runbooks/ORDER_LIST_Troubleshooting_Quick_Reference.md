# ORDER_LIST Pipeline - Troubleshooting Quick Reference

**Version**: 1.0  
**Date**: July 10, 2025  
**Status**: 🟢 Production  

## 🚨 Emergency Response Guide

### ⚡ Quick Fixes (< 5 minutes)

| Issue | Symptoms | Quick Fix | VS Code Task |
|-------|----------|-----------|--------------|
| **Pipeline Hanging** | Extract stage freezes | `Ctrl+C` → Restart with `--limit-files 5` | `ORDER_LIST: Complete Pipeline (Test Mode)` |
| **Authentication Error** | Azure auth failures | Check environment variables | `Ops: Validate Environment` |
| **Database Connection** | Connection timeouts | Verify VPN/network connectivity | `Ops: Validate Environment` |
| **Memory Issues** | High memory usage | Restart pipeline with smaller batches | `ORDER_LIST: Extract Only Pipeline` |
| **Unicode Errors** | Character encoding issues | Use PowerShell, not Command Prompt | Switch terminal type |

### 🔍 Diagnosis Commands (< 2 minutes)

```powershell
# Quick health check
python pipelines/scripts/load_order_list/order_list_pipeline.py --validation-only

# Test connectivity
python dev/audit-pipeline/validation/validate_env.py

# Limited pipeline test (5 files only)
python pipelines/scripts/load_order_list/order_list_pipeline.py --limit-files 5

# Extract-only test
python pipelines/scripts/load_order_list/order_list_pipeline.py --extract-only

# Transform-only test  
python pipelines/scripts/load_order_list/order_list_pipeline.py --transform-only
```

---

## 🔧 Common Issues & Solutions

### 1. **Extract Stage Issues**

#### ❌ Issue: Extract stage hangs or freezes
```
Symptoms: 
- Stage 1 starts but never progresses
- No file processing activity
- High CPU usage but no output

Root Cause: Module-level blob client initialization causing blocking
```
**✅ Solution:**
```powershell
# Kill the process and restart with limited files
Ctrl+C
python pipelines/scripts/load_order_list/order_list_pipeline.py --limit-files 5
```

#### ❌ Issue: Azure authentication failures
```
Symptoms:
- "No credential available" errors
- "Authentication failed" messages
- Empty token responses

Root Cause: Missing or incorrect environment variables
```
**✅ Solution:**
```powershell
# Check environment variables (run in PowerShell)
echo $env:AZURE_CLIENT_ID
echo $env:AZURE_CLIENT_SECRET  
echo $env:AZURE_TENANT_ID

# If missing, set them:
$env:AZURE_CLIENT_ID = "your-client-id"
$env:AZURE_CLIENT_SECRET = "your-client-secret"
$env:AZURE_TENANT_ID = "your-tenant-id"
```

#### ❌ Issue: Blob storage connectivity problems
```
Symptoms:
- "Container not found" errors
- SAS token generation failures
- Network timeout errors

Root Cause: Network connectivity or container permissions
```
**✅ Solution:**
```powershell
# Test Azure connectivity
python tests/debug/test_pipeline_imports.py

# Validate environment
python dev/audit-pipeline/validation/validate_env.py
```

### 2. **Transform Stage Issues**

#### ❌ Issue: Schema validation failures
```
Symptoms:
- "Column does not exist" errors
- Data type conversion failures
- DDL creation errors

Root Cause: Missing DDL schema file or incorrect column mappings
```
**✅ Solution:**
```powershell
# Check if DDL file exists
ls sql/ddl/tables/ORDER_LIST.sql

# Test transform with existing raw data
python pipelines/scripts/load_order_list/order_list_pipeline.py --transform-only
```

#### ❌ Issue: Database connection timeouts
```
Symptoms:
- "Connection timeout" errors
- "Login timeout expired" messages
- Database unavailable errors

Root Cause: Database connectivity or VPN issues
```
**✅ Solution:**
```powershell
# Test database connectivity
python dev/audit-pipeline/validation/validate_env.py

# Check specific database
python tests/debug/test_pipeline_imports.py
```

### 3. **Performance Issues**

#### ❌ Issue: Slow extract performance (< 200 records/second)
```
Symptoms:
- Extract taking > 3 minutes
- Low throughput metrics
- High memory usage

Root Cause: Inefficient blob client initialization or network issues
```
**✅ Solution:**
```powershell
# Run with performance monitoring
python pipelines/scripts/load_order_list/order_list_pipeline.py --limit-files 10

# Check network connectivity
python dev/audit-pipeline/validation/validate_env.py
```

#### ❌ Issue: Slow transform performance (< 500 records/second)
```
Symptoms:
- Transform taking > 2 minutes
- High CPU usage on database server
- Memory pressure

Root Cause: Database performance or query optimization issues
```
**✅ Solution:**
```powershell
# Run transform-only with monitoring
python pipelines/scripts/load_order_list/order_list_pipeline.py --transform-only

# Check database performance
# Monitor SQL Server performance counters during execution
```

### 4. **Data Quality Issues**

#### ❌ Issue: Missing or corrupted source files
```
Symptoms:
- "File not found" errors
- Zero records processed
- Unexpected file count

Root Cause: Blob storage sync issues or file corruption
```
**✅ Solution:**
```powershell
# Check blob storage connectivity
python tests/debug/test_pipeline_imports.py

# Run limited test to identify problematic files
python pipelines/scripts/load_order_list/order_list_pipeline.py --limit-files 5
```

#### ❌ Issue: Data type conversion errors
```
Symptoms:
- "Conversion failed" errors
- NULL values where not expected
- Precision loss warnings

Root Cause: Schema mismatches or data quality issues
```
**✅ Solution:**
```powershell
# Run comprehensive validation
python tests/end_to_end/test_order_list_complete_pipeline.py

# Check data quality
python pipelines/scripts/load_order_list/order_list_pipeline.py --validation-only
```

---

## 🏥 Health Checks

### 📊 Quick Health Assessment

Run this command for immediate pipeline health status:
```powershell
python pipelines/scripts/load_order_list/order_list_pipeline.py --validation-only
```

**Expected Output:**
```
✅ Database connectivity: SUCCESS
✅ Blob storage access: SUCCESS  
✅ ORDER_LIST table: 101,404 records
✅ Data quality: 100% valid records
✅ Last update: 2025-07-10 14:30:22
```

### 🔍 Detailed Diagnostics

For comprehensive system validation:
```powershell
python tests/end_to_end/test_order_list_complete_pipeline.py --limit-files 3
```

**Expected Results:**
- ✅ Phase 1: Data Availability (< 10 seconds)
- ✅ Phase 2: Extract Validation (< 30 seconds)
- ✅ Phase 3: Transform Validation (< 20 seconds)
- ✅ Phase 4: Data Integrity (< 5 seconds)
- ✅ Phase 5: Performance Testing (< 5 seconds)

---

## 🚨 Escalation Procedures

### Level 1: Self-Service (0-15 minutes)
1. **Check this troubleshooting guide**
2. **Run health checks**: `--validation-only`
3. **Try limited pipeline**: `--limit-files 5`
4. **Restart with clean environment**

### Level 2: Team Support (15-60 minutes)
1. **Gather diagnostics**: Run full test suite with `--limit-files 3`
2. **Check system resources**: Memory, CPU, network
3. **Review recent changes**: Code, configuration, environment
4. **Contact team lead with diagnostic output**

### Level 3: Infrastructure Support (60+ minutes)
1. **Database team**: SQL Server performance issues
2. **Azure team**: Blob storage or authentication issues  
3. **Network team**: Connectivity or VPN problems
4. **Management**: Business impact assessment

---

## 📊 Performance Baselines

### ⚡ Expected Performance Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| **Total Runtime** | < 6 minutes | > 8 minutes | > 10 minutes |
| **Extract Throughput** | > 400 rec/sec | < 300 rec/sec | < 200 rec/sec |
| **Transform Throughput** | > 700 rec/sec | < 500 rec/sec | < 300 rec/sec |
| **Memory Usage** | < 1.5 GB | > 2.0 GB | > 3.0 GB |
| **Success Rate** | 100% | < 99% | < 95% |

### 📈 Trend Analysis

**Weekly Performance Review:**
```powershell
# Generate performance trend report
python pipelines/scripts/load_order_list/order_list_pipeline.py > performance_log.txt
```

**Monthly Capacity Planning:**
- Review file count trends (current: 45 files)
- Monitor record volume growth (current: 101K+ records)
- Assess runtime trends and optimization opportunities

---

## 🛠️ Maintenance Procedures

### 📅 Daily Operations
- **Health Check**: Run `--validation-only` each morning
- **Monitor Logs**: Review console output for warnings
- **Verify Connectivity**: Ensure Azure and database access

### 📅 Weekly Maintenance
- **Cleanup Raw Tables**: Remove old `x_CUSTOMER_ORDER_LIST_RAW_*` tables
- **Performance Review**: Analyze runtime trends
- **Environment Validation**: Run comprehensive test suite

### 📅 Monthly Review
- **Capacity Planning**: Assess growth trends and resource needs
- **Performance Optimization**: Review and optimize slow components
- **Documentation Update**: Update troubleshooting guides and runbooks

---

## 📞 Emergency Contacts

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| **Production Down** | Data Engineering Team Lead | 15 minutes |
| **Database Issues** | DBA Team | 30 minutes |
| **Azure/Network** | Infrastructure Team | 60 minutes |
| **Business Impact** | Operations Manager | Immediate |

---

## 📋 Useful Commands Cheat Sheet

```powershell
# HEALTH & DIAGNOSTICS
python pipelines/scripts/load_order_list/order_list_pipeline.py --validation-only
python dev/audit-pipeline/validation/validate_env.py
python tests/debug/test_pipeline_imports.py

# TESTING & DEVELOPMENT  
python tests/end_to_end/test_order_list_complete_pipeline.py --limit-files 3
python pipelines/scripts/load_order_list/order_list_pipeline.py --limit-files 5

# PRODUCTION OPERATIONS
python pipelines/scripts/load_order_list/order_list_pipeline.py  # Full pipeline
python pipelines/scripts/load_order_list/order_list_pipeline.py --extract-only
python pipelines/scripts/load_order_list/order_list_pipeline.py --transform-only

# PERFORMANCE MONITORING
python pipelines/scripts/load_order_list/order_list_pipeline.py | Tee-Object performance.log
```

---

**📋 Document Control**
- **Created**: July 10, 2025
- **Last Updated**: July 10, 2025  
- **Next Review**: August 10, 2025
- **Version**: 1.0
- **Emergency Contact**: Data Engineering Team
