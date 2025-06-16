---

title: Viewers
source: https://developer.monday.com/api-reference/reference/viewers
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query an update's viewers using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Viewers

Learn how to query an update's viewers using the platform API

Updates contain notes and information added to items outside of their columns. They allow users to organize communication across their organization and respond asynchronously. Many users rely on the updates section as their primary form of communication within the platform.

Users can do things like react and reply to updates, attach files, pin them to the top, and see who has viewed an update. You can use the viewers endpoint to query an update's viewers.

# Queries

Required scope: updates:read

- Returns an array containing metadata about one or a collection of an update's viewers
- Must be nested within an updates query

GraphQLJavaScript
```
query {
  updates {
    viewers {
      user_id
      medium
      user {
        name
      }
    }
  }
}
```

```
let query = "query { updates { viewers { user_id medium user { name }}}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your viewers query.

Argument | Description
--- | ---
limitInt | The number of updates to return. The default is 100.
pageInt | The page number to get. Starts at 1.

## Fields

You can use the following field(s) to specify what information your viewers query will return.

Field | Description | Possible values
--- | --- | ---
mediumString! | The channel the user's viewers the update from. | "email""mobile""web"
userUser | The user who viewed the update. | 
user_idID! | The unique identifier of the user who viewed the update. | 

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
