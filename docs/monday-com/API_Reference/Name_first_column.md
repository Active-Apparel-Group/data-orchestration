---

title: Name_first_column
source: https://developer.monday.com/api-reference/reference/name
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, and update the name column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Name (first column)

Learn how to filter by, read, and update the name column on monday boards using the platform API

The name column is the first column you see on a board, and it holds the names of your item(s). You can filter by , read , and update the name column via the API, but you cannot clear it.

## Filter by the name column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the name column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The whole item name to filter by
not_any_of | The whole item name to filter by
contains_text | The partial or whole item name to filter by
not_contains_text | The partial or whole item name to filter by

### Examples

The following example returns all items on the specified board with an item whose name contains "Project 1".

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "name", compare_value: ["Project 1"], operator:contains_text}]}) {
      items {
        id
      }
    }
  }
}
```

## Read the name column

You can't read the name column using column_values , but you can read it using the items_page_by_column_values object.

The following example returns all items on board 1234567890 that have "Item 1" as their name column value.

GraphQL
```
query {
  items_page_by_column_values (board_id: 1234567890, columns: {column_id:"name", column_values: "Item 1"}) {
    items {
      id
      name
    }
  }
}
```

## Update the name column

You can update a preexisting item's name using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

To update the item's name using JSON, send a string between 1 and 255 characters long.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"name\" : \"My Item\"}") {
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
      myColumnValues: "{\"name\" : \"My Item\"}"
    })
  })
})
```

## Clear the item name column

Since every item must have a name, you can't use the API to clear the name column.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
