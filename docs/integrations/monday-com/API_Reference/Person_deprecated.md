---

title: Person_deprecated
source: https://developer.monday.com/api-reference/reference/person
author:
  - Monday
published:
created: 2025-05-25
description: ❗️ NOTE: This section refers to the person column which has been deprecated . If you are trying to change the column value of a people column, check out the People column . The person column contains the ID of a single user. This column type has been deprecated. Reading the person column You can ret...
tags: [code, api, monday-dot-com]
summary:

---

# Person (deprecated)

## ❗️NOTE

This section refers to the person column which has been deprecated . If you are trying to change the column value of a people column, check out the People column .

The person column contains the ID of a single user. This column type has been deprecated.

# Reading the person column

You can return the data in a person column in two different formats. The text field will return the data as a simple string, and the value field will return the data as a JSON string.

JSON
```
{
  "text": "Test User",
  "value": "{\"changed_at\":\"2022-07-21T12:00:00.000Z\",\"personsAndTeams\":[{\"id\":31855020,\"kind\":\"person\"}]}"
}
```

# Updating the person column

You can update a person column with both a simple string or a JSON string.

### Simple strings

To update a person column, send the user ID of the user you want to add to the column.

For example: "4616627"

### JSON

To update a person column with JSON, send an int representing the ID of the user.

For example: "{\"id\":235326}"

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:11111, board_id:22222, column_values: "{\"person\" : {\"id\" : \"234326\"}}") {
    id
  }
}
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY'
  },
  body: JSON.stringify({
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id }}",
    variables : JSON.stringify({
      myBoardId: YOUR_BOARD_ID,
      myItemId: YOUR_ITEM_ID,
      myColumnValues: "{\"person\" : {\"id\" : \"235326\"}}"
    })
  })
})
```

## 📘Have questions?

Join our developer community ! You can share your questions and learn from fellow users and monday.com product experts.

Don’t forget to search before opening a new topic!
