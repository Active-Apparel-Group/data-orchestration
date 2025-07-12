---

title: Version
source: https://developer.monday.com/api-reference/reference/version
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read which API version was used while making a call via the monday.com platform API
tags: [code, api, monday-dot-com]
summary:

---

# Version

Learn how to read which API version was used while making a call via the monday.com platform API

We support a handful of API versions at any given time to help ensure smooth transitions between version releases. Each version functions differently, so your request must be to the accurate API version in order for it to run successfully.

## 🚧Want data about all available API versions?

Query the version endpoint instead!

# Queries

- Returns an object containing metadata about the API version used to make a request
- Can only be queried directly at the root

GraphQLJavaScript
```
query {
  version {
    kind
    value
    display_name
  }
}
```

```
let query = 'query { version { kind value display_name }}';

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

This query would return the following:

JSON
```
{
  "data": {
    "version": {
      "display_name": "Release Candidate",
      "kind": "release_candidate",
      "value": "2024-10"
    }
  },
  "account_id": 1
}
```

## Fields

You can use the following field(s) to specify what information your version query will return.

Field | Description | Enum values
--- | --- | ---
display_nameString! | The display name of the API version. | 
kindVersionKind! | The type of API version in use. | currentdeprecatedmaintenanceprevious_maintenancerelease_candidate
valueString! | The API version name as a string that can be passed in theAPI-Versionheader. | 

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
