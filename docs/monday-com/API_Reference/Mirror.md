---

title: Mirror
source: https://developer.monday.com/api-reference/reference/mirror
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read the mirror column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Mirror

Learn how to read the mirror column on monday boards using the platform API

The mirror column shows a column value from another board through a linked item, allowing you to make changes to multiple boards simultaneously. You can read the mirror column via the API, but you cannot filter, update, or clear it. You may see some unexpected and inconsistent results if you try to set up filter rules for mirrored content.

## Read the mirror column

You can query the mirror column using the column_values object, or use the MirrorValue type to return column-specific fields.

If you want to get mirrored column values, use the display_value field on the MirrorValue type. The text field will always return null.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on MirrorValue {
        display_value
        id
      }
    }
  }
}
```

## 🚧Use thedisplay_valuefield to read mirror columns

If you want to read values from mirrored columns, you must add the following fragment to your query: ...on MirrorValue { display_value }

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
display_valueString! | The content of the mirrored column, in text format.
idID! | The column's unique identifier.
mirrored_items[MirroredItem!]! | The mirrored items.
textString | The column's long text. This field will always returnnull, usedisplay_valueinstead.
typeColumnType! | The column's type.
valueJSON | The column's JSON-formatted raw value. This field always returnsnull, uselinked_itemsandlinked_item_idsinstead.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
