---

title: Checkbox
source: https://developer.monday.com/api-reference/reference/checkbox
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, update, and clear the checkbox column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Checkbox

Learn how to read, update, and clear the checkbox column on monday boards using the platform API

The checkbox column represents a simple true or false value on a board. You can filter , read , update , and clear the checkbox column via the API.

## Filter the checkbox column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the checkbox column's supported operators and compare values.

Operators | Compare values
--- | ---
is_empty | null
is_not_empty | null

### Examples

The following example returns all items on the specified board that have an unchecked checkbox column.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "check", compare_value: [null], operator:is_empty}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Reading the checkbox column

You can query the checkbox column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the checkbox column are of the CheckboxValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on CheckboxValue {
        checked
        updated_at
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
checkedBoolean | Returnstrueif the column is checked.
columnColumn! | The column the value belongs to.
idID! | The column's unique identifier.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the checkbox column

You can update a checkbox column using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

To check the box, send {"checked" : "true"} in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:1234567890, board_id:9876543210, column_values: "{\"checkbox\" : {\"checked\" : \"true\"}}") {
    id
  }
}
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
  },
  body: JSON.stringify({
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id } }",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues: JSON.stringify({ checkbox: { checked: "true" }})
    })
  })
})
```

## Clear the checkbox column

You can also clear (uncheck) a checkbox column using the change_multiple_column_values mutation and passing null in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"checkbox\" : null}"){
    id
  }
}
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
  },
  body: JSON.stringify({
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id } }",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues: JSON.stringify({ checkbox: { null }})
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
