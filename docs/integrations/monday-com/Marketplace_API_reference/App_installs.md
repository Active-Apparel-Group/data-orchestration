---

title: App_installs
source: https://developer.monday.com/api-reference/reference/app-installs
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query app installation data using the monday.com platform API
tags: [code, api, monday-dot-com]
summary:

---

# App installs

Learn how to query app installation data using the monday.com platform API

Whenever a monday.com user installs an app, we send the installation information to the app developer to help them further understand their app's performance and usage. This information is available through webhooks and by querying app_installs .

# Queries

- Returns an object containing an app's installation details
- Can only be queried directly at the root
- Only works for app collaborators using a personal token

GraphQLJavaScript
```
query {
  app_installs (app_id: 123456789, account_id: 98766543210) {
    app_id
    timestamp
    app_install_account {
      id
    }
    app_install_user {
      id
    }
    app_version {
      major
      minor
      patch
      type
      text
    }
    permissions {
      approved_scopes
      required_scopes
    }
  }
}
```

```
let query = "query { app_installs (app_id: 123456789, account_id: 9876543210) { app_id timestamp app_install_account { id } app_install_user { id } app_version { major minor patch type text } permissions { approved_scopes required_scopes }}}";

fetch ("https://api.monday.com/v2", {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2024-01'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your app_installs query.

Argument | Description
--- | ---
account_idID | The account's unique identifier to filter results by.
app_idID! | The application's unique identifier to filter results by.
limitInt | The number of boards to return. The default is 25 and the maximum is 100.
pageInt | The page number to return. Starts at 1.

## Fields

You can use the following field(s) to specify what information your app_installs query will return. Some fields will have their own fields.

Fields | Description | Supported fields
--- | --- | ---
app_idInt! | The app's unique identifier. | 
app_install_accountAppInstallAccount! | The app installer's account details. | idInt!
app_install_userAppInstallUser! | The app installer's user details. | idInt
app_versionAppVersion | The app's version details when it was installed. | majorInt!minorInt!patchInt!textString!typeString
permissionsAppInstallPermissions | The required and approved scopes for an app installation. | approved_scopes[String!]!required_scopes[String!]!
timestampString | The date and time the app was installed. |
