---

title: Other_types
source: https://developer.monday.com/api-reference/reference/ea-other-types
author:
  - Monday
published:
created: 2025-05-25
description: Learn about other Emails &amp; Activities-specific types supported by the monday platform API
tags: [code, api, monday-dot-com]
summary:

---

# Other types

Learn about other Emails & Activities-specific types supported by the monday platform API

# Timeline items page

The TimelineItemsPage type is used as a field on timeline queries . It returns a paginated set of timeline items. It also utilizes cursor-based pagination to return the remaining pages of items.

### Arguments

Argument | Description
--- | ---
cursorString | The cursor for the next set of timeline items to return.
limitInt | The number of timeline items to get. The default is 25.

### Fields

Field | Description | Supported fields
--- | --- | ---
cursorString | An opaque token representing the position in a set of results to fetch timeline items from. Use this to paginate through large result sets. | 
timeline_items[TimelineItem!]! | The timeline items in the current page. | boardBoardcontentStringcreated_atDate!custom_activity_idStringidIDitemItemtitleStringtypeStringuserUser
