---

title: Plan
source: https://developer.monday.com/api-reference/reference/plan
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query an account's monday.com plan data using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Plan

Learn how to query an account's monday.com plan data using the platform API

monday.com offers a variety of plans for users to choose from based on their needs.

# Plan queries

Required scope: account:read

- Returns an array containing metadata about a specific plan
- Will return null for users on trial accounts
- Can only be nested inside an account query

GraphQLJavaScript
```
query { 
  account {
    plan {
      max_users
      period
      tier
      version
    }
  }
}
```

```
let query = "query { account { plan { max_users period tier version } } }";

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

## Fields

You can use the following field(s) to specify what information your plan query will return.

Fields | Description
--- | ---
max_usersInt! | The maximum number of users allowed on the plan. This will be 0 for free and developer accounts.Deprecated:useapps_monetization_infoinstead.
periodString | The plan's time period.
tierString | The plan's tier.
versionInt! | The plan's version.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
