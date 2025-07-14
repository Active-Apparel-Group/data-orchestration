# Future Developments Beyond Phase 1

## Overview

With the simplified staging → Monday.com → clear architecture in place, future enhancements focus on advanced capabilities while maintaining the clean design.

## 1. GraphQL Schema Management

### Current State
GraphQL queries embedded in Python code, making maintenance difficult.

### Proposed Solution
Centralized GraphQL schema management:

```
/src/monday_graphql/
  ├── schemas/
  │   ├── mutations/
  │   │   ├── create_item.graphql
  │   │   ├── update_item.graphql
  │   │   ├── create_subitem.graphql
  │   │   └── bulk_create_items.graphql
  │   ├── queries/
  │   │   ├── get_board_groups.graphql
  │   │   ├── get_item_by_column_value.graphql
  │   │   └── get_subitems.graphql
  │   └── fragments/
  │       ├── item_fields.graphql
  │       └── subitem_fields.graphql
  ├── schema_loader.py
  └── query_builder.py
```

### Implementation
```python
class GraphQLSchemaManager:
    """Manage GraphQL schemas with variable injection"""
    
    def __init__(self, schema_dir: str):
        self.schema_dir = schema_dir
        self._cache = {}
        self._fragments = self._load_fragments()
    
    def get_mutation(self, name: str, variables: dict) -> str:
        """Load and populate mutation with variables"""
        template = self._load_schema('mutations', name)
        return self._inject_variables(template, variables)
    
    def _inject_variables(self, template: str, variables: dict) -> str:
        """Safe variable injection with escaping"""
        for key, value in variables.items():
            if isinstance(value, str):
                value = value.replace('"', '\\"')
            template = template.replace(f'{{{key}}}', str(value))
        return template
```

## 2. Advanced Change Detection

### Hash-Based Change Tracking
```sql
-- Add to ORDERS_UNIFIED
ALTER TABLE dbo.ORDERS_UNIFIED ADD
    row_hash AS HASHBYTES('SHA2_256', 
        CONCAT(
            ISNULL([AAG ORDER NUMBER], ''),
            ISNULL([CUSTOMER], ''),
            ISNULL(CAST([ORDER QTY] AS VARCHAR), ''),
            -- ... other fields
        )
    ) PERSISTED,
    last_sync_hash VARCHAR(64),
    last_sync_date DATETIME2,
    monday_item_id BIGINT;

-- Index for efficient change detection
CREATE INDEX IX_ORDERS_UNIFIED_ChangeDetection 
ON dbo.ORDERS_UNIFIED (row_hash, last_sync_hash)
WHERE row_hash != last_sync_hash OR last_sync_hash IS NULL;
```

### Change Detection Query
```python
def get_changed_orders(self, customer: str) -> pd.DataFrame:
    """Get new and changed orders efficiently"""
    query = """
        SELECT *
        FROM dbo.ORDERS_UNIFIED
        WHERE CUSTOMER = ?
          AND (row_hash != last_sync_hash OR last_sync_hash IS NULL)
          AND [AAG ORDER NUMBER] NOT LIKE '%CANCELLED%'
        ORDER BY [AAG ORDER NUMBER]
    """
    return pd.read_sql(query, self.conn, params=[customer])
```

## 3. Bulk Operations Optimization

### Parallel Processing Framework
```python
class ParallelBatchProcessor:
    """Process multiple customers concurrently"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_customers_async(self, customers: List[str]) -> Dict[str, Any]:
        """Process customers in parallel with rate limiting"""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_with_limit(customer: str):
            async with semaphore:
                try:
                    return await self._process_customer_async(customer)
                except Exception as e:
                    logger.error(f"Failed processing {customer}: {e}")
                    return {'customer': customer, 'status': 'failed', 'error': str(e)}
        
        tasks = [process_with_limit(c) for c in customers]
        results = await asyncio.gather(*tasks)
        
        return {r['customer']: r for r in results}
```

### Bulk Monday.com Operations
```graphql
# bulk_create_items.graphql
mutation BulkCreateItems($boardId: ID!, $items: [ItemInput!]!) {
  create_items(
    board_id: $boardId,
    items: $items
  ) {
    items {
      id
      name
      column_values {
        id
        value
      }
    }
    errors {
      message
      code
    }
  }
}
```

## 4. Smart Error Recovery

### Circuit Breaker Pattern
```python
class MondayApiCircuitBreaker:
    """Prevent cascading failures with circuit breaker"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
    
    async def call_api(self, operation: Callable, *args, **kwargs):
        """Execute API call with circuit breaker protection"""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpen("Monday.com API circuit breaker is OPEN")
        
        try:
            result = await operation(*args, **kwargs)
            self._on_success()
            return result
        except MondayApiError as e:
            self._on_failure()
            raise
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning("Circuit breaker OPENED due to repeated failures")
```

### Intelligent Retry Strategy
```python
class AdaptiveRetryHandler:
    """Adapt retry strategy based on error type"""
    
    def __init__(self):
        self.strategies = {
            'RATE_LIMIT': self._exponential_backoff,
            'TIMEOUT': self._linear_backoff,
            'SERVER_ERROR': self._exponential_backoff,
            'INVALID_DATA': self._no_retry
        }
    
    async def retry_operation(self, operation: Callable, error_type: str, 
                            max_attempts: int = 3) -> Any:
        """Retry with appropriate strategy"""
        strategy = self.strategies.get(error_type, self._exponential_backoff)
        
        for attempt in range(max_attempts):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                
                wait_time = strategy(attempt)
                logger.info(f"Retry {attempt + 1}/{max_attempts} after {wait_time}s")
                await asyncio.sleep(wait_time)
```

## 5. Data Quality Framework

### Validation Pipeline
```python
class DataQualityValidator:
    """Comprehensive data validation before staging"""
    
    def __init__(self):
        self.validators = [
            RequiredFieldsValidator(),
            DataTypeValidator(),
            BusinessRuleValidator(),
            ReferentialIntegrityValidator()
        ]
    
    def validate_batch(self, df: pd.DataFrame) -> ValidationReport:
        """Run all validations and generate report"""
        report = ValidationReport()
        
        for validator in self.validators:
            result = validator.validate(df)
            report.add_result(result)
            
            if result.severity == 'CRITICAL' and not result.passed:
                report.halt_processing = True
                break
        
        return report

class BusinessRuleValidator:
    """Validate business logic rules"""
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        issues = []
        
        # Example: Order quantity must match sum of sizes
        for idx, row in df.iterrows():
            size_sum = sum([row[col] for col in df.columns 
                          if col.startswith('SIZE_') and pd.notna(row[col])])
            if row['TOTAL QTY'] != size_sum:
                issues.append({
                    'row': idx,
                    'field': 'TOTAL QTY',
                    'message': f"Total qty {row['TOTAL QTY']} != sum of sizes {size_sum}"
                })
        
        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            severity='WARNING'
        )
```

## 6. Monitoring and Observability

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

class StagingMetrics:
    """Prometheus metrics for staging workflow"""
    
    def __init__(self):
        self.orders_processed = Counter('staging_orders_processed_total', 
                                      'Total orders processed', 
                                      ['customer', 'status'])
        
        self.processing_time = Histogram('staging_processing_seconds',
                                       'Time to process batch',
                                       ['customer', 'operation'])
        
        self.staging_table_size = Gauge('staging_table_rows',
                                      'Current rows in staging',
                                      ['table'])
        
        self.api_calls = Counter('monday_api_calls_total',
                               'Monday.com API calls',
                               ['operation', 'status'])
    
    @contextmanager
    def track_batch(self, customer: str, operation: str):
        """Track batch processing time"""
        start = time.time()
        try:
            yield
            self.orders_processed.labels(customer=customer, status='success').inc()
        except Exception:
            self.orders_processed.labels(customer=customer, status='failed').inc()
            raise
        finally:
            duration = time.time() - start
            self.processing_time.labels(customer=customer, operation=operation).observe(duration)
```

### Health Check Endpoint
```python
class HealthChecker:
    """System health monitoring"""
    
    async def check_health(self) -> dict:
        """Comprehensive health check"""
        checks = {
            'database': await self._check_database(),
            'monday_api': await self._check_monday_api(),
            'staging_tables': await self._check_staging_tables(),
            'last_batch': await self._check_last_batch()
        }
        
        overall_health = all(c['healthy'] for c in checks.values())
        
        return {
            'status': 'healthy' if overall_health else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }
    
    async def _check_staging_tables(self) -> dict:
        """Check staging table health"""
        try:
            # Check for old unprocessed records
            old_records_query = """
                SELECT COUNT(*) as count
                FROM STG_MON_CustMasterSchedule
                WHERE stg_created_date < DATEADD(hour, -24, GETDATE())
                  AND stg_status = 'PENDING'
            """
            
            old_count = await self.db.fetch_scalar(old_records_query)
            
            return {
                'healthy': old_count == 0,
                'old_pending_records': old_count,
                'message': f"{old_count} records pending >24 hours" if old_count > 0 else "OK"
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
```

## 7. Advanced Features

### Dynamic Column Mapping
```python
class DynamicColumnMapper:
    """Handle Monday.com board schema changes dynamically"""
    
    async def refresh_board_schema(self, board_id: str):
        """Fetch current board schema from Monday.com"""
        query = """
            query GetBoardSchema($boardId: ID!) {
                boards(ids: [$boardId]) {
                    columns {
                        id
                        title
                        type
                        settings_str
                    }
                }
            }
        """
        
        result = await self.monday_client.query(query, {'boardId': board_id})
        self._update_mapping_cache(result)
    
    def map_value(self, column_id: str, value: Any) -> Any:
        """Map value based on current schema"""
        column_type = self.schema_cache[column_id]['type']
        
        if column_type == 'numeric':
            return float(value) if value else 0
        elif column_type == 'date':
            return self._format_date(value)
        elif column_type == 'dropdown':
            return {'labels': [str(value)]} if value else None
        
        return str(value) if value else ""
```

### Webhook Integration
```python
class MondayWebhookHandler:
    """Handle Monday.com webhooks for two-way sync"""
    
    async def handle_item_updated(self, webhook_data: dict):
        """Process item update from Monday.com"""
        item_id = webhook_data['event']['itemId']
        column_id = webhook_data['event']['columnId']
        new_value = webhook_data['event']['value']
        
        # Update local tracking if needed
        if column_id in self.tracked_columns:
            await self.update_local_tracking(item_id, column_id, new_value)
```

## Timeline

### Phase 2 (Months 1-2)
- Change detection implementation
- Update workflow
- Basic bulk operations

### Phase 3 (Months 2-3)
- GraphQL schema management
- Advanced error recovery
- Data quality framework

### Phase 4 (Months 3-4)
- Full monitoring suite
- Performance optimizations
- Dynamic mapping

### Phase 5 (Months 4-6)
- Webhook integration
- Advanced analytics
- Multi-board support

## Success Criteria

Each enhancement must:
1. Maintain the simple staging → Monday → clear pattern
2. Include comprehensive testing
3. Document all changes
4. Show measurable improvement
5. Support rollback capability