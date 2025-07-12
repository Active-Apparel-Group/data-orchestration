---

title: Subitems
source: https://developer.monday.com/api-reference/reference/subitems
author:
  - Monday
published:
created: 2025-05-25
description: Learn everything about using the API to read or write sub-item data in monday.com GraphQL API.
tags: [code, api, monday-dot-com]
summary:

---

# Subitems

Learn how to query subitems on monday boards using the platform API

Subitems are special items that are "nested" under the items on your board. They can be accessed via the subitem column, which can be added from the column's center or by right-clicking an item to expose its dropdown menu. Like items , subitems store data within their columns.

## Queries

Required scope: boards:read

- Returns an array containing metadata about one or a collection of subitems
- Can only be nested within another query

GraphQLJavaScript
```
query {
  items (ids: 1234567890) {
    subitems {
      id
      column_values {
        value
        text
      }
    }
  }
}
```

```
let query = "query {items (ids: 1234567890) { subitems  { id column_values { value text } } } } ";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query': query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Fields

You can use the following field(s) to specify what information your subitems query will return.

Field | Description | Enum values
--- | --- | ---
assets[Asset] | The subitem's assets/files. | 
boardBoard | The board that contains the subitem. | 
column_values[ColumnValue] | The subitem's column values. | 
created_atDate | The subitem's creation date. | 
creatorUser | The subitem's creator. | 
creator_idString! | The unique identifier of the user who created the subitem. Returnsnullif the item was created by default on the board. | 
emailString! | The subitem's email. | 
groupGroup | The subitem's group. | 
idID! | The subitem's unique identifier. | 
linked_items[Item!]! | The subitem's linked items. | 
nameString! | The subitem's name. | 
parent_itemItem | A subitem's parent item. If used for a parent item, it will returnnull. | 
relative_linkString | The subitem's relative path. | 
stateState | The subitem's state. | activeallarchiveddeleted
subitems[Item] | The subitem's subitems. | 
subscribers[User]! | The subitem's subscribers. | 
updated_atDate | The date the subitem was last updated. | 
updates[Update] | The subitem's updates. | 
urlString! | The subitem's link. | 

# Mutations

Required scope: boards:write

## Create a subitem

The create_subitem mutation allows you to create a new subitem via the API. You can also specify what fields to query back from the new subitem when you run the mutation.

The data of each subitem is stored in the subitem board columns (same as items), each of which holds a particular piece of information. Each column has a specific type, and different column types expect a different set of parameters to update their values. When sending data to a particular column, use a JSON-formatted string. If you're using Javascript, you can use JSON.stringify() to convert a JSON object into a string.

You can also use simple values in this mutation or combine them with regular values. Read more about sending data for each column in our column types reference .

GraphQLJavaScript
```
mutation {
  create_subitem (parent_item_id: 1234567890, item_name: "New subitem", column_values: "{\"date0\":\"2023-05-25\"}") {
    id
    board {
      id
    }
  }
}
```

```
let query = "mutation{ create_subitem (parent_item_id: 1234567890, item_name: \"New subitem\", column_values: \"{\\\"date0\\\":\\\"2023-05-25\\\"}\") { id board { id }}}";

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

You can use the following argument(s) to define the new subitem's characteristics.

Argument | Description
--- | ---
column_valuesJSON | The column values of the new subitem.
create_labels_if_missingBoolean | Creates status/dropdown labels if they're missing. Requires permission to change the board structure.
item_nameString! | The new subitem's name.
parent_item_idID! | The parent item's unique identifier.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
