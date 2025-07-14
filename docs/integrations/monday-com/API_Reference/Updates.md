---

title: Updates
source: https://developer.monday.com/api-reference/reference/updates
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query monday.com board or item updates using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Updates

Learn how to query monday.com board or item updates using the platform API

Updates contain notes and information added to items outside of their columns. They allow users to organize communication across their organization and respond asynchronously. Many users rely on the updates section as their primary form of communication within the platform.

Users can do things like react and reply to updates, attach files, pin them to the top, and see who has viewed an update.

# Queries

Required scope: updates:read

- Limit: up to 10,000 updates
- Returns an array containing metadata about one or a collection of updates
- Can be queried directly at the root to return all updates across an account
- Can also be nested inside a boards or items query to return updates from a specific board or item
- Updates are returned in reverse chronological order (newest ones first)

GraphQLJavaScript
```
query {
  boards (ids: 1234567890) {
    updates (limit: 100) {
      body
      id
      created_at
      creator {
        name
        id
      }
    }
  }
}
```

```
let query = "query { boards (ids: 1234567890) { updates (limit: 100) { body id  created_at  creator { name id } }}}";

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

You can use the following argument(s) to reduce the number of results returned in your updates query.

Argument | Description
--- | ---
ids[ID!] | The specific ID(s) to return updates for.
limitInt | The number of updates per page. The default is 25, and the maximum is 100.
pageInt | The page number to get. Starts at 1.

## Fields

You can use the following field(s) to specify what information your updates query will return. Please note that some fields will have their own fields.

Field | Description | Supported fields
--- | --- | ---
assets[Asset] | The update's assets/files. | created_atDatefile_extensionString!file_sizeInt!idID!nameString!original_geometryStringpublic_urlString!uploaded_byUser!urlString!url_thumbnailString
bodyString! | The update's HTML-formatted body. | 
created_atDate | The update's creation date. | 
creatorUser | The update's creator. | 
creator_idString | The unique identifier of the update's creator. | 
edited_atDate! | The date the update'sbodywas last edited. | 
idID! | The update's unique identifier. | 
itemItem | The update's item. | 
item_idString | The update's item ID. | 
likes[Like!]! | The update's likes. | 
pinned_to_top[UpdatePin!]! | The update's pin to top data. | item_idID!
replies[Reply!] | The update's replies. | bodyString!created_atDatecreatorUsercreator_idStringidID!text_bodyStringupdated_atDate
text_bodyString | The update's text body. | 
updated_atDate | The date the update was last edited. | 
viewers[Watcher!]! | The update's viewers. | mediumString!userUseruser_idID!

# Mutations

Required scope: updates:write

## Create an update

The create_update mutation allows you to add an update to an item via the API. You can also specify what fields to query back from the new update when you run the mutation.

GraphQLJavaScript
```
mutation {
  create_update (item_id: 1234567890, body: "This update will be added to the item") {
    id
  }
}
```

```
let query = "mutation {create_update (item_id: 1234567890, body: \"This update will be added to the item\") { id }}";

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

You can use the following argument(s) to define the new update's characteristics.

Argument | Description
--- | ---
bodyString! | The update's text.
item_idID | The item's unique identifier.
parent_idID | The parent update's unique identifier. This can be used to create a reply to an update.

## Like an update

The like_update mutation allows you to like an update via the API. You can also specify what fields to query back from the update when you run the mutation.

GraphQLJavaScript
```
mutation {
  like_update (update_id: 1234567890) {
    id
  }
}
```

```
let query = "mutation { like_update (update_id: 1234567890) { id }}";

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

You can use the following argument(s) to define which update to like.

Argument | Description
--- | ---
update_idID | The unique identifier of the update to like.

## Unlike an update

The unlike_update mutation allows you to unlike an update via the API. You can also specify what fields to query back from the update when you run the mutation.

GraphQLJavaScript
```
mutation {
  unlike_an_update (update_id: 1234567890) {
    creator_id
    item_id
  }
}
```

```
let query = "mutation { unlike_update (update_id: 1234567890) { creator_id item_id }}";

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

You can use the following argument(s) to define which update to pin.

Argument | Description
--- | ---
update_idID! | The unique identifier of the update to unlike.

## Edit an update

The edit_update mutation allows you to edit an update via the API. You can also specify what fields to query back from the update when you run the mutation.

GraphQLJavaScript
```
mutation {
  edit_update (id: 1234567890, body: "The updated text!") {
    creator_id
    item_id
  }
}
```

```
let query = "mutation { edit_update (id: 1234567890, body: \"The updated text!\" ) { creator_id item_id }}";

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

You can use the following argument(s) to define which update to pin.

Argument | Description
--- | ---
bodyString! | The update's new text.
idID! | The unique identifier of the update to edit.

## Pin an update

The pin_to_top mutation allows you to pin an update to the top of an item via the API. You can also specify what fields to query back from the update when you run the mutation.

GraphQLJavaScript
```
mutation {
  pin_to_top (id: 1234567890, item_id: 9876543210) {
    creator_id
    body
  }
}
```

```
let query = "mutation { pin_to_top (id: 1234567890, item_id: 9876543210) { creator_id body }}";

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

You can use the following argument(s) to define which update to pin.

Argument | Description
--- | ---
idID! | The unique identifier of the update to pin.
item_idID | The item's unique identifier.

## Unpin an update

The unpin_from_top mutation allows you to unpin an update from the top of an item via the API. You can also specify what fields to query back from the update when you run the mutation.

GraphQLJavaScript
```
mutation {
  unpin_from_top (id: 1234567890, item_id: 9876543210) {
    creator_id
    body
  }
}
```

```
let query = "mutation { unpin_from_top (id: 1234567890, item_id: 9876543210) { creator_id body }}";

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

You can use the following argument(s) to define which update to unpin.

Argument | Description
--- | ---
idID! | The unique identifier of the update to unpin.
item_idID | The item's unique identifier.

## Clear an item's updates

The clear_item_updates mutation allows you to clear all updates on a specific item, including replies and likes, via the API. You can also specify what fields to query back from the update when you run the mutation.

GraphQLJavaScript
```
mutation {
  clear_item_updates (item_id: 1234567890) {
    id
  }
}
```

```
let query = "mutation { clear_item_updates (item_id: 1234567890) { id }}";

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

You can use the following argument(s) to define which item's updates to clear.

Arguments | Description
--- | ---
item_idID! | The item's unique identifier.

## Delete an update

The delete_update mutation allows you to delete an item's update via the API. You can also specify what fields to query back from the update when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_update (id: 1234567890) {
    id
  }
}
```

```
let query = "mutation { delete_update (id: 1234567890) { id }}";

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

You can use the following argument(s) to define which updates to delete.

Argument | Description
--- | ---
idID! | The update's unique identifier.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
