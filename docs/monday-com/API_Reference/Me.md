---

title: Me
source: https://developer.monday.com/api-reference/reference/me
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to use API tokens to read user data through the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Me

Learn how to use API tokens to read user data through the platform API

All monday.com users have a unique set of user details and different roles within an account. These details are available to access via the API by querying the me object.

# Queries

Required scope: me:read

- Returns an object containing metadata about the user whose API key is being used
- Can only be queried directly at the root

GraphQLJavaScript
```
query {
  me {
    is_guest
    created_at
    name
    id
  }
}
```

```
let query = "query { me { is_guest created_at name id}}";

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

## Fields

You can use the following field(s) to specify what information your me query will return.

Fields | Description
--- | ---
accountAccount! | The user's account.
birthdayDate | The user's date of birth that's set in their profile. Returned asYYYY-MM-DD.
country_codeString | The user's country code.
created_atDate | The user's creation date. Returned as YYYY-MM-DD.
current_languageString | The user's language.
join_dateDate | The date the user joined the organization. Returned asYYYY-MM-DD.
emailString! | The user's email.
enabledBoolean! | Returnstrueif the user is enabled.
idID! | The user's unique identifier.
is_adminBoolean | Returnstrueif the user is an admin.
is_guestBoolean | Returnstrueif the user is a guest.
is_pendingBoolean | Returnstrueif the user didn't confirm their email yet.
is_verifiedBoolean | Returnstrueif the user verified their email.
is_view_onlyBoolean | Returnstrueif the user is only a viewer.
last_activityDate | The last date and time the user was active.
locationString | The user's location.
mobile_phoneString | The user's mobile phone number.
nameString! | The user's name.
phoneString | The user's phone number.
photo_originalString | Returns the URL of the user's uploaded photo in its original size.
photo_smallString | Returns the URL of the user's uploaded photo in a small size (150x150 px).
photo_thumbString | Returns the URL of the user's uploaded photo in thumbnail size (100x100 px).
photo_thumb_smallString | Returns the URL of the user's uploaded photo in a small thumbnail size (50x50 px).
photo_tinyString | Returns the URL of the user's uploaded photo in tiny size (30x30 px).
sign_up_product_kindString | The product the user first signed up to.
teams[Team] | The user's teams.
time_zone_identifierString | The user's timezone identifier.
titleString | The user's title.
urlString! | The user's profile URL.
utc_hours_diffInt | The user’s UTC hours difference.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
