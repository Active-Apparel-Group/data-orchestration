---

title: Notifications
source: https://developer.monday.com/api-reference/reference/notification
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to create notifications on monday using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Notifications

Learn how to create notifications on monday using the platform API

Notifications alert users of platform activities, such as due dates, updates, and more. They appear in multiple locations, including the bell icon and email.

Notifications relevant only to the signed-in user appear under the bell icon. By default, they will also receive an email whenever they get a notification. This can be turned off and customized in the user’s profile settings.

# Mutations

Required scope: notifications:write

## Create a notification

The create_notification mutation allows you to send a notification to the bell icon via the API. Doing so may also send an email if the recipient's email preferences are set up accordingly.

If you send a notification from a board view or widget using seamless authentication, it will be sent from the app and display its name and icon. If you use a personal API key to make the call, the notification will appear to come from the user who installed the app on the account.

This mutation only sends the notification. You can't query back the notification ID when running the mutation since notifications are asynchronous.

GraphQLJavaScript
```
mutation {
  create_notification (user_id: 12345678, target_id: 674387, text: "This is a notification", target_type: Project) {
    text
  }
}
```

```
let query = "mutation { create_notification (user_id: 12345678, target_id: 674387, text: \"This is a notification\", target_type: Project) { text } }";

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

### Arguments

You can use the following argument(s) to define the new notification's characteristics.

Argument | Description | Enum values
--- | --- | ---
target_idID! | The target's unique identifier. The value depends on thetarget_type:-Post: update or reply ID-Project: item or board ID | 
target_typeNotificationTargetType! | The target's type. | -Post(sends a notification referring to an update or reply)-Project(sends a notification referring to an item or board)
textString! | The notification's text. | 
user_idID! | The user's unique identifier. | 

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
