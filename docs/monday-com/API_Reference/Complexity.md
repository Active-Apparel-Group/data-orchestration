---

title: Complexity
source: https://developer.monday.com/api-reference/reference/complexity
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query the complexity of an API call using the monday.com platform API
tags: [code, api, monday-dot-com]
summary:

---

# Complexity

Learn how to query the complexity of an API call using the monday.com platform API

Query complexity defines the cost of each operation you make. Each API token is allotted a fixed complexity limit for a given period to help manage the load placed on the API. The complexity endpoint can be included in any API request to return the cost of that specific query or mutation.

# Queries

- Returns a JSON object containing the complexity cost of your queries
- Can only be queried directly at the root

GraphQL queryGraphQL mutationJavaScript queryJavaScript mutation
```
query {
  complexity {
    before
    query
    after
    reset_in_x_seconds
  }
  boards (ids: 1234567890) {
    items {
      id
      name
    }
  }
}
```

```
mutation {
  complexity {
    query
    before
    after
  }
  create_item(board_id:1234567890, item_name:"test item") {
    id
  }
}
```

```
let query = "query { complexity { before query after reset_in_x_seconds } boards (ids: 1234567890) { id	name } } }";
let mutation = "mutation { complexity { query before after } create_item(board_id: 1234567890, item_name: \"test\") { id }}";

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

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : mutation
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

```
let mutation = "mutation { complexity { query before after } create_item(board_id: 1234567890, item_name: \"test\") { id }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : mutation
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Fields

You can use the following field(s) to specify what information your complexity query will return.

Field | Description
--- | ---
afterInt! | The remaining complexity after the query's execution.
beforeInt! | The remaining complexity before the query's execution.
queryInt! | This specific query's complexity.
reset_in_x_secondsInt! | The length of time (in seconds) before the complexity budget resets.
