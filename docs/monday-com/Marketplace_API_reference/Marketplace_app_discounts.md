---

title: Marketplace_app_discounts
source: https://developer.monday.com/api-reference/reference/marketplace-app-discounts
author:
  - Monday
published:
created: 2025-05-25
description: Marketplace developers can grant app subscription discounts to attract and retain users. These can be managed, created, and deleted through both the Developer Center and the platform API. Queries Returns an array containing metadata about a specific app discount Can only be queried directly at the r...
tags: [code, api, monday-dot-com]
summary:

---

# Marketplace app discounts

Marketplace developers can grant app subscription discounts to attract and retain users. These can be managed, created, and deleted through both the Developer Center and the platform API.

# Queries

- Returns an array containing metadata about a specific app discount
- Can only be queried directly at the root
- Only works for app collaborators

GraphQLJavaScript
```
query {
  marketplace_app_discounts (app_id: 123456) {
    account_slug
    discount
    valid_until  	
  }
}
```

```
let query = "query { marketplace_app_discounts (input: { limit:1, app_id:123456 } ) { account_slug discount valid_until } }";

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

## Arguments

You can use the following argument(s) to reduce the number of results returned in your marketplace_app_discounts query.

Argument | Description
--- | ---
app_idID! | The app's unique identifier.

## Fields

You can use the following field(s) to specify what information your marketplace_app_discounts query will return.

Field | Description | Enum values
--- | --- | ---
account_idID! | The account's unique identifier. | 
account_slugString! | The account's slug. | 
app_plan_ids[String!]! | The app plan IDs. | 
created_atString! | The discount's creation date. | 
discountInt! | The discount's percentage. | 
is_recurringBoolean! | Returnstrueif the discount is recurring. | 
periodDiscountPeriod | The discount's period. If it returnsnull, the discount applies to both yearly and monthly plans. | MONTHLYYEARLY
valid_untilString! | The date the discount is valid until. | 

# Mutations

## Grant a discount

The grant_marketplace_app_discount mutation will grant a discount for a new marketplace app subscription. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  grant_marketplace_app_discount (
      account_slug: "Test",  
      app_id: 123456,
    	data: {
    		app_plan_ids: ["Basic"],
      	days_valid: 30, 
      	discount: 10, 
      	is_recurring: false, 
      	period: MONTHLY
    }) {
    granted_discount {
        app_id
      	period
      	discount
    }
  }
}
```

```
let query = 'mutation { grant_marketplace_app_discount ( account_slug: "Test", app_id: 123456, data: { app_plan_ids: ["Basic"], days_valid: 30, discount: 10, is_recurring: false, period: monthly }) { granted_discount { app_id period discount } } }';

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

### Arguments

You can use the following argument(s) to specify which discount to grant.

Argument | Description | Supported fields
--- | --- | ---
account_slugString! | The account's slug. | 
app_idID! | The app's unique identifier. | 
dataGrantMarketplaceAppDiscountData! | The discount's details. | app_plan_ids[String!]!days_validInt!discountInt!is_recurringBoolean!periodDiscountPeriod

## Delete a discount

The delete_marketplace_app_discount mutation will delete an existing discount for a marketplace app subscription. You can specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_marketplace_app_discount (
    account_slug: "Test", 
    app_id: 123456
  ) {
    deleted_discount {
      account_slug
      app_id
    }
  }
}
```

```
let query = 'mutation { delete_marketplace_app_discount ( account_slug: "Test", app_id: 123456 ) { deleted_discount { account_slug app_id } } }';

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

### Arguments

You can use the following argument(s) to specify which discount to delete.

Argument | Description
--- | ---
account_slugString! | The account's slug.
app_idID! | The app's unique identifier.
