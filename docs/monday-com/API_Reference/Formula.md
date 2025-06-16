---

title: Formula
source: https://developer.monday.com/api-reference/reference/formula
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read the formula column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Formula

Learn how to read the formula column on monday boards using the platform API

The formula column calculates anything from simple mathematic equations to complex formulas. You can read the formula column via the API, but you currently cannot filter, update, or clear it.

## Read the formula column

You can query the formula column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the formula column are of the FormulaValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on FormulaValue {
        value
        id
        display_value
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
textString | Reading calculated values is not supported, so this field will returnnull.
typeColumnType! | The column's type.
valueJSON | Reading calculated values is not supported, so this field will returnnull.
display_valueString | The formula column's content. Subject to the followinglimits:Does not support formulas with mirror columnsUp to 10,000 formula values per minuteMaximum of five formula columns in one request

### Workaround to read a column's formula (version2024-10)

While the FormulaValue implementation doesn't allow you to read the formula in the column or its calculated values, you can query the column's settings_str to return the formula itself as JSON.

#### Sample query

GraphQL
```
query {
  boards (ids:1234567890) {
    columns (ids: "formula") {
      settings_str
    }
  }
}
```

#### Sample response

JSON
```
{
  "data": {
    "boards": [
      {
        "columns": [
          {
            "settings_str": "{\"formula\":\"ADD_DAYS({date_1},15) \"}"
          }
        ]
      }
    ]
  },
  "account_id": 12345678
}
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
