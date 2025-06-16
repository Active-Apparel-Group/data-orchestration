---

title: Numbers
source: https://developer.monday.com/api-reference/reference/number
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the numbers column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Numbers

Learn how to filter by, read, update, and clear the numbers column on monday boards using the platform API

The numbers column holds number values (either floats or ints). You can filter , read , update , and clear the numbers column via the API.

## Filter by the numbers column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the number column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The numeric value to filter by"$$$blank$$$"(blank values)
not_any_of | The numeric value to filter by"$$$blank$$$"(blank values)
is_empty | null
is_not_empty | null
greater_than | The numeric value to filter by
greater_than_or_equals | The numeric value to filter by
lower_than | The numeric value to filter by
lower_than_or_equals | The numeric value to filter by

### Examples

The following example returns all items on the specified board with a number column value greater than 5.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "numbers", compare_value: [5], operator:greater_than}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the numbers column

You can query the numbers column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the numbers column are of the NumbersValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on NumbersValue {
        number
        id
        symbol
        direction
      }
    }
  }
}
```

### Fields

Field | Description | Enum values
--- | --- | ---
columnColumn! | The column the value belongs to. | 
directionNumberValueUnitDirection | Indicates whether the symbol is placed to the right or left of the number. | leftright
idID! | The column's unique identifier. | 
numberFloat | The column's number value. | 
symbolString | The symbol of the unit. | 
textString | The column's value as text. This field will return""if the column has an empty value. | 
typeColumnType! | The column's type. | 
valueJSON | The column's JSON-formatted raw value. | 

## Update the numbers column

You can update a numbers column using the change_simple_column_value mutation and sending a simple string in the value argument. You can also use the change_multiple_column_values mutation and pass a JSON string in the column_values argument.

### Simple strings

To update the numbers column, send a string containing a float or int.

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"numbers", value: "3") {
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
      columnId: "numbers",
      myColumnValue: "3"
      })
    })
  })
```

### JSON

To update the numbers column using JSON, send a string containing a float or int.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"numbers\" : \"3\"}") {
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
      myColumnValues: "{\"numbers\" : \"3\"}"
    })
  })
})
```

## Clear the numbers column

You can also clear a numbers column using the change_multiple_column_values mutation and passing null or an empty string in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"numbers\" : null}") {
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
      myColumnValues: "{\"numbers\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
