---

title: Account
source: https://developer.monday.com/api-reference/reference/account
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query monday.com accounts using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Account

Learn how to query monday.com accounts using the platform API

All monday.com users must either join an existing account or create a new one. On the account level, users can do many things, including inviting other users to join the account, specifying their primary use of the platform, or signing up for a plan.

# Queries

Required scope: account:read

- Returns an object containing metadata about a specific account
- Can be queried directly at the root or nested within a me or users query

GraphQLJavaScript
```
query {
  users {
    account {
      id
      show_timeline_weekends
      tier 
      slug
      plan {
        period
      }
    }
  }
}
```

```
let query = "query { users { account { id show_timeline_weekends tier slug plan { period }}}}";

fetch ("https://api.monday.com/v2", {
  method: 'POST',
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

You can use the following field(s) to specify what information your account query will return. Some fields will have their own fields.

Fields | Description | Enum values | Supported fields
--- | --- | --- | ---
active_members_countInt | The number of active users in the account - includes active users across all products who are not guests or viewers. |  | 
country_codeString | The account's two-letter country code in ISO3166 format.Please note:the result is based on the location of the first account admin. |  | 
first_day_of_the_weekFirstDayOfTheWeek! | The first day of the week for the account. | mondaysunday | 
idID! | The account's unique identifier. |  | 
logoString | The account's logo. |  | 
nameString! | The account's name. |  | 
planPlan | The account's payment plan. Returnsnullfor accounts with the multi-product infrastructure. |  | max_usersInt!periodStringtierStringversionInt!
products[AccountProduct] | The account's active products. |  | idIntkindAccountProductKind
show_timeline_weekendsBoolean! | Showstrueif weekends appear in the timeline. |  | 
sign_up_product_kindString | The product the account first signed up to. |  | 
slugString! | The account's slug. |  | 
tierString | The account's tier. |  |
