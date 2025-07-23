# Product Context

## Why This Project Exists

Active Apparel Group’s sales and operations team rely on **Monday.com** as a visual management and tracking tool. Prior to this project, order data from our internal systems was not integrated into Monday.com; team members had to manually enter or update orders on the board or use ad-hoc reports outside Monday.com. This led to **data duplication, delays, and potential errors** in keeping the Monday board up-to-date.

The Order List Monday.com Sync Pipeline was initiated to **solve this problem**. By automatically syncing order information from the source database to Monday.com, we ensure that:
- The Monday.com board always reflects the latest order status (new orders, quantities, customer info, etc.).
- Team members can trust the board as a single source of truth for order tracking, without needing to cross-reference separate systems.
- Manual data entry is minimized, reducing workload and human error.

In short, this project exists to **bridge our internal order processing system with our team’s project management workflow on Monday.com**, providing real-time visibility and updates.

## Problems It Solves

- **Delayed Updates:** Eliminates the lag between an order being created or updated in our system and that information showing up on Monday.com. The sync ensures near real-time updates.
- **Manual Work & Errors:** Removes the need for manual copying of order data to Monday.com. This reduces mistakes (like typos or missed orders) and frees up staff time for more valuable work.
- **Lack of Visibility:** Solves the issue where the operations team lacked a comprehensive, up-to-date view of order fulfillment progress. Now, all stakeholders can just check Monday.com for the latest info.
- **Complex Legacy Process:** Before this project, a complex and over-engineered script was planned to do the integration. It was hard to maintain and slowed our ability to adapt. This new solution dramatically simplifies the process, making it easier to adjust to business changes (like new data fields or different board configurations).

## How It Should Work (User Experience)

When a new order is entered into the internal Order Management System (which populates the `ORDER_LIST` table in the database), this pipeline will pick it up via the `ORDER_LIST` and `ORDER_LIST_LINES` tables. **Behind the scenes:**
- The pipeline groups orders by customer and processes each group, creating a new group on the Monday.com board for that customer if needed.
- Each order header becomes an **Item** in Monday.com under the appropriate customer group, and all the line items (sizes, quantities) for that order become **Subitems** of that Item.
- The Monday.com board will show, for example, an item like “Order #12345 – [Customer Name]” and beneath it subitems for each size or style in that order with quantity details.
- All key order fields (e.g., Order Number, Customer Name, PO Number, Style, Total Quantity, etc.) are populated in the Monday.com item fields so team members have complete information at a glance.
- This sync can be run on a schedule (for instance, every few minutes or hourly). Each run only processes orders that are new or pending sync (marked as `NEW` or `PENDING` in the delta tables), ensuring efficiency.

From a user’s perspective, **no manual steps are required**. They simply notice that new orders show up on the Monday board shortly after they are entered in the system. If an order is updated or corrected in the source, the changes reflect on the board as well (assuming the pipeline marks it for sync again via the delta mechanism).

Furthermore, the user experience includes reliability features: if something goes wrong (say an API outage), the team is informed through logs/alerts, and once the issue is resolved and the pipeline re-runs, any missed orders will sync then. This ensures confidence that the Monday.com view will eventually be consistent with the source data even if delays occur.

## User Experience Goals

- **Clarity:** Orders on Monday.com should be clearly organized by customer and easily readable, mirroring how our team naturally thinks about order groupings.
- **Timeliness:** Minimize the time gap between data changes in the source and updates on the board. Ideally, within the same business day or faster (potentially near real-time).
- **Trust:** Users should come to trust that if an order is in our internal system, it will appear on Monday.com. They shouldn’t have to double-check multiple systems.
- **Minimal Manual Intervention:** The process should rarely require human correction. If an order fails to sync due to an error, it should be logged and retried automatically, or flagged clearly for tech support, rather than silently dropped.
- **Visibility of Status:** It should be easy for a user (or support engineer) to see whether an order has been synced or not. This is facilitated by the `sync_state` fields in the database and could be extended to include status indicators on the Monday board (like a status column for “Synced” vs “Pending” if needed).

By achieving these goals, the project will improve operational efficiency and data transparency for Active Apparel Group’s order management process.
