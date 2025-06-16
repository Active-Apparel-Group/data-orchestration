---

title: Docs
source: https://developer.monday.com/api-reference/reference/docs
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read and create monday docs using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Docs

Learn how to read and create monday docs using the platform API

Workdocs serve as a central place for teams to plan and execute work in a collaborative format. They are like virtual whiteboards that allow you to jot down notes, create charts, and populate items on a board from the text you type. Docs enable teams to collaborate in real time without overwriting each other's work. Users can even implement built-in features like widgets, templates, and apps to enhance their docs.

# Queries

Required scope: docs:read

- Returns an array containing metadata about a collection of docs
- Can only be queried directly at the root

GraphQLJavaScript
```
query {
  docs (object_ids: 123456789, limit: 1) {
    id
    object_id
    settings
    created_by {
      id
      name
    }
  }
}
```

```
let query = "query { docs (ids: 123456789, limit: 1) { id object_id settings created_by { id name }}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YourSuperSecretAPIkey'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your docs query.

Argument | Description | Enum values
--- | --- | ---
ids[ID!] | The specific docs to return. In the UI, this is the ID that appears in the top-left corner of the doc whendeveloper modeis activated. | 
limitInt | The number of docs to get. The default is 25. | 
object_ids[ID!] | The unique identifiers of associated boards or objects. In the UI, this is the ID that appears in the URL and the doc column values. | 
order_byDocsOrderBy | The order in which to retrieve your boards. The default showscreated_atwith the newest docs listed first. This argument will not be applied if you query docs by specificids. | created_atused_at
pageInt | The page number to return. Starts at 1. | 
workspace_ids[ID] | The unique identifiers of the specific workspaces to return. | 

## Fields

You can use the following field(s) to specify what information your docs query will return. Please note that some fields will have their own arguments.

Field | Description | Enum values
--- | --- | ---
blocks[DocumentBlock] | The document's content blocks. | 
created_atDate | The document's creation date. | 
created_byUser | The document's creator. | 
doc_folder_idID | The unique identifier of the folder that contains the doc. Returnsnullfor the first level. | 
doc_kindBoardKind! | The document's kind. | privatepublicshare
idID! | The document's unique identifier. In the UI, this ID appears in the top-left corner of the doc whendeveloper modeis activated. | 
nameString! | The document's name. | 
object_idID! | The associated board or object's unique identifier. In the UI, this is the ID that appears in the URL and the doc column values. | 
relative_urlString | The document's relative URL. | 
urlString | The document's direct URL. | 
workspaceWorkspace | The workspace that contains this document. Returnsnullfor theMainworkspace. | 
workspace_idID | The unique identifier of the workspace that contains the doc. Returnsnullfor theMainworkspace. | 
settingsJSON | The document's settings. | 

### Settings field

The settings field returns document-level settings. You can view a sample payload below, but keep in mind that the API will return payloads in a slightly different format using escaped JSON.

JSON
```
{
  "fontSize": "small", // "small", "normal", or "large"
  "hasTitle": true, // true or false
  "coverPhoto": {
    "isEnabled": true, // true or false
    "imageUrl": "", 
    "fromTop": 0
 	 },
  "fontFamily": "Serif", // "Serif", "Mono", or "Default"
  "isPageLayout": true, // true or false
  "backgroundColor": "var(--color-sofia_pink-selected)", 
  "isFullWidthMode": false, // true or false
  "backgroundPattern": null, // "sticky-note", "notepad", or "cubes-notepad"
  "showTableOfContent": true // true or false
}
```

# Mutations

## Create a doc

Required scope: docs:write

The create_doc mutation allows you to create a new doc in a document column or workspace. You can also specify what fields to query back from the new doc when you run the mutation.

GraphQLJavaScript
```
mutation {
  create_doc (location: {workspace: { workspace_id: 12345678, name:"New doc", kind: private}}) {
    id
  }
}
```

```
let query = 'mutation { create_doc (location: {workspace: {workspace_id: 12345678, name: "New doc", kind:private}}) { id }}';

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

Argument | Description | Supported fields
--- | --- | ---
locationCreateDocInput! | The new document's location. | boardCreateDocBoardInputworkspaceCreateDocWorkspaceInput

## Create a doc column

The create_column mutation allows you to create a new doc column via the API. You can also specify what fields to query back from the new column when you run the mutation.

GraphQLJavaScript
```
mutation {
  create_column (board_id: 1234567890, column_type: doc, title: "Task info") {
    id
  }
}
```

```
let query = 'mutation {  create_column (board_id: 1234567890, column_type: doc, title: "Task info") { id }}';

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

You can use the following argument(s) to define the new column's characteristics.

Argument | Description
--- | ---
after_column_idID | The unique identifier of the column after which the new column will be created.
board_idID! | The unique identifier of the board where the new column should be created.
column_typeColumnType! | The type of column to create.
defaultsJSON | The new column's defaults.
descriptionString | The new column's description.
idString | The column's user-specified unique identifier. The mutation will fail if it does not meet any of the following requirements:- [1-20] characters in length (inclusive)- Only lowercase letters (a-z) and underscores (_)- Must be unique (no other column on the board can have the same ID)- Can't reuse column IDs, even if the column has been deleted from the board- Can't be null, blank, or an empty string
titleString! | The new column's title.
