---

title: Apps_monetization_status
source: https://developer.monday.com/api-reference/reference/apps-monetization-status
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query an account's app monetization status using the monday.com platform API
tags: [code, api, monday-dot-com]
summary:

---

# Apps monetization status

Learn how to query an account's app monetization status using the monday.com platform API

The monday.com apps framework utilizes monetization to accept and process payments within the platform itself. You can query an account's monetization status using the apps_monetization_status endpoint.

# Queries

- Returns a boolean representing whether or not an account supports monetization
- Can only be queried directly at the root

GraphQLJavaScript
```
query {
  apps_monetization_status {
    is_supported
  }
}
```

```
let query = "query { apps_monetization_status { is_supported } }";

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

You can use the following field(s) to specify what information your apps_monetization_status query will return.

Field | Description
--- | ---
is_supportedBoolean! | Returnstrueif the account supports app monetization.
