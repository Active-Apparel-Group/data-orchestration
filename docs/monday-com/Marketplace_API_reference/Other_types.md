---

title: Other_types
source: https://developer.monday.com/api-reference/reference/marketplace-other-types
author:
  - Monday
published:
created: 2025-05-25
description: Learn about other marketplace-specific types supported by the monday platform API
tags: [code, api, monday-dot-com]
summary:

---

# Other types

Learn about other marketplace-specific types supported by the monday platform API

# App install account

The AppInstallAccount type is used as a field on app install queries . It provides the app installer's account details.

### Fields

Field | Description
--- | ---
idInt! | The unique identifier of the app installer's account.

# App install permissions

The AppInstallPermissions type is used as a field on app install queries . It provides the required and approved scopes for an app installation.

### Fields

Field | Description
--- | ---
approved_scopes[String!]! | The scopes approved by the account admin.
required_scopes[String!]! | The scopes required by the latest live app version.

# App install user

The AppInstallUser type is used as a field on app install queries . It provides the app installer's user details.

### Fields

Field | Description
--- | ---
idInt | The app installer's unique identifier.

# App subscription details

The AppSubscriptionDetails type is used as a field on app subscriptions queries. It provides the app installer's account details.

### Fields

Field | Description | Enum values | Supported fields
--- | --- | --- | ---
account_idInt! | The account's unique identifier. |  | 
currencyString! | The currency used to make the purchase. |  | 
days_leftInt! | The number of days until the subscription ends. |  | 
discounts[SubscriptionDiscount!]! | The discounts granted to the subscription. |  | discount_model_typeSubscriptionDiscountModelType!discount_typeSubscriptionDiscountType!valueInt!
end_dateString | An inactive subscription's end date. Returns null for subscriptions with anactivestatus. |  | 
monthly_priceFloat! | The subscription's monthly price (after discounts) in the currency used to make the purchase. |  | 
period_typeSubscriptionPeriodType! | The subscription's billing period frequency. | monthlyyearly | 
plan_idString! | The pricing plan's unique identifier. |  | 
pricing_version_idInt! | The pricing version's unique identifier. |  | 
renewal_dateString | An active subscription’s renewal date. Returns null for subscriptions with aninactivestatus. |  | 
statusSubscriptionStatus! | The subscription's status. | activeinactive | 

## Subscription discount

The SubscriptionDiscount type is used as a field on the app subscription details query. It provides details about a single subscription discount.

### Fields

Field | Description | Enum values
--- | --- | ---
discount_model_typeSubscriptionDiscountModelType! | The discount's type. | nominal: dollar amount of the discountpercent: percentage of the discount
discount_typeSubscriptionDiscountType! | The discount's frequency. | one_timerecurring
valueInt! | The discount's value as a percent. | 

# App version

The AppVersion type is used as a field on app install queries . It provides details about the app version when the app was installed.

### Fields

Field | Description
--- | ---
majorInt! | The app's major version.
minorInt! | The app's minor version.
patchInt! | The app's patch version.
textString! | The app's version text.
typeString | The app's version type.

# Batch extend trial period

The batch_extend_trial_period mutation enables apps monetized by monday to provide trial extensions for up to five accounts through the API.

This mutation will only work for app collaborators and will fail if you do not have the correct permissions.

GraphQL
```
mutation {
  batch_extend_trial_period (account_slugs: ["test", "monday"], app_id: 12345678, plan_id: "Plan_1", duration_in_days: 21) {
    details {
      account_slug
      reason
      success
    }
    reason
    success
  }
}
```

### Arguments

Argument | Description
--- | ---
account_slugs[String!]! | The account slug(s) to provide trial extensions for. The maximum is5.
app_idID! | The unique identifier of the application.
duration_in_daysInt! | The number of days to extend the trial. The maximum is365. If the account slugs require different durations, you must make multiple calls.
plan_idString! | The unique identifier of the payment plan.

### Fields

Field | Description
--- | ---
details[ExtendTrialPeriod!] | The details of the batch operation.
reasonString | The reason the operation resulted in an error.Please notethat this will return an empty string if the operation is successful.
successBoolean! | The result of the batch operation.Please notethat when providing extensions to multiple account slugs, this will returnfalsewhenever even one of the operations fails.

## Extend trial period

The ExtendTrialPeriod type is used as a field on the batch_extend_trial_period mutation. It provides details about a single operation from the batch.

### Fields

Field | Description
--- | ---
account_slugString! | The individual account slug.
reasonString | The reason the single operation resulted in an error.Please notethat this will returnnullif the operation is successful.
successBoolean! | The result of the single operation.

# Delete marketplace app discount

The DeleteMarketplaceAppDiscount! type is used as a field on the delete_marketplace_app_discount mutation. It returns metadata for recently deleted marketplace app discounts.

### Fields

Field | Description
--- | ---
account_slugString! | The account's slug.
app_idInt! | The app's unique identifier.

# Grant marketplace app discount

The GrantMarketplaceAppDiscount! type is used as a field on the grant_marketplace_app_discount mutation. It returns metadata for recently granted marketplace app discounts.

### Fields

Field | Description | Enum values
--- | --- | ---
app_idID! | The app's unique identifier. | 
app_plan_ids[String!]! | The app plan IDs. | 
days_validInt! | The number of days the discount will be valid. | 
discountInt! | The discount's percentage. | 
is_recurringBoolean! | Returnstrueif the discount is recurring. | 
periodDiscountPeriod | The discount's period. If it returnsnull, the discount applies to both yearly and monthly plans. | MONTHLYYEARLY

## Grant marketplace app discount data

The GrantMarketplaceAppDiscountData! type is used as an argument on the grant_marketplace_app_discount mutation. It specifies details about the discount to be granted.

### Fields

Field | Description | Enum values
--- | --- | ---
app_plan_ids[String!]! | The app plan IDs. | 
days_validInt! | The number of days the discount will be valid. | 
discountInt! | The discount's percentage. | 
is_recurringBoolean! | Whether or not the discount is recurring. | 
periodDiscountPeriod | The discount's period. | MONTHLYYEARLY
