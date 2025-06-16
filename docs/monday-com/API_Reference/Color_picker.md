---

title: Color_picker
source: https://developer.monday.com/api-reference/reference/color-picker
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read the color picker column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Color picker

Learn how to read the color picker column on monday boards using the platform API

The color picker column allows you to pick specific colors on a board to help maintain a consistent board design. After selecting your color, the column will display the relevant color code in the format of your choice. You can read the color picker column via the API, but you currently cannot filter, update, or clear it.

## Read the color picker column

You can query the color picker column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the color picker column are of the ColorPickerValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on ColorPickerValue {
        color
        updated_at
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
colorString | The column's HEX color value.
columnColumn! | The column the value belongs to.
idID! | The column's unique identifier.
textString | The column's value as text. This field will returnnullif the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
