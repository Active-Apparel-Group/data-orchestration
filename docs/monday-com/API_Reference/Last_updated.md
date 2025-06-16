---

title: Last_updated
source: https://developer.monday.com/api-reference/reference/last-updated
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by and read the last updated column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Last updated

Learn how to filter by and read the last updated column on monday boards using the platform API

The last updated column represents when an item was last updated. You can filter by and read the last updated column via the API, but you currently cannot update or clear it.

## Filter by the last updated column

Using the items_page object, you can easily filter a board's items based on specific columns or column values.

The last updated column is unique in that you don't need to add the column to your board in order to filter by it. Instead, use "__last_updated__" as the column ID and define your rules as you would for any other column (see example here).

Regardless of whether the column is visible on the board, you can filter items by:

- Who last updated them
- When they were last updated

💡 The results depend on the timezone, date format, and first day of the week settings configured in the monday.com profile of the user making the API call.

The table below outlines the supported operators, compare values, and compare attributes for the last updated column. Note: The not_any_of operator returns items that do not match the specified compare value(s).

Compare value | Description | Operators | Compare attributes | Compare attribute required?
--- | --- | --- | --- | ---
"assigned_to_me" | Includes/excludes items last updated by the user making the API call | any_of,not_any_of | - | No
"person-123456" | Includes/excludes items last updated by a specific user | any_of,not_any_of | - | No
"TODAY" | Includes/excludes items last updated today | any_of,not_any_of | "UPDATED_AT" | Yes
"YESTERDAY" | Includes/excludes items last updated yesterday | any_of,not_any_of | "UPDATED_AT" | Yes
"THIS_WEEK" | Includes/excludes items last updated this week | any_of,not_any_of | "UPDATED_AT" | Yes
"LAST_WEEK" | Includes/excludes items last updated last week | any_of,not_any_of | "UPDATED_AT" | Yes
"THIS_MONTH" | Includes/excludes items last updated this month | any_of,not_any_of | "UPDATED_AT" | Yes
"LAST_MONTH" | Includes/excludes items last updated last month | any_of,not_any_of | "UPDATED_AT" | Yes
"PAST_DATETIME" | Includes all items last updated in the past | any_of | "UPDATED_AT" | Yes

### Examples

The following example returns all items on the specified board that were last updated on today's date, even though there is no last updated column on the board.

GraphQL
```
query {
  boards(ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "__last_updated__", compare_value: ["TODAY"], operator:any_of, compare_attribute:"UPDATED_AT"}]}) {
      items {
        id
        name
      }
    }
  }
}
```

The following example returns all items on the specified board that were last updated by user 123456.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "last_updated", compare_value: ["person-123456"], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the last updated column

You can query the last updated column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the last updated column are of the LastUpdatedValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on LastUpdatedValue {
        updated_at
        value
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
idID! | The column's unique identifier.
textString | The column's value as text.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
updaterUser! | The user who last updated the item.
updater_idID! | The unique identifier of the user who last updated the item.
valueJSON | The column's JSON-formatted raw value.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
