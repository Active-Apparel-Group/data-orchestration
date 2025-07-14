---

title: Groups
source: https://developer.monday.com/api-reference/reference/groups
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, create, update, and delete groups from monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Groups

Learn how to read, create, update, and delete groups from monday boards using the platform API

Items are organized in different sections called groups . Each board contains one or more groups that contain one or multiple items.

# Queries

Required scope: boards:read

- Returns an array containing metadata about one or a collection of groups on a specific board
- Can only be nested within another query

GraphQLJavaScript
```
query {
  boards (ids: 1234567890) {
    groups {
      title
      id
    }
  }
}
```

```
let query = "query { boards (ids: 1234567890) { groups { title id }}}";

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

You can use the following arguments to reduce the number of results returned in your groups query.

Argument | Description
--- | ---
ids[String] | The specific groups to return.

## Fields

You can use the following field(s) to specify what information your groups query will return.

Field | Description
--- | ---
archivedBoolean | Returnstrueif the group is archived.
colorString! | The group's color.
deletedBoolean | Returnstrueif the group is deleted.
idID! | The group's unique identifier.
items_pageItemsResponse! | The group's items.
positionString! | The group's position on the board.
titleString! | The group's title.

# Mutations

Required scope: boards:write

## Create a group

The create_group mutation allows you to create a new empty group. You can also specify what fields to query back from the new group when you run the mutation.

GraphQLJavaScript
```
mutation {
  create_group (board_id: 1234567890, group_name: "new group", relative_to: "test_group", group_color: "#ff642e", position_relative_method: before_at) {
    id
  }
}
```

```
let query = "mutation { create_group (board_id: 1234567890, group_name: \"new group\", relative_to: \"test group\", position_relative_method: before_at) { id } }";

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

You can use the following argument(s) to define the new group's characteristics.

Argument | Description | Accepted values
--- | --- | ---
board_idID! | The board's unique identifier. | 
group_colorString | The group's HEX code color. | See a full list of accepted HEX code values and their corresponding colorshere(don't forget to include # in your string!)
group_nameString! | The new group's name. Maximum of 255 characters. | 
positionString(DEPRECATED) | The group's position on the board. | The group's position is determined using a string containing only a number value (no letters or special characters). The higher the value, the lower the group sits on the board; the lower the value, the higher the group sits on the board. If you provide an invalid input using letters or special characters, the group will go to the top of the board. You will get an error if you provide anumberrather than astring.For example:AssumeGroup 1has a position of 10000 andGroup 3has a position of 30000. If you want to create a new group between the other two calledGroup 2, it needs a position greater than 10000 and less than 30000.
relative_toString | The unique identifier of the group you want to create the new one in relation to. The default creates the new group below the specifiedgroup_id.You can also use this argument in conjunction withposition_relative_methodto specify if you want to create the new group above or below the group in question. | 
position_relative_methodPositionRelative | The desired position of the new group. | You can use this argument in conjunction withrelative_toto specify which group you want to create the new group above or below.-before_at:  This enum value creates the new group above therelative_tovalue. If you don't use therelative_toargument, the new group will be created at the bottom of the board.-after_at: This enum value creates the new group below therelative_tovalue. If you don't use therelative_toargument, the new group will be created at the top of the board.

## Update a group

The update_group mutation allows you to update an existing group. You can also specify what fields to query back from the updated group when you run the mutation.

GraphQLJavaScript
```
mutation {
  update_group (board_id: 1234567890, group_id: "test group id", group_attribute: relative_position_before, new_value: "test_group") { 
    id
  } 
}
```

```
let query = 'mutation { update_group(board_id: 1234567890, group_id: "test group id", group_attribute: relative_position_before, new_value: "test_group")}';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which group to update and its new value.

Argument | Description | Accepted values
--- | --- | ---
board_idID! | The board's unique identifier. | 
group_attributeGroupAttributes! | The group attribute that you want to update. | colorpositionrelative_position_afterrelative_position_beforetitle
group_idString! | The group's unique identifier. | 
new_valueString! | The new attribute value. | See a full list of accepted color valueshere.When updating a group's position using therelative_position_afterorrelative_position_beforeattributes, the new attribute value should be the unique identifier of the group you intend to place the updated group above or below.

## Duplicate group

The duplicate_group mutation allows you to duplicate a group with all of its items. You can also specify what fields to query back from the duplicated group when you run the mutation.

## 🚧Mutation-specific rate limit

The duplicate_group mutation has an additional rate limit of 40 mutations per minute. If you exceed this limit, you will receive a response with a 429 status code, and the following error message: "Call limit exceeded for DuplicateGroup".

GraphQLJavaScript
```
mutation {
  duplicate_group (board_id: 1234567890, group_id: "test group id", add_to_top: true) {
    id
  }
}
```

```
let query = "mutation { duplicate_group (board_id: 1234567890, group_id: \"test group id\", add_to_top: true) { id } }";

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

You can use the following argument(s) to specify which group to duplicate and its new properties.

Argument | Description
--- | ---
add_to_topBoolean | Boolean to add the new group to the top of the board.
board_idID! | The board's unique identifier.
group_idString! | The group's unique identifier.
group_titleString | The group's title.

## Move item to group

The move_item_to_group mutation allows you to move an item between groups on the same board. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  move_item_to_group (item_id: 1234567890, group_id: "test group id") {
    id
  }
}
```

```
let query = "mutation { move_item_to_group (item_id: 1234567890, group_id: \"test group id\") { id }}";

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

You can use the following argument(s) to specify which item to move and to which group.

Argument | Description
--- | ---
group_idString! | The group's unique identifier.
item_idID | The item's unique identifier.

## Archive a group

The archive_group mutation allows you to archive a group with all of its items. You can also specify what fields to query back from the archived group when you run the mutation.

GraphQLJavaScript
```
mutation {
  archive_group (board_id: 1234567890, group_id: "test group id") {
    id
    archived
  }
}
```

```
let query = "mutation { archive_group (board_id: 1234567890, group_id: \"test group id\") { id archived } }";

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

You can use the following argument(s) to specify which group to archive.

Argument | Description
--- | ---
board_idID! | The board's unique identifier.
group_idString! | The group's unique identifier.

## Delete a group

The delete_group mutation allows you to delete a group with all of its items. You can also specify what fields to query back from the deleted group when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_group (board_id: 1234567890, group_id: "test group id") {
    id
    deleted
  }
}
```

```
let query = "mutation { delete_group (board_id: 1234567890, group_id: \"test group id\") { id deleted } }";

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

You can use the following argument(s) to specify which group to delete.

Argument | Description
--- | ---
board_idID! | The board's unique identifier.
group_idString! | The group's unique identifier.
