---

title: App_subscriptions
source: https://developer.monday.com/api-reference/reference/app-subscriptions
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query app subscription data using the monday.com platform API
tags: [code, api, monday-dot-com]
summary:

---

# App subscriptions

Learn how to query app subscription data using the monday.com platform API

App monetization utilizes subscriptions as a billing contract between a user and an app. Each subscription contains unique data about the user's billing frequency, plan type, and renewal period.

# Queries

- Returns an array containing data about all of your app's subscriptions
- Can only be queried directly at the root
- Only works for app collaborators
- Limit: 120 times per minute

## 🚧

If you only want to query a specific account's subscription from the context of your app, use the app_subscription object instead.

GraphQLJavaScript
```
query {
  app_subscriptions (app_id: 1234567890) {
    cursor
    total_count 
    subscriptions {
      account_id
      monthly_price
      currency
    }
  }
}
```

```
let query = "query { app_subscriptions (app_id: 1234567890) { cursor total_count subscriptions { account_id monthly_price currency } } }";

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

You can use the following argument(s) to reduce the number of app subscriptions returned.

Fields | Description | Enum values
--- | --- | ---
account_idInt | The account's unique identifier. | 
app_idID! | The app's unique identifier. | 
cursorString | An opaque token representing the position in a set of results to fetch subscriptions from. Use this to paginate through large result sets. | 
limitInt | The number of subscriptions to return. The default is 100, but the maximum is 500. | 
statusSubscriptionStatus | The subscription's status. | activeinactive

## Fields

You can use the following field(s) to specify what information your app_subscriptions query will return.

Fields | Description | Supported fields
--- | --- | ---
cursorString | An opaque cursor that represents the position in the list after the last returned subscription. Use this cursor for pagination to fetch the next set of subscriptions. If the cursor is null, there are no more subscriptions to fetch. | 
subscriptions[AppSubscriptionDetails!]! | Further details about the app's subscriptions. | account_idInt!currencyString!days_leftInt!discounts[SubscriptionDiscount!]!end_dateStringmonthly_priceFloat!period_typeSubscriptionPeriodType!plan_idString!pricing_version_idInt!renewal_dateStringstatusSubscriptionStatus!
total_countInt! | The total number of subscriptions. |
