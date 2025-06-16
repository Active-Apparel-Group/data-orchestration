---

title: Progress_tracking
source: https://developer.monday.com/api-reference/reference/progress-tracking
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by the progress tracking column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Progress tracking

Learn how to filter by the progress tracking column on monday boards using the platform API

The progress tracking column combines all the status columns on a board into one column to visually track your progress. You can filter by your results by the progress tracking column via the API, but you currently cannot read, update, or clear it.

## Filter by the progress tracking column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the progress tracking column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | 0(items less than 20% done)"20"(items more than 20% done)"50"(items more than 50% done)"80"(items more than 80% done)"100"(items that are done)""(blank values)
not_any_of | 0(items less than 20% done)"20"(items more than 20% done)"50"(items more than 50% done)"80"(items more than 80% done)"100"(items that are done)""(blank values)

### Examples

The following example returns all items on the specified board that are more than 80% complete.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "progress", compare_value: ["80"], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
