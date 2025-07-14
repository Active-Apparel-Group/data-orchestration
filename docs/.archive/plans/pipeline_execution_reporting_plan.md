# Pipeline Execution Reporting System Plan

## Overview
Create a comprehensive reporting system that generates beautiful markdown summaries for each customer pipeline execution, stored in PostgreSQL with JSON columns for rich formatting and historical tracking.

## System Architecture

### Database Schema (PostgreSQL)
```sql
-- Pipeline execution reports table
CREATE TABLE pipeline_execution_reports (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    execution_date DATE NOT NULL,
    pipeline_type VARCHAR(100) NOT NULL, -- 'orders', 'manufacturing', 'shipping'
    execution_id VARCHAR(255) NOT NULL,  -- Kestra execution ID
    status VARCHAR(50) NOT NULL,         -- 'success', 'failed', 'partial'
    markdown_content TEXT NOT NULL,      -- Full markdown report
    summary_json JSONB NOT NULL,         -- Structured summary data
    metrics_json JSONB,                  -- Performance metrics
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(customer_name, execution_date, pipeline_type)
);

-- Daily customer summaries (aggregated view)
CREATE TABLE daily_customer_summaries (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    summary_date DATE NOT NULL,
    total_pipelines INTEGER DEFAULT 0,
    successful_pipelines INTEGER DEFAULT 0,
    new_orders INTEGER DEFAULT 0,
    updated_orders INTEGER DEFAULT 0,
    manufacturing_updates INTEGER DEFAULT 0,
    shipping_updates INTEGER DEFAULT 0,
    combined_markdown TEXT,              -- Daily summary markdown
    status_json JSONB,                   -- Overall daily status
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(customer_name, summary_date)
);
```

## Report Format Examples

### Sample Order Pipeline Report
```markdown
# 📋 Pipeline Execution Report

**Customer**: ACTIVELY BLACK  
**Date**: 2025-06-17  
**Pipeline**: Order Sync  
**Execution ID**: kestra_exec_20250617_001234  
**Status**: ✅ SUCCESS  

---

## 📊 Execution Summary

| Metric | Value | Change |
|--------|-------|---------|
| **New Orders** | 45 | +12 from yesterday |
| **Updated Orders** | 23 | +5 from yesterday |
| **Processing Time** | 2.4 minutes | -30s improvement |
| **Records Processed** | 1,247 | +156 from yesterday |

---

## 🔄 Order Changes

### ✅ New Orders Added (45)
- **ACT-2025-001** - Spring Collection Hoodie (Qty: 500)
- **ACT-2025-002** - Summer Tee Basic (Qty: 1,200)
- **ACT-2025-003** - Winter Jacket Premium (Qty: 300)
- ... (42 more)

### 📝 Orders Updated (23)
- **ACT-2024-945** - Quantity changed: 800 → 850 (+50)
- **ACT-2024-902** - Delivery date updated: 2025-07-15 → 2025-07-10
- **ACT-2024-888** - Status: In Production → Ready to Ship
- ... (20 more)

---

## 🏭 Manufacturing Updates

### Production Status Changes
- **5 orders** moved to "Cut Complete"
- **8 orders** moved to "Sewing In Progress"  
- **12 orders** moved to "Finished Goods"

### Quality Control
- **3 orders** flagged for quality review
- **15 orders** passed final inspection

---

## 🚚 Shipping Updates

### Ready to Ship
- **18 orders** ready for pickup
- **Total volume**: 45,600 units
- **Estimated ship date**: 2025-06-18

### Shipped Today
- **12 orders** shipped via FedEx
- **8 orders** shipped via UPS
- **Total shipped volume**: 32,100 units

---

## ⚡ Performance Metrics

```json
{
  "execution_time_seconds": 144,
  "records_per_second": 8.66,
  "database_operations": {
    "inserts": 45,
    "updates": 23,
    "queries": 156
  },
  "api_calls": {
    "monday_com": 12,
    "manufacturing_system": 8,
    "shipping_system": 5
  },
  "error_count": 0,
  "warning_count": 2
}
```

---

## 🎯 Next Actions

- [ ] Review 3 quality flagged orders
- [ ] Coordinate pickup for 18 ready-to-ship orders
- [ ] Follow up on 2 delayed production items

---

*Report generated at: 2025-06-17 15:30:22*  
*Kestra Execution: [View Details](https://kestra.company.com/executions/20250617_001234)*
```

## Implementation Components

### 1. Report Generation Library (`scripts/reporting/`)

```python
# scripts/reporting/pipeline_reporter.py
class PipelineReporter:
    def __init__(self, customer_name, pipeline_type, execution_id):
        self.customer_name = customer_name
        self.pipeline_type = pipeline_type
        self.execution_id = execution_id
        self.start_time = datetime.now()
        self.metrics = {}
        self.changes = []
        self.warnings = []
        self.errors = []
    
    def log_change(self, category, description, count=1):
        """Log a change with category and description"""
        
    def log_metric(self, name, value, previous_value=None):
        """Log a performance metric"""
        
    def add_warning(self, message):
        """Add a warning to the report"""
        
    def add_error(self, message):
        """Add an error to the report"""
        
    def generate_markdown(self) -> str:
        """Generate beautiful markdown report"""
        
    def save_to_database(self, db_key="postgres"):
        """Save report to PostgreSQL database"""
```

### 2. Integration with Existing Scripts

```python
# Example integration in get_board_planning.py
from reporting.pipeline_reporter import PipelineReporter

async def main():
    # Initialize reporter
    reporter = PipelineReporter(
        customer_name="ACTIVELY BLACK",
        pipeline_type="order_sync", 
        execution_id=os.getenv('KESTRA_EXECUTION_ID')
    )
    
    try:
        # Existing ETL process
        truncate_table()
        reporter.log_change("data_refresh", "Table truncated for full refresh")
        
        items, board_name = fetch_board_data_with_pagination()
        reporter.log_metric("items_fetched", len(items))
        
        # ... existing processing ...
        
        success_count, fail_count = await production_concurrent_insert(df)
        reporter.log_metric("records_inserted", success_count)
        reporter.log_metric("records_failed", fail_count)
        
        # Generate and save report
        reporter.save_to_database()
        
    except Exception as e:
        reporter.add_error(f"Pipeline failed: {e}")
        reporter.save_to_database()
        raise
```

### 3. Daily Summary Aggregator

```python
# scripts/reporting/daily_summarizer.py
def generate_daily_summary(customer_name, summary_date):
    """Aggregate all pipeline reports for a customer on a given date"""
    reports = get_daily_reports(customer_name, summary_date)
    
    combined_markdown = f"""
# 📅 Daily Summary - {customer_name}
**Date**: {summary_date}

## 🏃‍♂️ Pipeline Executions
{len(reports)} total pipeline runs

## 📈 Daily Totals
- **New Orders**: {sum(r.new_orders for r in reports)}
- **Updated Orders**: {sum(r.updated_orders for r in reports)}
- **Manufacturing Updates**: {sum(r.manufacturing_updates for r in reports)}

## 🕒 Timeline
{generate_timeline(reports)}
"""
    
    save_daily_summary(customer_name, summary_date, combined_markdown)
```

## Use Cases

### 1. **Customer Dashboards**
- Daily email summaries with markdown reports
- Web dashboard showing latest pipeline status
- Historical trend analysis

### 2. **Operations Monitoring**
- Pipeline health monitoring
- Performance trending
- Error pattern detection

### 3. **Customer Success**
- Proactive communication about order changes
- Delivery timeline updates
- Production status visibility

## Implementation Timeline

### Phase 1 (Week 1)
- [ ] Design PostgreSQL schema
- [ ] Create basic `PipelineReporter` class
- [ ] Integrate with one pipeline (get_board_planning.py)

### Phase 2 (Week 2)  
- [ ] Add reporting to all major pipelines
- [ ] Create daily summary aggregator
- [ ] Build simple web dashboard

### Phase 3 (Week 3)
- [ ] Email notification system
- [ ] Historical analysis tools
- [ ] Customer-specific customization

## Benefits

1. **📊 Visibility**: Clear understanding of daily pipeline operations
2. **🚀 Proactive**: Early detection of issues and delays  
3. **💬 Communication**: Automated customer updates
4. **📈 Analytics**: Historical trends and performance optimization
5. **🔍 Debugging**: Detailed execution logs for troubleshooting

---

**Status**: 📋 Future Enhancement Plan  
**Priority**: 🌟 High Value - Customer Experience  
**Dependencies**: Current refactoring completion, PostgreSQL setup
