---

title: Items
source: https://developer.monday.com/api-reference/reference/items
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, create, update, and delete items from monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Items

Learn how to read, create, update, and delete items from monday boards using the platform API

Items are core objects in the monday.com platform that hold the actual data within the board. To better illustrate the platform, imagine that each board is a table and an item is a single row in that table. Take one row, fill it with whatever information you'd like, and you now have an item !

## 🚧Want to read all items on a board?

The items object allows you to query specific items by their IDs. If you want to read all items on a board, use the items_page object instead!

# Queries

Required scope: boards:read

Querying items will return metadata about one or a collection of specific items. This method accepts various arguments and returns an array.

You can only query items at the root, so it can't be nested within another query (like boards ). You can return up to 100 items at a time using the ids argument.

GraphQLJavaScript
```
query {
  items (ids: [1234567890, 9876543210, 2345678901]) {
    name
  }
}
```

```
let query = "query { items (ids: [1234567890, 9876543210, 2345678901]) { name }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your items query.

Argument | Description
--- | ---
exclude_nonactiveBoolean | Excludes items that are inactive, deleted, or belong to deleted items.Please notethat this argument will only work when used with theidsargument.
ids[ID!] | The IDs of the specific items, subitems, or parent items to return.Please notethat you can return a maximum of 100 IDs at one time using thelimitargument.
limitInt | The number of items returned. The default is 25.
newest_firstBoolean | Lists the most recently created items at the top.
pageInt | The page number to return. Starts at 1.

## Fields

You can use the following field(s) to specify what information your items query will return. Please note that some fields will have their own arguments.

Field | Description | Supported fields | Supported arguments
--- | --- | --- | ---
assets[Asset] | The item's assets/files. |  | assets_sourceAssetsSourcecolumn_ids[String]
boardBoard | The board that contains the item. |  | 
column_values[ColumnValue] | The item's column values. |  | ids[String]
column_values_strString! | The item's string-formatted column values. |  | 
created_atDate | The item's creation date. |  | 
creatorUser | The item's creator. |  | 
creator_idString! | The unique identifier of the item's creator. Returnsnullif the item was created by default on the board. |  | 
descriptionItemDescription | The item'sdescription.Only available in versions2025-07and later. | blocks[DocumentBlock]idID | 
emailString! | The item's email. |  | 
groupGroup | The item's group. |  | 
idID! | The item's unique identifier. |  | 
linked_items[Item!]! | The item's linked items. |  | linked_board_idID!link_to_item_column_idString!
nameString! | The item's name. |  | 
parent_itemItem | A subitem's parent item. If used for a parent item, it will returnnull. |  | 
relative_linkString | The item's relative path. |  | 
subitems[Item] | The item's subitems. |  | 
subscribers[User]! | The item's subscribers. |  | 
updated_atDate | The date the item was last updated. |  | 
updates[Update] | The item's updates. |  | limitIntpageInt
urlString! | The item's URL. |  | 

# Mutations

Required scope: boards:write

## Create an item

The create_item mutation allows you to create a new item via the API. You can also specify what fields to query back from the new item when you run the mutation.

Item data is stored in columns that hold particular information based on the column type. Each type expects a different set of parameters to update their values. When sending data to a particular column, use a JSON-formatted string. If you're using Javascript, you can use JSON.stringify() to convert a JSON object into a string.

You can also use simple values in this mutation or combine them with regular values. Read more about sending data for each column in our column types reference .

GraphQLJavaScript
```
mutation {
  create_item (board_id: 1234567890, group_id: "group_one", item_name: "new item", column_values: "{\"date\":\"2023-05-25\"}") {
    id
  }
}
```

```
let query = "mutation { create_item (board_id: 1234567890, group_id: \"Group 1\", item_name: \"new item\", column_values: \"{\\\"date4\\\":\\\"2023-05-25\\\"}\") { id }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to define the new item's characteristics.

Argument | Description | Accepted values
--- | --- | ---
board_idID! | The board's unique identifier. | 
column_valuesJSON | The column values of the new item. | 
create_labels_if_missingBoolean | Creates status/dropdown labels if they are missing (requires permission to change the board structure). | 
group_idString | The group's unique identifier. | 
item_nameString! | The new item's name. | 
position_relative_methodPositionRelative | The desired position of the new item. | You can use this argument in conjunction withrelative_toto specify which item you want to create the new item above or below.-before_at:  This enum value creates the new item above therelative_tovalue. If you don't use therelative_toargument, the new item will be created at the bottom of the first active group (unless you specify a group usinggroup_id).-after_at: This enum value creates the new item below therelative_tovalue. If you don't use therelative_toargument, the new item will be created at the top of the first active group (unless you specify a group usinggroup_id).
relative_toID | The unique identifier of the item you want to create the new one in relation to.You can also use this argument in conjunction withposition_relative_methodto specify if you want to create the new item above or below the item in question. | 

## 🚧Changing an item's name

If you'd like to change an existing item's name, you need to use the change_column_value mutation with a JSON string value. Check out this doc for more info!

## Duplicate an item

The duplicate_item mutation allows you to duplicate a single item via the API. You can also specify what fields to query back from the duplicated item when you run the mutation.

GraphQLJavaScript
```
mutation {
  duplicate_item (board_id: 1234567890, item_id: 9876543210, with_updates: true) {
    id
  }
}
```

```
let query = "mutation { duplicate_item (board_id: 1234567890, item_id: 9876543210, with_updates: true) { id }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which item to duplicate.

Argument | Description
--- | ---
board_idID! | The board's unique identifier.
item_idID | The item's unique identifier. Required.
with_updatesBoolean | Duplicates the item with existing updates.

## Move item to group

The move_item_to_group mutation allows you to move an item between groups on the same board via the API. You can also specify what fields to query back from the item when you run the mutation.

GraphQLJavaScript
```
mutation {
  move_item_to_group (item_id: 1234567890, group_id: "group_one") {
    id
  }
}
```

```
let query = "mutation { move_item_to_group (item_id: 1234567890, group_id: \"Group 1\") { id }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which item to move and to where.

Argument | Description
--- | ---
group_idString! | The group's unique identifier.
item_idID | The item's unique identifier.

## Move item to board

The move_item_to_board mutation allows you to move an item to a different board via the API. You can also specify what fields to query back from the item when you run the mutation.

GraphQLJavaScript
```
mutation {
  move_item_to_board (board_id:1234567890, group_id: "new_group", item_id:9876543210, columns_mapping: [{source:"status", target:"status2"}, {source:"person", target:"person"}, {source:"date", target:"date4"}]) {
    id
  }
}
```

```
let query = "mutation { move_item_to_board (board_id: 1234567890, group_id: \"new_group\", item_id: 9876543210, columns_mapping: [{source:\"status\", target:\"status2\"}, {source:\"person\", target:\"person\"}, {source:\"date\", target:\"date4\"}]) { id }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which item to move and to where.

Argument | Description | Supported fields
--- | --- | ---
board_idID! | The unique identifier of the board to move the item to (target board) | 
group_idID! | The unique identifier of the group to move the item to (target group). | 
item_idID! | The unique identifier of the item to move. | 
columns_mapping[ColumnMappingInput!] | The object that defines the column mapping between the original and target board. Every column type can be mappedexcept for formula columns.When using this argument, you must specify the mapping forallcolumns. You can select the target asnullfor any columns you don't want to map, but doing so will lose the column's data.If you omit this argument, the columns will be mapped based on the best match. | sourceID!targetID
subitems_columns_mapping[ColumnMappingInput!] | The object that defines the subitems' column mapping between the original and target board. Every column type can be mappedexcept for formula columns.When using this argument, you must specify the mapping forallcolumns. You can select the target asnullfor any columns you don't want to map, but doing so will lose the column's data.If you omit this argument, the columns will be mapped based on the best match. | sourceID!targetID

## Archive an item

The archive_item mutation allows you to archive a single item via the API. You can also specify what fields to query back from the archived item when you run the mutation.

GraphQLJavaScript
```
mutation {
  archive_item (item_id: 1234567890) {
    id
  }
}
```

```
let query = "mutation {archive_item (item_id: 1234567890) { id }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which item to archive.

Argument | Description
--- | ---
item_idID | The item's unique identifier.

## Delete an item

The delete_item mutation allows you to delete a single item via the API. You can also specify what fields to query back from the deleted item when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_item (item_id: 1234567890) {
    id
  }
}
```

```
let query = "mutation { delete_item (item_id: 1234567890) { id }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which item to delete.

Argument | Description
--- | ---
item_idID | The item's unique identifier.

## Clear an item's updates

The clear_item_updates mutation allows you to clear all updates on a specific item, including replies and likes. You can also specify what fields to query back from the item when you run the mutation.

GraphQLJavaScript
```
mutation {
  clear_item_updates (item_id: 1234567890) {
    id
  }
}
```

```
let query = "mutation { clear_item_updates (item_id: 1234567890) { id }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which item to clear updates from.

Arguments | Description
--- | ---
item_idID! | The item's unique identifier.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
