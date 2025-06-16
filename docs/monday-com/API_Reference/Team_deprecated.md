---

title: Team_deprecated
source: https://developer.monday.com/api-reference/reference/team
author:
  - Monday
published:
created: 2025-05-25
description: ❗️ NOTE: This section refers to the team column which has been deprecated . If you are trying to assign a team to an item, utilize the people column instead. Check out the People column for more information. The team column contains teams assigned and/or selected to an item on a board. This column h...
tags: [code, api, monday-dot-com]
summary:

---

# Team (deprecated)

## ❗️NOTE

This section refers to the team column which has been deprecated . If you are trying to assign a team to an item, utilize the people column instead.

Check out the People column for more information.

The team column contains teams assigned and/or selected to an item on a board. This column has been deprecated.

# Updating the team column

You can update a team column with a JSON string. Simple string updates are not supported.

### JSON

To update a team column send the ID of the team. The ID of a specific team can be found by using the Teams queries, checking which teams a particular user is a part of (with the User object), or opening the team’s page in monday.com and copying the number at the end of the URL.

For example: "{\"team_id\":51166}"

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:11111, board_id:22222, column_values: "{\"team2\" : {\"team_id\" : \"51166\"}}") {
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
      myColumnValues: "{\"team2\" : {\"team_id\" : \"51166\"}}"
    })
  })
})
```

## 📘Have questions?

Join our developer community ! You can share your questions and learn from fellow users and monday.com product experts.

Don’t forget to search before opening a new topic!
