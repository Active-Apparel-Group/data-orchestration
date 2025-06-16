---

title: Status
source: https://developer.monday.com/api-reference/reference/status
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the status column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Status

Learn how to filter by, read, update, and clear the status column on monday boards using the platform API

The status column represents a label designation for your item(s). It can be used to denote the status of a particular item or hold any other custom labeling for the item. Each status column is a collection of indexes and their corresponding labels. You can filter by , read , update , and clear the status column via the API.

## Filter by the status column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the status column's supported operators and compare values.

Compare values | Description | Operators
--- | --- | ---
The label's index | Items with a specific label index. You can find the index by queryingcolumn's settings. | -any_of: returns items with the specified index-not_any_of: returns items without the specified index
The label's text (as a string) | Items with a specific label. | -contains_terms: returns items with the specified text value
5 | Items with empty values. | -any_of: returns items with empty values-not_any_of: returns items without empty values
null | Items with empty values. | -is_empty: returns items with empty values-is_not_empty: returns items without empty values

### Examples

This example returns all items on the specified board with a blank status value.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "status", compare_value: [5], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

This example returns all items on the specific board with a "Done" label.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "status", compare_value: "Done", operator:contains_terms}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the status column

You can query the status column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the status column are of the StatusValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on StatusValue {
        index
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
indexInt | The column's status index in the board.
is_doneBoolean | Whether or not the item's status is done.
labelString | The column's status label value. This returns the current label value, not all possible values.
label_styleStatusLabelStyle | The status label's style.
textString | The column's value as text. This field will returnnullif the column has an empty value.
typeColumnType! | The column's type.
update_idID | The unique identifier of the update attached to the column's status.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the status column

You can update a status column with either a simple string or a JSON string, and each status column can have a maximum of 40 labels.

### Simple strings

Using the change_simple_column_value mutation, you can pass either the index or the label value of the status you want to update in the value argument. If the label is a number, send the index instead. Otherwise, the label will be treated as an index value, and the mutation will fail.

You can also send create_labels_if_missing: true in your mutation to create any labels that don't yet exist and avoid an error.

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"status", value: "8") {
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
      columnId: "status",
      myColumnValue: "8"
      })
    })
  })
```

### JSON

Using the change_multiple_column_values mutation, you can pass either the index or the label value of the status you want to update in the column_values argument. If the label is a number, send the index instead. Otherwise, the label will be treated as an index value, and the mutation will fail.

You can also send create_labels_if_missing: true in your mutation to create any labels that don't yet exist and avoid an error.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"status\" : {\"index\" : \"1\"}}") {
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
      myColumnValues: "{\"status\" : {\"index\" : \"1\"}}"
    })
  })
})
```

## Clear the status column

You have two options to clear a status column. First, you can use the change_multiple_column_values mutation and pass null an empty string, or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"status\" : null}") {
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
      myColumnValues: "{\"date\" : null}"
    })
  })
})
```

You can also use the change_simple_column_value mutation and pass an empty string in the value argument.

GraphQLJavaScript
```
mutation {
  change_simple_column_value(item_id:9876543210, board_id:1234567890, column_id: "status", value: "") {
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
      columnId: "status",
      myColumnValue: ""
      })
    })
  })
```

## Index values and color mapping

As mentioned above, you can use both Index and Label values when using JSON formatting in your Mutation calls to update the Status column.

- change_column_value
- change_multiple_column_values
- create_item , create_subitem

By default , every index value matches a specific color. For example, the Green status has the index 1. Here's a full list of the indexes and matching values.

When you create a new Status label, it will follow the default index value and its index will not change. However, the color of a status label can be changed. Therefore, you cannot assume a label’s color and index will always match.

Take the following example:

Index: 2 will have a color value of #e2445c . Thus, using this index value will set the Status column value to a Red-shadow color, as shown below:

And on the board, this will appear as such:

The color values are not static and can be changed within the Status column labels. You can find more info on this here .

Then, the index value will remain the same, but the color value will be changed. For example, if I chose Black as the new color, this is how the color value would appear in the API:

And this is how the item would appear on the board:

As such, using index values does not guarantee that you will populate the same color values across multiple boards.

If you encounter a mismatch of index values when sending data between boards in your account, we recommend changing the color of the labels back to the default values manually.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
