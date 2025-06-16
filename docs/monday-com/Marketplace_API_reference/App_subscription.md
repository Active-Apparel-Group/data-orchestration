---

title: App_subscription
source: https://developer.monday.com/api-reference/reference/app-subscription
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query app subscription data using the monday.com platform API
tags: [code, api, monday-dot-com]
summary:

---

# App subscription

Learn how to query app subscription data using the monday.com platform API

App monetization utilizes subscriptions as a billing contract between a user and an app. Each subscription contains unique data about the user's billing frequency, plan type, and renewal period.

# Queries

- Returns an array containing the current app and account subscription details based on the token used
- Can only be queried directly at the root
- If an account has a mock subscription and a real one, it will only return the mock subscription

## 🚧

This query is called on the app-level. It can only be called within the context of an app, not from the API Playground.

It only returns details based on the token used. If you want to query all of your app's subscriptions, use the app_subscriptions object instead.

GraphQLJavaScript
```
query {
  app_subscription {
    billing_period
    days_left
    is_trial
    plan_id
    renewal_date
  }
}
```

```
let query = "query { app_subscription { billing_period days_left is_trial plan_id renewal_date } }";

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

The example response body from the above query.

JSON
```
{ 
  "data": {
    "app_subscription":[
      {
        "billing_period": "yearly",
        "days_left": 278,
        "is_trial": true,
        "plan_id": "basic_plan_15_users",
        "renewal_date": "2023-08-27T00:00:00+00:00",
      }
    ]
  },
  "account_id": 5
}
```

## Fields

You can use the following field(s) to specify what information your app_subscription query will return.

Fields | Description
--- | ---
billing_periodString | The billing period frequency:monthlyoryearly.
days_leftInt | The number of days left until the subscription ends.
is_trialBoolean | Returnstrueif it is still a trial subscription.
max_unitsInt | The maximum number of seats allowed for seat-based plans. Returnsnullfor feature-based plans.
plan_idString! | The subscription plan ID from the app's side.
pricing_versionInt | The subscription's pricing version.
renewal_dateDate! | The date when the subscription renews.

# Mutations

## Set mock app subscription

The set_mock_app_subscription mutation will create a mock subscription for an account and app based on the token you're using, and it returns an app_subscription object. Mock subscriptions disappear after 24 hours, and each account-app pair can create one mock subscription.

Please note that you may need to refresh your browser after creating a mock subscription so that it shows in your account.

GraphQL
```
mutation {
  set_mock_app_subscription (
    app_id: 12345,
		partial_signing_secret: "abcde12345",
    is_trial: true,
    plan_id: "basic_plan_15_users",
    max_units: 15
  ) {
    plan_id
  }
}
```

### Arguments

Argument | Description
--- | ---
app_idID! | The app’s unique identifier. You can access this ID from the URL of your app in the following format:myaccount.monday.com/apps/manage/{YOUR_APP_ID}/app_versions/12345/sections/appDetails.
billing_periodString | The billing period frequency:monthlyoryearly.
is_trialBoolean | Specifies whether or not the subscription is a trial. Defaults tofalse.
max_unitsInt | For seat-based apps, the maximum number of seats allowed on the mock plan. Only available in2025-04and later.
partial_signing_secretString! | The last 10 characters of your app’s signing secret.
plan_idString | The plan's unique identifier for the mock subscription.
pricing_versionInt | The subscription's pricing version.
renewal_dateDate | The date when the subscription renews. Defaults to one year in the future and follows UTC DateTime.Please notethat the mutation will fail if you do not use a future date.

## Remove mock app subscription

The remove_mock_app_subscription mutation removes the mock subscription for the current account. It will return an app_subscription object or an error if no mock subscription exists.

GraphQL
```
mutation {
 remove_mock_app_subscription (app_id: 12345, partial_signing_secret: "abcde12345") {
   billing_period
   days_left
   is_trial
 }
}
```

### Arguments

Argument | Description
--- | ---
app_idID! | The app's unique identifier.
partial_signing_secretString! | The last 10 characters of your app's signing secret.
