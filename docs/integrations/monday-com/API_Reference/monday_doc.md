---

title: monday_doc
source: https://developer.monday.com/api-reference/reference/document
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, update, and clear the monday doc column on boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# monday doc

Learn how to read, update, and clear the monday doc column on boards using the platform API

Workdocs are essentially virtual whiteboards that enable teams and organizations to collaborate and communicate. The monday doc column stores these documents in one location and allows you to update and create new ones in the column itself. You can read , update , and clear the monday doc column via the API, but you currently cannot filter your results by it.

## Read the monday doc column

You can query the monday doc column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the monday doc column are of the DocValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on DocValue {
        file
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
fileFileDocValue | The column's attached document.
idID! | The column's unique identifier.
textString | The column's value as text. This field will always return"".
typeColumnType! | The column's type.
valueJSON | The column's JSON-formatted raw value.
valueJSON | The column's JSON-formatted raw value.

## Create a doc

You can update the monday doc column using the create_doc mutation. Please note that this requires the docs:write scope.

GraphQLJavaScript
```
mutation {
  create_doc (location: { board: {item_id: 1234567890, column_id: "monday_doc"}}) {
    id
  }
}
```

```
let query = 'mutation {  create_doc (location: {board: {item_id: 1234567890. column_id: "monday_doc"}}) { id }}';

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

## Create a doc column

You can use the create_column mutation to create a new doc column.

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

## Clear the monday doc column

You can clear a monday doc column using the change_column_value mutation and passing "{\"clear_all\": true}" in the value argument.

GraphQLJavaScript
```
mutation {
 change_column_value(board_id:1234567890, item_id:9876543210, column_id: "monday_doc", value: "{\"clear_all\": true}") {
  id
 }
}
```

```
var query = "mutation { change_column_value (board_id: 1234567890, item_id: 9876543210, column_id: \"files\", value: \"{\\\"clear_all\\\": true}\") {id}}";

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

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
