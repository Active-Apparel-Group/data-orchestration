---

title: Folders
source: https://developer.monday.com/api-reference/reference/folders
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, create, update, and delete folders using the monday.com platform API
tags: [code, api, monday-dot-com]
summary:

---

# Folders

Learn how to read, create, update, and delete folders using the monday.com platform API

Users can create folders inside their workspaces to help organize their boards, dashboards, and workdocs.

# Queries

Required scope: workspaces:read

- Returns an array containing metadata about one or a collection of folders
- Can only be queried directly at the root

GraphQLJavaScript
```
query {
  folders (workspace_ids: 1234567890) {
    name
    id
    children {
      id
      name
    }
  }
}
```

```
let query = "query { folders (workspace_ids: 1234567890) { name id children { id name }}}";

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

You can use the following argument(s) to reduce the number of results returned in your folders query.

Argument | Description
--- | ---
ids[ID!] | The specific folders to return.
limitInt | The number of folders to get. The default is 25 and the maximum is 100.
pageInt | The page number to return. Starts at 1.
workspace_ids[ID] | The unique identifiers of the specific workspaces to return. You can pass[null]to return folders in the Main Workspace.

## Fields

You can use the following field(s) to specify what information your folders query will return.

Field | Description
--- | ---
children[Board]! | The folder's contents, excluding dashboards and subfolders.
colorFolderColor | The folder's color. See a full list of colorshere.
created_atDate! | The folder's creation date.
idID! | The folder's unique identifier.
nameString! | The folder's name.
owner_idID | The unique identifier of the folder's owner.
parentFolder | The folder's parent folder.
sub_folders[Folder]! | The folders inside of the parent folder.
workspaceWorkspace! | The workspace that contains the folder.

# Mutations

Required scope: workspaces:write

## Create a folder

The create_folder mutation allows you to create a new folder in a workspace. You can also specify what fields to query back from the new folder when you run the mutation.

GraphQLJavaScript
```
mutation {
  create_folder (name: "New folder", workspace_id: 1234567890) {
    id
  }
}
```

```
let query = "mutation { create_folder (name: \"New folder\" , workspace_id: 1234567890) { id }}";

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

You can use the following arguments to define the new folder's characteristics.

Argument | Description
--- | ---
colorFolderColor | The folder's color. See a full list of colorshere.
nameString! | The folder's name.
parent_folder_idID | The ID of the folder you want to nest the new one under.
workspace_idID | The unique identifier of the workspace to create the new folder in.

## Update a folder

The update_folder mutation allows you to update a folder's color, name, or parent folder. You can also specify what fields to query back from the updated folder when you run the mutation.

GraphQLJavaScript
```
mutation {
  update_folder (folder_id: 1234567890, name: "Updated folder name") {
    id
  }
}
```

```
let query = "mutation { update_folder (folder_id: 1234567890, name: \"Updated folder name\") { id }}";

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

You can use the following arguments to define the updated folder's characteristics.

Argument | Description
--- | ---
colorFolderColor | The folder's color. See a full list of colorshere.
folder_idID! | The folder's unique identifier.
nameString | The folder's name.
parent_folder_idID | The ID of the folder you want to nest the updated one under.

## Delete a folder

The delete_folder mutation allows you to delete and folder and all its contents. You can also specify what fields to query back from the deleted folder when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_folder (folder_id: 1234567890) {
    id
  }
}
```

```
let query = "mutation { delete_folder (folder_id: 1234567890) { id }}";

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

You can use the following arguments to specify which folder to delete.

Argument | Description
--- | ---
folder_idID! | The folder's unique identifier.
