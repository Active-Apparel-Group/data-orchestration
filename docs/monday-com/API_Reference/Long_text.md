---

title: Long_text
source: https://developer.monday.com/api-reference/reference/long-text
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the long text column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Long text

Learn how to filter by, read, update, and clear the long text column on monday boards using the platform API

The long text column holds up to 2,000 characters of text. You can filter by , read , update , and clear the long text column via the API.

## Filter by the long text column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the long text column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The whole text value to filter by""(blank values)
not_any_of | The whole text value to filter by""(blank values)
is_empty | null
is_not_empty | null
contains_text | The partial or whole text value to filter by
not_contains_text | The partial or whole text value to filter by

### Examples

The following example returns all items on the specified board with an empty long text column.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "long_text", compare_value: [""], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the text column

You can query the long text column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the long text column are of the LongTextValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on LongTextValue {
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
textString | The column's long text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the long text column

You can update a long text column using the change_simple_column_value mutation and sending a simple string in the value argument. You can also use the change_multiple_column_values mutation and pass a JSON string in the column_values argument.

### Simple strings

To update the long text column, send a string with up to 2,000 characters.

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"long_text", value: "Sample text") {
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
      columnId: "long_text",
      myColumnValue: "Sample text"
      })
    })
  })
```

### JSON

To update the long text column using JSON, send the "text" key with up to 2,000 characters.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"long_text\" : {\"text\" : \"Sample text\"}}") {
    id
  }
}
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY'
  },
  body: JSON.stringify({
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id }}",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues: "{\"long_text\" : {\"text\" : \"Sample text\"}}"
    })
  })
})
```

## Clear the long text column

You can also clear a long text column using the change_multiple_column_values mutation and passing null , an empty string, or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"long_text\" : null}") {
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
      myColumnValues: "{\"long_text\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
