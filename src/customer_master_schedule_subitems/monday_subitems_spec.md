# Monday Subitems Integration Specification & Checklist

## Overview
This solution is split into two scripts for clarity and maintainability:

### 1. mon_get_subitems_async.py
- Fetches Item IDs from the MON_CustMasterSchedule (via the v_mon_customer_ms_itemIDs.sql view).
- For each Item ID, queries Monday.com (GraphQL API) to fetch all subitems and their details.
- Stores subitem data in an Azure SQL database, linking subitems to their parent MON_CustMasterSchedule items.

### 2. mon_update_subitems_async.py
- Connects subitem data to orders_shipped and orders_packed tables/views for downstream reporting.
- Supports updating Monday.com subitems via the GraphQL API.
- Uses async HTTP requests for efficient data retrieval from Monday.com.
- Configuration for Monday.com API and Azure SQL is loaded from config.yaml.
- Designed for robust error handling and logging.

---

## Checklist

### Common
- [ ] Load Monday.com and Azure SQL configuration from config.yaml.
- [ ] Use robust error handling and logging.
- [ ] Document all functions and key logic sections.

### mon_get_subitems_async.py
- [ ] Query Azure SQL to get all Item IDs from v_mon_customer_ms_itemIDs.sql.
- [ ] For each Item ID, asynchronously query Monday.com for subitems using the provided GraphQL query.
- [ ] Parse and normalize subitem data, including all relevant columns and parent/board IDs.
- [ ] Store subitem data in an Azure SQL table, linking to parent Item ID.

### mon_update_subitems_async.py
- [ ] Relate subitem table to MON_CustMasterSchedule, orders_shipped, and orders_packed.
- [ ] Provide a function to update Monday.com subitems via the GraphQL API.
- [ ] Implement async HTTP requests for Monday.com updates.
- [ ] Add summary and error report at the end of the script.

---

## Testing
- [ ] Test fetching subitems for a sample Item ID.
- [ ] Test storing and relating subitem data in Azure SQL.
- [ ] Test updating a subitem via the API.
- [ ] Validate error handling and logging.

## Notes
- All sensitive data (API keys, DB credentials) must be loaded from config.yaml.
