---

title: Time_tracking
source: https://developer.monday.com/api-reference/reference/time-tracking
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by and read the time tracking column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Time tracking

Learn how to filter by and read the time tracking column on monday boards using the platform API

The time tracking column represents the total time spent on a task. You can filter by and read the time tracking column via the API, but you currently cannot update or clear it.

## Filter by the time tracking column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the time tracking column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | 1(time tracker paused or empty)2(time tracker running)
not_any_of | 1(time tracker paused or empty)2(time tracker running)

### Examples

The following example returns all items on the specified board with a running time tracker.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "time_tracking", compare_value: [2], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the time tracking column

You can query the time tracking column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the time tracking column are of the TimeTrackingValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on TimeTrackingValue {
        running
        started_at
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
durationInt | The total duration of the time tracker in seconds.
history[TimeTrackingHistoryItem!]! | The column's history.
idID! | The column's unique identifier.
runningBoolean | Returnstrueif the time tracker is currently running.
started_atDate | The date the time tracker started.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
