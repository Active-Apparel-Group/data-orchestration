---

title: Apps_monetization_info
source: https://developer.monday.com/api-reference/reference/apps-monetization-info
author:
  - Monday
published:
created: 2025-05-25
description: Seat-based pricing is one pricing method available for marketplace apps. In this method, users purchase an app subscription based on the size of their monday account. When users make a purchase, our UI will intutitively recommend an app plan based on their monday account size. Seats fluctuate over t...
tags: [code, api, monday-dot-com]
summary:

---

# Apps monetization info

Seat-based pricing is one pricing method available for marketplace apps. In this method, users purchase an app subscription based on the size of their monday account.

When users make a purchase, our UI will intutitively recommend an app plan based on their monday account size. Seats fluctuate over time, so developers must monitor account size to ensure compliance using the apps_monetization_info API.

# Queries

Required scope: account:read

- Returns an integer representing the number of seats in an account
- Can only be queried directly at the root

GraphQLJavaScript
```
query {
  apps_monetization_info {
    seats_count
  }
}
```

```
let query = "query { apps_monetization_info { seats_count } }";

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

You can use the following field(s) to specify what information your apps_monetization_info query will return.

Field | Description
--- | ---
seats_countInt | For accounts withone product, this returns the total number of seats in the account.For accounts withmore than one product, this returns the product subscription with the highest seat count.
