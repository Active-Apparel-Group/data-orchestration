---

title: Dropdown
source: https://developer.monday.com/api-reference/reference/dropdown
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter, read, update, and clear the dropdown column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Dropdown

Learn how to filter, read, update, and clear the dropdown column on monday boards using the platform API

The dropdown column lets a user select one or more options from a selection. You can filter , read , update , and clear the dropdown column via the API.

## Filter the dropdown column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the dropdown column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | ""(blank values)The label IDs to filter by
not_any_of | ""(blank values)The label IDs to filter by
is_empty | null
is_not_empty | null
contains_text | The partial or whole label text value to filter by
not_contains_text | The partial or whole label text value to filter by

### Examples

The following example returns all items on the specified board that have a dropdown column value that contains "Marketing".

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "dropdown", compare_value: ["Marketing"], operator:contains_text}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the dropdown column

You can query the dropdown column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the dropdown column are of the DropdownValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on DropdownValue {
        values
        column
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
textString | The column's value as text. This field will returnnullif the column has an empty value.
typeColumnType! | The column's type.
valueJSON | The column's JSON-formatted raw value.
values[DropdownValueOption!]! | The selected dropdown values.

## Update the dropdown column

You can update a dropdown column with a simple string value or a JSON string value.

## ❗️NOTE

It is not possible to mix dropdown labels (the text values) with dropdown IDs in the string values.

### Simple strings

Send the IDs of the labels you want to set to update a dropdown column with strings. If you don’t know the IDs of the labels you’re trying to set, you can send the label's text value instead. If you need to update more than one value, you can also send a list of IDs or labels separated by commas.

If you make an API call to update the dropdown column value, but the label doesn't exist, the expected behavior will be an error message. In the output of that error, you will also receive the existing labels for that specific column. However, you can use create_labels_if_missing: true in your query to create labels that didn't previously exist.

Here is a sample query to update the dropdown column using simple string values via dropdown IDs.

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"dropdown", value: "1,2") {
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
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValue: String!, $columnId: String!) { change_simple_column_value (item_id:$myItemId, board_id:$myBoardId, column_id: $columnId, value: $myColumnValue) { id } }",
    variables : JSON.stringify({
      myBoardId: YOUR_BOARD_ID,
      myItemId: YOUR_ITEM_ID,
      columnId: "YOUR_COLUMN_ID",
      myColumnValue: "dropdown_index_1, dropdown_index_2"
      })
    })
  })
```

Here is a sample query to update the dropdown column using simple string values with dropdown labels.

GraphQLJavaScriptcURL
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"dropdown", value: "Cookie, Cupcake") {
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
    query : `mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValue: String!, $columnId: String!) {
                 change_simple_column_value (item_id:$myItemId, board_id:$myBoardId, column_id: $columnId, value: $myColumnValue) {
                   id
                 }
               }`,
    variables : JSON.stringify({
      myBoardId: YOUR_BOARD_ID,
      myItemId: YOUR_ITEM_ID,
      columnId: "YOUR_COLUMN_ID",
      myColumnValue: "dropdown_label_1, dropdown_label_2"
      })
    })
  })
  .then(res => res.json())
  .then(res => console.log(JSON.stringify(res, null, 2)));
```

```
curl "https://api.monday.com/v2" \
-X POST \
-H "Content-Type:application/json" \
-H "Authorization: MY_API_KEY" \
-d '{"query":"mutation{change_simple_column_value (item_id:9876543210,board_id:1234567890, column_id: \"dropdown\", value: \"Cookie, Cupcake\"){ name id}}"}'
```

### JSON

You can also update the dropdown column using JSON values with either the ID value or the text label.

## 👍Pro tip

You can use both String and JSON values when updating column values for change_multiple_column_values mutation, or when using the create_item mutation.

Here is a sample query to update the dropdown column using JSON values with dropdown IDs.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"dropdown\": {\"ids\":[\"1\"]}}") {
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
    query : `mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) {
                 change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) {
                   id
                 }
               }`,
    variables : JSON.stringify({
      myBoardId: YOUR_BOARD_ID,
      myItemId: MY_ITEM_ID,
      myColumnValues: JSON.stringify({
      dropdown : {
  			"ids": [\"1\"]
			},
      })
    })
  })
})
```

Here is a sample query to update the dropdown column using JSON values with dropdown labels.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"dropdown\":{\"labels\":[\"My label\"]}}") {
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
    query : `mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) {
                 change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) {
                   id
                 }
               }`,
    variables : JSON.stringify({
      myBoardId: YOUR_BOARD_ID,
      myItemId: MY_ITEM_ID,
      myColumnValues: JSON.stringify({
      dropdown : {
  			"labels": "Cookie"
			},
      })
    })
  })
})
```

### Add a dropdown value

You can add a new dropdown value to a column using the following mutation:

GraphQL
```
mutation {
  change_simple_column_value(item_id:1234567890, board_id:9876543210, column_id: "dropdown", value: "New dropdown value", create_labels_if_missing: true) {
    id
  }
}
```

#### Arguments for adding a dropdown value

Argument | Description
--- | ---
item_idInt! | The item's unique identifier.
board_idInt! | The board's unique identifier.
column_idInt! | The column's unique identifier.
valueString! | The new value of the column.
create_labels_if_missingBoolean | Create status/dropdown labels if they're missing. (Requires permission to change board structure)

## Clear a dropdown column

You can clear a dropdown column using the following mutation:

GraphQLGraphQL
```
mutation {
  change_multiple_column_values(item_id:123456789, board_id:987654321, column_values: "{\"dropdown\" : null}") {
    id
  }
}
```

```
mutation {
  change_multiple_column_values(item_id:123456789, board_id:987654321, column_values: "{\"dropdown\":{\"labels\":[]}}") {
    id
  }
}
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
