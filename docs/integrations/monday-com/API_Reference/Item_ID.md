---

title: Item_ID
source: https://developer.monday.com/api-reference/reference/item-id
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read the item ID column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Item ID

Learn how to read the item ID column on monday boards using the platform API

The item ID column represents the unique identifier assigned to each item. You can read the item ID column via the API, but you currently cannot filter, update, or clear it.

## Read the item ID column

You can query the item ID column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the item ID column are of the ItemIdValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on ItemIdValue {
        value
        text
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
item_idID! | The item's unique identifier.
textString | The column's value as text.
typeColumnType! | The column's type.
valueJSON | The column's JSON-formatted raw value.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
