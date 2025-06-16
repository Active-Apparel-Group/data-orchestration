---

title: Button
source: https://developer.monday.com/api-reference/reference/button
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read the button column on a monday board using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Button

Learn how to read the button column on a monday board using the platform API

The button column allows you to perform an action (i.e., move an item to a new group) with just the click of a button. You can read the button column via the API, but you currently cannot filter, update, or clear it.

## Read the button column

You can query the button column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the button column are of the ButtonValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on ButtonValue {
        color
        label
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
colorString | The button's HEX color value.
columnColumn! | The column the value belongs to.
idID! | The button column's unique identifier.
labelString! | The button's label.
textString | The button's text.
typeColumnType! | The column's type.
valueJSON | The column's JSON-formatted raw value.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
