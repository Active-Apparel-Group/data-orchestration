---

title: Dependency
source: https://developer.monday.com/api-reference/reference/dependency
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter, read, update, and clear the dependency column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Dependency

Learn how to filter, read, update, and clear the dependency column on monday boards using the platform API

The dependency column allows you to set up connections between items in the same board. They can then be visually represented in the Gantt View or Widget, or combined with automations. You can filter , read , update , and clear the dependency column via the API.

## Filter the dependency column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the dependency column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The item IDs to filter by
not_any_of | The item IDs to filter by
is_empty | null
is_not_empty | null

### Examples

The following example returns all items on the specified board that are dependent on item 9876543210.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "dependent_on", compare_value: [9876543210], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the dependency column

You can query the dependency column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the dependency column are of the DependencyValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on DependencyValue {
        linked_item_ids
        updated_at
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
display_valueString! | The names of the dependent items, separated by commas.
idID! | The column's unique identifier.
linked_item_idsID! | The unique identifiers of the linked items.
linked_items[Item!]! | The linked items.
textString | The column's value as text. This field will always returnnull. Usedisplay_valueinstead.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value. In version2025-04and later, this field will always returnnull. Uselinked_itemsandlinked_item_idsinstead.

## Update the dependency column

You can update a dependency column using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

To add a dependent-on item to the dependency column, send the item IDs as an array. You will get an error if the items do not belong to the connected board.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values (item_id:9876543210, board_id:1234567890, column_values: "{\"dependency\" : {\"item_ids\" : [\"11223344\", \"44332211\"]}}") {
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
    'query' : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id } }",
    'variables' : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues: "{\"dependency\" : {\"item_ids\" : [\"11223344\", \"44332211\"]}}
    })
  })
})
```

## Clear the dependency column

You can also clear a dependency column using the change_multiple_column_values mutation and passing null or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
 change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"dependent_on\" : null}") { 
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
      myColumnValues: "{\"dependent_on\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
