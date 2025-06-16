---

title: Boards
source: https://developer.monday.com/api-reference/reference/boards
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, update, create, and delete monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Boards

Learn how to read, update, create, and delete monday boards using the platform API

monday.com boards are where users input all of their data, making them one of the core platform components. The board's structure consists of items (rows), groups (groups of rows), and columns , and the board's data is stored in items and their respective updates sections.

# Queries

Required scope: boards:read

- Returns an array containing metadata about one or a collection of boards
- Can be queried directly at the root or nest within another query. If you want to retrieve all items on a board, you can use the items_page field in your board query.

GraphQLJavaScript
```
query {
  boards (ids: 1234567890) {
    name
    state
    permissions
    items_page {
      items {
        id
        name
      }
    }
  }
}
```

```
let query = 'query { boards (ids: 1234567890) { name state permissions items_page { items { id name }}}}';

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

## Arguments

You can use the following argument(s) to reduce the number of results returned in your boards query.

Argument | Description | Enum values
--- | --- | ---
board_kindBoardKind | The type of board to return. | privatepublicshare
ids[ID!] | The specific board IDs to return. | 
limitInt | The number of boards to return. The default is 25. | 
order_byBoardsOrderBy | The order in which to retrieve your boards. | created_at(desc.)used_at(desc.)
pageInt | The page number to return. Starts at 1. | 
stateState | The state of board to return. The default isactive. | activeallarchiveddeleted
workspace_ids[ID] | The specific workspace IDs that contain the boards to return. | 

## Fields

You can use the following field(s) to specify what information your boards query will return. Some fields will have their own fields.

Field | Description | Enum values
--- | --- | ---
activity_logs[ActivityLogType] | The activity log events for the queried board(s). | 
board_folder_idID | The unique identifier of the folder that contains the board(s). Returnsnullif the board is not in a folder. | 
board_kindBoardKind! | The type of board. | privatepublicshare
columns[Column] | The board's visible columns. | 
communicationJSON | The board's communication value (typically a meeting ID). | 
creatorUser! | The board's creator. | 
descriptionString | The board's description. | 
groups[Group] | The board's visible groups. | 
idID! | The board's unique identifier. | 
item_terminologyString | The nickname for items on the board. Can be a predefined or custom value. | 
items_countInt | The number of items on the board. | 
items_pageItemsResponse! | The board's items. | 
nameString! | The board's name. | 
ownerUser!(DEPRECATED) | The user who created the board. | 
owners[User]! | The board's owners. | 
permissionsString! | The board's permissions. | assignee,collaborators,everyone,owners
stateState! | The board's state. | active,all,archived,deleted
subscribers[User]! | The board's subscribers. | 
tags[Tag] | The specific tags on the board. | 
team_owners[Team!] | The board's team owners. | 
team_subscribers[Team!] | The board's team subscribers. A value of -1 indicates that the "everyone at account" team is subscribed to this board. | 
top_groupGroup! | The group at the top of the board. | 
typeBoardObjectType | The board's object type. | board,custom_object,document,sub_items_board
updated_atISO8601DateTime | The last time the board was updated. | 
updates[Update] | The board's updates. | 
urlString! | The board's URL. | 
views[BoardView] | The board's views. | 
workspaceWorkspace | The workspace that contains the board. Returnsnullfor theMainworkspace. | 
workspace_idID | The unique identifier of the board's workspace. Returnsnullfor theMainworkspace. | 

# Mutations

Required scope: boards:write

## Create a board

The create_board mutation allows you to create a new board via the API. You can also specify what fields to query back from the new board when you run the mutation. Please note that the user that creates the board via the API will automatically be added as the board's owner when creating a private or shareable board or if the board_owners_ids argument is missing.

## 🚧Mutation-specific rate limit

This mutation has an additional rate limit of 40 mutations per minute. If you exceed this limit, you will receive 429 HTTP response code with a Call limit exceeded for CreateBoard error message.

GraphQLJavaScript
```
mutation {
  create_board (board_name: "my board", board_kind: public) {
    id
  }
}
```

```
let query = 'mutation { create_board (board_name: \"my board\", board_kind: public) {	id }}';

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

You can use the following argument(s) to define the new board's characteristics.

Argument | Description | Enum values
--- | --- | ---
board_kindBoardKind! | The type of board to create. | privatepublicshare
board_nameString! | The new board's name. | 
board_owner_ids[ID!] | A list of the IDs of the users who will be board owners. | 
board_owner_team_ids[ID!] | A list of the IDs of the teams who will be board owners. | 
board_subscriber_ids[ID!] | A list of the IDs of the users who will subscribe to the board. | 
board_subscriber_teams_ids[ID!] | A list of the IDs of the teams who will subscribe to the board. | 
descriptionString | The new board's description. | 
emptyBoolean | Creates an empty board without any default items. Only available in version2025-07and later. | 
folder_idID | The board's folder ID. | 
template_idID | The board's template ID.* | 
workspace_idID | The board's workspace ID. | 

* You can see your personal template IDs in the template preview screen by activating Developer Mode in your monday.labs. For built-in templates, the template ID will be the board ID of the board created from the template.

## Duplicate a board

The duplicate_board mutation allows you to duplicate a board with all of its items and groups to a specific workspace or folder of your choice via the API.

## 🚧Mutation-specific rate limit

This mutation has an additional rate limit of 40 mutations per minute. If you exceed this limit, you will receive 429 HTTP response code with a "Call limit exceeded for DuplicateBoard" error message.

You can also specify what fields to query back from the new board when you run the mutation. The query will also indicate whether the process is synchronous or asynchronous. Since an asynchronous duplication process may take some time to complete, the query may initially return partial data.

GraphQLJavaScript
```
mutation {
  duplicate_board(board_id: 1234567890, duplicate_type: duplicate_board_with_structure) {
    board {
      id
    }
  }
}
```

```
let query = 'mutation { duplicate_board(board_id: 1234567890, duplicate_type: duplicate_board_with_structure) { board { id }}}';

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

You can use the following argument(s) to specify which board to duplicate and what properties to include.

Argument | Description | Enum values
--- | --- | ---
board_idID! | The board's unique identifier. | 
board_nameString | The duplicated board's name. If omitted, it will be automatically generated. | 
duplicate_typeDuplicateBoardType! | The duplication type. | duplicate_board_with_pulsesduplicate_board_with_pulses_and_updatesduplicate_board_with_structure
folder_idID | The destination folder within the destination workspace. Thefolder_idis required if you are duplicating to another workspace, otherwise, it is optional. If omitted, it will default to the original board's folder. | 
keep_subscribersBoolean | Ability to duplicate the subscribers to the new board. Defaults to false. | 
workspace_idID | The destination workspace. If omitted, it will default to the original board's workspace. | 

## Update a board

The update_board mutation allows you to update a board via the API.

GraphQlJavaScript
```
mutation {
  update_board(board_id: 1234567890, board_attribute: description, new_value: "This is my new description") 
}
```

```
let query = 'mutation { update_board(board_id: 1234567890, board_attribute: description, new_value: "This is my new description")}';

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

You can use the following argument(s) to specify which board to update and its new value.

Argument | Description | Enum values
--- | --- | ---
board_attributeBoardAttributes! | The board's attribute to update. | communication,description,name
board_idID! | The board's unique identifier. | 
new_valueString! | The new attribute value. | 

## Archive a board

The archive_board mutation allows you to archive a board via the API. You can also specify what fields to query back from the archived board when you run the mutation.

GraphQLJavaScript
```
mutation {
  archive_board (board_id: 1234567890) {
    id
  }
}
```

```
let query = 'mutation { archive_board (board_id: 1234567890) { id }}';

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

You can use the following argument(s) to specify which board to archive.

Argument | Description
--- | ---
board_idID! | The board's unique identifier.

## Delete a board

The delete_board mutation allows you to delete a board via the API. You can also specify what fields to query back from the deleted board when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_board (board_id: 1234567890) {
    id
  }
}
```

```
let query = 'mutation { delete_board (board_id: 1234567890) { id }}';

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

You can use the following argument(s) to specify which board to delete.

Argument | Description
--- | ---
board_idID! | The board's unique identifier.

## Add subscribers to a board (DEPRECATED)

The add_subscribers_to_board mutation allows you to add subscribers to a board via the API. You can use the add_users_to_board mutation instead.

GraphQLJavaScript
```
mutation {
  add_subscribers_to_board (board_id: 1234567890, user_ids: [12345678, 87654321, 01234567], kind: owner) {
    id
  }
}
```

```
let query = 'mutation { add_subscribers_to_board (board_id: 1234567890, user_ids: [12345678, 87654321, 01234567], kind: owner) { id } }';

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

You can use the following argument(s) to specify which users to subscribe to the board.

Argument | Description | Enum values
--- | --- | ---
board_idID! | The board's unique identifier. | 
kindBoardSubscriberKind | The subscriber's kind. | ownersubscriber
user_ids[Int]! | The user IDs to subscribe to the board. |
