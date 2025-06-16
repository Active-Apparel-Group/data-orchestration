---

title: Versions
source: https://developer.monday.com/api-reference/reference/versions
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to access all supported API versions using the monday.com platform API
tags: [code, api, monday-dot-com]
summary:

---

# Versions

Learn how to access all supported API versions using the monday.com platform API

At monday.com, we support multiple API versions to provide users with stability while still allowing us to continuously make improvements. You can find a list of current versions here , or you query the versions endpoint.

## 🚧Only want data about the specific version used in a request?

Query the version endpoint instead!

# Queries

- Returns an array containing metadata about all available API versions
- Can only be queried directly at the root

GraphQLJavaScript
```
query {
  versions {
    kind
    value
    display_name
  }
}
```

```
let query = 'query { versions { kind value display_name }}';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

This query would return the following:

JSON
```
{
  "data": {
    "versions": [
      {
        "display_name": "Previous Maintenance",
        "kind": "previous_maintenance",
        "value": "2024-01"
      },
      {
        "display_name": "Maintenance",
        "kind": "maintenance",
        "value": "2024-04"
      },
      {
        "display_name": "Current",
        "kind": "current",
        "value": "2024-07"
      },
      {
        "display_name": "Release Candidate",
        "kind": "release_candidate",
        "value": "2024-10"
      }
    ]
  },
  "account_id": 1
}
```

## Fields

You can use the following field(s) to specify what information your versions query will return.

Field | Description | Enum values
--- | --- | ---
display_nameString! | The display name of the API version. | 
kindVersionKind! | The type of API version. | currentdeprecatedmaintenanceprevious_maintenancerelease_candidate
valueString! | The API version name as a string that can be passed in theAPI-Versionheader. | 

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
