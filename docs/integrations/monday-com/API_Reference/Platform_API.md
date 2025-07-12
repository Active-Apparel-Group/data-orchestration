---

title: Platform_API
source: https://developer.monday.com/api-reference/reference/platform-api
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query an account's platform API daily usage
tags: [code, api, monday-dot-com]
summary:

---

# Platform API

Learn how to query an account's platform API daily usage

All monday.com accounts are subject to the platform API daily call limit . This limit restricts the number of calls made in a day to prevent excessive load from individual accounts, maintains the API service as a free feature across all plans, and controls operational costs to continue delivering value to all our users.

This data is available for enterprise accounts through the API analytics dashboard or can be queried through the platform_api endpoint.

# Queries

To retrieve API usage data, you can query the platform_api endpoint as follows:

- Must be executed directly at the root level
- Returns an object containing metadata about the account's daily API usage

GraphQL
```
query {
  platform_api {
    daily_analytics {
      by_day { 
        day
        usage
      }
      by_app {
        app {
          name
        }
        api_app_id
        usage
      }
      by_user {
        user {
          name
        }
        usage
      }
      last_updated
    }
  }
}
```

## Fields

You can use the following field(s) to specify what information your platform_api query will return. Some fields contain nested data as detailed in the Supported fields column.

Fields | Description | Supported fields
--- | --- | ---
daily_limitDailyLimit | The account'sdaily call limit. | baseInttotalInt(includes extensions, if any)
daily_analyticsDailyAnalytics | The account's daily call limit analytics (by app, by day, or by user). | by_app[PlatformApiDailyAnalyticsByApp!]!by_day[PlatformApiDailyAnalyticsByDay!]!by_user[PlatformApiDailyAnalyticsByUser!]!last_updatedISO8601DateTime
