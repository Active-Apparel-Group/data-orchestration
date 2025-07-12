---

title: App_subscription_operations
source: https://developer.monday.com/api-reference/reference/app-subscription-operations
author:
  - Monday
published:
created: 2025-05-25
description: Monetization by monday offers two different types of app pricing models: feature-based and seat-based . When using feature-based pricing, it's vital to track the number of operations an app completes so they don't exceed their allotted usage. The app_subscription_operations object and its associated...
tags: [code, api, monday-dot-com]
summary:

---

# App subscription operations

Monetization by monday offers two different types of app pricing models: feature-based and seat-based . When using feature-based pricing, it's vital to track the number of operations an app completes so they don't exceed their allotted usage.

The app_subscription_operations object and its associated queries and mutations allow you to do just that by counting usage per operation type (kind) and per account. For annual and monthly subscriptions, the counter resets monthly based on the renewal date. For example, if a subscription renews annually on the 15th of the month, the counter will reset on the 15th of each month.

Using the increase_app_subscription_operations mutation, you can increase the operation counter based on an account's usage and then query app_subscription_operations to read the updated values. These queries and mutations will only work with access tokens generated for the app , and the account must have an active app subscription . Developer access tokens will not work .

# Queries

- Returns an object containing an operation count for feature-based apps
- Can only be queried directly at the root

GraphQLJavaScript
```
query {
  app_subscription_operations (kind: "image_scan") {
    counter_value
    period_key
   }
 }
```

```
let query = "query { app_subscription_operations (kind: \"image_scan\") { counter_value period_key }}";

fetch ("https://api.monday.com/v2", {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-version' : '2024-01'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of app subscription operations returned.

Argument | Description
--- | ---
kindString | The operation's name.

## Fields

You can use the following field(s) to specify what information your app subscription operations query will return. Some fields will have their own fields.

Field | Description | Supported fields
--- | --- | ---
app_subscription[AppSubscription] | The account's app subscription details. | billing_periodStringdays_leftIntis_trialBooleanplan_idString!pricing_versionIntrenewal_dateDate!
counter_valueInt | The new counter value. The counter will restart each time a new app subscription period begins. | 
kindString! | The operation's name. | 
period_keyString | The unique window key (related to subscription periods). | 

# Mutations

## Increase app subscription operations

The increase_app_subscription_operations mutation will increase the counter for a specific operation. You can also specify what field(s) to query back when you run the mutation.

It will return an error if no active subscription exists for the supplied token.

GraphQLJavaScript
```
mutation {
   increase_app_subscription_operations(kind: "image_scan", increment_by: 2){
      counter_value
   }
 }
```

```
let query = "mutation { increase_app_subscription_operations (kind: \"image_scan\", increment_by: 2) { counter_value }}";

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

### Arguments

You can use the following argument(s) to specify which operation to increase and by how much. If you omit these arguments, it will default to a global kind and increment by 1.

Argument | Description
--- | ---
increment_byInt | The amount to increase the counter by. Must be a positive number.
kindString | This can be an alphanumeric string of up to 14 characters, including the-and_symbols.
