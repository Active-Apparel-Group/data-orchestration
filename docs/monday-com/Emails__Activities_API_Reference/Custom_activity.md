---

title: Custom_activity
source: https://developer.monday.com/api-reference/reference/custom-activity
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, create, and custom activities from the Email &amp; Activities app using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Custom activity

Learn how to read, create, and custom activities from the Email & Activities app using the platform API

The Emails & Activities app (E&A) is a useful tool that enables monday.com CRM customers to manage client communication in one centralized location. Each contact is logged and tracked as an activity in the app's timeline for easy access to important details and updates.

You can choose from default activities, like Meeting or Call Summary , or you can create custom activities to better organize your contacts.

# Queries

- Returns an array containing metadata about custom activities in the E&A timeline
- Can only be queried directly at the root
- Limit: up to 50 custom activities

GraphQLJavaScript
```
query {
  custom_activity {
    color
    icon_id
    id
    name
    type
  }
}
```

```
let query = 'query { custom_activity { color icon_id id name type }}';

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

## Fields

You can use the following field(s) to specify what information your custom_activity query will return.

Field | Description
--- | ---
colorCustomActivityColor | The custom activity's color. View a full list of names and their corresponding colorshere.
icon_idCustomActivityIcon | The custom activity's icon. View a full list of names and their corresponding iconshere.
idID | The custom activity's unique identifier.
nameString | The custom activity's name.
typeString | The custom activity's type.

# Mutations

## Create a custom activity

The create_custom_activity mutation allows you to create a custom activity in the E&A app via the API. You can also specify what fields to query back from the new activity when you run the mutation.

GraphQLJavaScript
```
mutation {
  create_custom_activity (color: SLATE_BLUE, icon_id: TRIPOD, name: "Test custom activity") {
    id
  }
}
```

```
let query = 'mutation { create_custom_activity (color: SLATE_BLUE, icon_id: TRIPOD, name: \"Test custom activity\") {	id }}';

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

You can use the following argument(s) to define the new custom activity.

Argument | Description | Enum values
--- | --- | ---
colorCustomActivityColor! | The custom activity's color. View a full list of names and their corresponding colorshere. | BRINK_PINKCELTIC_BLUECORNFLOWER_BLUEDINGY_DUNGEONGO_GREENGRAYLIGHT_DEEP_PINKLIGHT_HOT_PINKMAYA_BLUEMEDIUM_TURQUOISEPARADISE_PINKPHILIPPINE_GREENPHILIPPINE_YELLOWSLATE_BLUEVIVID_CERULEANYANKEES_BLUEYELLOW_GREENYELLOW_ORANGE
icon_idCustomActivityIcon! | The custom activity's icon. View a full list of names and their corresponding iconshere. | ASCENDINGCAMERACONFERENCEFLAGGIFTHEADPHONESHOMEKEYSLOCATIONNOTEBOOKPAPERPLANEPLANEPLIERSTRIPODTWOFLAGSUTENSILS
nameString! | The custom activity's name. | 

## Delete a custom activity

The delete_custom_activity mutation allows you to delete a custom activity in the E&A app via the API. You can also specify what fields to query back from the deleted activity when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_custom_activity (id: "cbb37d0e-04ee-3662-z832-c4150e80eddz") {
    name
  }
}
```

```
let query = 'mutation { delete_custom_activity (id: \"cbb37d0e-04ee-3662-z832-c4150e80eddz\") {	name }}';

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

You can use the following argument(s) to define which custom activity to delete.

Argument | Description
--- | ---
idString! | The custom activity's unique identifier.
