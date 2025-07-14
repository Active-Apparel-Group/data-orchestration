---

title: Text
source: https://developer.monday.com/api-reference/reference/text
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the text column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Text

Learn how to filter by, read, update, and clear the text column on monday boards using the platform API

The text column contains any text you want to store in a column on your board(s). You can filter by , read , update , and clear the text column via the API.

## 🚧Text column limit

The text column itself has no explicit character limit. However, each item has a column value limit of approximately 64KB.

## Filter by the text column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the text column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The whole text value to filter by""(blank values)
not_any_of | The whole text value to filter by""(blank values)
is_empty | null
is_not_empty | null
contains_text | The partial or whole text value to filter by
not_contains_text | The partial or whole text value to filter by

### Examples

The following example returns all items on the specified board without an empty text column.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "text", compare_value: [""], operator:not_any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the text column

You can query the text column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the text column are of the TextValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on TextValue {
        text
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
textString | The column's textual value. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
valueJSON | The column's JSON-formatted raw value.

## Update the text column

You can update a text column using the change_simple_column_value mutation and sending a simple string in the value argument. You can also use the change_multiple_column_values mutation and pass a JSON string in the column_values argument.

### Simple strings

To update the text column, send a simple String value.

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"text", value: "Sample text") {
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
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValue: String!, $columnId: String!) { change_simple_column_value (item_id:$myItemId, board_id:$myBoardId, column_id: $columnId, value: $myColumnValue) { id } }",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      columnId: "text",
      myColumnValue: "Sample text"
      })
    })
  })
```

### JSON

To update the text column using JSON, send the value as a string.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"text\" : \"Sample text\"}") {
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
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id }}",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues: "{\"text\" : \"Sample text\"}"
    })
  })
})
```

## Clear the text column

You have two options to clear a text column. First, you can use the change_multiple_column_values mutation and pass null or an empty string in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"text\" : null}") {
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
      myColumnValues: "{\"text\" : null}"
    })
  })
})
```

You can also use the change_simple_column_value mutation and pass an empty string in the value argument.

GraphQLJavaScript
```
mutation {
  change_simple_column_value(item_id:9876543210, board_id:1234567890, column_id: "text", value: "") {
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
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValue: String!, $columnId: String!) { change_simple_column_value (item_id:$myItemId, board_id:$myBoardId, column_id: $columnId, value: $myColumnValue) { id } }",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      columnId: "text",
      myColumnValue: ""
      })
    })
  })
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
