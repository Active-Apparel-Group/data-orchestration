# Update Monday.com Subitems - Plan & Checklist

## Overview
This script will:
- Load subitem and shipped/packed data from Azure SQL views.
- Use a field mapping matrix to align and join data.
- Match subitems to shipped/packed records.
- Prepare and send async updates to Monday.com via GraphQL API.
- Log all updates and errors.

## Steps & Checklist

- [ ] Load config from config.yaml
- [ ] Load DataFrame from v_mon_customer_ms_subitems.sql (subitems)
- [ ] Load DataFrame from v_shipped.sql (orders_shipped)
- [ ] Load and parse field_mapping_matrix.yaml
- [ ] Normalize and map key columns for join
- [ ] Join/match subitems to shipped/packed data
- [ ] Prepare Monday.com update payloads for each subitem
- [ ] Async update subitems via Monday.com API
- [ ] Log successes and failures
- [ ] Add error handling and summary reporting

## Notes
- Keys for join: Style, PO Number/Customer_PO, Size (mapped via matrix)
- Only update fields in Monday.com that are mapped and have changed
- Use aiohttp for async API calls
- Use robust normalization for matching (upper, strip, etc.)
