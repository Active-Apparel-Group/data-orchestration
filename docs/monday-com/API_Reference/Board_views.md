---

title: Board_views
source: https://developer.monday.com/api-reference/reference/board-views
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query monday board views using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Board views

Learn how to query monday board views using the platform API

monday.com board views allow you to visualize your board data differently. The API can provide you with records of all views added to a board (except for dashboard views).

# Queries

- Returns an array containing metadata about a collection of board views from a specific board
- Can only be nested inside a boards query

GraphQLJavaScript
```
query {
  boards (ids: 1234567890) {
    views {
      type
      settings_str
      view_specific_data_str
      name
      id
    }
  }
}
```

```
let query = 'query { boards (ids: 1234567890) { views { id name type } } }';

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

You can use the following argument(s) to reduce the number of results returned in your views query.

Argument | Description
--- | ---
ids[ID!] | The specific board IDs to return views for.
typeString | The specific type of views to return.

## Fields

You can use the following field(s) to specify what information your views query will return.

Field | Description
--- | ---
idID! | The view's unique identifier.
nameString! | The view's name.
settings_strString! | The view's settings.
typeString! | The view's type.
view_specific_data_strString! | Specific board view data (only supported for forms).
