---

title: Timeline
source: https://developer.monday.com/api-reference/reference/timeline-ea
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read an item's Email &amp; Activities timeline using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Timeline

Learn how to read an item's Email & Activities timeline using the platform API

The Emails & Activities app (E&A) is a useful tool that enables monday.com CRM customers to manage client communication in one centralized location. Each contact is logged and tracked in the app's timeline for easy access to important details and updates.

Every item has its own E&A timeline where activities are logged. You can use the timeline endpoint to query a specific item's timeline.

# Queries

- Returns an array containing metadata about a specific item's E&A timeline
- Can only be queried directly at the root
- Utilizes cursor-based pagination to return results

GraphQL
```
query {
  timeline (id: 1234567890) {
    timeline_items_page {
      cursor
      timeline_items {
        id 
        content
      }
    }
  }
}
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your timeline query.

Argument | Description
--- | ---
idID! | The unique identifier of the item to retrieve timeline activities from.

## Fields

You can use the following field(s) to specify what information your timeline query will return.

Field | Description | Supported fields
--- | --- | ---
timeline_items_pageTimelineItemsPage! | A paginated set of timeline items. | cursorStringtimeline_items[TimelineItem!]!
