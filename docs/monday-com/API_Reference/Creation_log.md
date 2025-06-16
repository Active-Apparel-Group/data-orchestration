---

title: Creation_log
source: https://developer.monday.com/api-reference/reference/creation-log
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter and read the creation log column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Creation log

Learn how to filter and read the creation log column on monday boards using the platform API

The creation log column represents an item's creator and the date and time they created it. You can filter and read the creation log via the API, but you currently cannot update or clear it.

## Filter the creation log column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the creation log column's supported operators, compare values, and compare attributes.

Operators | Compare values | Compare attributes
--- | --- | ---
any_of | The user IDs to filter by | "CREATED_BY"
not_any_of | The user IDs to filter by | "CREATED_BY"

### Examples

The following example returns all items on the specified board that were created by user 123456.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "creation_log", compare_value: [123456], compare_attribute: "CREATED_BY", operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the creation log column

You can query the creation log column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the creation log column are of the CreationLogValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on CreationLogValue {
        created_at
        creator
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
created_atDate! | The item's creation date.
creatorUser! | The item's creator.
creator_idID! | The unique identifier of the item's creator.
idID! | The column's unique identifier.
textString | The column's value as text.
typeColumnType! | The column's type.
valueJSON | The column's JSON-formatted raw value.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
