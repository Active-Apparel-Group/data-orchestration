---

title: App
source: https://developer.monday.com/api-reference/reference/app
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query apps built with the monday.com apps framework
tags: [code, api, monday-dot-com]
summary:

---

# App

Learn how to query apps built with the monday.com apps framework

Using the apps framework , you can build apps on top of the monday.com platform. These apps extend the platform's core functionality by bridging gaps and enabling you to customize your workflows.

Apps can be shared directly with select accounts, listed in the app marketplace for all monday.com users, or kept private within the account. They are created and managed through the Developer Center , but you can also retrieve certain data by querying the app endpoint.

# Queries

To retrieve app data, you can query the app endpoint as follows:

- Can be queried directly at the root level or nested within a daily_analytics query
- Returns an object containing metadata about an app(s)

GraphQL
```
query {
  platform_api {
    daily_analytics {
      by_app {
        app {
          name
          features {
            type
            name
          }
          id
          api_app_id
          state
        }
        usage
      }
    }
  }
}
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your app query.

Argument | Description
--- | ---
idID! | The app's unique identifier.

## Fields

You can use the following field(s) to specify what information your app query will return. Some fields contain nested data as detailed in the Supported fields column.

Field | Description | Supported fields
--- | --- | ---
api_app_idID | The app's unique API consumer identifier. | 
client_idString | The app's unique API consumer identifier. | 
created_atDate | The app's creation date. | 
features[AppFeatureType!] | The app's features. | app_idIDcreated_atDatedataJSONidID!nameStringtypeStringupdated_atDate
idID! | The app's unique identifier. | 
kindString | The app's kind. | 
nameString | The app's name. | 
stateString | The app's state (active/inactive). | 
updated_atDate | The date the app was last updated. | 
user_idID | The unique identifier of the user that created the app. |
