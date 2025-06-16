---

title: Connect_boards
source: https://developer.monday.com/api-reference/reference/connect
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter, read, update, and clear the connect boards column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Connect boards

Learn how to filter, read, update, and clear the connect boards column on monday boards using the platform API

The connect boards column links an item on the board with an item(s) on a different board(s). You can filter , read , update , and clear the connect boards column via the API.

## Filter the connect boards column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the connect boards column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The connected items' IDs to filter by
not_any_of | The connected items' IDs to filter by
is_empty | null
is_not_empty | null
contains_text | The partial or whole item name to filter by as a string
not_contains_text | The partial or whole item name to filter by as a string

### Examples

The following example returns all items on the specified board that are connected to an item whose name contains "Test".

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "connect_boards", compare_value: ["Test"], operator:contains_text}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the connect boards column

You can query the connect boards column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the connect boards column are of the BoardRelationValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on BoardRelationValue {
        linked_item_ids
        linked_items
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
display_valueString! | The names of the linked items, separated by commas.
idID! | The column's unique identifier.
linked_item_ids[ID!]! | The unique identifiers of linked items.
linked_items[Item!]! | The linked items.
textString | The column's value as text. This field will always returnnull. Usedisplay_valueinstead.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value. In version2025-04and later, this field will always returnnull. Uselinked_itemsandlinked_item_idsinstead.

## Update the connect boards column

You can update a connect boards column using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

## 🚧Warning

Boards can't be connected using the API - only items on boards that are already connected. Let's say your want to connect an item from Board B to Board A, but the boards are not yet connected. You must first manually connect Boards B and A, and then you can use the API to connect the items.

If you try to connect items from boards that are not connected, you will get an error.

To update a connect boards column, send the item IDs to be linked as an array.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"connect_boards\" : {\"item_ids\" : [\"44332211\", \"11223344\"]}}") {
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
      myBoardId: YOUR_BOARD_ID,
      myItemId: YOUR_ITEM_ID,
      myColumnValues: "{\"connect_boards\": {\"item_ids\": [\"44332211\", \"11223344\"]}}"
    })
  })
})
```

## Clear the connect boards column

You can also clear a connect boards column using the change_multiple_column_values mutation and passing null or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
 change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"connect_boards\" : null}") {
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
      myColumnValues: "{\"connect_boards\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
