---

title: Timeline_item
source: https://developer.monday.com/api-reference/reference/timeline-item-ea
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, create, and delete timeline items from the Email &amp; Activities app using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Timeline item

Learn how to read, create, and delete timeline items from the Email & Activities app using the platform API

The Emails & Activities app (E&A) is a useful tool that enables monday.com CRM customers to manage client communication in one centralized location. Each contact is logged and tracked in the app's timeline for easy access to important details and updates.

# Queries

- Returns an array containing metadata about newly created items in the E&A timeline
- Can only be queried directly at the root

GraphQL
```
query {
  timeline_item (id: 1234567890) {
    board {
      id
    }
    item {
      name
    }
    id
    user {
      id
      name
    }
    title
    type
    content
    created_at
  }
}
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your timeline_item query.

Argument | Description
--- | ---
idID! | The unique identifier of the timeline item to return.

## Fields

You can use the following field(s) to specify what information your timeline_item query will return.

Field | Description
--- | ---
boardBoard | The board that the timeline item is on.
contentString | The timeline items's content.
created_atDate! | The timeline item's creation date.
custom_activity_idString | The unique identifier of the timeline item'scustom activity.
idID | The timeline item's unique identifier.
itemItem | The item that the timeline item is on.
titleString | The title of the timeline item.
typeString | The type of timeline item. Always returns"activity".
userUser | The user who created the timeline item.

# Mutations

## Create a timeline item

The create_timeline_item mutation allows you to create a new timeline item in the E&A app via the API. You can also specify what fields to query back from the new item when you run the mutation. Please note that currently, this is the only way you can retrieve a timeline item's ID. It is not possible to retrieve it from the UI.

## 🚧

Timeline items created via the API won't trigger automations that run when a new E&A timeline item is created.

GraphQL
```
mutation {
	create_timeline_item (
  item_id: 9876543210,
  custom_activity_id: "8ca12626-7aeb-3ca7-7z1a-8ebdda488cd2",
  title: "Migrated Email",
  summary: "internal company email",
  content: "From:
[email protected]
<br> To:
[email protected]
[Asi Monday],
[email protected]
[Yoni Monday] <br> Subject: Deploy our first alpha version <br><br>Hey guys, <br>We are ready to deploy our first alpha version and enable<br>our clients to migrate into E&A!<br><br>Best regards,<br> Saar",
	timestamp: "2024-06-06T18:00:30Z",
  time_range: {
   start_timestamp: "2024-05-06T18:00:30Z", 
   end_timestamp: "2024-05-06T19:00:30Z"
  }
 ) {
  id
 }
}
```

### Arguments

You can use the following argument(s) to define the new timeline item's characteristics.

Argument | Description | Supported fields
--- | --- | ---
contentString | The new timeline item's content. | 
custom_activity_idString! | The ID of the new timeline item'scustom activity. | 
item_idID! | The ID of the item to create the new timeline item on. | 
locationString | The location to add to the new timeline item.Please notethat this input isn't verified as alocation. | 
phoneString | The phone number to add to the new timeline item.Please notethat this input isn't verified as aphone number. | 
summaryString | The new timeline item's summary. The maximum is 255 characters. | 
timestampISO8601DateTime! | The new timeline item's creation time. | 
time_rangeTimelineItemTimeRange | The start and end time of the new timeline item. | end_timestampISO8601DateTime!start_timestampISO8601DateTime!
titleString! | The new timeline item's title. | 
urlString | The URL to add to the new timeline item. | 

## Delete a timeline item

The delete_timeline_item mutation allows you to delete a timeline item in the E&A app via the API. You can also specify what fields to query back from the deleted item when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_timeline_item (id: 1234567890) {
    id
  }
}
```

```

```

### Arguments

You can use the following argument to define which timeline item to delete.

Argument | Description
--- | ---
idID! | The unique identifier of the timeline item to delete.
